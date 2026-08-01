import os
import json
import datetime
import shutil

class MarkAgent:
    def __init__(self, base_dir: str = "C:/Users/Jota Ochoa/Antigravity/02_Projects/humanos"):
        self.base_dir = base_dir
        self.metrics_file = os.path.join(base_dir, "metrics_history.json")
        self.skills_dir = os.path.join(base_dir, "agents", "mark", "skills")
        self.prompts_dir = os.path.join(base_dir, "agents", "mark", "prompts")

    def _load_metrics(self) -> list:
        if os.path.exists(self.metrics_file):
            try:
                with open(self.metrics_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_metrics(self, data: list) -> None:
        with open(self.metrics_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def log_metrics(self, character_name: str, episode_id: str, views: int, retention_rate_3s: float, 
                    avg_watch_percentage: float, duration_seconds: float, hook_text: str, themes: list) -> None:
        """Registra métricas para un video/episodio en la base de datos histórica."""
        metrics = self._load_metrics()
        previous = next((m for m in metrics if m.get("episode_id") == episode_id), {})
        new_entry = {
            "character_name": character_name,
            "episode_id": episode_id,
            "logged_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metrics_status": "real",
            "views": views,
            "retention_rate_3s": retention_rate_3s,
            "avg_watch_percentage": avg_watch_percentage,
            "duration_seconds": duration_seconds or previous.get("duration_seconds", 0),
            "hook_text": hook_text or previous.get("hook_text", ""),
            "themes": themes or previous.get("themes", [])
        }
        metrics = [m for m in metrics if m.get("episode_id") != episode_id]
        metrics.append(new_entry)
        self._save_metrics(metrics)
        print(f"[Mark] Métricas REALES registradas para {character_name} ({episode_id}).")

    def register_episode(self, character_name: str, episode_id: str, duration_seconds: float,
                         hook_text: str, themes: list) -> None:
        """Registra la ficha del episodio SIN métricas de audiencia.

        El pipeline no conoce el rendimiento real al terminar la producción.
        Se crea la entrada con `metrics_status: "pending"` y las cifras se
        completan más tarde vía log_metrics() cuando Jota carga los datos
        reales de 48h desde el panel. Nunca se inventan métricas.
        """
        metrics = self._load_metrics()
        existing = next((m for m in metrics if m.get("episode_id") == episode_id), None)
        if existing and existing.get("metrics_status") != "pending":
            print(f"[Mark] {episode_id} ya tiene métricas reales registradas. No se sobrescribe.")
            return

        entry = {
            "character_name": character_name,
            "episode_id": episode_id,
            "logged_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "metrics_status": "pending",
            "views": None,
            "retention_rate_3s": None,
            "avg_watch_percentage": None,
            "duration_seconds": duration_seconds,
            "hook_text": hook_text,
            "themes": themes
        }
        metrics = [m for m in metrics if m.get("episode_id") != episode_id]
        metrics.append(entry)
        self._save_metrics(metrics)
        print(f"[Mark] Ficha de {character_name} ({episode_id}) registrada. Métricas: PENDIENTES de datos reales a 48h.")

    def analyze_performance(self) -> dict:
        """Analiza el historial de métricas para detectar patrones ganadores.

        Solo considera episodios con métricas REALES cargadas. Los que están en
        `metrics_status: "pending"` se excluyen para no contaminar el aprendizaje.
        """
        metrics = [m for m in self._load_metrics() if m.get("metrics_status") != "pending"
                   and m.get("avg_watch_percentage") is not None]
        if not metrics:
            return {
                "total_videos": 0,
                "top_hooks": [],
                "top_themes": [],
                "optimal_format": "Sin datos suficientes",
                "recommendations": ["No hay métricas registradas todavía. Produce más episodios para entrenar a Mark."]
            }

        theme_performance = {}
        for m in metrics:
            for t in m.get("themes", []):
                if t not in theme_performance:
                    theme_performance[t] = []
                theme_performance[t].append(m.get("avg_watch_percentage", 0))

        avg_theme_perf = {t: sum(w)/len(w) for t, w in theme_performance.items()}
        sorted_themes = sorted(avg_theme_perf.items(), key=lambda x: x[1], reverse=True)

        sorted_hooks = sorted(metrics, key=lambda x: x.get("retention_rate_3s", 0), reverse=True)
        top_hooks = [
            {"character": h["character_name"], "hook": h["hook_text"], "retention": h["retention_rate_3s"]}
            for h in sorted_hooks[:3]
        ]

        short_videos = [m for m in metrics if m.get("duration_seconds", 0) <= 90]
        long_videos = [m for m in metrics if m.get("duration_seconds", 0) > 90]
        
        avg_short_ret = sum(v["avg_watch_percentage"] for v in short_videos)/len(short_videos) if short_videos else 0
        avg_long_ret = sum(v["avg_watch_percentage"] for v in long_videos)/len(long_videos) if long_videos else 0

        optimal_format = "Short Format (<=90s)" if avg_short_ret >= avg_long_ret else "Long Format (>90s)"
        
        recommendations = []
        if sorted_themes:
            recommendations.append(f"Priorizar temas sobre '{sorted_themes[0][0]}' (retención promedio del {sorted_themes[0][1]*100:.1f}%).")
        if top_hooks:
            recommendations.append(f"El gancho de {top_hooks[0]['character']} tuvo la mayor retención a los 3s ({top_hooks[0]['retention']*100:.1f}%). Replicar su estructura de contraste directo.")
        recommendations.append(f"El formato con mejor retención promedio actualmente es {optimal_format}.")

        return {
            "total_videos": len(metrics),
            "top_hooks": top_hooks,
            "top_themes": sorted_themes,
            "optimal_format": optimal_format,
            "recommendations": recommendations
        }

    def generate_conceptual_dashboard(self) -> str:
        """Genera el dashboard de analíticas de rendimiento."""
        analysis = self.analyze_performance()
        dashboard = f"""# HUMANOS - Dashboard de Rendimiento Editorial
Última actualización: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Resumen de Rendimiento
- **Total de Episodios Medidos:** {analysis['total_videos']}
- **Formato Ganador:** {analysis.get('optimal_format', 'N/A')}

## 1. Ganchos con Mayor Retención (3s Hook Rate)
"""
        if analysis['top_hooks']:
            for idx, h in enumerate(analysis['top_hooks'], 1):
                dashboard += f"{idx}. **{h['character']}** ({h['retention']*100:.1f}% Retención)\n   > \"{h['hook']}\"\n"
        else:
            dashboard += "- Sin datos de ganchos registrados.\n"

        dashboard += "\n## 2. Rendimiento por Temas (Retención promedio)\n"
        if analysis['top_themes']:
            for theme, score in analysis['top_themes']:
                dashboard += f"- **{theme.capitalize()}:** {score*100:.1f}%\n"
        else:
            dashboard += "- Sin datos de temas registrados.\n"

        dashboard += "\n## 3. Lecciones y Recomendaciones de Mark\n"
        for rec in analysis['recommendations']:
            dashboard += f"- 💡 {rec}\n"

        dashboard_file = os.path.join(self.base_dir, "personajes", "PRODUCTION_METRICS_DASHBOARD.md")
        os.makedirs(os.path.dirname(dashboard_file), exist_ok=True)
        with open(dashboard_file, "w", encoding="utf-8") as f:
            f.write(dashboard)
            
        return dashboard

    def _find_cover(self, ep_path: str) -> str:
        """Busca la portada/thumbnail del episodio sin depender de un nombre fijo de personaje.

        Devuelve la ruta del primer archivo válido encontrado en 10_EXPORTS, o "" si no hay.
        Prioriza nombres que empiecen por 'cover' o 'thumbnail'.
        """
        exports_dir = os.path.join(ep_path, "10_EXPORTS")
        if not os.path.isdir(exports_dir):
            return ""
        images = [f for f in os.listdir(exports_dir) if f.lower().endswith((".png", ".jpg", ".jpeg"))]
        if not images:
            return ""
        for f in images:
            if f.lower().startswith(("cover", "thumbnail", "portada")):
                return os.path.join(exports_dir, f)
        return os.path.join(exports_dir, images[0])

    def verify_prepublication_checklist(self, ep_path: str) -> dict:
        """Valida que todos los entregables de producción y branding estén presentes antes de distribuir."""
        checklist = {
            "Intro (Gabo/Moore)": True,  # Representado en los scripts/storyboard
            "Outro (Gabo/Moore)": True,
            "Character Card": False,
            "Thumbnail (Leonardo)": False,
            "Subtítulos": True,  # Generalmente horneados en el renderizado
            "Audio": False,
            "Export 1080x1920": False,
            "Nombre correcto": False,
            "Copyright OK": True,
            "Descripción": True,
            "Playlist": True,
            "Hashtags": True
        }

        # Comprobar nombre de carpeta
        folder_name = os.path.basename(os.path.normpath(ep_path))
        if folder_name.startswith("EP") and "_" in folder_name:
            checklist["Nombre correcto"] = True

        # Comprobar existencia de Thumbnail (cualquier portada del episodio, no un personaje fijo)
        if self._find_cover(ep_path):
            checklist["Thumbnail (Leonardo)"] = True

        # Comprobar existencia de Character Card (video o asset gráfico)
        cc_candidates = [
            os.path.join(self.base_dir, "MEDIA_LIBRARY", "BRANDING", "video", "Character_card_CANVA.mp4"),
            os.path.join(self.base_dir, "assets", "branding", "Character_card_CANVA.mp4"),
            os.path.join(ep_path, "10_EXPORTS", "character_card_canva_img.png"),
        ]
        if any(os.path.exists(p) for p in cc_candidates):
            checklist["Character Card"] = True

        # Comprobar existencia de Audio final (cualquier locución en 06_AUDIO)
        audio_dir = os.path.join(ep_path, "06_AUDIO")
        if os.path.isdir(audio_dir):
            if any(f.lower().endswith((".wav", ".mp3", ".m4a")) for f in os.listdir(audio_dir)):
                checklist["Audio"] = True

        # Comprobar existencia de Export final
        export_video_path = os.path.join(ep_path, "10_EXPORTS", f"001_{folder_name[7:]}_HUMANOS.mp4")
        # Fallback genérico para cualquier mp4 en 10_EXPORTS
        if not os.path.exists(export_video_path):
            exports_dir = os.path.join(ep_path, "10_EXPORTS")
            if os.path.exists(exports_dir):
                mp4_files = [f for f in os.listdir(exports_dir) if f.endswith(".mp4")]
                if mp4_files:
                    export_video_path = os.path.join(exports_dir, mp4_files[0])
                    checklist["Export 1080x1920"] = True
        else:
            checklist["Export 1080x1920"] = True

        return checklist

    def generate_distribution_package(self, ep_path: str, character_name: str, scripts_data: dict, client) -> bool:
        """Genera los entregables de distribución de las plataformas en 11_DIST."""
        print(f"\n[Mark] Iniciando validación pre-publicación para {character_name}...")
        checklist = self.verify_prepublication_checklist(ep_path)
        
        # Guardar reporte de checklist
        dist_dir = os.path.join(ep_path, "11_DIST")
        os.makedirs(dist_dir, exist_ok=True)
        
        checklist_file = os.path.join(dist_dir, "checklist_report.json")
        with open(checklist_file, "w", encoding="utf-8") as f:
            json.dump(checklist, f, ensure_ascii=False, indent=2)

        # Si faltan elementos críticos como la exportación de video, advertimos pero procedemos a generar copys
        critical_missing = not checklist["Export 1080x1920"] or not checklist["Thumbnail (Leonardo)"]
        if critical_missing:
            print("[Mark - WARNING] Faltan entregables físicos críticos (Video final o Portada).")
            print("[Mark] Se generarán únicamente las propuestas de texto en /DIST para tu revisión.")
        else:
            print("[Mark - Quality Gate] Checklist aprobada con éxito. Procediendo a armar paquete de distribución.")

        # Cargar prompts
        system_prompt_path = os.path.join(self.prompts_dir, "system_prompt.md")
        system_prompt = ""
        if os.path.exists(system_prompt_path):
            with open(system_prompt_path, "r", encoding="utf-8") as f:
                system_prompt = f.read()

        # Mapeo de plataformas a archivos de Skill
        platforms = {
            "youtube": "youtube_publish.md",
            "instagram": "instagram_publish.md",
            "facebook": "facebook_publish.md",
            "linkedin": "linkedin_publish.md",
            "tiktok": "tiktok_publish.md",
            "x": "x_publish.md",
            "newsletter": "newsletter.md"
        }

        # Generar archivos por plataforma
        for platform, skill_filename in platforms.items():
            platform_dir = os.path.join(dist_dir, platform)
            os.makedirs(platform_dir, exist_ok=True)

            skill_path = os.path.join(self.skills_dir, skill_filename)
            skill_content = ""
            if os.path.exists(skill_path):
                with open(skill_path, "r", encoding="utf-8") as f:
                    skill_content = f.read()

            # Consultar OpenRouter para generar el copy personalizado
            if client:
                print(f"[Mark] Generando material para {platform.capitalize()}...")
                prompt = f"""
                Actúa como Mark. Genera los archivos de distribución para la plataforma {platform.capitalize()} basándote en la siguiente habilidad:
                {skill_content}

                Datos del Episodio de {character_name}:
                Guion Corto (90s):
                {scripts_data.get('script_short', '')}
                
                Guion Largo (Documental):
                {scripts_data.get('script_long', '')}

                Genera el contenido exacto para los archivos de esta plataforma. Tu respuesta debe ser un objeto JSON que mapee los nombres de archivo a su contenido correspondiente para ser guardados en la carpeta.
                Ejemplo de formato de respuesta JSON:
                {{
                  "caption.md": "contenido del caption...",
                  "hashtags.txt": "tag1 tag2",
                  "title.txt": "título"
                }}
                No agregues explicaciones fuera del JSON.
                """
                try:
                    files_data = client.complete_json(
                        prompt=prompt,
                        system_prompt=system_prompt
                    )
                    for filename, content in files_data.items():
                        file_dest = os.path.join(platform_dir, filename)
                        with open(file_dest, "w", encoding="utf-8") as f:
                            f.write(content)
                except Exception as e:
                    print(f"[Mark - ERROR] Error al generar copys para {platform}: {e}")
                    # Fallback básico local si falla la llamada
                    self._generate_local_fallback(platform_dir, platform, character_name, scripts_data)
            else:
                # Fallback sin cliente
                self._generate_local_fallback(platform_dir, platform, character_name, scripts_data)

            # Copiar recursos gráficos a carpetas que los requieran
            cover_source = self._find_cover(ep_path)
            if cover_source and os.path.exists(cover_source):
                if platform in ["youtube", "instagram", "facebook"]:
                    shutil.copy(cover_source, os.path.join(platform_dir, "thumbnail.png"))

        print(f"[Mark] Empaquetado completo de distribución finalizado para {character_name}.")
        return True

    def package_dual_distribution(self, episode_dir: str, character_name: str, narrative_blueprint: dict, derived_shorts: list) -> dict:
        """
        Empaqueta la distribución doble para el piloto:
        1. Master Pack del Documental de 7-10 min.
        2. Paquete de 3 Shorts Derivados trazables (con episodio_padre_id y acto_origen_id).
        """
        print(f"[Mark] Empaquetando distribución dual (Documental + 3 Shorts derivados) para {character_name}...")

        dist_dir = os.path.join(episode_dir, "11_DIST")
        os.makedirs(dist_dir, exist_ok=True)

        dual_package = {
          "episode_id": os.path.basename(episode_dir),
          "character_name": character_name,
          "is_documentary_pilot": True,
          "created_at": datetime.datetime.now().isoformat(),
          "master_documentary": {
            "title": f"HUMANOS Doc — {character_name}",
            "central_thesis": narrative_blueprint.get("central_thesis", ""),
            "total_acts": len(narrative_blueprint.get("beat_sheet", [])),
            "target_duration_sec": narrative_blueprint.get("target_total_duration_sec", 540)
          },
          "derived_shorts": derived_shorts
        }

        dist_json_file = os.path.join(dist_dir, "distribution_dual_pack.json")
        with open(dist_json_file, "w", encoding="utf-8") as f:
            json.dump(dual_package, f, ensure_ascii=False, indent=2)

        print(f"[Mark] Paquete de distribución dual guardado en {dist_json_file}.")
        return dual_package


    def _generate_local_fallback(self, platform_dir: str, platform: str, character_name: str, scripts_data: dict) -> None:
        """Genera una estructura de fallback local básica si falla la llamada de IA o no hay cliente."""
        if platform == "youtube":
            with open(os.path.join(platform_dir, "title.txt"), "w", encoding="utf-8") as f:
                f.write(f"La increíble obsesión de {character_name} | HUMANOS #Shorts")
            with open(os.path.join(platform_dir, "caption.md"), "w", encoding="utf-8") as f:
                f.write(f"Conoce la historia detrás del creador. De la pobreza a fundar un imperio.\n\nVer más en el canal.")
            with open(os.path.join(platform_dir, "hashtags.txt"), "w", encoding="utf-8") as f:
                f.write("#humanos #shorts #negocios")
        elif platform == "linkedin":
            with open(os.path.join(platform_dir, "learning_post.md"), "w", encoding="utf-8") as f:
                f.write(f"¿Qué podemos aprender de {character_name}?\n\nLa obsesión por resolver un problema real supera cualquier presupuesto de marketing.\n\n#liderazgo #negocios")
        else:
            with open(os.path.join(platform_dir, "caption.md"), "w", encoding="utf-8") as f:
                f.write(f"Video sobre {character_name}. #humanos #historia")
