import os
import json
from openrouter_client import OpenRouterClient

class HumanizerAgent:
    def __init__(self, client: OpenRouterClient):
        self.client = client
        self.base_dir = os.path.dirname(os.path.abspath(__file__))

    def _load_voice_sample(self) -> str:
        sample_path = os.path.join(self.base_dir, "voice_sample.txt")
        if os.path.exists(sample_path):
            try:
                with open(sample_path, "r", encoding="utf-8") as f:
                    return f.read().strip()
            except Exception as e:
                print(f"[Humanizer] Advertencia al leer voice_sample.txt: {e}")
        return ""

    def _load_skill_instructions(self) -> str:
        possible_paths = [
            os.path.expanduser("~/.agents/skills/humanizer/SKILL.md"),
            os.path.expanduser("~/.gemini/config/skills/humanizer/SKILL.md"),
            "C:/Users/Jota Ochoa/.agents/skills/humanizer/SKILL.md",
            "C:/Users/Jota Ochoa/.gemini/config/skills/humanizer/SKILL.md",
            os.path.join(self.base_dir, "skills", "humanizer", "SKILL.md"),
        ]
        for path in possible_paths:
            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        print(f"[Humanizer] Instrucciones cargadas de: {path}")
                        return f.read()
                except Exception:
                    pass
        
        print("[Humanizer] No se encontró SKILL.md. Usando instrucciones inline de fallback.")
        return """
        Eres un editor de escritura que identifica y elimina signos de texto generado por IA.
        Reglas de reescritura:
        1. Identifica y remueve patrones de IA (significance inflation, promotional language, -ing analyses, vague attributions, em-dashes, rule of three, vocabulary overused like 'delve', 'testament', 'tapestry').
        2. Preserva la información, no la forma. Cada afirmación del original debe sobrevivir, pero condensa las partes aburridas y expande donde convenga.
        3. Nunca inventes hechos. No agregues datos, nombres o fechas que no estén en el texto original.
        4. Estilo conversacional de HUMANOS: Frases cortas, pausas claras, ironía seca, tono directo e intelectual.
        """

    def execute_humanization(self, character_name: str, scripts_json: dict, editorial_context: dict | None = None, human_evidence_context: dict | None = None) -> tuple:
        """
        Ejecuta la humanización del material de Gabo.
        Devuelve (humanized_scripts_json_dict, script_short_md, script_long_md, newsletter_md, twitter_thread_md, logs_str).
        """
        print(f"[Humanizer] Iniciando pulido y humanización de guiones para: {character_name}...")
        
        voice_sample = self._load_voice_sample()
        skill_instructions = self._load_skill_instructions()

        system_prompt = (
            "Eres el HUMANIZER, la capa final de pulido editorial de HUMANOS.\n"
            "Tu misión es reescribir la prosa generada por otros agentes para eliminar cualquier rastro de lenguaje de IA y adaptarlo al ADN tonal humano.\n\n"
            "INSTRUCCIONES DE HUMANIZACIÓN:\n"
            f"{skill_instructions}\n"
        )
        
        if (editorial_context or {}).get("rewrite_mode") == "GATE_3B_STRUCTURAL":
            system_prompt += (
                "\nGATE 3B: preserve the audiovisual score and every structural tag literally. "
                "Do not convert it into continuous prose, fill [SILENCIO JOTA], remove MOSAICO DE GRATITUD, "
                "Character Cards, B&W earthquake, PODRÍA SER EL TUYO| or LA VIDA ES UN ECO. "
                "Keep VO Jota at 80 words maximum and add no claims.\n"
            )

        if voice_sample:
            system_prompt += (
                "\nVOICE CALIBRATION (ADN TONAL A IMITAR):\n"
                "Debes imitar estrictamente la estructura, ritmo, longitud de oraciones y el tono directo de esta muestra de escritura:\n"
                f"\"\"\"\n{voice_sample}\n\"\"\"\n"
            )

        prompt = f"""
        Toma el contenido original en JSON de Gabo para el personaje {character_name}:
        {json.dumps(scripts_json, ensure_ascii=False, indent=2)}

        CONTEXTO EDITORIAL PERSISTENTE (si existe; preserva sus locks):
        {json.dumps(editorial_context or {}, ensure_ascii=False, indent=2)}

        PUENTE DE EVIDENCIA HUMANA (si existe; no agregues claims no soportados):
        {json.dumps(human_evidence_context or {}, ensure_ascii=False, indent=2)}

        Si rewrite_mode es GATE_3B_STRUCTURAL, conserva literalmente la partitura audiovisual de script_short.
        No la conviertas en prosa. Debe mantener [CHARACTER CARD], [AUDIO ORIGINAL — CAMILO],
        [AUDIO ORIGINAL — PERSONA], [TELECAFÉ — CAMILO], [VO JOTA], [SILENCIO JOTA],
        [B&N — TERREMOTO], [TEXT ON SCREEN], ## MOSAICO DE GRATITUD, PODRÍA SER EL TUYO| y
        LA VIDA ES UN ECO. No agregues claims ni texto fuera de esos bloques. VO Jota máximo: 80 palabras.

        Genera un nuevo objeto JSON con el mismo esquema, pero con TODO el contenido textual humanizado:
        - 'script_short': El guion corto reescrito, sin intro/outros genéricos, con tu firma intacta, adaptado al ADN de voz.
        - 'script_long': El guion largo reescrito en Markdown, manteniendo los actos y marcas visuales [IMAGEN: ...], pero puliendo el texto.
        - 'newsletter': El ensayo corto humanizado.
        - 'twitter_thread': Lista de tweets humanizados.
        - 'scenes': La lista de escenas, donde el campo 'voiceover' DEBE actualizarse para ser el fragmento exacto secuencial correspondiente al nuevo 'script_short'. Los campos 'scene', 'duration', 'visual_intent', 'required_assets' y 'emotional_purpose' deben quedar idénticos a los originales.

        Es fundamental que respondas únicamente con el objeto JSON estructurado:
        {{
          "script_short": "...",
          "script_long": "...",
          "newsletter": "...",
          "twitter_thread": [
            "..."
          ],
          "scenes": [
            {{
              "scene": 1,
              "duration": 6.0,
              "voiceover": "...",
              "visual_intent": "...",
              "required_assets": [...],
              "emotional_purpose": "..."
            }}
          ]
        }}
        """

        humanized_data = self.client.complete_json(prompt, system_prompt)

        # Si script_short es demasiado corto o falló la alineación de escenas
        if len(humanized_data.get("script_short", "")) < 100 and humanized_data.get("scenes"):
            reconstructed = " ".join([s.get("voiceover", "") for s in humanized_data["scenes"] if s.get("voiceover")])
            if len(reconstructed) > len(humanized_data.get("script_short", "")):
                humanized_data["script_short"] = reconstructed

        # Extraer guiones y newsletter limpios en variables separadas
        script_short_md = f"# Guion Corto: {character_name}\n\n{humanized_data.get('script_short', '')}"
        script_long_md = f"# Guion Largo: {character_name}\n\n{humanized_data.get('script_long', '')}"
        newsletter_md = f"# Newsletter HUMANOS: El enigma de {character_name}\n\n{humanized_data.get('newsletter', '')}"

        # Generar formato md para el hilo de Twitter
        thread_list = humanized_data.get("twitter_thread", [])
        twitter_thread_md = f"# Hilo de X/Twitter: {character_name}\n\n"
        for i, tweet in enumerate(thread_list, 1):
            twitter_thread_md += f"### {i}/{len(thread_list)}\n{tweet}\n\n"

        logs = f"Humanización finalizada para {character_name}. Se reescribieron todos los entregables narrativos y se alinearon las {len(humanized_data.get('scenes', []))} escenas del storyboard."
        print(f"[Humanizer] Guiones pulidos con éxito.")

        return humanized_data, script_short_md, script_long_md, newsletter_md, twitter_thread_md, logs
