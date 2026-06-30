import os
import re
import json
import urllib.request
import urllib.parse
import hashlib
from hermoso_core import HermosoCore

class AssetCollector:
    def __init__(self, ep_path: str):
        self.ep_path = ep_path
        self.hermoso = HermosoCore()
        self.registry_path = os.path.join(ep_path, "asset_registry.json")
        self.metadata_path = os.path.join(ep_path, "01_RESEARCH", "metadata")
        os.makedirs(self.metadata_path, exist_ok=True)
        
        # Cargar registro de deduplicación
        self.registry = self._load_registry()

    def _load_registry(self) -> list:
        if os.path.exists(self.registry_path):
            try:
                with open(self.registry_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception:
                return []
        return []

    def _save_registry(self) -> None:
        with open(self.registry_path, "w", encoding="utf-8") as f:
            json.dump(self.registry, f, ensure_ascii=False, indent=2)

    def calculate_hash(self, file_path: str) -> str:
        """Calcula el hash SHA-256 de un archivo físico."""
        sha256 = hashlib.sha256()
        with open(file_path, "rb") as f:
            while chunk := f.read(8192):
                sha256.update(chunk)
        return sha256.hexdigest()

    def get_destination_folder(self, asset_type: str) -> str:
        """Devuelve la subcarpeta correspondiente al tipo de asset según el estándar de 10 carpetas."""
        mapping = {
            "photo": "04_IMAGES",
            "logo": "04_IMAGES",
            "screenshot": "04_IMAGES",
            "video": "05_VIDEO",
            "audio": "06_AUDIO",
            "music": "07_MUSIC",
            "broll": "08_BROLL",
            "article_clip": "01_RESEARCH",
            "quote": "01_RESEARCH"
        }
        subfolder = mapping.get(asset_type, "04_IMAGES")
        folder_path = os.path.join(self.ep_path, subfolder)
        os.makedirs(folder_path, exist_ok=True)
        return folder_path

    def deduplicate_asset(self, file_hash: str) -> str:
        """Verifica si el hash ya existe en el registro local. Devuelve la ruta existente o None."""
        for entry in self.registry:
            if entry["hash"] == file_hash:
                return entry["storage_path"]
        return None

    def download_wikimedia_commons(self, asset: dict) -> dict:
        """Descarga un archivo desde Wikimedia Commons de manera automática."""
        url = asset.get("url", "")
        if "commons.wikimedia.org" not in url:
            return asset # No es de Wikimedia Commons

        print(f"[Asset Collector] Intentando descargar de Wikimedia: {url}")
        
        # 1. Resolver la URL directa de la imagen desde la página de Wikimedia File:
        # Buscamos el nombre del archivo de la URL
        # Wikimedia Commons URLs can be formatted as File:Name.jpg or wiki/File:Name.jpg
        # We need to extract the filename portion after 'File:' and handle parameters like '?uselang=en'
        match = re.search(r"File:([^?#]+)", url)
        if not match:
            # Fallback a ver si es un enlace directo a upload.wikimedia.org
            if "upload.wikimedia.org" in url:
                raw_url = url
                file_name = os.path.basename(url.split("?")[0])
            else:
                print(f"[Asset Collector] URL de Wikimedia no formateada como 'File:': {url}")
                return asset
        else:
            file_name_encoded = match.group(1)
            # Deshacer codificación url-encoded y reemplazar guiones bajos por espacios para la API de MediaWiki si es necesario
            file_name = urllib.parse.unquote(file_name_encoded).replace("_", " ")
            file_name_query = urllib.parse.quote(f"File:{file_name}")
            
            api_url = f"https://commons.wikimedia.org/w/api.php?action=query&titles={file_name_query}&prop=imageinfo&iiprop=url&format=json"
            try:
                print(f"[Asset Collector] Consultando API Wikimedia: {api_url}")
                req = urllib.request.Request(api_url, headers={"User-Agent": "HUMANOS-Agent-System/1.0 (contact@humanos.com)"})
                with urllib.request.urlopen(req) as response:
                    data = json.loads(response.read().decode("utf-8"))
                    pages = data.get("query", {}).get("pages", {})
                    page = next(iter(pages.values()))
                    image_info = page.get("imageinfo", [{}])[0]
                    raw_url = image_info.get("url", "")
            except Exception as e:
                print(f"[Asset Collector] No se pudo obtener el URL directo de la API de Wikimedia: {e}")
                return asset

        if not raw_url:
            print(f"[Asset Collector] No se pudo resolver URL cruda de Wikimedia.")
            return asset

        # 2. Descargar el archivo
        dest_folder = self.get_destination_folder(asset.get("type", "photo"))
        _, ext = os.path.splitext(file_name)
        if not ext:
            ext = ".jpg"
            
        parent_dir = os.path.basename(os.path.dirname(self.ep_path))
        try:
            asset_idx = int(asset.get("asset_id", "1"))
        except ValueError:
            asset_idx = 1
            
        description_slug = asset.get("title", "asset")
        sanitized_filename = self.hermoso.get_standard_asset_name(parent_dir, asset_idx, description_slug, ext)
        local_file_path = os.path.join(dest_folder, sanitized_filename)

        try:
            print(f"[Asset Collector] Descargando desde: {raw_url}")
            req = urllib.request.Request(raw_url, headers={"User-Agent": "HUMANOS-Agent-System/1.0"})
            with urllib.request.urlopen(req) as response, open(local_file_path, "wb") as out_file:
                out_file.write(response.read())
            
            # 3. Calcular hash SHA-256
            file_hash = self.calculate_hash(local_file_path)
            
            # 4. Comprobar deduplicación
            existing_path = self.deduplicate_asset(file_hash)
            if existing_path:
                print(f"[Asset Collector] Asset duplicado encontrado. Removiendo descarga temporal y enlazando a: {existing_path}")
                os.remove(local_file_path)
                asset["downloaded"] = True
                asset["local_path"] = existing_path
                return asset

            # 5. Generar archivo de metadatos asociado
            metadata_file = os.path.join(self.metadata_path, f"{sanitized_filename}.json")
            metadata = {
                "asset_id": asset.get("asset_id"),
                "title": asset.get("title"),
                "source": asset.get("source"),
                "url": url,
                "raw_download_url": raw_url,
                "license": asset.get("license"),
                "file_size_bytes": os.path.getsize(local_file_path),
                "hash": file_hash,
                "downloaded_at": datetime_str()
            }
            with open(metadata_file, "w", encoding="utf-8") as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            # 6. Registrar en el registro global del episodio
            self.registry.append({
                "asset_id": asset.get("asset_id"),
                "hash": file_hash,
                "source": asset.get("source"),
                "storage_path": local_file_path
            })
            self._save_registry()

            asset["downloaded"] = True
            asset["local_path"] = local_file_path
            print(f"[Asset Collector] Descargado y catalogado con éxito en: {local_file_path}")

        except Exception as e:
            print(f"[Asset Collector] Error al descargar asset {asset.get('asset_id')}: {e}")
            if os.path.exists(local_file_path):
                os.remove(local_file_path)

        return asset

    def collect_all_assets(self, manifest: dict) -> dict:
        """Itera por los assets del manifiesto e intenta descargar los de Wikimedia Commons."""
        updated_assets = []
        for asset in manifest.get("assets", []):
            if "wikimedia.org" in asset.get("url", ""):
                updated_asset = self.download_wikimedia_commons(asset)
                updated_assets.append(updated_asset)
            else:
                updated_assets.append(asset)
        
        manifest["assets"] = updated_assets
        return manifest

def datetime_str():
    import datetime
    return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
