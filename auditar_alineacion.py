"""
auditar_alineacion — revisa que TODOS los agentes estén alineados con la
constitución de marca.

Por qué existe
--------------
El 2026-08-01 se descubrió que ningún agente leía los documentos de marca de
Jota. Mr. You operaba con una tesis de canal —"Jota Ochoa construye cosas con
IA"— que la estrategia v1.0 contradice de forma explícita ("Jota Ochoa no debe
construirse como una marca de inteligencia artificial").

Si esa contradicción existió sin que nadie la viera durante meses, hay que
asumir que hay más. Este script las busca de forma sistemática.

Qué hace
--------
Por cada agente del sistema: lee su system_prompt.md, su SOUL.md y su
personality.md, y le pide a un modelo que los confronte contra la constitución
buscando contradicciones concretas y citables.

Seguro para correr sin supervisión:
  - SOLO LECTURA sobre los agentes. No modifica un solo prompt.
  - Escribe un unico informe en claude_improvement/.
  - Si un agente falla, sigue con el resto y lo registra.

Uso:
    python auditar_alineacion.py
"""

import os
import sys
import json
import argparse
from datetime import datetime

import env_boot
import marca

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
AGENTS_DIR = os.path.join(BASE_DIR, "agents")
JOTAOS_AGENTS = r"C:\JotaOS\agents"
SALIDA = os.path.join(BASE_DIR, "claude_improvement", "AUDITORIA_ALINEACION.md")
LOG = os.path.join(BASE_DIR, "_LAB", "auditar_alineacion.log")

MODELO = os.environ.get("AUDIT_MODEL", "anthropic/claude-sonnet-5")

# Agentes que participan del pipeline editorial. Dali y BuilderJota quedan
# fuera a proposito: pertenecen a la linea Lab IA, no a HUMANOS.
AGENTES = ["mr-you", "borges", "veritas", "gabo", "moore",
           "leonardo", "mark", "talese", "curie", "hermoso"]

ARCHIVOS = ["prompts/system_prompt.md", "SOUL.md", "personality.md",
            "brand_bible.md"]


def registrar(msg):
    linea = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    print(linea, flush=True)
    try:
        os.makedirs(os.path.dirname(LOG), exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
    except OSError:
        pass


def leer_agente(nombre, limite=14000):
    """Junta todo lo que define a un agente, del repo y de JotaOS."""
    piezas, encontrados = [], []
    for raiz in (os.path.join(AGENTS_DIR, nombre),
                 os.path.join(JOTAOS_AGENTS, nombre)):
        for rel in ARCHIVOS:
            p = os.path.join(raiz, *rel.split("/"))
            if os.path.exists(p):
                clave = rel
                if clave in encontrados:
                    continue  # el repo manda sobre JotaOS
                encontrados.append(clave)
                with open(p, "r", encoding="utf-8", errors="ignore") as f:
                    piezas.append(f"### {rel}\n\n{f.read()}")
    return "\n\n".join(piezas)[:limite], encontrados


SISTEMA = """Eres un auditor de coherencia de marca. Tu trabajo NO es mejorar
los prompts ni hacerlos mas obedientes: es detectar donde un agente esta
trabajando con un criterio distinto del de la marca.

Reglas:
1. Cita TEXTUAL el fragmento del agente, y TEXTUAL la parte de la constitucion.
   Sin citas no hay hallazgo.
2. No inventes contradicciones para parecer util. Si el agente esta alineado,
   decilo y devolve lista vacia. Un informe honesto que dice "todo bien" vale
   mas que uno inflado.
3. Diferencia CONTRADICCION (criterios opuestos) de OMISION (falta algo util).
4. Severidad: alta (postura opuesta a la marca o ignora la pregunta filtro),
   media (tension de enfoque), baja (matiz de redaccion).

MUY IMPORTANTE — como NO auditar:
- Distingui POSTURA de TEMA. Que un agente mencione IA, herramientas o
  automatizacion NO es una desalineacion. Jota usa las olas sin ser definido por
  ellas. El problema seria una postura de guru, de divulgador que resena sin
  construir, o de afiliacion en vez de criterio.
- NO marques como fallo que un agente sea creativo, ambicioso o proponga cosas
  arriesgadas. La marca pide "creatividad fuera de serie". Un agente timido
  tambien esta desalineado, y ese hallazgo SI vale reportarlo.
- Si encontras que la constitucion misma esta mal, limitando o desactualizada,
  decilo en `enmienda_a_la_constitucion`. Auditar hacia arriba tambien es tu
  trabajo: el documento es vivo y revisable.

Responde SOLO con este JSON:
{
  "agente": "...",
  "veredicto": "alineado | tension | contradice",
  "contradicciones": [
    {"severidad": "alta|media|baja",
     "cita_agente": "texto literal del agente",
     "cita_constitucion": "texto literal de la constitucion",
     "por_que": "1-2 lineas",
     "correccion_sugerida": "que frase poner en su lugar"}
  ],
  "omisiones": [
    {"que_falta": "...", "por_que_importa": "...", "donde_anadirlo": "..."}
  ],
  "agente_demasiado_timido": "vacio, o que le falta para proponer con mas audacia",
  "enmienda_a_la_constitucion": "vacio, o que parte de la constitucion cambiarias y por que",
  "resumen": "2 lineas"
}"""


def auditar(cliente, nombre, contenido):
    prompt = f"""AGENTE A AUDITAR: {nombre}

--- SUS ARCHIVOS DE DEFINICION ---
{contenido}

--- FIN ---

Confronta este agente contra la constitucion de marca. Se especifico y honesto."""
    return cliente.complete_json(
        prompt,
        system_prompt=marca.anteponer(SISTEMA, agente="Auditor"),
        model=MODELO,
    )


def escribir_informe(resultados, sin_archivos):
    os.makedirs(os.path.dirname(SALIDA), exist_ok=True)
    contradicen = [r for r in resultados if r.get("veredicto") == "contradice"]
    tension = [r for r in resultados if r.get("veredicto") == "tension"]
    alineados = [r for r in resultados if r.get("veredicto") == "alineado"]

    with open(SALIDA, "w", encoding="utf-8") as f:
        f.write("# Auditoría de alineación de marca\n\n")
        f.write(f"*Generada {datetime.now():%Y-%m-%d %H:%M} · modelo {MODELO}*\n\n")
        f.write("Confronta la definición de cada agente contra "
                "`agents/_MARCA/constitucion_marca.md`.\n\n")
        f.write("**Solo lectura: ningún prompt fue modificado.**\n\n---\n\n")

        f.write("## Resumen\n\n")
        f.write(f"- **Contradicen:** {len(contradicen)} "
                f"({', '.join(r['agente'] for r in contradicen) or '—'})\n")
        f.write(f"- **En tensión:** {len(tension)} "
                f"({', '.join(r['agente'] for r in tension) or '—'})\n")
        f.write(f"- **Alineados:** {len(alineados)} "
                f"({', '.join(r['agente'] for r in alineados) or '—'})\n")
        if sin_archivos:
            f.write(f"- **Sin archivos de definición:** {', '.join(sin_archivos)}\n")
        f.write("\n---\n\n")

        orden = contradicen + tension + alineados
        for r in orden:
            icono = {"contradice": "🔴", "tension": "🟡", "alineado": "🟢"}
            f.write(f"## {icono.get(r.get('veredicto'), '')} {r.get('agente')}\n\n")
            f.write(f"{r.get('resumen', '')}\n\n")

            for c in r.get("contradicciones", []):
                f.write(f"### Contradicción — severidad {c.get('severidad')}\n\n")
                f.write(f"**El agente dice:**\n> {c.get('cita_agente','')}\n\n")
                f.write(f"**La constitución dice:**\n> {c.get('cita_constitucion','')}\n\n")
                f.write(f"**Por qué:** {c.get('por_que','')}\n\n")
                f.write(f"**Corrección sugerida:** {c.get('correccion_sugerida','')}\n\n")

            if r.get("omisiones"):
                f.write("### Omisiones\n\n")
                for o in r["omisiones"]:
                    f.write(f"- **{o.get('que_falta')}** — {o.get('por_que_importa')} "
                            f"*(dónde: {o.get('donde_anadirlo')})*\n")
                f.write("\n")
            if (r.get("agente_demasiado_timido") or "").strip():
                f.write(f"### Demasiado tímido\n\n{r['agente_demasiado_timido']}\n\n")
            f.write("---\n\n")

        # Auditar hacia arriba: la constitución también se revisa.
        enmiendas = [(r["agente"], r["enmienda_a_la_constitucion"])
                     for r in resultados
                     if (r.get("enmienda_a_la_constitucion") or "").strip()]
        if enmiendas:
            f.write("## Enmiendas propuestas a la propia constitución\n\n")
            f.write("Los agentes pueden auditar hacia arriba. Esto es lo que "
                    "proponen cambiar del documento de marca:\n\n")
            for agente, e in enmiendas:
                f.write(f"- **{agente}:** {e}\n")
            f.write("\n---\n\n")

        f.write("## Nota\n\n")
        f.write("Nada se corrigió automáticamente. Cambiar el prompt de un agente "
                "cambia cómo piensa, y eso es decisión de Jota.\n\n")
        f.write("Un agente marcado como *tímido* también está desalineado: la "
                "estrategia pide creatividad fuera de serie, no prudencia.\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--solo", nargs="*", help="auditar solo estos agentes")
    args = ap.parse_args()

    registrar("=" * 60)
    registrar("Auditoria de alineacion de marca iniciada.")

    if not marca.leer_constitucion():
        registrar("ABORTADO: no encuentro la constitucion de marca.")
        return 2

    env_boot.exigir("OPENROUTER_API_KEY", contexto="la auditoria necesita modelo")
    from openrouter_client import OpenRouterClient
    cliente = OpenRouterClient()

    lista = args.solo or AGENTES
    resultados, sin_archivos = [], []

    for nombre in lista:
        contenido, encontrados = leer_agente(nombre)
        if not contenido.strip():
            registrar(f"{nombre}: sin archivos de definicion. Se omite.")
            sin_archivos.append(nombre)
            continue
        registrar(f"{nombre}: auditando ({len(encontrados)} archivos, "
                  f"{len(contenido)} caracteres)...")
        try:
            r = auditar(cliente, nombre, contenido)
            r["agente"] = nombre
            resultados.append(r)
            n = len(r.get("contradicciones", []))
            registrar(f"{nombre}: {r.get('veredicto')} — {n} contradiccion(es)")
        except Exception as e:
            registrar(f"{nombre}: FALLO ({type(e).__name__}: {str(e)[:100]})")
            resultados.append({
                "agente": nombre, "veredicto": "tension",
                "resumen": f"No se pudo auditar: {type(e).__name__}",
                "contradicciones": [], "omisiones": [],
            })

    escribir_informe(resultados, sin_archivos)
    registrar(f"Informe escrito en {SALIDA}")
    registrar(f"{len(resultados)} agentes auditados.")
    registrar("Auditoria completada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
