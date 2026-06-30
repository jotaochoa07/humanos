import os
import json
import urllib.request

class OpenRouterClient:
    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "")
        self.api_url = "https://openrouter.ai/api/v1/chat/completions"

    def complete_json(self, prompt: str, system_prompt: str = "Eres un asistente experto.") -> dict:
        """Realiza una consulta a OpenRouter exigiendo un formato JSON de respuesta con reintentos."""
        import time
        if not self.api_key:
            raise ValueError("La variable de entorno OPENROUTER_API_KEY no está configurada.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
            "X-Title": "HUMANOS AI Agent System"
        }

        payload = {
            "model": "google/gemini-2.5-flash-lite",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"},
            "max_tokens": 8000
        }

        req = urllib.request.Request(
            self.api_url, 
            data=json.dumps(payload).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )

        max_attempts = 3
        for attempt in range(1, max_attempts + 1):
            try:
                with urllib.request.urlopen(req, timeout=60) as response:
                    res_body = response.read().decode("utf-8")
                    res_json = json.loads(res_body)
                    
                    choices = res_json.get("choices")
                    if not choices:
                        raise ValueError(f"Respuesta inválida de OpenRouter (sin choices): {res_body}")
                        
                    content = choices[0]["message"]["content"].strip()
                    
                    if content.startswith("```json"):
                        content = content[7:]
                    if content.startswith("```"):
                        content = content[3:]
                    if content.endswith("```"):
                        content = content[:-3]
                    content = content.strip()
                    
                    try:
                        return json.loads(content)
                    except json.JSONDecodeError as jde:
                        print(f"[ERROR] Intento {attempt}/{max_attempts}: Falló parseo de JSON. Reintentando...")
                        if attempt == max_attempts:
                            print(f"[ERROR] JSON parse final failed on: \n{content}\n")
                            raise jde
            except Exception as e:
                print(f"[ERROR OpenRouter] Intento {attempt}/{max_attempts} falló: {e}")
                if attempt == max_attempts:
                    raise e
                time.sleep(2)

    def complete_text(self, prompt: str, system_prompt: str = "Eres un asistente experto.") -> str:
        """Realiza una consulta de texto libre a OpenRouter."""
        if not self.api_key:
            raise ValueError("La variable de entorno OPENROUTER_API_KEY no está configurada.")

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/google-deepmind/antigravity",
            "X-Title": "HUMANOS AI Agent System"
        }

        payload = {
            "model": "google/gemini-2.5-flash-lite",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": prompt}
            ]
        }

        req = urllib.request.Request(
            self.api_url, 
            data=json.dumps(payload).encode("utf-8"), 
            headers=headers, 
            method="POST"
        )

        try:
            with urllib.request.urlopen(req) as response:
                res_body = response.read().decode("utf-8")
                res_json = json.loads(res_body)
                return res_json["choices"][0]["message"]["content"]
        except Exception as e:
            print(f"[ERROR OpenRouter] Falló la llamada al LLM: {e}")
            raise e
