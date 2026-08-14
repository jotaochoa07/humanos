"""
insumos_produccion — lo que los datos le enseñan al OFICIO, no a la dirección.

La distinción (Jota, 2026-08-01)
--------------------------------
Los mismos números sirven para dos cosas muy distintas, y confundirlas fue el
error de la mañana:

  DIRECCION EDITORIAL   qué producir, si seguir con un formato, qué línea empujar
                        -> NO la deciden los datos. La decide la visión de Jota.

  OFICIO / PRODUCCION   retención, ritmo, dónde abandona la gente, largo del
                        hook, duración óptima de plano
                        -> ACA el dato es alimento directo. Sirve, y mucho.

Sus palabras: *"que sea un alimento para el proyecto, no necesariamente para la
dirección editorial"*.

Este módulo produce SOLO lo segundo. No opina sobre qué publicar ni sobre si el
formato largo conviene. Responde una pregunta distinta: **dado que vamos a
producir esto, ¿qué nos enseñó lo anterior sobre cómo hacerlo mejor?**

Se sirve en el panel bajo `/api/mr-you/insumos`.
"""

import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAB_DIR = os.path.join(BASE_DIR, "_LAB")
DIARIO = os.path.join(LAB_DIR, "channel_daily.jsonl")
MAPA = os.path.join(LAB_DIR, "youtube_video_map.json")


def _cargar_json(path, por_defecto):
    if not os.path.exists(path):
        return por_defecto
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return por_defecto


def _ultima_captura():
    if not os.path.exists(DIARIO):
        return None
    ultima = None
    with open(DIARIO, encoding="utf-8") as f:
        for linea in f:
            if linea.strip():
                try:
                    ultima = json.loads(linea)
                except json.JSONDecodeError:
                    continue
    return ultima


def calcular():
    """Devuelve insumos de producción, separados por línea de producto."""
    captura = _ultima_captura()
    mapa = _cargar_json(MAPA, {})

    if not captura:
        return {
            "disponible": False,
            "motivo": "Todavía no hay capturas del canal. Corré la captura diaria.",
            "insumos": [],
        }

    piezas = []
    for v in captura.get("videos", []):
        info = mapa.get(v.get("video"))
        if not info:
            continue  # videos ajenos al proyecto (inmobiliaria, hoteles)
        dur = v.get("averageViewDuration")
        pct = v.get("averageViewPercentage")
        # Duración total reconstruida desde los dos datos que sí tenemos.
        total = round(dur / (pct / 100)) if dur and pct else None
        piezas.append({
            "episodio": info["episode_id"],
            "titulo": info["titulo"],
            "linea": info.get("linea", "HUMANOS"),
            "duracion_total_s": total,
            "segundos_vistos": dur,
            "retencion_pct": pct,
            "vistas": v.get("views"),
            "shares": v.get("shares"),
            "likes": v.get("likes"),
            "subs_ganados": v.get("subscribersGained"),
        })

    humanos = [p for p in piezas if p["linea"] == "HUMANOS" and p["segundos_vistos"]]
    humanos.sort(key=lambda p: p["segundos_vistos"], reverse=True)

    insumos = []

    # --- Insumo 1: techo de atención observado ------------------------------
    if humanos:
        mejor = humanos[0]
        insumos.append({
            "titulo": "Techo de atención observado",
            "valor": f"{mejor['segundos_vistos']}s",
            "detalle": (
                f"El máximo de atención sostenida que consiguió una pieza de "
                f"HUMANOS son {mejor['segundos_vistos']} segundos, en «{mejor['titulo']}» "
                f"({mejor['retencion_pct']}% de {mejor['duracion_total_s']}s)."
            ),
            "para_que_sirve": (
                "Referencia de ritmo: hasta ese punto la atención está probada. "
                "Después de ese punto, cada minuto hay que ganárselo con estructura."
            ),
            "tipo": "oficio",
            "evidencia": "DATO",
        })

    # --- Insumo 2: dispersión de retención ---------------------------------
    if len(humanos) >= 2:
        pcts = [p["retencion_pct"] for p in humanos if p["retencion_pct"]]
        if pcts:
            mn, mx = min(pcts), max(pcts)
            peor = min(humanos, key=lambda p: p["retencion_pct"] or 999)
            mejor_ret = max(humanos, key=lambda p: p["retencion_pct"] or 0)
            insumos.append({
                "titulo": "Rango de retención en HUMANOS",
                "valor": f"{mn:.0f}% – {mx:.0f}%",
                "detalle": (
                    f"«{mejor_ret['titulo']}» retiene {mejor_ret['retencion_pct']}% y "
                    f"«{peor['titulo']}» retiene {peor['retencion_pct']}%. "
                    f"{mx - mn:.0f} puntos de diferencia entre piezas del mismo formato."
                ),
                "para_que_sirve": (
                    "La diferencia no la explica la duración: la explica cómo está "
                    "armada la apertura. Vale comparar los primeros 15 segundos de "
                    "la mejor contra la peor y ver qué cambió."
                ),
                "tipo": "oficio",
                "evidencia": "DATO",
            })

    # --- Insumo 3: propagación ---------------------------------------------
    con_shares = [p for p in humanos if p.get("shares")]
    if con_shares:
        top = max(con_shares, key=lambda p: p["shares"])
        ratio = round((top["shares"] / top["vistas"]) * 1000, 1) if top["vistas"] else None
        insumos.append({
            "titulo": "Pieza más compartida",
            "valor": f"{top['shares']} shares",
            "detalle": (
                f"«{top['titulo']}» — {top['shares']} veces compartida"
                + (f", {ratio} por cada 1.000 vistas." if ratio else ".")
            ),
            "para_que_sirve": (
                "Compartir es la señal más honesta de que una historia funcionó: "
                "alguien puso su reputación en ella. Vale identificar qué momento "
                "de esa pieza la gente estaba citando."
            ),
            "tipo": "oficio",
            "evidencia": "DATO",
        })

    # --- Insumo 4: conversión a suscriptor ---------------------------------
    con_subs = [p for p in humanos if p.get("subs_ganados") and p.get("vistas")]
    if con_subs:
        top = max(con_subs, key=lambda p: p["subs_ganados"] / p["vistas"])
        tasa = round((top["subs_ganados"] / top["vistas"]) * 100, 2)
        insumos.append({
            "titulo": "Mejor conversión a suscriptor",
            "valor": f"{tasa}%",
            "detalle": (
                f"«{top['titulo']}» convirtió {top['subs_ganados']} suscriptores "
                f"sobre {top['vistas']} vistas."
            ),
            "para_que_sirve": (
                "Suscribirse después de ver es la señal de que la persona quiere "
                "MÁS de esto. Mide el cierre, no la apertura: vale revisar cómo "
                "termina esa pieza."
            ),
            "tipo": "oficio",
            "evidencia": "DATO",
        })

    # --- Lo que todavía no se puede saber ----------------------------------
    faltan = [
        "Curva de abandono segundo a segundo (requiere el reporte "
        "audienceWatchRatio de la API; hoy solo se trae el promedio).",
        "Retención a los 3 segundos por pieza.",
        "De dónde llega el tráfico (browse, búsqueda, sugeridos).",
    ]

    return {
        "disponible": True,
        "capturado_en": captura.get("capturado_en"),
        "canal": captura.get("canal", {}),
        "piezas": piezas,
        "insumos": insumos,
        "no_disponible_todavia": faltan,
        "nota_de_uso": (
            "Todo esto es insumo de OFICIO: cómo producir mejor. No es dirección "
            "editorial. Qué producir y con qué frecuencia lo decide la visión de "
            "Jota, no estos números."
        ),
    }


if __name__ == "__main__":
    print(json.dumps(calcular(), indent=2, ensure_ascii=False))
