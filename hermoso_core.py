import os
import json
import datetime

class HermosoCore:
    def __init__(self, base_dir: str = "C:/Users/Jota Ochoa/Antigravity/02_Projects/humanos"):
        self.base_dir = base_dir

    def sanitize_name(self, name: str) -> str:
        """Sanitiza nombres para directorios (reemplaza espacios por guiones bajos)."""
        return name.strip().replace(" ", "_")

    def get_episode_folder(self, character_name: str, episode_num: int) -> str:
        """Devuelve la ruta física del episodio."""
        char_folder = self.sanitize_name(character_name)
        ep_folder = f"EP{episode_num:04d}_{char_folder}"
        return os.path.join(self.base_dir, "PERSONAJES", char_folder, ep_folder)

    def create_episode_structure(self, character_name: str, episode_num: int) -> str:
        """Crea la estructura física de carpetas local para un episodio de 10 carpetas."""
        ep_path = self.get_episode_folder(character_name, episode_num)
        
        subfolders = [
            "01_RESEARCH",
            "02_SCRIPT",
            "03_STORYBOARD",
            "04_IMAGES",
            "05_VIDEO",
            "06_AUDIO",
            "07_MUSIC",
            "08_BROLL",
            "09_PROJECT",
            "10_EXPORTS"
        ]
        
        for folder in subfolders:
            os.makedirs(os.path.join(ep_path, folder), exist_ok=True)
            
        # Asegurar la creación de la biblioteca global de medios
        self.create_media_library_structure()
        return ep_path

    def create_media_library_structure(self) -> None:
        """Crea la biblioteca global de medios (MEDIA_LIBRARY) y sus subcarpetas."""
        media_path = os.path.join(self.base_dir, "MEDIA_LIBRARY")
        subfolders = [
            "BROLL/TECH", "BROLL/MONEY", "BROLL/CITY", "BROLL/PHONES", "BROLL/OFFICES", "BROLL/PEOPLE", "BROLL/TRAINS", "BROLL/AIRPORTS",
            "MUSIC/INSPIRATIONAL", "MUSIC/TENSION", "MUSIC/DRAMATIC", "MUSIC/TRIUMPH",
            "SFX/WHOOSH", "SFX/CLICKS", "SFX/GLITCH", "SFX/NOTIFICATIONS",
            "BRANDS/APPLE", "BRANDS/GOOGLE", "BRANDS/META", "BRANDS/MICROSOFT",
            "LOCATIONS/NEW_YORK", "LOCATIONS/SAN_FRANCISCO", "LOCATIONS/SILICON_VALLEY", "LOCATIONS/LONDON",
            "TECH_OBJECTS/IPHONES", "TECH_OBJECTS/COMPUTERS", "TECH_OBJECTS/SERVERS", "TECH_OBJECTS/SATELLITES",
            "UI_SCREENSHOTS/WHATSAPP", "UI_SCREENSHOTS/AIRBNB", "UI_SCREENSHOTS/UBER", "UI_SCREENSHOTS/YOUTUBE",
            "BRANDING/video", "BRANDING/audio"
        ]
        for folder in subfolders:
            os.makedirs(os.path.join(media_path, folder), exist_ok=True)

        # Migración automática desde la carpeta vieja assets/branding
        legacy_branding = os.path.join(self.base_dir, "assets", "branding")
        dest_branding = os.path.join(media_path, "BRANDING")
        if os.path.exists(legacy_branding):
            import shutil
            print(f"[Hermoso Core] Migrando automáticamente biblioteca de branding heredada de {legacy_branding} a {dest_branding}...")
            for root, dirs, files in os.walk(legacy_branding):
                rel_path = os.path.relpath(root, legacy_branding)
                target_dir = os.path.normpath(os.path.join(dest_branding, rel_path))
                os.makedirs(target_dir, exist_ok=True)
                for file in files:
                    src_file = os.path.join(root, file)
                    dst_file = os.path.join(target_dir, file)
                    if not os.path.exists(dst_file):
                        shutil.copy2(src_file, dst_file)

    def get_standard_asset_name(self, char_name: str, index: int, description: str, extension: str) -> str:
        """Devuelve el nombre formateado según la convención de naming de HUMANOS."""
        # Tomamos las primeras 3 letras del personaje en mayúsculas como prefijo
        prefix = self.sanitize_name(char_name)[:3].upper()
        clean_desc = self.sanitize_name(description).upper()
        return f"{prefix}_{index:03d}_{clean_desc}.{extension.strip('.')}"

    def write_json(self, file_path: str, data: dict) -> None:
        """Escribe un diccionario JSON en disco de forma formateada."""
        with open(file_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def write_markdown(self, file_path: str, content: str) -> None:
        """Escribe contenido de texto plano / markdown en disco."""
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    def log_agent_run(self, ep_path: str, agent_name: str, status: str, log_messages: str) -> None:
        """Registra la ejecución de un agente en un log local."""
        log_file = os.path.join(ep_path, "agent_runs.log")
        timestamp = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] Agent: {agent_name} | Status: {status}\nLogs:\n{log_messages}\n{'-'*50}\n"
        
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(log_entry)
            
    def update_status_local(self, ep_path: str, new_status: str) -> None:
        """Actualiza un archivo de estado local en el directorio del episodio."""
        state_file = os.path.join(ep_path, "pipeline_state.json")
        state = {
            "status": new_status,
            "last_updated": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
        self.write_json(state_file, state)
