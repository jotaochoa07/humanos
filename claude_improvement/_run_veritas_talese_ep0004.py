"""
Script puente de un solo uso: corre Veritas (fact-check del guion largo
locutado) y Talese (comparacion editorial v3_optimizado vs locutado_final)
sobre EP0004_Ferruccio_Lamborghini.

Ninguno de los dos agentes tenia un modo pensado para el guion LARGO por
actos (verify_manual_script de Veritas espera script_short/newsletter/
linkedin_post; run_immediate_retro de Talese compara script_short_original
vs script_short). Este puente reusa el mismo cliente y los mismos system
prompts pero les pasa el guion largo y las dos versiones del beat_sheet.

Se puede borrar despues de correrlo. No modifica agentes existentes.
"""
import os
import sys
import json
from datetime import datetime

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, BASE)
os.chdir(BASE)

from openrouter_client import OpenRouterClient
from veritas import VeritasAgent
from talese import TaleseAgent

EP = os.path.join(BASE, "personajes", "Ferruccio_Lamborghini", "EP0004_Ferruccio_Lamborghini")

def load_env():
    env_path = os.path.join(BASE, ".env")
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            k, v = line.split("=", 1)
            k = k.strip()
            v = v.strip().strip("'").strip('"')
            if k not in os.environ:
                os.environ[k] = v

load_env()

with open(os.path.join(EP, "02_SCRIPT", "script_long.md"), "r", encoding="utf-8") as f:
    script_long = f.read()
with open(os.path.join(EP, "01_RESEARCH", "approved_claims.json"), "r", encoding="utf-8") as f:
    approved_claims = json.load(f)
with open(os.path.join(EP, "01_RESEARCH", "research.json"), "r", encoding="utf-8") as f:
    research_data = json.load(f)
with open(os.path.join(EP, "02_SCRIPT", "scripts_long.json"), "r", encoding="utf-8") as f:
    scripts_long = json.load(f)

client = OpenRouterClient()

# ---------- VERITAS: fact-check del guion largo locutado ----------
print("=" * 60)
print("VERITAS - fact check del guion largo (locutado_final)")
print("=" * 60)

veritas = VeritasAgent(client)
# Reusa verify_manual_script pasando el guion LARGO como si fuera el
# contenido a auditar (el metodo solo necesita texto + approved_claims +
# research_data, es agnostico al formato).
audit, logs = veritas.verify_manual_script(
    character_name="Ferruccio Lamborghini",
    scripts_data={"script_short": script_long, "newsletter": "", "linkedin_post": ""},
    research_data=research_data,
    approved_claims=approved_claims,
)
print(logs)

veritas_out_path = os.path.join(EP, "01_RESEARCH", "veritas_audit_locutado_final.json")
with open(veritas_out_path, "w", encoding="utf-8") as f:
    json.dump({"audited_at": datetime.now().isoformat(), "target": "script_long.md (locutado_final)", "script_audit": audit}, f, ensure_ascii=False, indent=2)
print(f"Guardado en {veritas_out_path}")

# ---------- TALESE: aprendizaje entre versiones (v3_optimizado vs locutado_final) ----------
print()
print("=" * 60)
print("TALESE - aprendizaje entre versiones (v3_optimizado vs locutado_final)")
print("=" * 60)

talese = TaleseAgent(base_dir=BASE)
talese.system_prompt_path = os.path.join(BASE, "agents", "talese", "prompts", "system_prompt.md")
system_prompt = talese._get_system_prompt()

# Extraer version v3_optimizado del version_history para comparar
v3_entry = next((v for v in scripts_long.get("version_history", []) if v.get("version") == "v3_optimizado"), None)
locutado_entry = next((v for v in scripts_long.get("version_history", []) if v.get("version") == "locutado_final"), None)

prompt = f"""
Analiza el episodio 'EP0004_Ferruccio_Lamborghini' comparando dos versiones
sucesivas del guion largo documental (mismo episodio, no episodios distintos):

VERSION ANTERIOR (v3_optimizado, generada por Claude en sesion de escritorio,
sin pasar por locucion real):
{json.dumps(v3_entry, ensure_ascii=False, indent=2)}

VERSION NUEVA (locutado_final, edicion manual de Jota en el panel editorial,
grabada como voz en off real):
{json.dumps(locutado_entry, ensure_ascii=False, indent=2)}

GUION COMPLETO DE LA VERSION NUEVA (locutado_final):
---
{script_long}
---

Jota quiere aprendizaje de oficio, no solo un veredicto de aprobado/rechazado.
Genera un informe estructurado JSON con exactamente estas claves:
{{
  "creator_intent": "Que buscaba lograr Jota al editar/locutar esta version sobre la v3_optimizado",
  "editorial_delta": "Que corto, que agrego, que enfatizo Jota respecto a la version de Claude. Se especifico: cita las frases que cambiaron.",
  "what_worked": "Que mejoro la version locutada respecto a la v3_optimizado (ritmo, precision, voz)",
  "what_surprised": "Decision editorial inesperada de Jota (ej: por que corto el cierre retorico del Acto 5)",
  "next_experiment": "Una sola hipotesis pequena y accionable para el proximo episodio, basada en este delta",
  "proposed_observations": [
    {{
      "axis": "nombre_del_eje (ej: hook_structure, pacing, tone, precision_factual)",
      "title": "Titulo corto de la observacion",
      "description": "Explicacion basada en evidencia del delta de edicion"
    }}
  ]
}}
"""

try:
    result_json = client.complete_json(prompt=prompt, system_prompt=system_prompt, model=talese.model_name)
except Exception as e:
    print(f"[Talese] Error LLM: {e}")
    result_json = {"error": str(e)}

talese_out_path = os.path.join(EP, "EPISODE_LEARNING_v3_vs_locutado.json")
with open(talese_out_path, "w", encoding="utf-8") as f:
    json.dump({"generated_at": datetime.now().isoformat(), "compares": ["v3_optimizado", "locutado_final"], "report": result_json}, f, ensure_ascii=False, indent=2)
print(f"Guardado en {talese_out_path}")

review_md = f"""# Aprendizaje entre versiones — EP0004 Ferruccio Lamborghini
*v3_optimizado (Claude) -> locutado_final (Jota, panel editorial + locucion real)*
*Generado por Gay Talese: {datetime.now().strftime('%Y-%m-%d %H:%M')}*

## 1. Intencion del creador
{result_json.get('creator_intent', 'N/A')}

## 2. Delta editorial
{result_json.get('editorial_delta', 'N/A')}

## 3. Lo que funciono / Lo que sorprendio
* **Fortalezas:** {result_json.get('what_worked', 'N/A')}
* **Sorpresa:** {result_json.get('what_surprised', 'N/A')}

## 4. Experimento para el proximo episodio
{result_json.get('next_experiment', 'N/A')}

---
*Tales Rule: "Talese no mide exito. Mide evolucion."*
"""
review_md_path = os.path.join(EP, "EPISODE_LEARNING_v3_vs_locutado.md")
with open(review_md_path, "w", encoding="utf-8") as f:
    f.write(review_md)
print(f"Guardado en {review_md_path}")

print()
print("LISTO.")
