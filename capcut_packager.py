import os
import re
import json
import hashlib
import urllib.request
import urllib.parse
from hermoso_core import HermosoCore

class CapCutPackager:
    def __init__(self, base_dir="C:/Users/Jota Ochoa/Antigravity/02_Projects/humanos"):
        self.base_dir = base_dir
        self.hermoso = HermosoCore(base_dir)
        self.packs_dir = os.path.join(base_dir, "CapCut_Packs")
        os.makedirs(self.packs_dir, exist_ok=True)

    def generate_capcut_notes(self, char_folder, ep_folder, storyboard, gaps, prod_package):
        notes = f"""# Guía de Edición en CapCut - {char_folder}

## Estilo Visual y Ritmo
- **Estilo General:** {prod_package.get('visual_style', 'Color gradado cálido, grano de película analógica')}
- **Estilo de Música:** {prod_package.get('music_style', 'Tensión minimalista')}
- **Horas de Edición Estimadas:** {prod_package.get('estimated_edit_time_hours', 12)} horas

## Estructura de Edición de Escenas:
"""
        for s in storyboard:
            notes += f"""
### Escena {s['scene']} (Duración: {s['duration']}s)
- **Locución (Voiceover):** "{s['voiceover']}"
- **Efecto de Transición/Cámara:** {s.get('effect', 'cut')}
- **Texto en Pantalla (Caption):** "{s.get('caption', '')}"
- **Estado de Asset:** {s.get('asset_status', 'missing').upper()}
- **Estrategia Fallback (Visual):** {s.get('fallback_strategy', '')}
"""
            if s.get('gap_id'):
                notes += f"- **ID de Vacío Crítico (Gap):** {s.get('gap_id')}\n"
        return notes

    def process_episode(self, character_name):
        char_folder = self.hermoso.sanitize_name(character_name)
        char_path = os.path.join(self.base_dir, "PERSONAJES", char_folder)
        if not os.path.exists(char_path):
            print(f"[ERROR] No existe directorio de personaje para {character_name}")
            return None
            
        ep_subfolder = None
        for item in sorted(os.listdir(char_path), reverse=True):
            if item.startswith("EP") and os.path.isdir(os.path.join(char_path, item)):
                ep_subfolder = item
                break
                
        if not ep_subfolder:
            print(f"[ERROR] No se encontró carpeta de episodio para {character_name}")
            return None
            
        ep_dir = os.path.join(char_path, ep_subfolder)
        
        # Paths de archivos fuente
        research_file = os.path.join(ep_dir, "01_RESEARCH", "research.json")
        manifest_file = os.path.join(ep_dir, "01_RESEARCH", "asset_manifest.json")
        registry_file = os.path.join(ep_dir, "asset_registry.json")
        scripts_file = os.path.join(ep_dir, "02_SCRIPT", "scripts.json")
        storyboard_file = os.path.join(ep_dir, "03_STORYBOARD", "storyboard.json")
        gaps_file = os.path.join(ep_dir, "03_STORYBOARD", "asset_gaps.json")
        package_file = os.path.join(ep_dir, "03_STORYBOARD", "production_package.json")
        
        if not os.path.exists(storyboard_file):
            print(f"[ERROR] No existe storyboard para {character_name}")
            return None

        # Cargar archivos de origen con codificación UTF-8 explícita
        with open(research_file, "r", encoding="utf-8") as f:
            research = json.load(f)
        with open(manifest_file, "r", encoding="utf-8") as f:
            manifest = json.load(f)
        try:
            with open(registry_file, "r", encoding="utf-8") as f:
                registry = json.load(f)
        except:
            registry = []
        with open(scripts_file, "r", encoding="utf-8") as f:
            scripts = json.load(f)
        with open(storyboard_file, "r", encoding="utf-8") as f:
            storyboard = json.load(f)
        with open(gaps_file, "r", encoding="utf-8") as f:
            gaps = json.load(f)
        with open(package_file, "r", encoding="utf-8") as f:
            prod_package = json.load(f)

        # 1. Crear directorios de CapCut Pack
        pack_path = os.path.join(self.packs_dir, char_folder)
        subfolders = ["01_SCRIPT", "02_VOICEOVER", "03_LOCAL_ASSETS", "04_REFERENCE_URLS", "05_MISSING_ASSETS", "06_CAPCUT_NOTES"]
        for sf in subfolders:
            os.makedirs(os.path.join(pack_path, sf), exist_ok=True)

        # 2. Generar voiceover_script_clean.txt (SOLO locución limpia)
        voiceover_clean = scripts.get("script_short", "")
        # Limpiar notas de producción residuales si el modelo dejó marcas
        voiceover_clean = re.sub(r"\[.*?\]", "", voiceover_clean)
        voiceover_clean = re.sub(r"VISUAL:.*", "", voiceover_clean)
        
        # 3. Generar script_with_pauses.md (Con guías de locución)
        # Reemplazar puntos seguidos por pausas sugeridas
        script_pauses = voiceover_clean.replace(". ", " [Pausa 1s]\n")
        script_pauses = script_pauses.replace(", ", " [Pausa breve] ")
        script_pauses = f"# Guía de Locución: {character_name}\n\n[Énfasis inicial]\n" + script_pauses

        with open(os.path.join(pack_path, "01_SCRIPT", "voiceover_script_clean.txt"), "w", encoding="utf-8") as f:
            f.write(voiceover_clean)
        with open(os.path.join(pack_path, "01_SCRIPT", "script_with_pauses.md"), "w", encoding="utf-8") as f:
            f.write(script_pauses)

        # 4. Copiar assets locales existentes físicamente usando hard links (cero duplicación)
        local_copied_count = 0
        for entry in registry:
            src = entry.get("storage_path", "")
            if os.path.exists(src):
                dest = os.path.join(pack_path, "03_LOCAL_ASSETS", os.path.basename(src))
                if os.path.exists(dest):
                    try:
                        os.remove(dest)
                    except:
                        pass
                try:
                    os.link(src, dest)
                except OSError:
                    import shutil
                    shutil.copy2(src, dest)
                local_copied_count += 1

        # 5. Escribir reference_urls.md
        ref_urls = f"# URLs de Referencia para Descarga Manual - {character_name}\n\n"
        ref_count = 0
        for asset in manifest.get("assets", []):
            if not asset.get("downloaded"):
                ref_urls += f"- **{asset['title']}**\n  - URL: {asset['url']}\n  - Fuente: {asset['source']}\n  - Licencia: {asset['license']}\n  - Escena recomendada: {asset['recommended_scene']}\n  - Uso: {asset['recommended_usage']}\n\n"
                ref_count += 1
        with open(os.path.join(pack_path, "04_REFERENCE_URLS", "reference_urls.md"), "w", encoding="utf-8") as f:
            f.write(ref_urls)

        # 6. Escribir missing_assets.md
        missing_content = f"# Assets Faltantes Críticos (Gaps) - {character_name}\n\n"
        missing_count = 0
        for index, gap in enumerate(gaps, 1):
            gid = gap.get("gap_id", f"gap_{index:03d}")
            missing_content += f"- **ID:** {gid} (Escena {gap.get('scene', 'N/A')})\n  - Faltante: {gap.get('missing_asset', '')}\n  - Criticidad: {gap.get('criticality', 'medium')}\n  - Solución sugerida: {gap.get('suggested_solution', '')}\n  - Búsqueda recomendada: {', '.join(gap.get('manual_search_queries', []))}\n\n"
            missing_count += 1
        with open(os.path.join(pack_path, "05_MISSING_ASSETS", "missing_assets.md"), "w", encoding="utf-8") as f:
            f.write(missing_content)

        # 7. Escribir capcut_editing_guide.md
        notes_content = self.generate_capcut_notes(char_folder, ep_dir, storyboard, gaps, prod_package)
        with open(os.path.join(pack_path, "06_CAPCUT_NOTES", "capcut_editing_guide.md"), "w", encoding="utf-8") as f:
            f.write(notes_content)

        # 8. Generar ASSET_INTEGRITY_REPORT.md en el directorio del episodio
        integrity_report = f"# Reporte de Integridad de Assets - {character_name}\n\n"
        integrity_report += "| asset_id | title | downloaded_flag | physical_file_exists | registry_exists | status | action_needed |\n"
        integrity_report += "| --- | --- | --- | --- | --- | --- | --- |\n"
        
        registered_ids = {r["asset_id"]: r["storage_path"] for r in registry}
        
        for asset in manifest.get("assets", []):
            aid = asset["asset_id"]
            d_flag = asset.get("downloaded", False)
            reg_exists = aid in registered_ids
            file_exists = False
            if reg_exists:
                file_exists = os.path.exists(registered_ids[aid])
            
            # Clasificar estado
            if d_flag and not file_exists:
                status = "ERROR_MISSING_PHYSICAL"
                action = "Volver a descargar o limpiar registro"
            elif file_exists and not reg_exists:
                status = "ERROR_UNREGISTERED"
                action = "Re-registrar en el index"
            elif not d_flag and asset.get("url"):
                status = "OK_REFERENCE_ONLY"
                action = "Descargar manualmente vía URL"
            elif not asset.get("url"):
                status = "MISSING"
                action = "Buscar reemplazo contextual"
            else:
                status = "OK_AVAILABLE_LOCAL"
                action = "Ninguna"
                
            integrity_report += f"| {aid} | {asset['title']} | {d_flag} | {file_exists} | {reg_exists} | {status} | {action} |\n"
            
        with open(os.path.join(ep_dir, "ASSET_INTEGRITY_REPORT.md"), "w", encoding="utf-8") as f:
            f.write(integrity_report)

        # 9. Generar EDITOR_ASSET_PACK.md
        editor_pack = f"# EDITOR ASSET PACK - {character_name}\n\n"
        for s in storyboard:
            editor_pack += f"## ESCENA {s['scene']}\n\n"
            editor_pack += f"**Voiceover:**\n> {s['voiceover']}\n\n"
            
            # Local assets
            editor_pack += "### Assets locales disponibles:\n"
            aid = s.get("selected_asset_id")
            if aid and aid in registered_ids:
                editor_pack += f"- **Nombre de archivo:** {os.path.basename(registered_ids[aid])}\n  - Ruta local: {registered_ids[aid]}\n  - Uso sugerido: {s.get('recommended_usage', 'background_context')}\n"
            else:
                editor_pack += "- Ninguno disponible en local.\n"
                
            # References
            editor_pack += "\n### Assets de referencia:\n"
            ref_found = False
            for asset in manifest.get("assets", []):
                if asset.get("recommended_scene") == s["scene"] and not asset.get("downloaded"):
                    editor_pack += f"- **Título:** {asset['title']}\n  - URL: {asset['url']}\n  - Fuente: {asset['source']}\n  - Licencia: {asset['license']}\n  - Uso sugerido: {asset.get('recommended_usage', 'background_context')}\n"
                    ref_found = True
            if not ref_found:
                editor_pack += "- Sin referencias adicionales sugeridas.\n"
                
            # Gaps
            editor_pack += "\n### Assets faltantes:\n"
            gap_id = s.get("gap_id")
            if gap_id:
                matching_gap = next((g for g in gaps if g.get("gap_id") == gap_id), None)
                if matching_gap:
                    editor_pack += f"- **Faltante:** {matching_gap.get('missing_asset', '')}\n  - Búsqueda: {', '.join(matching_gap.get('manual_search_queries', []))}\n  - Prioridad: {matching_gap.get('criticality', 'medium')}\n  - Reemplazo: {matching_gap.get('suggested_solution', '')}\n"
            else:
                editor_pack += "- Sin vacíos críticos identificados.\n"
                
            editor_pack += f"\n### Notas de edición:\n- **Efecto:** {s.get('effect', 'cut')}\n- **Texto en pantalla:** {s.get('caption', '')}\n\n---\n\n"
            
        with open(os.path.join(ep_dir, "EDITOR_ASSET_PACK.md"), "w", encoding="utf-8") as f:
            f.write(editor_pack)

        return {
            "char_folder": char_folder,
            "pack_path": pack_path,
            "local_copied_count": local_copied_count,
            "ref_count": ref_count,
            "missing_count": missing_count,
            "prep_level": "READY" if missing_count == 0 else "PARTIAL"
        }
        
    def generate_global_summary(self, results):
        summary = """# Resumen del Día de Producción (PRODUCTION_DAY_SUMMARY)

## Estado de Episodios
"""
        for r in results:
            if r:
                summary += f"""
### {r['char_folder']}
- **Nivel de preparación:** `{r['prep_level']}`
- **Ruta del Guion Limpio:** `CapCut_Packs/{r['char_folder']}/01_SCRIPT/voiceover_script_clean.txt`
- **Ruta del Pack CapCut:** `CapCut_Packs/{r['char_folder']}/`
- **Cantidad de Assets Locales:** {r['local_copied_count']}
- **Cantidad de Referencias URL:** {r['ref_count']}
- **Cantidad de Assets Faltantes:** {r['missing_count']}
"""
        summary += """
## Guía Rápida para el Productor
1. **Qué grabar primero:** Jan Koum (tiene mayor consistencia y menor cantidad de gaps gráficos complejos).
2. **Episodio más listo:** Jan Koum (PARTIAL, con assets y logos listos en local).
3. **Advertencias de Licencia:** Todos los logotipos descargados y referencias marcadas como 'Derechos reservados' o 'Fair Use' deben usarse únicamente bajo derecho de citación documental/educativo.
"""
        with open(os.path.join(self.packs_dir, "PRODUCTION_DAY_SUMMARY.md"), "w", encoding="utf-8") as f:
            f.write(summary)

if __name__ == "__main__":
    packager = CapCutPackager()
    results = []
    for char in ["Adidas vs Puma", "Ehud Shabtai", "Jan Koum"]:
        res = packager.process_episode(char)
        results.append(res)
    packager.generate_global_summary(results)
    print("[Packager] Paquetes de producción CapCut y reportes generados con éxito.")
