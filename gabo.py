import json
import re
from openrouter_client import OpenRouterClient

class GaboAgent:
    def __init__(self, client: OpenRouterClient):
        self.client = client

    def execute_narrative(self, character_name: str, research_data: dict, timeline_data: dict, approved_claims: dict) -> tuple:
        """
        Ejecuta la dirección narrativa de Gabo a partir de los datos de Borges y los claims aprobados por Veritas.
        Devuelve (scripts_json_dict, script_short_md, script_long_md, newsletter_md, twitter_thread_md, logs_str).
        """
        print(f"[Gabo] Diseñando la estructura narrativa para {character_name}...")

        system_prompt = (
            "Eres GABO, el Narrative Director de HUMANOS. Tu objetivo es convertir la investigación de Borges "
            "en dos versiones narrativas principales de cada episodio (V1 Short y V2 Documental), centrado en heridas, obsesiones o contradicciones.\n\n"
            "REGLAS DE DURACIÓN Y PALABRAS DE HUMANOS (ESTRICTO):\n"
            "- V1: Short (Reels, TikTok, Shorts): 150 a 180 palabras (≈ 60-75 segundos).\n"
            "- Short Premium: 180 a 220 palabras (≈ 80-90 segundos).\n"
            "- Mini documental: 350 a 500 palabras (≈ 3 minutos).\n"
            "- V2: Documental (YouTube, Podcast, Blog): 800 a 1200 palabras (≈ 8 minutos).\n\n"
            "REGLAS DE FACT CHECKING (OBLIGATORIO):\n"
            "1. SÓLO puedes usar afirmaciones que aparezcan listadas bajo 'approved_claims' en el JSON provisto.\n"
            "2. NO uses de ninguna forma como hechos afirmaciones de la sección 'rejected_or_blocked_claims' o que estén marcadas como UNVERIFIED o REJECTED.\n"
            "3. Respeta las guías de uso ('usage_guidance') indicadas para cada claim aprobado.\n"
            "4. BAJO NINGUNA CIRCUNSTANCIA incluyas los códigos o IDs de los claims (como C001, C002, etc.) ni ningún tipo de cita técnica dentro del texto final del guion. El guion debe estar libre de anotaciones de claims y listo para ser leído en voz alta.\n\n"
            "REGLAS EDITORIALES Y DE TONO DE HUMANOS (EL MANIFIESTO EDITORIAL):\n"
            "1. EL PUNTO DE NO RETORNO: No contamos biografías ni imperios. Contamos la transformación de identidad. Cada episodio debe responder implícitamente a: '¿Cuál fue el momento psicológico del que ya no hubo regreso?' (ej: la puerta de Maranello cerrándose tras el insulto de Enzo).\n"
            "2. EL ANCLA MENTAL: Todo guion DEBE construir y orbitar alrededor de una ESCENA VISUAL ANCLA MENTAL que el espectador pueda dibujar de memoria (ej: Ferruccio con grasa de tractor levantando el capó y descubriendo su propio embrague en un Ferrari de lujo; Dyson tirando el prototipo 5.126 al contenedor; Koum haciendo cola por bonos de comida). Las personas no recuerdan fechas ni datos abstractos: recuerdan escenas inolvidables.\n"
            "3. ANTES DE CAMBIAR EL MUNDO, ALGO CAMBIÓ A ESTA PERSONA: El protagonista no es el imperio ni el producto; el protagonista es el cambio de identidad. Presenta al personaje en estado estable, muestra la escena de ruptura (insulto, pérdida, rechazo, humillación) y muestra el nacimiento de una nueva identidad que ya no quiere depender ni encajar.\n"
            "4. TONO: Directo, seco cuando conviene, curioso, incómodo, narrativo y con tensión. Sin grandilocuencia ni moraleja explícita. Evita sonar corporativo o motivacional barato.\n"
            "5. RITMO: Frases cortas, mucho aire, pocas subordinadas. Líneas limpias para narrar fácilmente en voz alta.\n"
            "4. FRASES PROHIBIDAS:\n"
            "   - 'Su nombre resuena...', 'La historia de...', 'Cambió el mundo para siempre...', 'El destino...'\n"
            "   - 'La libertad...', 'El coloso...', 'Contra todo pronóstico...', 'Y esa es la lección...'\n"
            "   - 'Nos enseña que...', 'Un visionario...', 'Un genio...', 'El resto es historia...'\n"
            "   - 'No sabía que estaba a punto de cambiar el mundo...'\n"
            "   - 'Su paradoja...', 'La paradoja de...', 'paradoja:', 'Su contradicción...', 'Su ironía...'\n"
            "   - Metáforas cursis como 'La privacidad no era una función, era una forma de respirar', 'Una herida muy pequeña', 'El poder de los sueños', 'La magia de creer'.\n"
            "5. MOSTRAR, NO NOMBRAR LA CONTRADICCIÓN: Queda terminantemente prohibido usar palabras explicativas abstractas como 'paradoja', 'contradicción' o 'ironía' para calificar el conflicto. Describe las dos acciones o hechos reales contrapuestos en frases consecutivas para que el espectador sienta el contraste por sí mismo (ej: 'Los empleados elegían a sus jefes y fijaban su propio sueldo').\n"
            "6. CONSISTENCIA FACTUAL (ESTRICTO): Las cifras, cantidades, fechas y nombres deben ser 100% consistentes en todas las partes del guion (ej: si el gancho menciona 'más de cinco mil prototipos', no uses cifras contradictorias o inconsistentes como '5.000' en un lado y '5.127' en otro si rompe la precisión del dato; mantén la coherencia exacta del dato principal).\n\n"
            "5. ESTRUCTURA OBLIGATORIA DEL GUION V1 (SHORT):\n"
            "   - GANCHO: En los primeros 3 segundos. Usar apertura de '¿Sabías que...?', paradoja, escena concreta o contraste numérico. Nunca usar 'La historia de...', 'Pocos saben que...', 'Su nombre resuena...'.\n"
            "   - CONTRASTE HUMANO: Bajar de la escala grande al detalle humano inicial.\n"
            "   - OBSESIÓN CENTRAL: Nombrar rápido la obsesión, herida o contradicción.\n"
            "   - ORIGEN DE LA OBSESIÓN: Mostrar el contexto que la explica.\n"
            "   - ESCALADA: Conexión con la construcción. Cada 5-8 segundos una nueva revelación o decisión. Sin relleno.\n"
            "   - PARADOJA PRINCIPAL: Enfrentar dos fuerzas opuestas sin dar moraleja y sin usar la palabra 'paradoja'.\n"
            "   - CONSECUENCIA O SALIDA INCÓMODA: Cierre de la historia.\n"
            "   - CIERRE DE MARCA HUMANOS (VARIADO Y DINÁMICO):\n"
            "     Queda TERMINANTEMENTE PROHIBIDO repetir siempre la misma frase rígida ('Yo soy Jota y esto es HUMANOS: historias de personas que construyeron desde...').\n"
            "     Varía el cierre en cada episodio con frases cortas y orgánicas adaptadas al tema (ej: 'Yo soy Jota y esto es HUMANOS. Nos vemos en la próxima historia.', 'Esto es HUMANOS: la revancha hecha imperio.', 'Yo soy Jota y esto es HUMANOS. ¿Qué decisión habrías tomado tú?').\n"
            "6. CIFRAS: Usar máximo 2 o 3 cifras fuertes para crear escala o paradoja. Indicar posibles textos sugeridos en pantalla.\n"
            "7. IDIOMA Y ACENTO (CRÍTICO):\n"
            "   - Escribe TODO en ESPAÑOL NEUTRO estricto.\n"
            "   - Está TERMINANTEMENTE PROHIBIDO usar el acento argentino, rioplatense o voseo (evita palabras como 'vos', 'elegís', 'tenés', 'decime', 'pensás', etc.).\n"
            "   - Usa conjugaciones del español neutro estándar (tú, eliges, tienes, dime, piensas, etc.)."
        )

        prompt = f"""
        Utilizando los datos de investigación recopilados por Borges:
        {json.dumps(research_data, ensure_ascii=False, indent=2)}

        Y su cronología:
        {json.dumps(timeline_data, ensure_ascii=False, indent=2)}

        Y los AFIRMACIONES APROBADAS Y RECHAZADAS (approved_claims.json) de Veritas:
        {json.dumps(approved_claims, ensure_ascii=False, indent=2)}

        Reescribe desde cero todo el contenido narrativo para {character_name}.
        Toma en cuenta de manera estricta que no debes usar hechos rechazados y debes respetar la guía de uso de cada claim aprobado.
        Genera un objeto JSON que siga exactamente esta estructura:
        {{
          "script_short": "Locución COMPLETA y corrida del vídeo vertical V1 Short de 60-75 segundos. Debe tener ESTRICTAMENTE entre 150 y 180 palabras en total. Centrada en la obsesión y la paradoja, conversacional y sin rodeos.",
          "script_long": "Guion narrativo detallado V2 Documental de 8 a 12 minutos para YouTube, Podcast y Blog. Debe tener ESTRICTAMENTE entre 800 y 1200 palabras en formato Markdown, estructurado en actos (Acto 1: Gancho y paradoja, Acto 2: Construcción y obsesión, Acto 3: Ruptura e impacto). Incluye sugerencias visuales entre corchetes.",
          "newsletter": "Ensayo literario corto (aprox 500 palabras) en markdown, analizando la obsesión y las contradicciones de este caso desde una perspectiva psicológica y de mercado.",
          "twitter_thread": [
            "Tweet 1 (Gancho viral y paradoja)",
            "Tweet 2...",
            "Tweet 10 (Cierre y llamada a la acción)"
          ],
          "scenes": [
            {{
              "scene": 1,
              "duration": 6.0,
              "voiceover": "Fragmento exacto y secuencial extraído de 'script_short' (V1 Short) para esta escena. La suma de los voiceovers de todas las escenas debe ser idéntica al 'script_short'.",
              "visual_intent": "Descripción del material visual real sugerido",
              "required_assets": ["nombre_asset.jpg"],
              "emotional_purpose": "Propósito de tensión o ironía de la escena"
            }}
          ]
        }}
        """

        scripts_data = self.client.complete_json(prompt, system_prompt)

        # Limpieza programática de voseo argentino y abstracciones editoriales
        def clean_voseo(text: str) -> str:
            if not isinstance(text, str):
                return text
            replacements = {
                " a vos": " a ti",
                " vos ": " tú ",
                " vos,": " tú,",
                " vos.": " tú.",
                " vos?": " tú?",
                " vos!": " tú?",
                " elegís": " eliges",
                " tenés": " tienes",
                " decime": " dime",
                " pensás": " piensas",
                " querés": " quieres",
                " hacés": " haces",
                " podés": " puedes",
                " sabés": " sabes",
                " sos ": " eres ",
                " sos.": " eres.",
                " sos,": " eres,",
                " vení": " ven"
            }
            for k, v in replacements.items():
                text = text.replace(k, v)
                text = text.replace(k.capitalize(), v.capitalize())
            # Regex insensible a mayúsculas para eliminar variantes de "[Una/La/Su/Esta] paradoja/contradicción/ironía: "
            text = re.sub(r'(?i)\b(una|la|su|esta)?\s*(paradoja|contradicción|ironía)\s*:\s*', '', text)
            return text

        # Aplicar limpieza a todo el JSON de salida
        if "script_short" in scripts_data:
            scripts_data["script_short"] = clean_voseo(scripts_data["script_short"])
        if "script_long" in scripts_data:
            scripts_data["script_long"] = clean_voseo(scripts_data["script_long"])
        if "newsletter" in scripts_data:
            scripts_data["newsletter"] = clean_voseo(scripts_data["newsletter"])
        if "twitter_thread" in scripts_data:
            scripts_data["twitter_thread"] = [clean_voseo(t) for t in scripts_data["twitter_thread"]]
        if "scenes" in scripts_data:
            for scene in scripts_data["scenes"]:
                if "voiceover" in scene:
                    scene["voiceover"] = clean_voseo(scene["voiceover"])

        # Si script_short es demasiado corto o genérico, intentar reconstruirlo sumando los voiceovers de las escenas
        if len(scripts_data.get("script_short", "")) < 100 and scripts_data.get("scenes"):
            reconstructed = " ".join([s.get("voiceover", "") for s in scripts_data["scenes"] if s.get("voiceover")])
            if len(reconstructed) > len(scripts_data.get("script_short", "")):
                scripts_data["script_short"] = reconstructed

        # Extraer guiones y newsletter limpios en variables separadas para los archivos .md
        script_short_md = f"# Guion Corto (V1 Short): {character_name}\n\n{scripts_data.get('script_short', '')}"
        script_long_md = f"# Guion Largo (V2 Documental): {character_name}\n\n{scripts_data.get('script_long', '')}"
        newsletter_md = f"# Newsletter HUMANOS: El enigma de {character_name}\n\n{scripts_data.get('newsletter', '')}"

        # Generar formato md para el hilo de Twitter
        thread_list = scripts_data.get("twitter_thread", [])
        twitter_thread_md = f"# Hilo de X/Twitter: {character_name}\n\n"
        for i, tweet in enumerate(thread_list, 1):
            twitter_thread_md += f"### {i}/{len(thread_list)}\n{tweet}\n\n"

        logs = f"Narrativa multiformato creada bajo reglas de duración estrictas de HUMANOS. Se definieron {len(scripts_data.get('scenes', []))} escenas secuenciales para el guion vertical."
        print(f"[Gabo] Estructura narrativa multiformato finalizada para {character_name}.")

        return scripts_data, script_short_md, script_long_md, newsletter_md, twitter_thread_md, logs
