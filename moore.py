import os
import json
from openrouter_client import OpenRouterClient

class MooreAgent:
    def __init__(self, client: OpenRouterClient):
        self.client = client

    def execute_production(self, character_name: str, manifest_data: dict, registry_data: list, scripts_data: dict, approved_claims: dict) -> tuple:
        """
        Ejecuta el diseño de producción de Moore cruzando con los assets reales.
        Devuelve (storyboard_json_dict, asset_gaps_json_dict, shotlist_md_str, editing_notes_md_str, production_package_json_dict, logs_str).
        """
        print(f"[Moore] Analizando escenas de Gabo y mapeando de forma estricta contra assets reales descargados...")

        system_prompt = (
            "Eres MOORE, el Documentary Producer de HUMANOS. Tu prioridad es la fidelidad documental. "
            "Asocias el guion con assets reales del manifiesto de Borges y marcas de forma honesta como gap todo "
            "recurso que no exista físicamente en la carpeta o que no haya sido descargado en el asset_registry.json.\n"
            "REGLA DE EVITAR RECHAZADOS: No debes incluir ni proponer tomas, referencias visuales, clips o assets relacionados con hechos marcados como REJECTED o UNVERIFIED en approved_claims."
        )

        prompt = f"""
        A partir de las escenas de Gabo:
        {json.dumps(scripts_data.get('scenes', []), ensure_ascii=False, indent=2)}

        Y los assets reales del manifiesto de Borges (asset_manifest.json):
        {json.dumps(manifest_data.get('assets', []), ensure_ascii=False, indent=2)}

        Y los claims auditados (approved_claims.json):
        {json.dumps(approved_claims, ensure_ascii=False, indent=2)}

        Y los archivos que YA están descargados y confirmados físicamente en el registro (asset_registry.json):
        {json.dumps(registry_data, ensure_ascii=False, indent=2)}

        Genera un objeto JSON estructurado con los siguientes campos:
        {{
          "storyboard": [
            {{
              "scene": 1,
              "duration": 5.0,
              "voiceover": "Locución de la escena",
              "selected_asset": "Nombre físico del archivo si está descargado en asset_registry.json, de lo contrario null",
              "selected_asset_id": "asset_id correspondiente si está descargado en asset_registry.json, de lo contrario null",
              "asset_status": "available | missing | reference_only", // available si está en registry.json, reference_only si está en manifest pero no descargado, missing si no hay asset real.
              "fallback_asset_id": "asset_id alternativo del manifest de Borges (si aplica) o null",
              "fallback_strategy": "Explicación breve de qué hacer visualmente ante el gap",
              "effect": "slow_zoom | pan_left | pan_right | fade | cut | text_overlay",
              "caption": "Subtítulo de apoyo en pantalla",
              "gap_id": "gap_001 o null" // Si asset_status es missing o reference_only, debes asignar un gap_id único
            }}
          ],
          "asset_gaps": [
            {{
              "gap_id": "gap_001",
              "scene": 1,
              "missing_asset": "Descripción detallada del asset faltante",
              "criticality": "high | medium | low",
              "reason": "Por qué se necesita este recurso visual históricamente",
              "suggested_solution": "Cómo adquirirlo manualmente (ej: buscar en archivo histórico, prensa local)",
              "manual_search_queries": ["búsqueda recomendada 1", "búsqueda recomendada 2"],
              "ai_generation_allowed": false,
              "ai_generation_prompt": "Prompt de generación IA detallado sólo como último recurso si ai_generation_allowed es true"
            }}
          ],
          "production_package": {{
            "estimated_voiceover_duration": 75.0,
            "asset_count": 12,
            "missing_assets_count": 3,
            "estimated_edit_time_hours": 12.0,
            "music_style": "Documental tension / piano minimalista",
            "visual_style": "Color gradado cálido, textura de grano de película analógica",
            "required_images": ["Lista de imágenes fijas necesarias (retratos reales, fotos de época)"],
            "required_videos": ["Lista de clips de video históricos o metraje de archivo necesario"],
            "required_motion_graphics": ["Lista de motion graphics y gráficos animados necesarios"],
            "required_maps": ["Lista de mapas geográficos o animaciones de mapas necesarias"],
            "required_historical_screenshots": ["Lista de capturas históricas de interfaces, software o prensa necesaria"],
            "required_ai_recreations": ["Lista de prompts o ideas para recrear pasajes visualmente con IA"],
            "recommended_next_action": "Búsqueda manual de retratos del taller en 1948."
          }}
        }}
        """

        moore_output = self.client.complete_json(prompt, system_prompt)

        storyboard_list = moore_output.get("storyboard", [])
        asset_gaps_list = moore_output.get("asset_gaps", [])
        production_package_dict = moore_output.get("production_package", {})

        # --- REGLA DE VALIDACIÓN ESTRICTA (POST-PROCESAMIENTO) ---
        registered_ids = {entry["asset_id"] for entry in registry_data}
        manifest_ids = {asset["asset_id"] for asset in manifest_data.get("assets", [])}
        
        valid_storyboard = []
        for index, item in enumerate(storyboard_list, 1):
            asset_id = item.get("selected_asset_id")
            
            # Regla 1: Si selected_asset_id no está registrado, debe forzarse a null
            if asset_id and asset_id not in registered_ids:
                item["selected_asset_id"] = None
                item["selected_asset"] = None
                
                # Clasificar estado
                if asset_id in manifest_ids:
                    item["asset_status"] = "reference_only"
                else:
                    item["asset_status"] = "missing"
            elif asset_id and asset_id in registered_ids:
                item["asset_status"] = "available"
                # Rellenar con la ruta real del registro
                for reg in registry_data:
                    if reg["asset_id"] == asset_id:
                        item["selected_asset"] = os.path.basename(reg["storage_path"])
                        break
            else:
                item["asset_status"] = "missing"
                item["selected_asset_id"] = None
                item["selected_asset"] = None

            # Regla 2: Generar gap_id automático si falta el asset físicamente
            if item["asset_status"] in ["missing", "reference_only"]:
                if not item.get("gap_id"):
                    item["gap_id"] = f"gap_{index:03d}"
            else:
                item["gap_id"] = None
                
            valid_storyboard.append(item)

        # Alinear gaps de forma correspondiente
        valid_gaps = []
        for gap in asset_gaps_list:
            # Mantener consistencia
            valid_gaps.append(gap)

        # Generar shotlist.md y editing_notes.md
        shotlist_prompt = f"""
        Genera una lista de tomas en formato Markdown (shotlist.md) para {character_name}.
        Debe ser una guía secuencial y limpia para que el editor de video organice el timeline físico.
        Usa los siguientes datos de storyboard validados:
        {json.dumps(valid_storyboard, ensure_ascii=False, indent=2)}
        """
        shotlist_md = self.client.complete_text(shotlist_prompt, system_prompt)

        notes_prompt = f"""
        Genera notas de edición y estilo en formato Markdown (editing_notes.md) para {character_name}.
        Indica el ritmo de corte, sugerencias de color, diseño sonoro, fuentes tipográficas y pautas generales de marca de HUMANOS.
        """
        editing_notes_md = self.client.complete_text(notes_prompt, system_prompt)

        # Generar asset_shotlist.md
        asset_shotlist_prompt = f"""
        Genera una lista de planos accionable llamada "asset_shotlist.md" en formato Markdown para {character_name}.
        Esta lista servirá como puente de comunicación directo entre Moore (diseño de producción), Commet (búsqueda de assets) y Leonardo (diseño/IA).
        
        Usa el siguiente storyboard validado:
        {json.dumps(valid_storyboard, ensure_ascii=False, indent=2)}
        
        El formato de salida DEBE ser limpio, sin explicaciones introductorias ni bloques de código redundantes, estructurado exactamente así:
        
        # EP001 - Shot List - {character_name}
        
        ## Escena [Número de escena con 2 dígitos, ej: 01]
        - [Lista de elementos visuales específicos necesarios para esta escena. Ej: Retrato heroico de Jan Koum]
        - [Estilo de fondo y composición. Ej: Fondo oscuro con mucho espacio negativo]
        - [Movimiento de cámara. Ej: Paneo horizontal lento o zoom suave]
        - Términos de Búsqueda (Inglés): [Términos clave en inglés optimizados para buscar en Pexels, Getty o Google Images, separados por comas. Ej: jan koum serious portrait, black background]
        - Duración: [Duración] s
        - Estado del Asset: [available | missing | reference_only]
        - Archivo Local: [Nombre físico del archivo si está 'available', o 'Pendiente de búsqueda' si falta]
        
        Asegúrate de detallar qué objetos o planos históricos se necesitan en cada frase para que un buscador web (como Commet) pueda encontrar exactamente la imagen o video correspondiente.
        """
        asset_shotlist_md = self.client.complete_text(asset_shotlist_prompt, system_prompt)

        logs = f"storyboard y producción completados. Se registraron {len(valid_storyboard)} escenas en el storyboard y {len(valid_gaps)} gaps de producción."
        print(f"[Moore] Diseño de storyboard y producción completado bajo reglas estrictas.")

        return valid_storyboard, valid_gaps, shotlist_md, editing_notes_md, production_package_dict, asset_shotlist_md, logs
