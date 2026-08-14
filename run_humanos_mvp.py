import os
import sys
import argparse
import json
import shutil
from dotenv import load_dotenv
load_dotenv()

from openrouter_client import OpenRouterClient
from hermoso_core import HermosoCore
from borges import BorgesAgent
from veritas import VeritasAgent
from gabo import GaboAgent
from moore import MooreAgent
from asset_collector import AssetCollector
from mark import MarkAgent
from leonardo import LeonardoAgent
from scripts.youtube_searcher import search_episode_videos
from humanizer_agent import HumanizerAgent

def stripMarkdownTitle(text: str) -> str:
    """Elimina títulos markdown como '# Guion Corto: Name' del inicio del texto."""
    lines = text.splitlines()
    clean_lines = []
    for line in lines:
        if line.strip().startswith("#"):
            continue
        clean_lines.append(line)
    return "\n".join(clean_lines).strip()

def run_recovery_write(character_name: str, ep_path: str, client: OpenRouterClient, hermoso: HermosoCore, preflight: dict) -> bool:
    """Panel-compatible recovery write; never reads legacy 01_RESEARCH."""
    from recovery_pipeline import recovery_inputs, RECOVERY_DIR
    research_json, timeline_json, approved_claims_json, creative_lock, evidence_bridge = recovery_inputs(preflight)
    if not preflight.get("legacy_research_excluded") or preflight.get("research_source") != RECOVERY_DIR:
        raise RuntimeError("recovery isolation receipt missing")
    os.makedirs(os.path.join(ep_path, "02_SCRIPT"), exist_ok=True)
    script_dir = os.path.join(ep_path, "02_SCRIPT")
    revision_dir = os.path.join(script_dir, "revisions", "gate_3a_first_draft")
    if os.path.exists(os.path.join(script_dir, "scripts_raw.json")) and not os.path.exists(revision_dir):
        os.makedirs(revision_dir, exist_ok=True)
        for filename in os.listdir(script_dir):
            source = os.path.join(script_dir, filename)
            if os.path.isfile(source):
                shutil.copy2(source, os.path.join(revision_dir, filename))
    creative_lock = {**creative_lock, "rewrite_mode": "GATE_3B_STRUCTURAL"}
    print(f"[Recovery] Fuente canónica: {RECOVERY_DIR}; 01_RESEARCH excluido.")
    hermoso.write_json(os.path.join(ep_path, "01_RESEARCH_RECOVERY", "recovery_dispatch_trace.json"), {
        "episode_id": preflight["config"].get("episode_id"),
        "input_mode": "recovery",
        "research_source": RECOVERY_DIR,
        "legacy_research_excluded": True,
        "creative_lock_loaded": creative_lock.get("status") == "LOCKED",
        "human_evidence_loaded": evidence_bridge.get("evidence_class") == "HUMAN_VERIFIED_PRIMARY_SOURCE",
        "manifest_required_files": preflight["manifest"].get("required_files", []),
        "agents_allowed_by_this_dispatch": ["Gabo", "Humanizer"],
        "agents_forbidden_in_gate_2f": ["Borges", "Veritas", "Moore"],
    })
    gabo = GaboAgent(client)
    scripts_json, script_short_md, script_long_md, newsletter_md, twitter_thread_md, gabo_logs = gabo.execute_narrative(
        character_name, research_json, timeline_json, approved_claims_json,
        editorial_context=creative_lock, human_evidence_context=evidence_bridge
    )
    hermoso.write_json(os.path.join(ep_path, "02_SCRIPT", "scripts_raw.json"), scripts_json)
    hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "script_short_raw.md"), script_short_md)
    hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "script_long_raw.md"), script_long_md)
    hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "newsletter_raw.md"), newsletter_md)
    hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "twitter_thread_raw.md"), twitter_thread_md)
    hermoso.log_agent_run(ep_path, "Gabo", "success", gabo_logs)
    humanizer = HumanizerAgent(client)
    scripts_json, script_short_md, script_long_md, newsletter_md, twitter_thread_md, humanizer_logs = humanizer.execute_humanization(
        character_name, scripts_json, editorial_context=creative_lock, human_evidence_context=evidence_bridge
    )
    hermoso.write_json(os.path.join(ep_path, "02_SCRIPT", "scripts.json"), scripts_json)
    hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "script_short.md"), script_short_md)
    hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "script_long.md"), script_long_md)
    hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "newsletter.md"), newsletter_md)
    hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "twitter_thread.md"), twitter_thread_md)
    hermoso.log_agent_run(ep_path, "Humanizer", "success", humanizer_logs)
    hermoso.update_status_local(ep_path, "script_pending_review")
    state_path = os.path.join(ep_path, "pipeline_state.json")
    state = {}
    if os.path.exists(state_path):
        with open(state_path, "r", encoding="utf-8") as stream:
            state = json.load(stream)
    state.update({
        "episode_id": preflight["config"].get("episode_id"),
        "status": "script_pending_review",
        "input_mode": "recovery",
        "research_source": RECOVERY_DIR,
        "forbidden_sources": ["01_RESEARCH"],
        "gate_2d": "PASS",
        "execution_authorized": bool(preflight["config"].get("execution_authorized")),
        "authorization_scope": preflight["config"].get("authorization_scope", "GATE_3_WRITE_ONLY"),
        "script_source": "recovery_only",
        "legacy_research_excluded": True,
    })
    with open(state_path, "w", encoding="utf-8") as stream:
        json.dump(state, stream, ensure_ascii=False, indent=2)
    return True

def run_mvp(character_name: str, episode_focus: str, themes: list, episode_num: int = 1, stage: str = "all"):
    print("="*60)
    print(f"INICIANDO PIPELINE HUMANOS MVP EPISODIO {episode_num}: {character_name} [Etapa: {stage.upper()}]")
    print("="*60)

    # 1. Inicializar cliente API, Hermoso Core y Mark Agent
    client = OpenRouterClient()
    hermoso = HermosoCore()
    mark = MarkAgent()

    # Determinar ruta del episodio
    char_folder_name = character_name.strip().replace(" ", "_")
    ep_path = os.path.join("personajes", char_folder_name, f"EP{episode_num:04d}_{char_folder_name}")

    recovery_config = os.path.join(ep_path, "episode_config.json")
    if stage == "write" and os.path.exists(recovery_config):
        from recovery_pipeline import validate_recovery_episode, recovery_inputs
        preflight = validate_recovery_episode(ep_path)
        _, _, _, creative_lock, evidence_bridge = recovery_inputs(preflight)
        print(f"[Recovery] research_source={preflight['research_source']}")
        print("[Recovery] forbidden_source=01_RESEARCH")
        print(f"[Recovery] creative_lock_loaded={creative_lock.get('status') == 'LOCKED'}")
        print(f"[Recovery] human_evidence_bridge_loaded={evidence_bridge.get('evidence_class') == 'HUMAN_VERIFIED_PRIMARY_SOURCE'}")
        print(f"[Recovery] execution_authorized={bool(preflight['config'].get('execution_authorized'))}")
        if not preflight["config"].get("execution_authorized"):
            print("[Recovery] Preflight PASS; ejecución no autorizada. Gabo/Humanizer no ejecutados.")
            return False
        return run_recovery_write(character_name, ep_path, client, hermoso, preflight)

    if stage in ["write", "all"]:
        # 2. Hermoso Core: Crear estructura local (10 carpetas y biblioteca global de medios)
        print("[Hermoso Core] Creando directorios locales para el episodio (10 carpetas)...")
        ep_path = hermoso.create_episode_structure(character_name, episode_num=episode_num)
        hermoso.update_status_local(ep_path, "research_pending")
        print(f"[Hermoso Core] Directorios creados en: {ep_path}")

        # 3. Borges: Investigación y clasificación
        hermoso.update_status_local(ep_path, "research_in_progress")
        borges = BorgesAgent(client)
        research_json, timeline_json, sources_md, asset_manifest, claims_json, sources_json, dossier_md, borges_logs = borges.execute_research(
            character_name, episode_focus, themes
        )
        
        # Ingestión y descarga automática de assets verificados de Wikimedia Commons
        print("[Asset Collector] Iniciando recopilación e ingestión de assets desde Wikimedia Commons...")
        collector = AssetCollector(ep_path)
        asset_manifest = collector.collect_all_assets(asset_manifest)
        
        # Persistir outputs de Borges en 01_RESEARCH
        hermoso.write_json(os.path.join(ep_path, "01_RESEARCH", "research.json"), research_json)
        hermoso.write_json(os.path.join(ep_path, "01_RESEARCH", "timeline.json"), timeline_json)
        hermoso.write_markdown(os.path.join(ep_path, "01_RESEARCH", "sources.md"), sources_md)
        hermoso.write_markdown(os.path.join(ep_path, "01_RESEARCH", "Editorial_Dossier.md"), dossier_md)
        hermoso.write_json(os.path.join(ep_path, "01_RESEARCH", "asset_manifest.json"), asset_manifest)
        hermoso.write_json(os.path.join(ep_path, "01_RESEARCH", "claims.json"), claims_json)
        hermoso.write_json(os.path.join(ep_path, "01_RESEARCH", "sources.json"), sources_json)
        hermoso.log_agent_run(ep_path, "Borges", "success", borges_logs)

        # 3.5 Veritas: Fact checking y Quality Gate inicial
        hermoso.update_status_local(ep_path, "verification_in_progress")
        veritas = VeritasAgent(client)
        fact_check_json, approved_claims_json, veritas_logs = veritas.execute_verification(
            character_name, claims_json, research_json, sources_json
        )

        # Persistir outputs de Veritas en 01_RESEARCH
        hermoso.write_json(os.path.join(ep_path, "01_RESEARCH", "fact_check.json"), fact_check_json)
        hermoso.write_json(os.path.join(ep_path, "01_RESEARCH", "approved_claims.json"), approved_claims_json)
        hermoso.log_agent_run(ep_path, "Veritas", "success", veritas_logs)

        # Regla: Si score es menor a 80, vuelve a investigación
        overall_score = fact_check_json.get("overall_confidence_score", 0)
        status_global = fact_check_json.get("status", "REJECTED")

        if overall_score < 80 or status_global in ["NEEDS_REVIEW", "REJECTED"]:
            print(f"[Veritas - Quality Gate] RECHAZADO: Score global de confianza ({overall_score}) es menor a 80 o estado es {status_global}.")
            print("[Hermoso Core] Devolviendo episodio a estado 'needs_research'.")
            hermoso.update_status_local(ep_path, "needs_research")
            return False

        hermoso.update_status_local(ep_path, "research_done")

        # 4. Gabo: Redacción narrativa multiformato
        gabo = GaboAgent(client)
        scripts_json, script_short_md, script_long_md, newsletter_md, twitter_thread_md, gabo_logs = gabo.execute_narrative(
            character_name, research_json, timeline_json, approved_claims_json
        )

        # Persistir outputs de Gabo crudos (raw)
        hermoso.write_json(os.path.join(ep_path, "02_SCRIPT", "scripts_raw.json"), scripts_json)
        hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "script_short_raw.md"), script_short_md)
        hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "script_long_raw.md"), script_long_md)
        hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "newsletter_raw.md"), newsletter_md)
        hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "twitter_thread_raw.md"), twitter_thread_md)
        hermoso.log_agent_run(ep_path, "Gabo", "success", gabo_logs)

        # 4.5. Humanizer: Pulido de textos y alineación de voz
        humanizer = HumanizerAgent(client)
        scripts_json, script_short_md, script_long_md, newsletter_md, twitter_thread_md, humanizer_logs = humanizer.execute_humanization(
            character_name, scripts_json
        )

        # Persistir outputs humanizados finales en 02_SCRIPT
        hermoso.write_json(os.path.join(ep_path, "02_SCRIPT", "scripts.json"), scripts_json)
        hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "script_short.md"), script_short_md)
        hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "script_long.md"), script_long_md)
        hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "newsletter.md"), newsletter_md)
        hermoso.write_markdown(os.path.join(ep_path, "02_SCRIPT", "twitter_thread.md"), twitter_thread_md)
        hermoso.log_agent_run(ep_path, "Humanizer", "success", humanizer_logs)
        
        hermoso.update_status_local(ep_path, "script_pending_review")
        print(f"\n[Fase Escritura Completada] Deteniendo pipeline para revisión manual del editor.")
        print(f"Edita los guiones en: {os.path.join(ep_path, '02_SCRIPT')}")
        
        if stage == "write":
            try:
                print(f"[YouTube Searcher] Buscando fuentes de video iniciales en YouTube para: {character_name}...")
                from scripts.youtube_searcher import search_youtube_scraping
                query = f"{character_name} documentary biography"
                videos = search_youtube_scraping(query, max_results=5)
                if videos:
                    sources_path = os.path.join(ep_path, "01_RESEARCH", "sources.md")
                    if os.path.exists(sources_path):
                        with open(sources_path, "r", encoding="utf-8") as f:
                            content = f.read()
                        
                        yt_markdown = "\n\n## YouTube Video Reference Sources (Scraped)\n"
                        for v in videos:
                            yt_markdown += f"*   **[{v['title']}]({v['url']})** - Canal: {v['channel']} (Duración: {v['duration']})\n"
                        
                        with open(sources_path, "w", encoding="utf-8") as f:
                            f.write(content + yt_markdown)
                        print(f"[YouTube Searcher] {len(videos)} fuentes de video añadidas a sources.md.")
            except Exception as e:
                print(f"[ERROR] Error al añadir fuentes de YouTube: {e}")
            return True

    # ------------------------------------------------------------------
    # FASE PRODUCCIÓN (stage == produce o continuación tras stage == all)
    # ------------------------------------------------------------------
    if stage == "produce" or stage == "all":
        print(f"\n[Fase Producción] Iniciando validación y ensamblado físico...")
        
        # Validar existencia de datos en disco si entramos directo a produce
        research_file = os.path.join(ep_path, "01_RESEARCH", "research.json")
        approved_claims_file = os.path.join(ep_path, "01_RESEARCH", "approved_claims.json")
        scripts_file = os.path.join(ep_path, "02_SCRIPT", "scripts.json")
        manifest_file = os.path.join(ep_path, "01_RESEARCH", "asset_manifest.json")
        dossier_file = os.path.join(ep_path, "01_RESEARCH", "Editorial_Dossier.md")
        
        if not (os.path.exists(research_file) and os.path.exists(approved_claims_file) and os.path.exists(scripts_file)):
            print(f"[ERROR] No se encontraron archivos de la etapa previa. Ejecuta primero `--stage write`.")
            return False
            
        with open(research_file, "r", encoding="utf-8") as f:
            research_json = json.load(f)
        with open(approved_claims_file, "r", encoding="utf-8") as f:
            approved_claims_json = json.load(f)
        with open(scripts_file, "r", encoding="utf-8") as f:
            scripts_json = json.load(f)
        with open(manifest_file, "r", encoding="utf-8") as f:
            asset_manifest = json.load(f)

        dossier_md = ""
        if os.path.exists(dossier_file):
            with open(dossier_file, "r", encoding="utf-8") as f:
                dossier_md = f.read()

        # 4.5 Veritas: Quality Gate Final del Guion Editado
        veritas = VeritasAgent(client)
        print("[Veritas] Iniciando auditoría final del guion modificado manualmente...")
        
        # Leer el contenido real de script_short.md
        script_short_real_path = os.path.join(ep_path, "02_SCRIPT", "script_short.md")
        if os.path.exists(script_short_real_path):
            with open(script_short_real_path, "r", encoding="utf-8") as sf:
                raw_script_content = sf.read()
                # Limpiar el título markdown si existe
                script_short_clean = stripMarkdownTitle(raw_script_content)
                scripts_json["script_short"] = script_short_clean
                
                # Forzar a recrear una estructura de escenas dinámicas y fluidas agrupando oraciones
                import re
                raw_sentences = [s.strip() for s in re.split(r'(?<=[.!?]) +', script_short_clean) if s.strip()]
                
                grouped_texts = []
                current_chunk = []
                current_count = 0
                
                for s in raw_sentences:
                    words = s.split()
                    # Si añadir la oración excede 22 palabras y ya tenemos texto acumulado, consolidamos el bloque anterior
                    if current_count + len(words) > 22 and current_chunk:
                        grouped_texts.append(" ".join(current_chunk))
                        current_chunk = [s]
                        current_count = len(words)
                    else:
                        current_chunk.append(s)
                        current_count += len(words)
                        
                if current_chunk:
                    grouped_texts.append(" ".join(current_chunk))
                
                new_scenes = []
                for idx, text_block in enumerate(grouped_texts, 1):
                    new_scenes.append({
                        "scene": idx,
                        "duration": max(4.0, min(10.0, round(len(text_block.split()) * 0.38, 1))),
                        "voiceover": text_block,
                        "visual_intent": f"Ilustrar visualmente: {text_block[:50]}..."
                    })
                scripts_json["scenes"] = new_scenes

        audit_json, veritas_logs = veritas.verify_manual_script(
            character_name, scripts_json, research_json, approved_claims_json
        )
        hermoso.log_agent_run(ep_path, "Veritas_Manual_Audit", "success", veritas_logs)
        
        accuracy_score = audit_json.get("overall_accuracy_score", 0)
        status_global = audit_json.get("status", "REJECTED")
        
        if accuracy_score < 80 or status_global in ["NEEDS_REVIEW", "REJECTED"]:
            print(f"\n[Veritas - Quality Gate Final] RECHAZADO: Score de veracidad ({accuracy_score}) es menor a 80 o estado es {status_global}.")
            print(f"Problemas detectados: {json.dumps(audit_json.get('detected_issues', []), ensure_ascii=False, indent=2)}")
            print("[Hermoso Core] Devolviendo episodio a estado 'script_pending_review' para correcciones.")
            hermoso.update_status_local(ep_path, "script_pending_review")
            return False
            
        print(f"[Veritas - Quality Gate Final] APROBADO: Score de veracidad {accuracy_score}%. Avanzando a producción...")

        # 5. Curie: Ingestión, escaneo e indexación física de assets
        print("[Curie] Escaneando assets físicos y actualizando registro en asset_registry.json...")
        collector = AssetCollector(ep_path)
        registry_data = collector.registry
        print(f"[Curie] Indexación física terminada. Assets disponibles: {len(registry_data)}")

        # 5.5 Moore: Storyboard y gaps de producción
        print("[Moore] Iniciando cruce de assets y diseño de producción...")
        moore = MooreAgent(client)
        storyboard_json, asset_gaps_json, shotlist_md, editing_notes_md, production_package_json, asset_shotlist_md, moore_logs = moore.execute_production(
            character_name, asset_manifest, registry_data, scripts_json, approved_claims_json, dossier_markdown=dossier_md
        )

        # Persistir outputs de Moore en 03_STORYBOARD
        hermoso.write_json(os.path.join(ep_path, "03_STORYBOARD", "storyboard.json"), storyboard_json)
        hermoso.write_json(os.path.join(ep_path, "03_STORYBOARD", "asset_gaps.json"), asset_gaps_json)
        hermoso.write_markdown(os.path.join(ep_path, "03_STORYBOARD", "shotlist.md"), shotlist_md)
        hermoso.write_markdown(os.path.join(ep_path, "03_STORYBOARD", "editing_notes.md"), editing_notes_md)
        hermoso.write_markdown(os.path.join(ep_path, "03_STORYBOARD", "asset_shotlist.md"), asset_shotlist_md)
        hermoso.write_json(os.path.join(ep_path, "03_STORYBOARD", "production_package.json"), production_package_json)
        hermoso.log_agent_run(ep_path, "Moore", "success", moore_logs)

        # 5.6 Búsqueda automática de videos candidatos en YouTube basados en el Shot List
        try:
            search_episode_videos(ep_path)
        except Exception as e:
            print(f"[ERROR] Error al buscar candidatos de YouTube: {e}")

        # 5.7 Ingestión y recolección automatizada de Assets
        try:
            from scripts.automated_asset_gatherer import run_gatherer
            run_gatherer(ep_path)
        except Exception as e:
            print(f"[ERROR] Error al recolectar assets automáticamente: {e}")


        # 5.8 Leonardo: Dirección de Arte y Branding
        print("[Leonardo] Diseñando la dirección de arte y especificaciones visuales...")
        leonardo = LeonardoAgent(client)
        branding_spec_json, branding_spec_md, leonardo_logs = leonardo.execute_branding(
            character_name, scripts_json, storyboard_json, approved_claims_json
        )

        # Persistir outputs de Leonardo en 04_IMAGES
        hermoso.write_json(os.path.join(ep_path, "04_IMAGES", "branding_spec.json"), branding_spec_json)
        hermoso.write_markdown(os.path.join(ep_path, "04_IMAGES", "branding_spec.md"), branding_spec_md)
        hermoso.log_agent_run(ep_path, "Leonardo", "success", leonardo_logs)
        
        # 5.9 Gate de derechos: audita la procedencia de TODO el material.
        #
        # Va aqui, despues de que todos los agentes terminaron de traer y
        # generar assets, y antes del paquete de produccion. No usa LLM: una
        # licencia es un dato categorico y meter un modelo a opinar sobre
        # derechos agregaria alucinacion a una decision legal.
        #
        # Rechaza si hay material inusable. Solo avisa si hay material sin
        # verificar o sin registrar, porque bloquear el pipeline por eso
        # frenaria episodios que solo necesitan que alguien mire una ficha.
        try:
            from derechos import auditar_episodio, imprimir
            print("[Derechos] Auditando procedencia y licencias del material...")
            auditoria = auditar_episodio(ep_path, monetizado=False)
            imprimir(auditoria)
            hermoso.write_json(
                os.path.join(ep_path, "01_RESEARCH", "auditoria_derechos.json"),
                auditoria)
            hermoso.log_agent_run(
                ep_path, "Derechos",
                "success" if auditoria["estado"] != "RECHAZADO" else "blocked",
                f"Veredicto {auditoria['estado']} ({auditoria['puntaje_limpio']}% limpio). "
                f"verde {auditoria['conteo']['verde']}, ambar {auditoria['conteo']['ambar']}, "
                f"rojo {auditoria['conteo']['rojo']}, sin registrar {len(auditoria['huerfanos'])}.")

            if auditoria["estado"] == "RECHAZADO":
                print("[Derechos - Quality Gate] RECHAZADO: hay material que no se puede usar.")
                print("[Hermoso Core] Episodio detenido en 'assets_pending_rights'.")
                hermoso.update_status_local(ep_path, "assets_pending_rights")
                return
        except Exception as e:
            print(f"[ERROR] El gate de derechos no pudo correr: {e}")

        # 6. Generar ASSET_COLLECTION_REPORT.md en 01_RESEARCH
        print("[Asset Collector] Generando reporte de colección e ingesta...")
        total_assets = len(asset_manifest.get("assets", []))
        downloaded = sum(1 for a in asset_manifest.get("assets", []) if a.get("downloaded"))
        failed_downloads = sum(1 for a in asset_manifest.get("assets", []) if "wikimedia.org" in a.get("url", "") and not a.get("downloaded"))
        reference_only = sum(1 for a in asset_manifest.get("assets", []) if "wikimedia.org" not in a.get("url", ""))
        
        failed_list_str = "- Ninguna descarga fallida detectada"
        if failed_downloads > 0:
            failed_items = [f"- {a['title']} ({a['url']})" for a in asset_manifest.get("assets", []) if "wikimedia.org" in a.get("url", "") and not a.get("downloaded")]
            failed_list_str = "\n".join(failed_items)
            
        manual_search_items = [f"- Escena {gap['scene']}: Buscar \"{gap['missing_asset']}\". Solución: {gap['suggested_solution']}" for gap in asset_gaps_json]
        manual_search_str = "\n".join(manual_search_items)
        
        report_content = f"""# Reporte de Recopilación de Assets (ASSET_COLLECTION_REPORT)

## Métricas del Manifiesto
- **Total de assets en manifiesto:** {total_assets}
- **Descargados con éxito:** {downloaded}
- **Descargas fallidas (Wikimedia):** {failed_downloads}
- **Assets de sólo referencia (No descargables automáticamente):** {reference_only}
- **Assets críticos faltantes (Gaps de Moore):** {len(asset_gaps_json)}

## Detalle de Descargas Fallidas
{failed_list_str}

## Acciones de Búsqueda Manual Recomendadas
{manual_search_str}
"""
        hermoso.write_markdown(os.path.join(ep_path, "01_RESEARCH", "ASSET_COLLECTION_REPORT.md"), report_content)
        
        # Estado final del MVP
        hermoso.update_status_local(ep_path, "storyboard_done")

        # 6.5 Generar paquete de distribución en 11_DIST con Mark
        mark.generate_distribution_package(
            ep_path=ep_path,
            character_name=character_name,
            scripts_data=scripts_json,
            client=client
        )

        # 7. Registrar la FICHA del episodio (sin métricas inventadas).
        #    Las métricas reales se cargan desde el panel a las 48h (/api/save-metrics).
        #    Nunca simular audiencia: contamina metrics_history.json y el aprendizaje
        #    de Mark, Talese y Mr. You.
        duration = production_package_json.get("estimated_voiceover_duration", 75.0)
        hook_text = scripts_json.get("script_short", "")[:120]

        mark.register_episode(
            character_name=character_name,
            episode_id=f"EP{episode_num:04d}",
            duration_seconds=duration,
            hook_text=hook_text,
            themes=themes
        )

        print("="*60)
        print(f"PIPELINE DE PRODUCCIÓN COMPLETADO CON ÉXITO PARA {character_name}")
        print(f"Todos los entregables persisten en: {ep_path}")
        print("="*60)
        return True

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Correr pipeline MVP local de HUMANOS.")
    parser.add_argument("--character", type=str, default="all", help="Nombre del personaje ('all' para correr lote fundacional)")
    parser.add_argument("--focus", type=str, default=None, help="Enfoque del episodio (si se especifica un personaje)")
    parser.add_argument("--themes", nargs="+", default=None, help="Temas asociados (si se especifica un personaje)")
    parser.add_argument("--stage", type=str, choices=["write", "produce", "all"], default="all", help="Etapa del pipeline a ejecutar")
    parser.add_argument("--episode", type=int, default=1, help="Número de episodio para el personaje")

    args = parser.parse_args()

    # Validar variable de entorno obligatoria
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("[ERROR] La variable de entorno OPENROUTER_API_KEY no está configurada.")
        print("Configúrala antes de ejecutar este script.")
        sys.exit(1)

    if args.character.lower() == "all":
        # Ejecutar lote fundacional completo
        lote = [
            {
                "name": "Jan Koum",
                "focus": "De la pobreza extrema en Ucrania a vender WhatsApp por 19 mil millones de dólares",
                "themes": ["pobreza", "migración", "obsesión", "privacidad", "resiliencia"],
                "ep": 1
            },
            {
                "name": "Ehud Shabtai",
                "focus": "El programador de Israel que desafió a los gigantes del GPS creando mapas colaborativos con la comunidad",
                "themes": ["GPS", "comunidad", "innovación", "colaboración", "geolocalización"],
                "ep": 2
            },
            {
                "name": "Adidas vs Puma",
                "focus": "La guerra familiar de dos hermanos que dividió una ciudad alemana y parió dos gigantes mundiales del deporte",
                "themes": ["conflicto", "negocios", "guerra", "rivalidad", "deporte"],
                "ep": 3
            }
        ]
        
        print("INICIANDO EJECUCIÓN DEL LOTE FUNDACIONAL DE HUMANOS...")
        success_count = 0
        for item in lote:
            if run_mvp(item["name"], item["focus"], item["themes"], episode_num=item["ep"], stage=args.stage):
                success_count += 1
                
        # Generar dashboard de Mark
        mark = MarkAgent()
        mark.generate_conceptual_dashboard()
        print(f"\nPROCESAMIENTO COMPLETADO. {success_count}/{len(lote)} episodios procesados con éxito.")
        print("Dashboard de Mark generado en: personajes/PRODUCTION_METRICS_DASHBOARD.md")
    else:
        # Correr personaje individual
        focus = args.focus or "Enfoque general del personaje"
        themes = args.themes or ["historia", "construcción"]
        run_mvp(args.character, focus, themes, episode_num=args.episode, stage=args.stage)
        # Generar dashboard de Mark
        mark = MarkAgent()
        mark.generate_conceptual_dashboard()
