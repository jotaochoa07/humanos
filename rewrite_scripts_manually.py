import os
import json
import sys
import subprocess
from openrouter_client import OpenRouterClient
from moore import MooreAgent
from asset_collector import AssetCollector

def load_env():
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    os.environ[k.strip()] = v.strip()

def rewrite():
    load_env()
    base_path = "C:/Users/Jota Ochoa/Antigravity/02_Projects/humanos/personajes"
    
    # Validar variable de entorno obligatoria
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("[ERROR] La variable de entorno OPENROUTER_API_KEY no está configurada.")
        print("Configúrala antes de ejecutar este script o colócala en tu archivo .env.")
        sys.exit(1)
        
    client = OpenRouterClient()

    # ---------------------------------------------
    # 1. JAN KOUM
    # ---------------------------------------------
    jk_dir = os.path.join(base_path, "Jan_Koum", "EP0001_Jan_Koum")
    jk_script_short = (
        "¿Sabías que el fundador de WhatsApp dependía de cupones de comida?\n"
        "Antes de conectar a miles de millones de personas, Jan Koum era un inmigrante intentando sobrevivir.\n"
        "Y tenía una obsesión: la privacidad.\n"
        "Koum creció en la Unión Soviética, donde el teléfono no era solo un teléfono.\n"
        "Era la posibilidad de que alguien estuviera escuchando.\n"
        "Y cuando un niño aprende que hablar puede ser peligroso, no lo olvida.\n"
        "A los 16 llegó a Estados Unidos.\n"
        "Sin dinero.\n"
        "Sin inglés.\n"
        "Sin épica.\n"
        "Su madre limpiaba casas.\n"
        "Él barría supermercados.\n"
        "Años después, Facebook lo rechazó.\n"
        "Entonces creó WhatsApp.\n"
        "Una app sin anuncios.\n"
        "Sin juegos.\n"
        "Sin feed.\n"
        "Sin likes.\n"
        "Solo mensajes.\n"
        "Una persona hablando con otra.\n"
        "Y nadie más en la habitación.\n"
        "Lo paradójico es que en 2014 vendió WhatsApp a Facebook por 19 mil millones de dólares.\n"
        "Y firmó el acuerdo en el mismo edificio de asistencia social donde, años antes, hacía fila con su madre para recibir comida.\n"
        "Facebook.\n"
        "La empresa obsesionada con saberlo todo compró una app creada por alguien que desconfiaba de quienes escuchan demasiado.\n"
        "Koum duró cuatro años allí.\n"
        "Luego se fue.\n"
        "Sin manifiesto.\n"
        "Sin drama.\n"
        "Solo se fue.\n"
        "Yo soy Jota y esto es HUMANOS:\n"
        "historias de personas que construyeron desde una herida, una obsesión o una contradicción. Nos vemos en la próxima historia."
    )
    jk_newsletter = (
        "## La paranoia de Jan Koum y el precio de la intimidad\n\n"
        "La mayoría de las biografías de Jan Koum relatan el clásico sueño americano: el inmigrante ucraniano que limpiaba pisos en un supermercado y terminó firmando la venta de su empresa a Facebook sobre el capó de su Porsche por 19.000 millones de dólares. Pero esa narrativa elude la verdadera fuerza motriz de su vida: una paranoia de origen estatal convertida en obsesión de mercado.\n\n"
        "Koum no fundó WhatsApp para revolucionar la mensajería ni para enriquecerse. La fundó para recrear una burbuja de privacidad que le fue negada en su infancia. En la Ucrania soviética de los años 80, cada llamada telefónica era tratada como propiedad pública del régimen. El silencio no era solo la ausencia de ruido; era la única forma segura de comunicarse. Cuando Koum llegó a Silicon Valley, encontró que el nuevo capitalismo de vigilancia hacía exactamente lo mismo que el Politburó soviético, pero bajo el nombre de 'experiencia personalizada' y 'publicidad orientada'. Su obsesión consistía en desafiar ese modelo.\n\n"
        "WhatsApp nació con una regla draconiana: 'Sin anuncios, sin juegos, sin trucos'. No almacenaban mensajes en servidores ni pedían nombres ni fechas de nacimiento. Para el ecosistema financiero de Silicon Valley, esto era absurdo; estaban desperdiciando minas de oro de información. Pero para Koum, esa austeridad de datos era la fortaleza. La paradoja de su vida culminó cuando vendió su creación a Mark Zuckerberg. La tensión entre la obsesión de Koum por el cifrado extremo y la necesidad existencial de Facebook por monetizar la atención del usuario era inevitable. Al final, Koum renunció y abandonó millones en acciones no devengadas. Demostró que, para algunos hombres, la privacidad no es un costo de transacción ni un eufemismo corporativo: es el único espacio donde se puede ser libre."
    )
    jk_linkedin = (
        "Jan Koum vendió WhatsApp por $19,000 millones, pero su mayor legado fue lo que rechazó. "
        "Habiendo crecido en la Ucrania soviética bajo sospecha de vigilancia estatal, la privacidad para él era la esencia de la libertad, no un nicho de mercado. "
        "Cuando Facebook intentó romper el cifrado de su app para monetizar los datos de sus usuarios, Koum renunció y dejó una fortuna sobre la mesa. "
        "En un mundo donde los datos personales se comercializan sin pudor, Koum nos recuerda que algunos principios no tienen precio de adquisición."
    )
    jk_scenes_vo = [
        "¿Sabías que el fundador de WhatsApp dependía de cupones de comida? Antes de conectar a miles de millones de personas, Jan Koum era un inmigrante intentando sobrevivir. Y tenía una obsesión: la privacidad.",
        "Koum creció en la Unión Soviética, donde el teléfono no era solo un teléfono. Era la posibilidad de que alguien estuviera escuchando. Y cuando un niño aprende que hablar puede ser peligroso, no lo olvida.",
        "A los 16 llegó a Estados Unidos. Sin dinero. Sin inglés. Sin épica. Su madre limpiaba casas. Él barría supermercados. Años después, Facebook lo rechazó. Entonces creó WhatsApp.",
        "Una app sin anuncios. Sin juegos. Sin feed. Sin likes. Solo mensajes. Una persona hablando con otra. Y nadie más en la habitación.",
        "Lo paradójico es que en 2014 vendió WhatsApp a Facebook por 19 mil millones de dólares. Y firmó el acuerdo en el mismo edificio de asistencia social donde, años antes, hacía fila con su madre para recibir comida.",
        "Facebook. La empresa obsesionada con saberlo todo compró una app creada por alguien que desconfiaba de quienes escuchan demasiado. Koum duró cuatro años allí. Luego se fue. Sin manifiesto. Sin drama. Solo se fue. Yo soy Jota y esto es HUMANOS: historias de personas que construyeron desde una herida, una obsesión o una contradicción. Nos vemos en la próxima historia."
    ]

    episodes = [
        ("Jan Koum", jk_dir, jk_script_short, jk_newsletter, jk_linkedin, jk_scenes_vo)
    ]

    for char_name, dir_path, script_short, newsletter, linkedin, scenes_vo in episodes:
        if not os.path.exists(dir_path):
            print(f"[Aviso] El directorio {dir_path} no existe. Saltando...")
            continue

        scripts_file = os.path.join(dir_path, "02_SCRIPT", "scripts.json")
        
        # Guardar scripts.json
        if os.path.exists(scripts_file):
            print(f"\n[Curie] Actualizando guiones en {scripts_file}...")
            with open(scripts_file, "r", encoding="utf-8") as f:
                data = json.load(f)
            data["script_short"] = script_short
            data["newsletter"] = newsletter
            data["linkedin_post"] = linkedin
            
            # Actualizar escenas secuenciales
            data["scenes"] = []
            for idx, vo in enumerate(scenes_vo):
                data["scenes"].append({
                    "scene": idx + 1,
                    "duration": 6.0,
                    "voiceover": vo,
                    "visual_intent": "Material de archivo representativo o logo",
                    "required_assets": [],
                    "emotional_purpose": "Desarrollar la narrativa del guion manual"
                })
            
            with open(scripts_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            # Escribir archivos md sueltos
            with open(os.path.join(dir_path, "02_SCRIPT", "script_short.md"), "w", encoding="utf-8") as f:
                f.write(f"# Guion Corto: {char_name}\n\n{script_short}")
            with open(os.path.join(dir_path, "02_SCRIPT", "newsletter.md"), "w", encoding="utf-8") as f:
                f.write(newsletter)
                
        # 1. Cargar datos de investigación para Moore
        research_dir = os.path.join(dir_path, "01_RESEARCH")
        manifest_path = os.path.join(research_dir, "asset_manifest.json")
        claims_path = os.path.join(research_dir, "approved_claims.json")
        
        with open(manifest_path, "r", encoding="utf-8") as f:
            manifest_data = json.load(f)
        with open(claims_path, "r", encoding="utf-8") as f:
            approved_claims = json.load(f)
            
        # 2. Curie: Mapear assets con AssetCollector
        print("[Curie] Escaneando assets físicos y actualizando registro...")
        collector = AssetCollector(dir_path)
        registry_data = collector.registry
        
        # 3. Moore: Diseñar producción basándose en el guion modificado
        print("[Moore] Diseñando producción y storyboard para el nuevo guion...")
        moore = MooreAgent(client)
        storyboard_json, asset_gaps_json, shotlist_md, editing_notes_md, production_package_json, moore_logs = moore.execute_production(
            char_name, manifest_data, registry_data, data, approved_claims
        )
        
        # Guardar entregables de Moore en 03_STORYBOARD
        storyboard_dir = os.path.join(dir_path, "03_STORYBOARD")
        with open(os.path.join(storyboard_dir, "storyboard.json"), "w", encoding="utf-8") as f:
            json.dump(storyboard_json, f, ensure_ascii=False, indent=2)
        with open(os.path.join(storyboard_dir, "asset_gaps.json"), "w", encoding="utf-8") as f:
            json.dump(asset_gaps_json, f, ensure_ascii=False, indent=2)
        with open(os.path.join(storyboard_dir, "shotlist.md"), "w", encoding="utf-8") as f:
            f.write(shotlist_md)
        with open(os.path.join(storyboard_dir, "editing_notes.md"), "w", encoding="utf-8") as f:
            f.write(editing_notes_md)
        with open(os.path.join(storyboard_dir, "production_package.json"), "w", encoding="utf-8") as f:
            json.dump(production_package_json, f, ensure_ascii=False, indent=2)
            
        print("[Moore] Storyboard y assets de producción guardados.")

    # 4. Correr Empaquetador de CapCut
    print("\n[Packager] Ejecutando compilador de paquetes de edición...")
    try:
        subprocess.run(["python", "capcut_packager.py"], check=True)
        print("[Packager] Paquetes de edición generados correctamente.")
    except Exception as e:
        print(f"[ERROR Packager] Falló la ejecución de capcut_packager.py: {e}")

    print("\nSincronización del guion manual y pipeline downstream completados.")

if __name__ == "__main__":
    rewrite()
