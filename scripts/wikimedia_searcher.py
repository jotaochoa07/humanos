import os
import sys
import json
import urllib.request
import urllib.parse
import argparse
import re

# Añadir el directorio raíz al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asset_collector import AssetCollector

def search_wikimedia_commons(query_str: str) -> tuple:
    """
    Busca en Wikimedia Commons un término de búsqueda.
    Retorna (direct_url, file_title) de la primera coincidencia, o (None, None).
    """
    encoded_query = urllib.parse.quote(query_str)
    # Buscamos en namespace 6 (Files) y solicitamos el URL directo de la imagen
    api_url = f"https://commons.wikimedia.org/w/api.php?action=query&generator=search&gsrsearch={encoded_query}&gsrnamespace=6&gsrlimit=1&prop=imageinfo&iiprop=url&format=json"
    
    try:
        req = urllib.request.Request(api_url, headers={"User-Agent": "HUMANOS-Agent-System/1.0 (contact@humanos.com)"})
        with urllib.request.urlopen(req, timeout=15) as response:
            data = json.loads(response.read().decode("utf-8"))
            pages = data.get("query", {}).get("pages", {})
            if not pages:
                return None, None
            
            # Obtener la primera página de resultados
            page = next(iter(pages.values()))
            title = page.get("title", "")
            image_info = page.get("imageinfo", [{}])[0]
            direct_url = image_info.get("url", "")
            
            return direct_url, title
    except Exception as e:
        print(f"[Wikimedia Searcher] Error buscando '{query_str}': {e}")
        return None, None

def search_and_download_assets(ep_path: str):
    manifest_path = os.path.join(ep_path, "01_RESEARCH", "asset_manifest.json")
    if not os.path.exists(manifest_path):
        print(f"[Wikimedia Searcher] [ERROR] No se encontró el manifiesto de assets en: {manifest_path}")
        return
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    collector = AssetCollector(ep_path)
    character_name = manifest.get("character_name", "protagonista")
    assets = manifest.get("assets", [])
    
    print(f"\n[Wikimedia Searcher] Escaneando {len(assets)} sugerencias de assets para {character_name}...")
    
    any_downloaded = False
    for idx, asset in enumerate(assets):
        asset_id = asset.get("asset_id", f"{idx+1:03d}")
        # Si ya fue descargado, saltamos
        if asset.get("downloaded"):
            continue
            
        title = asset.get("title", "")
        asset_type = asset.get("type", "photo")
        
        # Construir consulta
        # Si el título ya contiene el nombre del personaje, lo usamos directamente. De lo contrario, lo combinamos
        search_query = title
        if character_name.lower() not in title.lower():
            search_query = f"{character_name} {title}"
            
        print(f"\n[Wikimedia Searcher] Buscando asset {asset_id}: '{search_query}' (Tipo: {asset_type})...")
        direct_url, file_title = search_wikimedia_commons(search_query)
        
        if not direct_url:
            print(f"[Wikimedia Searcher] No se encontraron resultados en Wikimedia Commons.")
            continue
            
        print(f"[Wikimedia Searcher] Coincidencia encontrada: '{file_title}' -> {direct_url}")
        
        # Descargar el archivo usando el motor del Collector
        # Reemplazar url original del manifest por la url directa encontrada para que el Collector lo procese
        asset["url"] = direct_url
        # Aseguramos que tenga el dominio de wikimedia para que download_wikimedia_commons lo acepte con el literal 'File:'
        clean_title = file_title.replace("File:", "").strip()
        asset["url"] = "https://commons.wikimedia.org/wiki/File:" + urllib.parse.quote(clean_title.replace(" ", "_"))
        
        # Ejecutar descarga
        updated_asset = collector.download_wikimedia_commons(asset)
        if updated_asset.get("downloaded"):
            print(f"[Wikimedia Searcher] Asset {asset_id} descargado exitosamente!")
            assets[idx] = updated_asset
            any_downloaded = True
        else:
            print(f"[Wikimedia Searcher] Falló la descarga automática.")
            
    if any_downloaded:
        manifest["assets"] = assets
        with open(manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, ensure_ascii=False, indent=2)
        print("\n[Wikimedia Searcher] Manifiesto actualizado en disco.")
    else:
        print("\n[Wikimedia Searcher] No se descargaron nuevos assets en esta corrida.")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Buscar y descargar assets de Wikimedia Commons para un episodio.")
    parser.add_argument("--ep_path", type=str, required=True, help="Ruta física del episodio")
    args = parser.parse_args()
    
    search_and_download_assets(args.ep_path)
