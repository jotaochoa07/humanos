import os
import json
from openrouter_client import OpenRouterClient

class LeonardoAgent:
    def __init__(self, client: OpenRouterClient):
        self.client = client
        self.base_dir = os.path.dirname(os.path.abspath(__file__))
        
    def execute_branding(self, character_name: str, scripts_data: dict, storyboard_data: dict, approved_claims: dict) -> tuple:
        """
        Ejecuta la dirección de arte y branding de Leonardo.
        Devuelve (branding_spec_json_dict, branding_spec_md_str, logs_str).
        """
        print(f"[Leonardo] Analizando la dirección de arte y especificaciones visuales para {character_name}...")
        
        # Cargar brand_bible y system_prompt desde sus respectivas rutas
        brand_bible_path = os.path.join(self.base_dir, "agents", "leonardo", "brand_bible.md")
        system_prompt_path = os.path.join(self.base_dir, "agents", "leonardo", "prompts", "system_prompt.md")
        
        if os.path.exists(brand_bible_path):
            with open(brand_bible_path, "r", encoding="utf-8") as f:
                brand_bible = f.read()
        else:
            brand_bible = "Manual de marca no encontrado."
            
        if os.path.exists(system_prompt_path):
            with open(system_prompt_path, "r", encoding="utf-8") as f:
                system_prompt_base = f.read()
        else:
            system_prompt_base = "Eres Leonardo, el Director Creativo de HUMANOS."
            
        system_prompt = (
            f"{system_prompt_base}\n\n"
            f"--- MANUAL DE MARCA (BRAND BIBLE) ---\n"
            f"{brand_bible}"
        )
        
        prompt = f"""
        A partir del guion corto de Gabo:
        {json.dumps(scripts_data.get('script_short', ''), ensure_ascii=False, indent=2)}
        
        Y el storyboard diseñado por Moore:
        {json.dumps(storyboard_data, ensure_ascii=False, indent=2)}
        
        Y los claims auditados:
        {json.dumps(approved_claims, ensure_ascii=False, indent=2)}
        
        Genera una especificación de branding completa para {character_name}.
        El formato de respuesta DEBE ser un JSON con los siguientes campos:
        {{
          "character_card": {{
            "category": "BUILDER | PIONERO | CIENTÍFICO | etc.",
            "name": "Nombre en mayúsculas (ej: JAN KOUM)",
            "description": "Logro o cargo breve en minúsculas (ej: fundador de whatsapp)",
            "visual_style": "Descripción corta de la composición siguiendo la Brand Bible (ej: Retrato documental en primer plano a sangre, fondo fundido a negro, nombre cian, abundantes espacios vacíos)"
          }},
          "thumbnail": {{
            "headline": "Texto corto de curiosidad en minúsculas excepto énfasis (máximo 5 palabras, ej: El hombre que CAMBIÓ la comunicación)",
            "highlight_word": "Palabra exacta a resaltar en cian (ej: CAMBIÓ)",
            "composition_description": "Instrucciones de composición (rostro del personaje ocupando 70-80% de la miniatura, mirada poderosa, fondo desenfocado y oscuro)"
          }},
          "midjourney_prompts": [
            {{
              "purpose": "Retrato de miniatura / B-roll de escena / etc.",
              "prompt": "El prompt en inglés optimizado para Midjourney o Flux siguiendo las leyes de fotografía documental y la fórmula de Leonardo"
            }}
          ],
          "motion_specs": {{
            "camera_speed": "subtle_zoom | pan_slow",
            "default_transition": "subtle_fade | ken_burns",
            "branding_color_use": "Explicación breve de cómo se introduce el cian en las animaciones de este episodio",
            "titles_font": "Satoshi",
            "subtitles_font": "Inter"
          }}
        }}
        """
        
        branding_spec_json = self.client.complete_json(prompt, system_prompt=system_prompt)
        
        # Generar un reporte legible en Markdown
        report_prompt = f"""
        A partir de la especificación de branding generada:
        {json.dumps(branding_spec_json, ensure_ascii=False, indent=2)}
        
        Genera un reporte de dirección de arte detallado y profesional en formato Markdown para {character_name}.
        Enfócate en la justificación estética de por qué elegiste el encuadre, la tipografía y los prompts. Usa un tono directo, sobrio y en español neutro de Latinoamérica.
        """
        branding_spec_md = self.client.complete_text(report_prompt, system_prompt=system_prompt)
        
        logs = f"LeonardoAgent ejecutado con éxito para {character_name}.\nGeneradas especificaciones para miniatura, character card y prompts de IA visual."
        return branding_spec_json, branding_spec_md, logs
