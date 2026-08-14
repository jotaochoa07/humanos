"""
direccion_semanal — Mr. You lee la semana y devuelve dirección de canal.

Es la Fase 5 de su sistema operativo (Postmortem & Aprendizaje) convertida en
un proceso que corre solo, sin que nadie lo pida.

Qué lee
-------
`_LAB/channel_daily.jsonl`, la serie histórica que escribe `capturar_canal.py`.
Compara la captura de hoy contra la de hace 7 días y le entrega a Mr. You los
deltas reales: qué video creció, cuál se enfrió, cómo se mueve la retención.

Qué escribe
-----------
`_LAB/direccion_canal/YYYY-MM-DD.md` — una nota corta y accionable.

Honestidad forzada
------------------
Mr. You solo puede afirmar PATRON si hay al menos dos capturas separadas en el
tiempo. Con una sola, esta obligado a decir que todavia no puede comparar. Esa
regla esta en el prompt y en el codigo, porque la version que "sonaba segura
sin datos" ya costo un episodio falso.

Uso:
    python direccion_semanal.py
    python direccion_semanal.py --ventana 14
"""

import os
import sys
import json
import argparse
from datetime import datetime, date, timedelta

import env_boot
import canal
import marca

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAB_DIR = os.path.join(BASE_DIR, "_LAB")
DIARIO = os.path.join(LAB_DIR, "channel_daily.jsonl")
SALIDA_DIR = os.path.join(LAB_DIR, "direccion_canal")

MODELO = os.environ.get("MR_YOU_MODEL", "anthropic/claude-sonnet-5")


def leer_serie():
    if not os.path.exists(DIARIO):
        return []
    filas = []
    with open(DIARIO, encoding="utf-8") as f:
        for linea in f:
            if linea.strip():
                try:
                    filas.append(json.loads(linea))
                except json.JSONDecodeError:
                    continue
    filas.sort(key=lambda x: x.get("fecha", ""))
    return filas


def calcular_deltas(serie, ventana_dias):
    """Compara la captura mas reciente contra la mas cercana a hace N dias."""
    if len(serie) < 2:
        return None

    hoy = serie[-1]
    objetivo = date.fromisoformat(hoy["fecha"]) - timedelta(days=ventana_dias)
    anterior = min(
        serie[:-1],
        key=lambda x: abs((date.fromisoformat(x["fecha"]) - objetivo).days),
    )

    def indexar(cap):
        return {v.get("video"): v for v in cap.get("videos", [])}

    a, b = indexar(anterior), indexar(hoy)
    cambios = []
    for vid, actual in b.items():
        previo = a.get(vid)
        if not previo:
            cambios.append({"video": vid, "estado": "nuevo",
                            "views": actual.get("views")})
            continue
        cambios.append({
            "video": vid,
            "views_antes": previo.get("views"),
            "views_ahora": actual.get("views"),
            "views_delta": (actual.get("views") or 0) - (previo.get("views") or 0),
            "retencion_antes": previo.get("averageViewPercentage"),
            "retencion_ahora": actual.get("averageViewPercentage"),
            "subs_delta": (actual.get("subscribersGained") or 0)
                          - (previo.get("subscribersGained") or 0),
        })
    cambios.sort(key=lambda c: c.get("views_delta", 0), reverse=True)

    return {
        "desde": anterior["fecha"],
        "hasta": hoy["fecha"],
        "dias_reales": (date.fromisoformat(hoy["fecha"])
                        - date.fromisoformat(anterior["fecha"])).days,
        "canal_antes": anterior.get("canal", {}),
        "canal_ahora": hoy.get("canal", {}),
        "por_video": cambios,
    }


PROMPT_SISTEMA = """Eres Mr. You, Chief YouTube Officer del canal de Jota Ochoa.

Esta no es una evaluacion de Greenlight. Es tu revision periodica de CANAL:
mirar como se movio el portfolio y decir que conviene hacer despues.

REGLAS QUE NO PUEDES ROMPER:
1. Clasifica cada afirmacion como DATO, PATRON, HIPOTESIS o BEST_PRACTICE_EXTERNA.
2. Si solo hay UNA captura en la serie historica, NO puedes hablar de tendencia.
   Di explicitamente que todavia no hay con que comparar.
3. No inventes cifras. Si un numero no esta en los datos, no existe.
4. Se breve. Esto lo lee alguien que produce, no alguien que analiza.
5. Las metricas informan; no deciden. Un dato de corto plazo no alcanza para
   recomendar abandonar un formato o una linea. Si igual creés que hay que
   hacerlo, argumentalo y decí que evidencia te convenceria de lo contrario.
   Jota "no quiere producir por ansiedad de metricas": mostrale lo que ocurrio,
   no lo empujes.
6. Si la unica forma de subir un numero es adoptar una postura que Jota evita
   (guru que ya llego, vendedor de humo, fabricar polarizacion), señalalo en vez
   de proponerlo — y ofrece una alternativa que consiga algo parecido sin eso.
7. Si algo del criterio de marca te impide dar una buena lectura, DECILO y
   propone la enmienda. Preferimos un agente que discute con criterio a uno que
   obedece sin pensar.

Responde SOLO con este JSON:
{
  "titular": "una frase con lo mas importante de la semana",
  "lectura": "3-5 lineas interpretando el movimiento real",
  "que_funciona": [{"observacion": "...", "tipo_evidencia": "..."}],
  "que_se_enfria": [{"observacion": "...", "tipo_evidencia": "..."}],
  "recomendacion_publicar": "que conviene publicar despues y por que",
  "riesgo_a_vigilar": "...",
  "lo_que_no_se": ["..."],
  "confianza": "alta | media | baja"
}"""


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--ventana", type=int, default=7)
    args = ap.parse_args()

    serie = leer_serie()
    resumen = canal.resumen_para_mr_you()

    if not serie:
        raise SystemExit(
            "No hay serie historica todavia.\n"
            "Corre primero 'Programar Captura Diaria.bat' o "
            "'python capturar_canal.py'."
        )

    deltas = calcular_deltas(serie, args.ventana)

    if deltas is None:
        print("\n" + "=" * 72)
        print(" DIRECCION DE CANAL — Mr. You")
        print("=" * 72)
        print(f"  Solo hay {len(serie)} captura en la serie historica.")
        print("  Mr. You no puede hablar de tendencia con un solo punto.")
        print("  Vuelve a correr esto cuando haya al menos dos dias capturados.")
        print("=" * 72 + "\n")
        return 0

    env_boot.exigir("OPENROUTER_API_KEY", contexto="Mr. You necesita modelo")
    from openrouter_client import OpenRouterClient
    cliente = OpenRouterClient()

    prompt = f"""REVISION DE CANAL — {deltas['desde']} a {deltas['hasta']}
({deltas['dias_reales']} dias reales de diferencia entre capturas)

--- ESTADO DEL CANAL ---
Antes : {json.dumps(deltas['canal_antes'], ensure_ascii=False)}
Ahora : {json.dumps(deltas['canal_ahora'], ensure_ascii=False)}

--- MOVIMIENTO POR VIDEO ---
{json.dumps(deltas['por_video'][:15], ensure_ascii=False, indent=2)}

--- CAPA DE CANAL (calidad de la evidencia) ---
{json.dumps({
    'hay_evidencia_real': resumen['hay_evidencia_real'],
    'conteos': resumen['conteos'],
    'promedios_solo_reales': resumen['promedios_solo_reales'],
}, ensure_ascii=False, indent=2)}

--- CAPTURAS DISPONIBLES ---
{len(serie)} dias en la serie historica.

Da tu lectura de canal."""

    print(f"[Mr. You] Analizando {deltas['dias_reales']} dias con {MODELO}...")
    r = cliente.complete_json(
        prompt,
        system_prompt=marca.anteponer(PROMPT_SISTEMA, agente="Mr. You (semanal)"),
        model=MODELO,
    )

    print("\n" + "=" * 72)
    print(f" DIRECCION DE CANAL — {deltas['desde']} a {deltas['hasta']}")
    print("=" * 72)
    print(f"\n  {r.get('titular', '')}\n")
    print(f"  {r.get('lectura', '')}\n")
    print("  FUNCIONA:")
    for x in r.get("que_funciona", []):
        print(f"    + {x.get('observacion')}  [{x.get('tipo_evidencia')}]")
    print("  SE ENFRIA:")
    for x in r.get("que_se_enfria", []):
        print(f"    - {x.get('observacion')}  [{x.get('tipo_evidencia')}]")
    print(f"\n  PUBLICAR DESPUES: {r.get('recomendacion_publicar')}")
    print(f"  RIESGO          : {r.get('riesgo_a_vigilar')}")
    print(f"  CONFIANZA       : {r.get('confianza')}")
    if r.get("lo_que_no_se"):
        print("  NO SE:")
        for x in r["lo_que_no_se"]:
            print(f"    ? {x}")
    print("=" * 72 + "\n")

    os.makedirs(SALIDA_DIR, exist_ok=True)
    destino = os.path.join(SALIDA_DIR, f"{date.today().isoformat()}.md")
    with open(destino, "w", encoding="utf-8") as f:
        f.write(f"# Dirección de canal — {deltas['desde']} a {deltas['hasta']}\n\n")
        f.write(f"*Mr. You · {MODELO} · generado {datetime.now():%Y-%m-%d %H:%M}*\n\n")
        f.write(f"## {r.get('titular','')}\n\n{r.get('lectura','')}\n\n")
        f.write("## Funciona\n")
        for x in r.get("que_funciona", []):
            f.write(f"- {x.get('observacion')} `[{x.get('tipo_evidencia')}]`\n")
        f.write("\n## Se enfría\n")
        for x in r.get("que_se_enfria", []):
            f.write(f"- {x.get('observacion')} `[{x.get('tipo_evidencia')}]`\n")
        f.write(f"\n## Qué publicar después\n{r.get('recomendacion_publicar','')}\n")
        f.write(f"\n## Riesgo a vigilar\n{r.get('riesgo_a_vigilar','')}\n")
        f.write(f"\n## Lo que Mr. You no sabe\n")
        for x in r.get("lo_que_no_se", []):
            f.write(f"- {x}\n")
        f.write(f"\n---\n*Confianza declarada: {r.get('confianza')}*\n")
    print(f"  Guardado en: {destino}\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
