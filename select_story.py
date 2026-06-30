import os
import json
import urllib.request
import sys
import subprocess

def load_env():
    env = {}
    if os.path.exists(".env"):
        with open(".env", "r", encoding="utf-8") as f:
            for line in f:
                if "=" in line and not line.strip().startswith("#"):
                    k, v = line.strip().split("=", 1)
                    env[k.strip()] = v.strip()
    return env

def query_supabase(url, key, query_url, method="GET", data=None):
    headers = {
        "apikey": key,
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "Prefer": "return=representation" if method in ["POST", "PATCH"] else ""
    }
    
    req = urllib.request.Request(
        query_url,
        data=json.dumps(data).encode("utf-8") if data else None,
        headers=headers,
        method=method
    )
    
    try:
        with urllib.request.urlopen(req, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except Exception as e:
        print(f"[ERROR Supabase] {e}")
        return None

def main():
    env = load_env()
    supabase_url = env.get("SUPABASE_URL")
    supabase_key = env.get("SUPABASE_KEY")
    openrouter_key = env.get("OPENROUTER_API_KEY") or os.environ.get("OPENROUTER_API_KEY")

    if not supabase_url or not supabase_key:
        print("[ERROR] Credenciales de Supabase no configuradas en el archivo .env.")
        sys.exit(1)

    print("="*60)
    print("HUMANOS - Selección Editorial de Historias (Supabase)")
    print("="*60)

    # 1. Traer backlog de historias en estado 'idea' o 'needs_research'
    api_endpoint = f"{supabase_url}/rest/v1/humanos_stories?editorial_status=in.(idea,needs_research)&select=id,protagonist_name,human_angle,domain_category"
    print("[Supabase] Conectando y trayendo historias pendientes...")
    stories = query_supabase(supabase_url, supabase_key, api_endpoint)

    if not stories:
        print("No se encontraron historias pendientes en Supabase.")
        sys.exit(0)

    print(f"\nSe encontraron {len(stories)} historias:")
    for idx, story in enumerate(stories, 1):
        name = story.get("protagonist_name", "Desconocido")
        angle = story.get("human_angle") or "Sin ángulo específico aún"
        category = story.get("domain_category") or "Sin categoría"
        print(f"[{idx}] {name} | Categoría: {category.upper()}\n    Ángulo: {angle}\n")

    # 2. Elegir personaje
    try:
        choice = input(f"Selecciona el número de la historia a producir (1-{len(stories)}) o 'q' para salir: ")
        if choice.lower() == 'q':
            sys.exit(0)
        selected_idx = int(choice) - 1
        if selected_idx < 0 or selected_idx >= len(stories):
            raise ValueError()
    except ValueError:
        print("Selección inválida.")
        sys.exit(1)

    selected_story = stories[selected_idx]
    protagonist = selected_story["protagonist_name"]
    angle = selected_story.get("human_angle") or "Ángulo general"
    category = selected_story.get("domain_category") or "technology"

    print("\n" + "-"*50)
    print(f"PROCESANDO HISTORIA DE: {protagonist.upper()}")
    print("-"*50)

    # 3. Preguntas de confirmación y refinamiento de Hermoso
    print("\nHermoso: Vamos a configurar el episodio.")
    
    # Pregunta 1: Ángulo narrativo
    angle_input = input(f"¿Qué tipo de ángulo narrativo quieres para este episodio?\n[Por defecto: {angle}]: ").strip()
    final_angle = angle_input if angle_input else angle

    # Pregunta 2: Categoría
    categories = [
        "ENTREPRENEURS", "DESIGNERS", "ARTISTS", "MAKERS", "FOUNDERS", 
        "BUILDERS", "INVENTORS", "CREATORS", "SCIENTISTS", "EXPLORERS", 
        "ENGINEERS", "VISIONARIES"
    ]
    print("\nCategorías disponibles:")
    for idx, cat in enumerate(categories, 1):
        print(f"[{idx}] {cat}")
    
    cat_choice = input(f"\nSelecciona la categoría (1-{len(categories)}) [Por defecto: {category.upper()}]: ").strip()
    if cat_choice:
        try:
            final_category = categories[int(cat_choice) - 1].lower()
        except:
            final_category = category.lower()
    else:
        final_category = category.lower()

    # Pregunta 3: Extensión
    print("\nFormatos/Extensión disponibles:")
    print("[1] Short (60-90s)")
    print("[2] Long Form (8-15 min)")
    print("[3] Completo (Ambos formatos + Newsletter + Twitter)")
    ext_choice = input("Selecciona la extensión (1-3) [Por defecto: 3]: ").strip()
    
    # 4. Aprobación final antes de Borges
    print("\n" + "="*50)
    print("RESUMEN EDITORIAL APROBADO:")
    print(f"Protagonista: {protagonist}")
    print(f"Ángulo Narrativo: {final_angle}")
    print(f"Categoría: {final_category.upper()}")
    print(f"Extensión seleccionada: {ext_choice if ext_choice else '3'}")
    print("="*50)

    confirm = input("\n¿Confirmas esta configuración para iniciar la investigación con Borges? (s/n): ").strip().lower()
    if confirm != 's':
        print("Ejecución cancelada por el editor.")
        sys.exit(0)

    # 5. Cambiar estado a 'researching' en Supabase
    print("\n[Supabase] Actualizando estado a 'researching'...")
    update_endpoint = f"{supabase_url}/rest/v1/humanos_stories?id=eq.{selected_story['id']}"
    query_supabase(
        supabase_url, 
        supabase_key, 
        update_endpoint, 
        method="PATCH", 
        data={"editorial_status": "researching", "domain_category": final_category, "human_angle": final_angle}
    )

    # 6. Disparar el pipeline de agentes
    print("\n[Hermoso Core] Detonando pipeline de agentes en cadena...")
    
    # Determinamos número de episodio buscando carpetas existentes
    char_folder_name = protagonist.strip().replace(" ", "_")
    char_path = os.path.join("PERSONAJES", char_folder_name)
    ep_num = 1
    if os.path.exists(char_path):
        existing_eps = [d for d in os.listdir(char_path) if d.startswith("EP")]
        ep_num = len(existing_eps) + 1

    # Ejecutar run_humanos_mvp.py mediante subprocess
    env_vars = os.environ.copy()
    if openrouter_key:
        env_vars["OPENROUTER_API_KEY"] = openrouter_key

    # Pasamos los temas basados en la categoría
    themes = [final_category, "obsesión", "paradoja"]
    
    run_cmd = [
        "python", "run_humanos_mvp.py",
        "--character", protagonist,
        "--focus", final_angle,
        "--themes"
    ] + themes

    try:
        # Ejecutamos el pipeline
        subprocess.run(run_cmd, env=env_vars, check=True)
        
        # Una vez completado con éxito, actualizamos a 'researched' y corremos empaquetado
        print("\n[Supabase] Actualizando estado a 'researched'...")
        query_supabase(
            supabase_url, 
            supabase_key, 
            update_endpoint, 
            method="PATCH", 
            data={"editorial_status": "researched"}
        )
        
        print("\n[Packager] Generando paquetes de producción CapCut...")
        packager_cmd = ["python", "capcut_packager.py"]
        subprocess.run(packager_cmd, check=True)
        
        print("\n" + "="*60)
        print("¡PROCESAMIENTO EDITORIAL COMPLETADO CON ÉXITO!")
        print("="*60)
        
    except Exception as e:
        print(f"\n[ERROR Pipeline] La ejecución del pipeline falló: {e}")
        query_supabase(
            supabase_url, 
            supabase_key, 
            update_endpoint, 
            method="PATCH", 
            data={"editorial_status": "needs_research"}
        )
        sys.exit(1)

if __name__ == "__main__":
    main()
