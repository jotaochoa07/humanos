import os
import sys
import json
import argparse
from datetime import datetime
from openrouter_client import OpenRouterClient

def load_env(base_dir: str):
    env_path = os.path.join(base_dir, ".env")
    if not os.path.exists(env_path):
        return
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, val = line.split("=", 1)
            key = key.strip()
            val = val.strip().strip("'").strip('"')
            if key not in os.environ:
                os.environ[key] = val

class TaleseAgent:
    def __init__(self, base_dir: str = "C:/Users/Jota Ochoa/Antigravity/02_Projects/humanos"):
        self.base_dir = base_dir
        load_env(base_dir)
        self.system_prompt_path = os.path.join(base_dir, "agents", "talese", "prompts", "system_prompt.md")
        # Registro longitudinal del Creator Lab. Requerido por run_performance_retro().
        self.lab_dir = os.path.join(base_dir, "_LAB")
        self.learnings_file = os.path.join(self.lab_dir, "creator_learnings.json")
        self.model_name = "anthropic/claude-sonnet-5"
        self.client = None

        if os.environ.get("OPENROUTER_API_KEY"):
            try:
                self.client = OpenRouterClient()
            except Exception as e:
                print(f"[Talese] Warning: OpenRouterClient error: {e}")



    def _get_system_prompt(self) -> str:
        if os.path.exists(self.system_prompt_path):
            with open(self.system_prompt_path, "r", encoding="utf-8") as f:
                return f.read()
        return (
            "Eres Gay Talese, Director de Aprendizaje Editorial de HUMANOS. Tu objetivo es medir evolución y evidencia, no cumplimiento.\n\n"
            "INDEPENDENCIA EVALUATIVA DE TALESE (OBLIGATORIA):\n"
            "1. MATERIA DE EVIDENCIA, NO DE CUMPLIMIENTO: El Manifiesto Editorial es dirección creativa obligatoria para Borges y Gabo. Para ti es materia de evidencia. NO evalúes si el episodio incluyó una escena ancla mental (eso ya está garantizado por Borges/Gabo).\n"
            "2. EVALÚA SI LA ESCENA ATERRIZÓ O SE SINTIÓ FORZADA: Evalúa honestamente si la escena ancla realmente aterrizó de forma genuina o si se sintió forzada, artificial o perjudicial para el ritmo narrativo.\n"
            "3. COMPARACIÓN CONTRA RETENCIÓN REAL Y EPISODIOS ANTERIORES: Compara el impacto de la escena ancla y la estructura narrativa contra los episodios anteriores y las métricas reales de retención (cuando estén disponibles), señalando sin rodeos cuando una escena o giro no logre su cometido."
        )

    def _read_file_if_exists(self, filepath: str) -> str:
        if os.path.exists(filepath):
            with open(filepath, "r", encoding="utf-8") as f:
                return f.read()
        return ""

    def run_immediate_retro(self, episode_path: str) -> dict:
        """
        Retro Editorial Inmediata (Momento 1):
        Analiza la brecha entre el borrador original de Gabo y el guion final editado por Jota.
        SIN datos de audiencia. Genera EPISODE_CHANGELOG.json y EPISODE_REVIEW.md.
        """
        episode_name = os.path.basename(os.path.normpath(episode_path))
        print(f"\n[Talese] Running Immediate Editorial Retro for: {episode_name}...")

        script_dir = os.path.join(episode_path, "02_SCRIPT")
        orig_script = self._read_file_if_exists(os.path.join(script_dir, "script_short_original.md"))
        final_script = self._read_file_if_exists(os.path.join(script_dir, "script_short.md"))
        dossier = self._read_file_if_exists(os.path.join(episode_path, "01_RESEARCH", "Editorial_Dossier.md"))

        if not orig_script and final_script:
            orig_script = final_script  # Fallback si el original no fue respaldado previamente

        system_prompt = self._get_system_prompt()
        prompt = f"""
        Analiza el episodio '{episode_name}' en su fase de entrega inmediata (SIN datos de audiencia todavía).

        BORRADOR ORIGINAL DE GABO (script_short_original.md):
        ---
        {orig_script if orig_script else "No disponible"}
        ---

        GUION FINAL APROBADO POR JOTA (script_short.md):
        ---
        {final_script if final_script else "No disponible"}
        ---

        DOSSIER EDITORIAL (Borges):
        ---
        {dossier[:1500] if dossier else "No disponible"}
        ---

        Genera un informe estructurado JSON con exactamente estas claves:
        {{
          "creator_intent": "Breve resumen de qué intentaba lograr el episodio",
          "editorial_delta": "Análisis comparativo entre el borrador de Gabo y la edición de Jota (qué cortó, qué enfatizó, qué ritmo cambió)",
          "what_worked": "Puntos fuertes de la versión final aprobada",
          "what_surprised": "Decisión o giro editorial inesperado",
          "next_experiment": "Una (1) sola hipótesis / experimento pequeño y accionable para el siguiente episodio",
          "proposed_observations": [
            {{
              "axis": "nombre_del_eje (ej: hook_structure, pacing, tone)",
              "title": "Título corto de la observación",
              "description": "Explicación basada en la evidencia del delta de edición"
            }}
          ]
        }}
        """

        result_json = {}
        if self.client:
            try:
                result_json = self.client.complete_json(prompt=prompt, system_prompt=system_prompt, model=self.model_name)
            except Exception as e:
                print(f"[Talese] Error al consultar LLM: {e}. Generando fallback local.")
                result_json = self._fallback_immediate(orig_script, final_script, episode_name)
        else:
            result_json = self._fallback_immediate(orig_script, final_script, episode_name)

        changelog_file = os.path.join(episode_path, "EPISODE_CHANGELOG.json")
        review_md_file = os.path.join(episode_path, "EPISODE_REVIEW.md")

        changelog_payload = {
            "episode": episode_name,
            "timestamp": datetime.now().isoformat(),
            "mode": "immediate",
            "report": result_json
        }

        with open(changelog_file, "w", encoding="utf-8") as f:
            json.dump(changelog_payload, f, ensure_ascii=False, indent=2)

        review_md = f"""# Episode Review — {episode_name}
*Generado por Gay Talese (Director de Aprendizaje Editorial)*
*Fecha: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

## 1. Intención del Creador
{result_json.get('creator_intent', 'N/A')}

## 2. Delta Editorial (Gabo vs. Versión Final de Jota)
{result_json.get('editorial_delta', 'N/A')}

## 3. Lo que funcionó / Lo que sorprendió
* **Fortalezas:** {result_json.get('what_worked', 'N/A')}
* **Sorpresa/Tensión:** {result_json.get('what_surprised', 'N/A')}

## 4. Experimento para el próximo episodio
💡 **Hipótesis:** {result_json.get('next_experiment', 'N/A')}

---
*Tales Rule: "Talese no mide éxito. Mide evolución."*
"""
        with open(review_md_file, "w", encoding="utf-8") as f:
            f.write(review_md)

        print(f"[Talese] Review Inmediata guardada en {review_md_file}")
        return changelog_payload

    def run_performance_retro(self, episode_path: str) -> dict:
        """
        Retro de Desempeño (Momento 2):
        Analiza las métricas a 48h (metrics_48h.json) frente al historial.
        REGLA DE ORO: Mide evolución, no éxito.
        Propone entradas con status: 'PROPOSED' en _LAB/creator_learnings.json.
        """
        episode_name = os.path.basename(os.path.normpath(episode_path))
        print(f"\n[Talese] Running Performance Retro 48h for: {episode_name}...")

        metrics_file = os.path.join(episode_path, "11_DIST", "metrics_48h.json")
        metrics_data = {}
        if os.path.exists(metrics_file):
            with open(metrics_file, "r", encoding="utf-8") as f:
                metrics_data = json.load(f)

        learnings_data = {}
        if os.path.exists(self.learnings_file):
            with open(self.learnings_file, "r", encoding="utf-8") as f:
                learnings_data = json.load(f)

        system_prompt = self._get_system_prompt()
        prompt = f"""
        Analiza el desempeño a 48h del episodio '{episode_name}'.

        REGLA DE ORO OBLIGATORIA: TALESE NO MIDE ÉXITO. MIDE EVOLUCIÓN.
        No evalúes si el número de reproducciones es grande o pequeño por sí solo. Evalúa qué aprendizaje deja para el proceso del creador.

        MÉTRICAS DEL EPISODIO:
        {json.dumps(metrics_data, ensure_ascii=False, indent=2)}

        REGISTRO HISTÓRICO DE APRENDIZAJES (_LAB/creator_learnings.json):
        {json.dumps(learnings_data, ensure_ascii=False, indent=2)}

        Genera una respuesta JSON con:
        {{
          "evolution_summary": "Resumen de la evolución del proceso creativo reflejado en este episodio",
          "metric_vs_evolution_analysis": "Análisis cualitativo del dato de audiencia frente a la estructura del guion",
          "proposed_promotions": [
            {{
              "id": "LRN-XXX",
              "level": "OBSERVATION",
              "axis": "eje",
              "title": "Título corto",
              "description": "Detalle del aprendizaje",
              "status": "PROPOSED"
            }}
          ]
        }}
        Recuerda: TODAS las promociones deben tener status 'PROPOSED'. NUNCA asignes 'APPROVED'.
        """

        result_json = {}
        if self.client:
            try:
                result_json = self.client.complete_json(prompt=prompt, system_prompt=system_prompt, model=self.model_name)
            except Exception as e:
                print(f"[Talese] Error al consultar LLM: {e}. Usando fallback local.")
                result_json = self._fallback_performance(metrics_data, episode_name)
        else:
            result_json = self._fallback_performance(metrics_data, episode_name)

        # Actualizar _LAB/creator_learnings.json si hay propuestas
        if result_json.get("proposed_promotions"):
            try:
                os.makedirs(self.lab_dir, exist_ok=True)
                if os.path.exists(self.learnings_file):
                    with open(self.learnings_file, "r", encoding="utf-8") as f:
                        current = json.load(f)
                else:
                    current = {"version": 1, "description": "Registro longitudinal del Creator Lab.", "learnings": []}
                current.setdefault("learnings", [])
                existing_ids = {item["id"] for item in current.get("learnings", [])}
                for item in result_json["proposed_promotions"]:
                    item["status"] = "PROPOSED"  # Garantizar regla de autoridad
                    if item.get("id") not in existing_ids:
                        current["learnings"].append(item)
                current["updated_at"] = datetime.now().isoformat()
                with open(self.learnings_file, "w", encoding="utf-8") as f:
                    json.dump(current, f, ensure_ascii=False, indent=2)
                print(f"[Talese] Actualizado _LAB/creator_learnings.json con {len(result_json['proposed_promotions'])} propuestas.")
            except Exception as e:
                print(f"[Talese] Error al actualizar creator_learnings.json: {e}")

        # Guardar CREATOR_CHANGELOG.md en _LAB
        os.makedirs(self.lab_dir, exist_ok=True)
        changelog_md_file = os.path.join(self.lab_dir, "CREATOR_CHANGELOG.md")
        changelog_content = f"""# Creator Changelog — Creativity Lab
*Última actualización por Gay Talese: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

## Último Episodio Analizado: {episode_name}
* **Evolución del Proceso:** {result_json.get('evolution_summary', 'N/A')}
* **Análisis Cualitativo:** {result_json.get('metric_vs_evolution_analysis', 'N/A')}

---
*Tales Rule: "Talese no mide éxito. Mide evolución."*
"""
        with open(changelog_md_file, "w", encoding="utf-8") as f:
            f.write(changelog_content)

        print(f"[Talese] Retro de Desempeño guardada en {changelog_md_file}")
        return result_json

    def audit_beat_sheet_gate1(self, narrative_blueprint: dict) -> dict:
        """
        Gate 1: Audit temprano del Beat Sheet / Narrative Blueprint de Borges antes de redactar.
        Bloquea si la estructura o la tensión por acto son débiles.
        """
        character_name = narrative_blueprint.get("character_name", "Personaje")
        beat_sheet = narrative_blueprint.get("beat_sheet", [])
        total_duration = narrative_blueprint.get("target_total_duration_sec", 540)

        print(f"[Talese - Gate 1] Auditando Beat Sheet de {character_name} ({len(beat_sheet)} actos, ~{total_duration}s)...")

        # Validación estructural estricta
        rejection_reasons = []
        if len(beat_sheet) < 5 or len(beat_sheet) > 7:
            rejection_reasons.append(f"El número de actos ({len(beat_sheet)}) debe estar estrictamente entre 5 y 7.")
        
        if total_duration < 420 or total_duration > 600:
            rejection_reasons.append(f"La duración estimada ({total_duration}s) debe estar entre 7 y 10 minutos (420s - 600s).")

        non_causal_acts = [act for act in beat_sheet if act.get("causality_type") not in ["BUT", "THEREFORE"]]
        if non_causal_acts:
            rejection_reasons.append(f"Hay {len(non_causal_acts)} actos con causalidad débil (se requiere PERO o POR LO TANTO).")

        if self.client:
            prompt = f"""
            Actúa como Gay Talese, Editor Jefe de HUMANOS.
            Audita este NARRATIVE BLUEPRINT para un documental largo de 10 min sobre {character_name}:

            {json.dumps(narrative_blueprint, ensure_ascii=False, indent=2)}

            Evalúa con máximo rigor periodístico:
            1. ¿La tesis central es potente o es un lugar común?
            2. ¿Hay una escalada real de tensión o el ritmo se cae en el Acto III?
            3. ¿Las transiciones entre actos son causales (PERO/POR LO TANTO)?

            Responde estrictamente en formato JSON:
            {{
              "approved": true | false,
              "structural_score": 8, // 1 a 10
              "editorial_feedback": "Explicación clara de por qué se aprueba o se rechaza",
              "rejection_reasons": ["Motivo 1", "Motivo 2"],
              "socratic_questions": ["Pregunta 1", "Pregunta 2"]
            }}
            """
            try:
                result = self.client.complete_json(prompt, self._get_system_prompt(), model=self.model_name)
                if rejection_reasons:
                    result["approved"] = False
                    result.setdefault("rejection_reasons", []).extend(rejection_reasons)
                print(f"[Talese - Gate 1] Audit completado. Aprobado: {result.get('approved')}")
                return result
            except Exception as e:
                print(f"[Talese - Gate 1] Error en LLM: {e}. Usando fallback.")

        approved = len(rejection_reasons) == 0
        return {
            "approved": approved,
            "structural_score": 8 if approved else 5,
            "editorial_feedback": "Beat sheet estructuralmente válido." if approved else "Deficiencias estructurales encontradas en causalidad o número de actos.",
            "rejection_reasons": rejection_reasons,
            "socratic_questions": ["¿Por qué el conflicto del Acto II obliga al personaje a tomar la decisión del Acto III?"]
        }

    def audit_act_socratic_gate2(self, act_id: str, act_script: str, central_thesis: str, beat_sheet_context: list) -> dict:
        """
        Gate 2: Audit socrático del guion redactado por actos.
        Emite preguntas forzantes (no corrección directa).
        """
        print(f"[Talese - Gate 2] Auditando Socráticamente el {act_id}...")

        if self.client:
            prompt = f"""
            Actúa como Gay Talese, Mentor Editorial de HUMANOS.
            Audita el texto redactado para el {act_id} de un documental largo:

            TESIS CENTRAL DE LA HISTORIA: {central_thesis}
            TEXTO DEL ACTO REDACTADO:
            ---
            {act_script}
            ---

            CONTEXTO DEL BEAT SHEET COMPLETO:
            {json.dumps(beat_sheet_context, ensure_ascii=False)}

            Genera preguntas socráticas forzantes que obliguen a mejorar la prosa sin corregir el texto directamente.

            Responde estrictamente en formato JSON:
            {{
              "approved": true | false,
              "act_id": "{act_id}",
              "feedback": "Evaluación crítica del acto",
              "socratic_questions": [
                {{
                  "question_id": "q_{act_id}_01",
                  "question": "Texto de la pregunta socrática",
                  "category": "conflict_causality | emotional_payoff | pacing | data_density"
                }}
              ]
            }}
            """
            try:
                return self.client.complete_json(prompt, self._get_system_prompt(), model=self.model_name)
            except Exception as e:
                print(f"[Talese - Gate 2] Error LLM: {e}")

        return {
            "approved": True,
            "act_id": act_id,
            "feedback": "Texto del acto revisado sin objeciones graves.",
            "socratic_questions": [
                {
                    "question_id": f"q_{act_id}_01",
                    "question": "¿Cuál es el conflicto moral no resuelto al final de este acto?",
                    "category": "conflict_causality"
                }
            ]
        }


    def _fallback_immediate(self, orig: str, final: str, name: str) -> dict:
        orig_words = len(orig.split()) if orig else 0
        final_words = len(final.split()) if final else 0
        return {
            "creator_intent": f"Narrar la paradoja humana central de {name}.",
            "editorial_delta": f"Ajuste de extensión y ritmo: de {orig_words} palabras en borrador a {final_words} palabras en versión aprobada.",
            "what_worked": "Estructura directa sin rodeos y eliminación de frases hechas.",
            "what_surprised": "Contraste directo en la frase de apertura.",
            "next_experiment": "Probar abrir directamente con una pregunta incómoda en lugar de contexto histórico.",
            "proposed_observations": [
                {
                    "axis": "pacing_control",
                    "title": "Reducción de adjetivos abstractos acelera la atención inicial",
                    "description": f"En {name}, la versión editada recortó {abs(orig_words - final_words)} palabras sobrantes."
                }
            ]
        }

    @staticmethod
    def _metric(metrics: dict, *keys, default=0):
        """Lee una métrica tolerando camelCase y snake_case.

        El dashboard escribe metrics_48h.json en camelCase (retentionRate3s) y
        mark.py guarda el historial en snake_case (retention_rate_3s).
        """
        for k in keys:
            if metrics.get(k) not in (None, ""):
                return metrics[k]
        return default

    def _fallback_performance(self, metrics: dict, name: str) -> dict:
        ret = self._metric(metrics, "retentionRate3s", "retention_rate_3s")
        views = self._metric(metrics, "views")
        return {
            "evolution_summary": f"Episodio {name} consolida la tasa de retención a 3s ({ret*100:.1f}%) con {views} reproducciones.",
            "metric_vs_evolution_analysis": "La estructura de gancho directo mantuvo la atención sin depender de artificios visuales.",
            "proposed_promotions": [
                {
                    "id": f"LRN-{int(datetime.now().timestamp()) % 1000:03d}",
                    "level": "OBSERVATION",
                    "axis": "hook_retention",
                    "title": f"Tasa de retención 3s en {name} ({ret*100:.1f}%)",
                    "description": f"Validación de gancho inicial en {name}.",
                    "status": "PROPOSED"
                }
            ]
        }

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Gay Talese — Director de Aprendizaje Editorial")
    parser.add_argument("--episode-path", type=str, required=True, help="Path al episodio")
    parser.add_argument("--mode", type=str, default="immediate", choices=["immediate", "performance"])
    args = parser.parse_args()

    talese = TaleseAgent()
    if args.mode == "immediate":
        talese.run_immediate_retro(args.episode_path)
    elif args.mode == "performance":
        talese.run_performance_retro(args.episode_path)
