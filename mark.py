import os
import json
import datetime

class MarkAgent:
    def __init__(self, base_dir: str = "C:/Users/Jota Ochoa/Antigravity/02_Projects/humanos"):
        self.base_dir = base_dir
        self.metrics_file = os.path.join(base_dir, "metrics_history.json")

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
        new_entry = {
            "character_name": character_name,
            "episode_id": episode_id,
            "logged_at": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "views": views,
            "retention_rate_3s": retention_rate_3s,  # e.g., 0.65 (65%)
            "avg_watch_percentage": avg_watch_percentage,  # e.g., 0.45 (45%)
            "duration_seconds": duration_seconds,
            "hook_text": hook_text,
            "themes": themes
        }
        # Evitar duplicados por id de episodio
        metrics = [m for m in metrics if m.get("episode_id") != episode_id]
        metrics.append(new_entry)
        self._save_metrics(metrics)
        print(f"[Mark] Métricas registradas con éxito para {character_name} ({episode_id}).")

    def analyze_performance(self) -> dict:
        """Analiza el historial de métricas para detectar patrones ganadores."""
        metrics = self._load_metrics()
        if not metrics:
            return {
                "total_videos": 0,
                "top_hooks": [],
                "top_themes": [],
                "optimal_format": "Sin datos suficientes",
                "recommendations": ["No hay métricas registradas todavía. Produce más episodios para entrenar a Mark."]
            }

        # 1. Agrupar por temas y calcular watch time
        theme_performance = {}
        for m in metrics:
            for t in m.get("themes", []):
                if t not in theme_performance:
                    theme_performance[t] = []
                theme_performance[t].append(m.get("avg_watch_percentage", 0))

        avg_theme_perf = {t: sum(w)/len(w) for t, w in theme_performance.items()}
        sorted_themes = sorted(avg_theme_perf.items(), key=lambda x: x[1], reverse=True)

        # 2. Hooks ganadores (retention rate > 70% o top 3)
        sorted_hooks = sorted(metrics, key=lambda x: x.get("retention_rate_3s", 0), reverse=True)
        top_hooks = [
            {"character": h["character_name"], "hook": h["hook_text"], "retention": h["retention_rate_3s"]}
            for h in sorted_hooks[:3]
        ]

        # 3. Duración óptima
        short_videos = [m for m in metrics if m.get("duration_seconds", 0) <= 90]
        long_videos = [m for m in metrics if m.get("duration_seconds", 0) > 90]
        
        avg_short_ret = sum(v["avg_watch_percentage"] for v in short_videos)/len(short_videos) if short_videos else 0
        avg_long_ret = sum(v["avg_watch_percentage"] for v in long_videos)/len(long_videos) if long_videos else 0

        optimal_format = "Short Format (<=90s)" if avg_short_ret >= avg_long_ret else "Long Format (>90s)"
        
        # 4. Recomendaciones heurísticas
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
        """Genera el dashboard de analíticas conceptuales en formato Markdown."""
        analysis = self.analyze_performance()
        
        dashboard = f"""# HUMANOS - Dashboard Conceptual de Aprendizaje
Última actualización: {datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Resumen del Canal
- **Total de Episodios Medidos:** {analysis['total_videos']}
- **Formato Ganador Actual:** {analysis.get('optimal_format', 'N/A')}

## 1. Ganchos (Hooks) con Mayor Retención a los 3s
"""
        if analysis['top_hooks']:
            for idx, h in enumerate(analysis['top_hooks'], 1):
                dashboard += f"{idx}. **{h['character']}** ({h['retention']*100:.1f}% Retención)\n   > \"{h['hook']}\"\n"
        else:
            dashboard += "- Sin datos de ganchos cargados.\n"

        dashboard += "\n## 2. Rendimiento por Temas (Retención promedio)\n"
        if analysis['top_themes']:
            for theme, score in analysis['top_themes']:
                dashboard += f"- **{theme.capitalize()}:** {score*100:.1f}%\n"
        else:
            dashboard += "- Sin datos de temas cargados.\n"

        dashboard += "\n## 3. Recomendaciones de Optimización de Mark\n"
        for rec in analysis['recommendations']:
            dashboard += f"- 💡 {rec}\n"

        dashboard_file = os.path.join(self.base_dir, "PERSONAJES", "PRODUCTION_METRICS_DASHBOARD.md")
        os.makedirs(os.path.dirname(dashboard_file), exist_ok=True)
        with open(dashboard_file, "w", encoding="utf-8") as f:
            f.write(dashboard)
            
        return dashboard
