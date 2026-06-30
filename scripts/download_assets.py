import os
import json
import sys

# Añadir el directorio raíz al path para poder importar módulos
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from asset_collector import AssetCollector

def main():
    print("="*60)
    print("[Asset Downloader] Iniciando descarga automática de assets verificados...")
    print("="*60)
    
    ep_path = "C:/Users/Jota Ochoa/Antigravity/02_Projects/humanos/personajes/Jan_Koum/EP0001_Jan_Koum"
    manifest_path = os.path.join(ep_path, "01_RESEARCH", "asset_manifest.json")
    
    if not os.path.exists(manifest_path):
        print(f"[ERROR] No se encontró el manifiesto en: {manifest_path}")
        sys.exit(1)
        
    with open(manifest_path, "r", encoding="utf-8") as f:
        manifest = json.load(f)
        
    collector = AssetCollector(ep_path)
    updated_manifest = collector.collect_all_assets(manifest)
    
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(updated_manifest, f, ensure_ascii=False, indent=2)
        
    print("="*60)
    print("[Asset Downloader] Proceso finalizado.")
    print("="*60)

if __name__ == "__main__":
    main()
