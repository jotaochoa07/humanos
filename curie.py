import os
import json
import urllib.request
import numpy as np
from turbovec import TurboQuantIndex

class CurieAgent:
    def __init__(self, client=None, base_dir: str = "C:/Users/Jota Ochoa/Antigravity/02_Projects/humanos"):
        self.base_dir = base_dir
        self.library_dir = os.path.join(self.base_dir, "base_de_datos", "curie_library")
        os.makedirs(self.library_dir, exist_ok=True)
        
        # Si no se pasa el cliente OpenRouter, lo importamos y creamos localmente
        if client is None:
            try:
                from openrouter_client import OpenRouterClient
                self.client = OpenRouterClient()
            except ImportError:
                self.client = None
                print("[Curie] Advertencia: No se pudo importar OpenRouterClient. Se usarán embeddings simulados.")
        else:
            self.client = client

    def _get_embedding(self, text: str) -> np.ndarray:
        """Obtiene el embedding de 1536 dimensiones para un texto usando OpenRouter."""
        if not self.client or not getattr(self.client, "api_key", None):
            # Fallback a embedding aleatorio determinista para pruebas si no hay API key
            print("[Curie] Usando embedding simulado (sin API key de OpenRouter).")
            # Generamos un vector pseudo-aleatorio basado en el hash del texto para consistencia
            np.random.seed(abs(hash(text)) % (2**32))
            vector = np.random.randn(1536).astype(np.float32)
            # Normalizar para similitud de coseno
            norm = np.linalg.norm(vector)
            return vector / norm if norm > 0 else vector

        api_url = "https://openrouter.ai/api/v1/embeddings"
        headers = {
            "Authorization": f"Bearer {self.client.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
            "X-Title": "HUMANOS AI Agent System"
        }
        payload = {
            "model": "openai/text-embedding-3-small",
            "input": [text]
        }

        req = urllib.request.Request(
            api_url,
            data=json.dumps(payload).encode("utf-8"),
            headers=headers,
            method="POST"
        )

        try:
            with urllib.request.urlopen(req, timeout=30) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                embedding = res_json["data"][0]["embedding"]
                return np.array(embedding, dtype=np.float32)
        except Exception as e:
            print(f"[Curie] Error al llamar a la API de embeddings: {e}. Usando fallback simulado.")
            # Fallback determinista
            np.random.seed(abs(hash(text)) % (2**32))
            vector = np.random.randn(1536).astype(np.float32)
            norm = np.linalg.norm(vector)
            return vector / norm if norm > 0 else vector

    def _get_char_paths(self, character_name: str):
        """Retorna las rutas físicas del índice y metadatos de un personaje."""
        char_clean = character_name.strip().replace(" ", "_")
        char_dir = os.path.join(self.library_dir, char_clean)
        os.makedirs(char_dir, exist_ok=True)
        
        index_path = os.path.join(char_dir, "index.tq")
        metadata_path = os.path.join(char_dir, "metadata.json")
        return index_path, metadata_path

    def has_library(self, character_name: str) -> bool:
        """Verifica si el personaje ya tiene biblioteca e índice creados."""
        index_path, metadata_path = self._get_char_paths(character_name)
        return os.path.exists(index_path) and os.path.exists(metadata_path)

    def ingest_document(self, character_name: str, text: str, source: str = "Desconocido"):
        """Ingesta un documento de texto para un personaje, calcula su embedding y actualiza el índice."""
        print(f"[Curie] Ingestando nuevo documento para {character_name}...")
        index_path, metadata_path = self._get_char_paths(character_name)
        
        # 1. Obtener embedding
        vector = self._get_embedding(text)
        
        # 2. Cargar o crear índice turbovec (dimensión 1536, bit_width=4)
        if os.path.exists(index_path):
            index = TurboQuantIndex.load(index_path)
            with open(metadata_path, "r", encoding="utf-8") as f:
                metadata = json.load(f)
        else:
            index = TurboQuantIndex(dim=1536, bit_width=4)
            metadata = {"character_name": character_name, "documents": []}
            
        # 3. Registrar documento en metadatos y agregar vector al índice
        doc_id = len(metadata["documents"])
        metadata["documents"].append({
            "id": doc_id,
            "text": text,
            "source": source,
            "timestamp": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        
        # add espera un array de vectores 2D
        index.add(vector.reshape(1, -1))
        
        # 4. Persistir índice y metadatos
        index.write(index_path)
        with open(metadata_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
            
        print(f"[Curie] Documento ID {doc_id} ingestado e indexado con éxito.")

    def search_library(self, character_name: str, query: str, k: int = 3) -> list:
        """Realiza una búsqueda semántica local en la base de conocimientos del personaje."""
        if not self.has_library(character_name):
            print(f"[Curie] No existe biblioteca indexada para {character_name}.")
            return []
            
        index_path, metadata_path = self._get_char_paths(character_name)
        
        # 1. Obtener embedding de la consulta
        query_vector = self._get_embedding(query)
        
        # 2. Cargar índice y metadatos
        index = TurboQuantIndex.load(index_path)
        with open(metadata_path, "r", encoding="utf-8") as f:
            metadata = json.load(f)
            
        # 3. Realizar búsqueda
        # search espera un array 2D y retorna (distances, indices)
        k_val = min(k, len(metadata["documents"]))
        if k_val == 0:
            return []
            
        distances, indices = index.search(query_vector.reshape(1, -1), k=k_val)
        
        # 4. Formatear y retornar resultados
        results = []
        for rank, idx in enumerate(indices[0]):
            if idx < len(metadata["documents"]):
                doc = metadata["documents"][idx]
                results.append({
                    "text": doc["text"],
                    "source": doc["source"],
                    "distance": float(distances[0][rank])
                })
        return results

    def get_naming_recommendation(self, character_name: str, index: int, description: str, extension: str) -> str:
        """Genera el nombre estandarizado oficial para un asset de medios en la biblioteca de HUMANOS."""
        char_clean = character_name.strip().replace(" ", "_")
        prefix = char_clean[:3].upper()
        clean_desc = char_clean.upper() if not description else description.strip().replace(" ", "_").upper()
        return f"{prefix}_{index:03d}_{clean_desc}.{extension.strip('.')}"

    def get_episode_naming_recommendation(self, character_name: str, episode_num: int) -> str:
        """Genera el nombre estandarizado oficial de la carpeta de un episodio."""
        char_clean = character_name.strip().replace(" ", "_")
        return f"EP{episode_num:04d}_{char_clean}"

import datetime
