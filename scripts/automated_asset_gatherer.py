import os
import sys
import json
import urllib.request
import urllib.parse
import subprocess
import re
from curie import CurieAgent

def clean_slug(text):
    """Limpia el texto para generar palabras clave descriptivas en mayúsculas."""
    t = text.lower()
    t = re.sub(r'[^a-z0-9\s]', '', t)
    words = t.split()
    # Palabras irrelevantes a ignorar para el nombre del archivo
    ignored_words = {
        'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 
        'by', 'video', 'footage', 'clip', 'stock', 'illustration', 'image', 'photo', 'james', 'dyson'
    }
    filtered = [w for w in words if w not in ignored_words]
    if not filtered:
        filtered = words[:3]
    return "_".join(filtered).upper()[:30]

def search_pexels(query, asset_type="photo", api_key=None):
    """Realiza una búsqueda de imágenes o videos en la API de Pexels."""
    if not api_key:
        return None
    
    headers = {
        "Authorization": api_key,
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    encoded_query = urllib.parse.quote(query)
    
    if asset_type == "video":
        url = f"https://api.pexels.com/videos/search?query={encoded_query}&per_page=1"
    else:
        url = f"https://api.pexels.com/v1/search?query={encoded_query}&per_page=1"
        
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            if asset_type == "video":
                videos = data.get("videos", [])
                if videos:
                    files = videos[0].get("video_files", [])
                    for f in files:
                        if f.get("link"):
                            return f["link"]
            else:
                photos = data.get("photos", [])
                if photos:
                    return photos[0].get("src", {}).get("large")
    except Exception as e:
        print(f"[Pexels Search] Error al buscar '{query}': {e}")
    return None

def search_wikimedia(query):
    """Busca una imagen libre en Wikimedia Commons utilizando búsqueda semántica API."""
    encoded_query = urllib.parse.quote(query)
    search_url = f"https://commons.wikimedia.org/w/api.php?action=query&list=search&srsearch={encoded_query}&srnamespace=6&format=json&srlimit=1"
    try:
        req = urllib.request.Request(search_url, headers={"User-Agent": "HUMANOS-Agent-System/1.0"})
        with urllib.request.urlopen(req) as response:
            data = json.loads(response.read().decode("utf-8"))
            search_results = data.get("query", {}).get("search", [])
            if search_results:
                title = search_results[0]["title"]
                title_query = urllib.parse.quote(title)
                api_url = f"https://commons.wikimedia.org/w/api.php?action=query&titles={title_query}&prop=imageinfo&iiprop=url&format=json"
                with urllib.request.urlopen(urllib.request.Request(api_url, headers={"User-Agent": "HUMANOS-Agent-System/1.0"})) as info_res:
                    info_data = json.loads(info_res.read().decode("utf-8"))
                    pages = info_data.get("query", {}).get("pages", {})
                    page = next(iter(pages.values()))
                    image_info = page.get("imageinfo", [])
                    if image_info:
                        return image_info[0]["url"]
    except Exception as e:
        print(f"[Wikimedia Search] Error al buscar '{query}': {e}")
    return None

def download_file(url, dest_path):
    """Descarga física de un archivo a disco."""
    try:
        print(f"[Descarga] Guardando: {url} -> {dest_path}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
        with urllib.request.urlopen(req) as response, open(dest_path, "wb") as out_file:
            out_file.write(response.read())
        return True
    except Exception as e:
        print(f"[Descarga] Error al guardar {url}: {e}")
        return False

def download_youtube_clip(youtube_url, dest_path, duration_seconds=10):
    """Descarga los primeros segundos de un video de YouTube como B-roll de referencia usando yt-dlp."""
    print(f"[yt-dlp] Descargando clip de 10s desde: {youtube_url}")
    try:
        cmd = [
            "yt-dlp",
            "-f", "mp4/best",
            "--download-sections", f"*00:00-{duration_seconds:02d}",
            "--force-keyframes-at-cuts",
            "-o", dest_path,
            youtube_url
        ]
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0 and os.path.exists(dest_path):
            print(f"[yt-dlp] Descargado con éxito: {dest_path}")
            return True
        else:
            print(f"[yt-dlp] Error de descarga: {result.stderr}")
            cmd_fallback = [
                "yt-dlp",
                "-f", "best[ext=mp4]",
                "--max-filesize", "20M",
                "-o", dest_path,
                youtube_url
            ]
            fallback_res = subprocess.run(cmd_fallback, capture_output=True, text=True)
            return fallback_res.returncode == 0
    except Exception as e:
        print(f"[yt-dlp] Excepción al invocar descarga: {e}")
        return False

def rewrite_lists(ep_path, character_name, storyboard_list):
    """Actualiza y regenera los reportes de Shot Lists descriptivos para el editor."""
    shotlist_path = os.path.join(ep_path, "03_STORYBOARD", "shotlist.md")
    asset_shotlist_path = os.path.join(ep_path, "03_STORYBOARD", "asset_shotlist.md")
    
    # 1. Regenerar shotlist.md
    shotlist_content = f"# Shot List - {character_name}\n\n"
    for item in storyboard_list:
        shotlist_content += (
            f"## Escena {item['scene']:02d} ({item['duration']}s) - Acto: {item.get('act', 'Hook')}\n"
            f"* **Locución**: {item['voiceover']}\n"
            f"* **Transición/Efecto**: {item.get('effect', 'cut')}\n"
            f"* **Asset Seleccionado**: `{item.get('selected_asset') or 'Pendiente'}` [{item.get('asset_status', 'missing')}]\n"
            f"* **Composición Visual**: {item.get('visual_description', '-')}\n"
            f"* **Subtítulo**: \"{item.get('caption', '-')}\"\n\n"
        )
    with open(shotlist_path, "w", encoding="utf-8") as f:
        f.write(shotlist_content)
        
    # 2. Regenerar asset_shotlist.md
    asset_content = f"# EP003 - Shot List - {character_name}\n\n"
    for item in storyboard_list:
        asset_content += (
            f"## Escena {item['scene']:02d}\n"
            f"- Detalle: {item.get('visual_description', '-')}\n"
            f"- Duración: {item['duration']} s\n"
            f"- Estado del Asset: {item.get('asset_status', 'missing')}\n"
            f"- Archivo Local: `{item.get('selected_asset') or 'Pendiente de búsqueda'}`\n\n"
        )
    with open(asset_shotlist_path, "w", encoding="utf-8") as f:
        f.write(asset_content)

def run_gatherer(ep_path):
    print("="*60)
    print(f"INICIANDO RECOLECTOR INTELIGENTE DE ASSETS EN: {ep_path}")
    print("="*60)
    
    # 1. Rutas de archivos
    storyboard_file = os.path.join(ep_path, "03_STORYBOARD", "storyboard.json")
    gaps_file = os.path.join(ep_path, "03_STORYBOARD", "asset_gaps.json")
    yt_file = os.path.join(ep_path, "03_STORYBOARD", "youtube_candidates.json")
    
    if not os.path.exists(storyboard_file):
        print("[Error] No se encontró el archivo storyboard.json en 03_STORYBOARD.")
        return
        
    with open(storyboard_file, "r", encoding="utf-8") as f:
        storyboard = json.load(f)
        
    yt_candidates = {}
    if os.path.exists(yt_file):
        with open(yt_file, "r", encoding="utf-8") as f:
            yt_candidates = json.load(f)
            
    pexels_key = os.environ.get("PEXELS_API_KEY")
    
    # Obtener prefijo del personaje
    character_name = "James Dyson" # Nombre por defecto
    character_prefix = "JAM"
    # Buscar el nombre real si está en el path del episodio
    match_char = re.search(r"personajes[\\/]([^\\/]+)", ep_path)
    if match_char:
        character_name = match_char.group(1).replace("_", " ")
        character_prefix = match_char.group(1)[:3].upper()
        
    # Inicializar Curie Agent para etiquetar y registrar los assets en la base de datos
    curie = CurieAgent()
    
    img_folder = os.path.join(ep_path, "04_IMAGES")
    video_folder = os.path.join(ep_path, "05_VIDEO")
    os.makedirs(img_folder, exist_ok=True)
    os.makedirs(video_folder, exist_ok=True)
    
    # Leer gaps para cruzarlos
    gaps_dict = {}
    if os.path.exists(gaps_file):
        try:
            with open(gaps_file, "r", encoding="utf-8") as gf:
                for g in json.load(gf):
                    gaps_dict[g.get("scene")] = g
        except Exception:
            pass
            
    for item in storyboard:
        scene_num = item["scene"]
        act = item.get("act", "Hook").upper().replace(" ", "_")
        voiceover = item.get("voiceover", "")
        visual_desc = item.get("visual_description", "")
        
        # Omitir si ya tiene un asset físico registrado y existente
        if item.get("asset_status") == "available" and item.get("selected_asset"):
            local_path = os.path.join(img_folder if item.get("source_type") != "video" else video_folder, item["selected_asset"])
            if os.path.exists(local_path):
                print(f"[Gatherer] Escena {scene_num} ya cuenta con asset local: {item['selected_asset']}")
                continue
                
        # Buscar en el Gap correspondiente
        gap = gaps_dict.get(scene_num, {})
        queries = gap.get("manual_search_queries", [])
        primary_query = queries[0] if queries else visual_desc[:50]
        
        # Determinar si es video
        source_type = item.get("source_type", "STOCK")
        is_video = source_type == "video" or "video" in primary_query.lower() or "footage" in primary_query.lower() or "clip" in primary_query.lower()
        ext = ".mp4" if is_video else ".jpg"
        
        desc_slug = clean_slug(primary_query)
        descriptive_name = f"{character_prefix}_{scene_num:02d}_{act}_{desc_slug}{ext}"
        target_path = os.path.join(video_folder if is_video else img_folder, descriptive_name)
        
        print(f"\n[Mapeando Escena {scene_num}] -> {descriptive_name}")
        
        # 1. Descarga desde Pexels
        download_url = None
        if pexels_key:
            target_type = "video" if is_video else "photo"
            download_url = search_pexels(primary_query, asset_type=target_type, api_key=pexels_key)
            
        # 2. Descarga desde Wikimedia Commons
        if not download_url and not is_video:
            download_url = search_wikimedia(primary_query)
            
        download_success = False
        if download_url:
            download_success = download_file(download_url, target_path)
            
        # 3. Descarga desde YouTube si falla la descarga de Pexels/Wikimedia y hay videos candidatos
        escena_key = f"escena_{scene_num:02d}"
        if not download_success and escena_key in yt_candidates:
            cands = yt_candidates[escena_key].get("candidates", [])
            if cands:
                yt_url = cands[0]["url"]
                download_success = download_youtube_clip(yt_url, target_path)
                
        # 4. Actualizar metadata e indexación de Curie si se descargó con éxito
        if download_success and os.path.exists(target_path):
            item["selected_asset"] = descriptive_name
            item["selected_asset_id"] = f"{scene_num:03d}"
            item["asset_status"] = "available"
            
            # Registrar en la biblioteca semántica de Curie
            tag_text = (
                f"Asset local de HUMANOS. Archivo: {descriptive_name}. "
                f"Uso: Escena {scene_num} (Acto {act}) para {character_name}. "
                f"Descripción visual: {visual_desc}. Locución asociada: {voiceover}."
            )
            curie.ingest_document(character_name, tag_text, source="Descarga Automática de Producción")
        else:
            item["selected_asset"] = None
            item["selected_asset_id"] = None
            item["asset_status"] = "missing"
            
    # Guardar cambios
    with open(storyboard_file, "w", encoding="utf-8") as f:
        json.dump(storyboard, f, ensure_ascii=False, indent=2)
        
    # Regenerar Shot Lists para el editor
    rewrite_lists(ep_path, character_name, storyboard)
    print("\n[Gatherer] Indexación, renombrado descriptivo y shot lists actualizados con éxito.")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python automated_asset_gatherer.py <ruta_del_episodio>")
        sys.exit(1)
    run_gatherer(sys.argv[1])
