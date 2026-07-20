import json
from openrouter_client import OpenRouterClient
from curie import CurieAgent

class BorgesAgent:
    def __init__(self, client: OpenRouterClient):
        self.client = client
        self.curie = CurieAgent(client=self.client)

    def execute_research(self, character_name: str, episode_focus: str, themes: list) -> tuple:
        """
        Ejecuta la investigación de Borges a través del LLM.
        Devuelve (research_json_dict, timeline_json_dict, sources_markdown_str, asset_manifest_json_dict, claims_json_dict, sources_json_dict, dossier_markdown_str, logs_str).
        """
        print(f"[Borges] Iniciando investigación profunda de: {character_name}...")
        
        local_context_str = ""
        if self.curie.has_library(character_name):
            print(f"[Borges] Consultando base de conocimientos de la biblioteca de Curie para: {character_name}...")
            local_docs = self.curie.search_library(character_name, episode_focus, k=5)
            if local_docs:
                local_context_str = "\n".join([f"- [Fuente: {doc['source']}] {doc['text']}" for doc in local_docs])
                print(f"[Borges] Curie recuperó {len(local_docs)} fragmentos relevantes.")

        system_prompt = (
            "Eres BORGES, el Chief Researcher del proyecto HUMANOS. Tu objetivo es investigar hechos reales, "
            "hitos históricos y decisiones críticas para construir Dossiers Editoriales.\n\n"
            "MANIFIESTO EDITORIAL DE HUMANOS (INVESTIGACIÓN):\n"
            "1. BUSCA EL PUNTO DE NO RETORNO: No investigues biografías enciclopédicas ni listas de millones. Busca el instante de ruptura psicológica del que ya no hubo regreso (la humillación, la pérdida, el rechazo o la frase que cambió la trayectoria).\n"
            "2. BUSCA LA ESCENA ANCLA MENTAL: Identifica y rescata los detalles empíricos y escenas visuales inolvidables que el espectador pueda recordar (ej: componentes mecánicos idénticos, prototipos descartados numéricos, bonos de comida). Las escenas concretas valen más que las abstracciones.\n"
            "3. Decisión -> Conflicto -> Consecuencias. Sé extremadamente conciso en tus descripciones "
            "y campos de texto para mantener el JSON compacto. No alucines información. "
            "Prioriza fuentes reales e históricas. Debes responder estrictamente en formato JSON utilizando el esquema solicitado.\n\n"
            "REGLA DE IDIOMA (OBLIGATORIA):\n"
            "- Escribe absolutamente TODO en ESPAÑOL NEUTRO estricto.\n"
            "- Queda TERMINANTEMENTE PROHIBIDO el uso de voseo (vos, tenés, elegís, etc.) o modismos del acento argentino/rioplatense."
        )
        
        if local_context_str:
            system_prompt += f"\n\n[CONTEXTO HISTÓRICO VERIFICADO DE REFERENCIA (GROUND TRUTH)]:\n{local_context_str}"


        research_prompt = f"""
        Investiga a fondo al personaje: {character_name}.
        Enfoque del episodio: {episode_focus}
        Temas asociados: {themes}

        Genera un objeto JSON con los siguientes campos obligatorios:
        {{
          "character_name": "{character_name}",
          "short_format_research": {{
            "core_obsession": "Obsesión o herida central del personaje",
            "emotional_arc": "Descripción del arco emocional del personaje",
            "key_paradox": "Contradicción principal que guiará el gancho del video corto",
            "raw_emotional_hooks": [
              "Ideas específicas de ganchos impactantes de 3 segundos"
            ],
            "key_facts_short": [
              "5 o 6 hechos cortos y demoledores sobre el conflicto"
            ]
          }},
          "long_format_research": {{
            "historical_context": "Contexto socio-histórico detallado y profundo",
            "societal_impact": "Impacto cultural, de mercado o tecnológico del personaje en la sociedad",
            "key_chapters": [
              {{
                "chapter_title": "Título del capítulo cronológico o temático",
                "milestones": ["Hitos detallados de este período o tema"]
              }}
            ]
          }},
          "newsletter_research": {{
            "psychological_depth": "Análisis psicológico profundo del personaje y su herida",
            "business_market_implications": "Implicaciones para el mercado, innovación o sociedad en general",
            "thematic_angles": [
              "Ángulos editoriales reflexivos para un ensayo escrito"
            ],
            "relevant_quotes": [
              "Citas textuales verificadas del personaje o sobre él"
            ]
          }},
          "twitter_research": {{
            "viral_hook_concepts": [
              "Conceptos para ganchos virales adaptados a formato hilo"
            ],
            "chronological_milestones_simplified": [
              "Hitos secuenciales redactados de forma corta y directa para un hilo de X"
            ]
          }},
          "themes": {themes},
          "metrics": {{
            "viral_potential": 8,
            "uniqueness": 9,
            "source_quality": 10,
            "story_strength": 9
          }},
          "suggested_assets": [
            {{
              "name": "Nombre descriptivo del asset",
              "type": "photo | video | logo | article_clip | screenshot | quote",
              "description": "Detalle de qué muestra el asset real y su importancia.",
              "candidate_url": "URL aproximada o fuente oficial recomendada (ej: Wikimedia, YouTube oficial, artículo de prensa)."
            }}
          ]
        }}
        """

        timeline_prompt = f"""
        Genera una cronología detallada de eventos reales para: {character_name}.
        Debes responder estrictamente en formato JSON con la siguiente estructura de lista:
        {{
          "timeline": [
            {{
              "date": "Año o fecha específica (ej: 1992 o Febrero 2009)",
              "event": "Descripción del suceso real",
              "importance": "Alto | Medio | Bajo",
              "source_url": "Enlace sugerido de prensa u oficial",
              "confidence": 10 // Puntuación de certeza histórica del 1 al 10
            }}
          ]
        }}
        """

        # Llamadas a OpenRouter para investigación base
        research_data = self.client.complete_json(research_prompt, system_prompt)
        timeline_data = self.client.complete_json(timeline_prompt, system_prompt)

        # Generar sources.md a partir de los datos investigados
        sources_prompt = f"""
        Genera un catálogo bibliográfico en formato Markdown (sources.md) para {character_name}.
        Clasifica las fuentes estrictamente en las siguientes categorías:
        - Primary / official sources
        - High reliability sources
        - Medium reliability sources
        - Visual sources (dónde conseguir fotos/videos reales)

        Utiliza la información encontrada sobre: {episode_focus}. Escribe solo el código Markdown limpio.
        """
        sources_md = self.client.complete_text(sources_prompt, system_prompt)

        # ----------------- ASSET DISCOVERY ENGINE -----------------
        print(f"[Borges - Asset Discovery Engine] Buscando y validando fotografías, entrevistas, logos y documentos históricos...")
        
        discovery_prompt = f"""
        Actúa como el ASSET DISCOVERY ENGINE de HUMANOS para el personaje: {character_name}.
        Tu prioridad absoluta es encontrar y documentar los mejores assets reales disponibles.
        
        Debes estructurar tu respuesta en formato JSON de la siguiente manera:
        {{
          "episode_id": "EP0001",
          "character_name": "{character_name}",
          "assets": [
            {{
              "asset_id": "001",
              "type": "photo | logo | interview | screenshot | video | quote | document",
              "title": "Título descriptivo del asset (ej: Jan Koum portrait 2014)",
              "source": "Wikimedia Commons | Archive.org | Biblioteca pública | Sitio oficial corporativo | YouTube oficial | Medios confiables",
              "url": "URL directa o de búsqueda exacta en la fuente prioritaria (ej: https://commons.wikimedia.org/...)",
              "license": "Dominio público | Creative Commons | Fair Use | Derechos reservados",
              "confidence": 10, // 1-10
              "editorial_priority": 1, // 1 = crítico, 2 = importante, 3 = complemento
              "recommended_scene": 1, // Número de escena de Gabo (1 a 5) asociada
              "recommended_usage": "opening_hero | lower_third | background_context | transition | emotional_peak | closing_visual",
              "emotional_tone": "struggle | hope | curiosity | obsession | tension | victory | reflection",
              "downloaded": false
            }}
          ],
          "metrics": {{
            "total_assets_found": 8,
            "critical_assets_found": 3,
            "missing_critical_assets": 1,
            "downloadable_assets": 4, // Disponibles para descarga automática en Wikimedia Commons
            "reference_only_assets": 4
          }}
        }}

        REGLAS DE BÚSQUEDA Y PRIORIDADES:
        - Prioriza fuentes en este orden: 1. Wikimedia Commons, 2. Archive.org, 3. Sitios oficiales corporativos, 4. YouTube oficial, 5. Medios confiables.
        - Evita Pinterest, blogs dudosos o imágenes sin licencia.
        - Mapea de forma coherente recommended_scene del 1 al 5 en base a las escenas de Gabo.
        - Genera al menos 6-8 assets estructurados con todos los campos especificados.
        """
        
        asset_manifest = self.client.complete_json(discovery_prompt, system_prompt)

        # ----------------- CLAIMS & SOURCES STRUCTURING -----------------
        print(f"[Borges - Claims & Sources Generator] Generando afirmaciones importantes y fuentes estructuradas...")
        
        claims_prompt = f"""
        A partir de la investigación de {character_name} y el enfoque {episode_focus}, extrae una lista con los 5 o 6 hechos o afirmaciones históricas más críticas y determinantes (claims) que sustentan el conflicto y obsesión del personaje. No extraigas más de 6 claims.
        Asegúrate de incluir tanto decisiones/conflictos principales como hallazgos mecánicos o citas directas de época documentadas (ej: piezas o componentes compartidos, modelos exactos, citas textuales de entrevistas de época).
        Cada claim debe tener un ID único secuencial (ej: C001, C002...), el texto del claim detallado y una puntuación de importancia para el episodio (del 1 al 10, siendo 10 crítico).
        
        Debes responder estrictamente en formato JSON con la siguiente estructura:
        {{
          "project": "HUMANOS",
          "episode_id": "EP0001",
          "character_name": "{character_name}",
          "claims": [
            {{
              "claim_id": "C001",
              "claim": "Texto exacto de la afirmación",
              "importance": 10
            }}
          ]
        }}
        """
        claims_data = self.client.complete_json(claims_prompt, system_prompt)

        sources_json_prompt = f"""
        Genera un catálogo estructurado de fuentes bibliográficas para el personaje {character_name} y el enfoque {episode_focus}.
        Cada fuente debe tener título, URL de referencia (si existe o es aproximada), tipo de fuente (official | news | biography | database | archive), nivel de calidad de fuente según la jerarquía (A | B | C | D | F) y notas adicionales sobre la fuente.
        
        Jerarquía de Tiers:
        - A: Documentos oficiales, filings regulatorios (SEC), investor relations, publicaciones académicas, bases de datos verificadas.
        - B: Entrevistas directas, biografías autorizadas, medios Tier 1 (WSJ, Reuters, etc.).
        - C: Medios secundarios, artículos de opinión, reportes de analistas.
        - D: Blogs, redes sociales, agregadores.
        - F: Rumores, IA sin respaldo.
        
        Debes responder estrictamente en formato JSON con la siguiente estructura:
        {{
          "project": "HUMANOS",
          "episode_id": "EP0001",
          "character_name": "{character_name}",
          "sources": [
            {{
              "title": "Título de la fuente",
              "url": "https://...",
              "type": "official | news | biography | database | archive",
              "tier": "A | B | C | D | F",
              "notes": "Notas sobre lo que sustenta esta fuente"
            }}
          ]
        }}
        """
        sources_data = self.client.complete_json(sources_json_prompt, system_prompt)

        # ----------------- EDITORIAL DOSSIER GENERATION -----------------
        print(f"[Borges - Editorial Dossier Generator] Generando el Editorial Dossier (Editorial_Dossier.md)...")
        
        dossier_prompt = f"""
        Actúa como BORGES, el Chief Researcher de HUMANOS. Tu misión es redactar el Editorial Dossier definitivo en formato Markdown para {character_name}.
        Enfoque de investigación: {episode_focus}
        
        Usa los siguientes datos estructurados que has descubierto:
        - Investigación Base: {json.dumps(research_data, ensure_ascii=False)}
        - Cronología: {json.dumps(timeline_data, ensure_ascii=False)}
        - Afirmaciones Clave: {json.dumps(claims_data, ensure_ascii=False)}
        
        Debes formatear la salida estrictamente en Markdown, con el siguiente contenido estructurado:
        
        # Editorial Dossier: {character_name}
        
        ## 1. Editorial Thesis
        Una tesis editorial potente sobre el personaje y su decisión. ¿Por qué esta historia importa hoy? (Enfoque humano, no de negocios plano).
        
        ## 2. The Big Decision
        - **La Decisión Clave:** Detalle del punto de no retorno.
        - **El Conflicto Existencial:** El choque de fuerzas opuestas.
        - **The Stakes (Riesgos y Pérdidas):** Qué estaba en juego y qué sacrificó.
        - **La Transformación:** La metamorfosis del personaje y su entorno.
        - **El Legado Histórico:** Por qué resuena hoy.
        
        ## 3. Hook Ideas
        Propón exactamente 3 ideas de ganchos (hooks) de 3 segundos específicos para video vertical, enfocados en la paradoja o decisión.
        
        ## 4. Emotional Turning Points
        Los picos y valles emocionales de la historia que guiarán la narración y edición.
        
        ## 5. Timeline
        Una cronología dramática y simplificada enfocada en la escalada hacia la decisión y sus consecuencias directas (no eventos irrelevantes de su niñez o retiro).
        
        ## 6. Visual Opportunities
        Lista de assets visuales concretos a buscar para hacer sentir el drama (entrevistas históricas, fotos de época, videos, mapas de conflicto, interfaces antiguas, recortes de prensa).
        
        ## 7. Primary Sources & Quotes
        - Citas textuales verificadas que demuestren su obsesión o conflicto.
        - Libros, documentales o bases de datos de alta credibilidad (Tier A/B).
        
        ## 8. Interesting Facts
        Datos curiosos de color que aporten textura humana o paradoja a la historia.
        
        ## 9. Research Risks
        Advertencias sobre datos inciertos, leyendas urbanas o puntos grises que Veritas debe auditar.
        
        ## 10. Recommendation
        Elección de formato: "90 segundos" (Short) o "Long Documentary" con justificación editorial detallada.
        
        Escribe únicamente el contenido de Markdown limpio.
        """
        dossier_md = self.client.complete_text(dossier_prompt, system_prompt)

        logs = (
            f"Investigación finalizada para {character_name}. Se recuperaron {len(research_data.get('suggested_assets', []))} sugerencias de assets, "
            f"{len(timeline_data.get('timeline', []))} hitos cronológicos, y el motor de descubrimiento catalogó {len(asset_manifest.get('assets', []))} assets históricos reales. "
            f"Se extrajeron {len(claims_data.get('claims', []))} afirmaciones (claims) y {len(sources_data.get('sources', []))} fuentes estructuradas."
        )
        print(f"[Borges] Investigación, afirmaciones, fuentes y Dossier Editorial completados con éxito.")

        return research_data, timeline_data, sources_md, asset_manifest, claims_data, sources_data, dossier_md, logs


