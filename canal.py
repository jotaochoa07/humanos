"""
canal — capa de agregación de métricas del canal Jota Growth.

Por qué existe
--------------
La auditoría del 2026-08-01 identificó el eslabón que faltaba en el sistema:

    Mark (captura por episodio)
            |
            v
    [capa de agregación de canal]  <-- también recibe data de Lab IA
            |
            v
    Mr. You (lee métricas GENERALES -> dirección del canal)

Sin esta capa, Mr. You no puede hacer su trabajo: opinaría sobre el portfolio
sin ver el portfolio. Con ella, puede distinguir DATO de HIPÓTESIS, que es
exactamente lo que su system prompt le exige.

Jerarquía que respeta este módulo:
  - Mark    -> nivel EPISODIO. Captura y entrega. No aconseja.
  - Talese  -> nivel PRODUCTO (HUMANOS). Aprendizaje editorial. No mide vistas.
  - Mr. You -> nivel CANAL. Lee lo agregado y devuelve dirección.

Regla dura: este módulo NO inventa métricas. Si un episodio no tiene datos
reales, sale como `pending` y queda fuera de todo promedio. La alternativa
—rellenar con `random`— ya produjo un episodio falso.
"""

import os
import json
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAB_DIR = os.path.join(BASE_DIR, "_LAB")
CANAL_FILE = os.path.join(LAB_DIR, "channel_metrics.json")
METRICS_HISTORY = os.path.join(BASE_DIR, "metrics_history.json")

# Estados posibles de una ficha de métricas.
PENDIENTE = "pending"    # publicado, aún sin datos cargados
REAL = "real"            # datos cargados a mano o por API desde YouTube Studio
SIMULADO = "simulated"   # heredado del bug del `random`. Nunca entra en promedios.

LINEAS = ("HUMANOS", "LAB_IA")


def _ahora():
    return datetime.now().isoformat(timespec="seconds")


def _cargar(path, por_defecto):
    if not os.path.exists(path):
        return por_defecto
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return por_defecto


def _guardar(path, data):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def _estructura_vacia():
    return {
        "schema_version": 1,
        "creado": _ahora(),
        "descripcion": (
            "Metricas agregadas del canal Jota Growth. Alimentado por Mark "
            "(HUMANOS) y por carga manual (Lab IA). Leido por Mr. You."
        ),
        "publicaciones": [],
    }


# ---------------------------------------------------------------------------
# Escritura — la usa Mark
# ---------------------------------------------------------------------------

def registrar_publicacion(episode_id, titulo, linea="HUMANOS", plataforma="youtube",
                          publicado_en=None, metricas=None, estado=PENDIENTE,
                          notas=""):
    """Registra una publicación en la capa de canal.

    `metricas` es un dict libre (views, ctr, retention_3s, avg_watch_pct...).
    Si `estado` es PENDIENTE, las métricas se guardan pero no se promedian.
    """
    if linea not in LINEAS:
        raise ValueError(f"linea debe ser una de {LINEAS}, recibido: {linea!r}")

    datos = _cargar(CANAL_FILE, _estructura_vacia())

    ficha = {
        "episode_id": episode_id,
        "titulo": titulo,
        "linea": linea,
        "plataforma": plataforma,
        "publicado_en": publicado_en,
        "registrado_en": _ahora(),
        "metrics_status": estado,
        "metricas": metricas or {},
        "notas": notas,
    }

    # Aditivo: si ya existe la misma publicación, se actualiza en sitio.
    for i, p in enumerate(datos["publicaciones"]):
        if p.get("episode_id") == episode_id and p.get("plataforma") == plataforma:
            ficha["registrado_en"] = p.get("registrado_en", ficha["registrado_en"])
            datos["publicaciones"][i] = ficha
            break
    else:
        datos["publicaciones"].append(ficha)

    _guardar(CANAL_FILE, datos)
    return ficha


def importar_metrics_history(marcar_como=SIMULADO):
    """Trae metrics_history.json a la capa de canal SIN borrar el original.

    Las 4 entradas EP0001-EP0004 provienen del bug de `random.randint`
    (run_humanos_mvp.py L322-327, corregido el 2026-08-01). Se importan
    marcadas como `simulated` para que quede constancia y para que ningún
    promedio las use. No se borra nada: el archivo original queda intacto.
    """
    historial = _cargar(METRICS_HISTORY, [])
    importadas = 0
    for e in historial:
        ep = e.get("episode_id")
        if not ep:
            continue
        registrar_publicacion(
            episode_id=ep,
            titulo=e.get("character_name", ep),
            linea="HUMANOS",
            plataforma="youtube",
            publicado_en=e.get("logged_at"),
            metricas={
                "views": e.get("views"),
                "retention_3s": e.get("retention_rate_3s"),
                "avg_watch_pct": e.get("avg_watch_percentage"),
                "duration_seconds": e.get("duration_seconds"),
                "hook_text": e.get("hook_text"),
                "themes": e.get("themes", []),
            },
            estado=marcar_como,
            notas=(
                "Importado de metrics_history.json. Marcado como simulado: "
                "proviene del generador random anterior al 2026-08-01. "
                "El archivo original NO fue modificado."
            ),
        )
        importadas += 1
    return importadas


# ---------------------------------------------------------------------------
# Lectura — la usa Mr. You
# ---------------------------------------------------------------------------

def leer_canal():
    return _cargar(CANAL_FILE, _estructura_vacia())


def resumen_para_mr_you():
    """Devuelve lo que Mr. You necesita para distinguir DATO de HIPÓTESIS.

    Si no hay una sola métrica real, lo dice explícitamente. Su system prompt
    se lo exige: "Nunca inventes certeza."
    """
    datos = leer_canal()
    pubs = datos.get("publicaciones", [])

    reales = [p for p in pubs if p.get("metrics_status") == REAL]
    simuladas = [p for p in pubs if p.get("metrics_status") == SIMULADO]
    pendientes = [p for p in pubs if p.get("metrics_status") == PENDIENTE]

    def promedio(campo, subconjunto=None):
        fuente = reales if subconjunto is None else subconjunto
        vals = [p["metricas"].get(campo) for p in fuente
                if isinstance(p.get("metricas", {}).get(campo), (int, float))]
        return round(sum(vals) / len(vals), 4) if vals else None

    # Segmentado por linea. Doctrina de canal §1: HUMANOS y LAB IA son dos
    # productos con audiencias y horizontes distintos. Promediarlos juntos
    # produce numeros que no significan nada. Se conserva el promedio global
    # solo por compatibilidad, marcado como no interpretable.
    por_linea = {}
    for l in LINEAS:
        de_linea = [p for p in reales if p.get("linea") == l]
        por_linea[l] = {
            "publicaciones_con_datos_reales": len(de_linea),
            "total_registradas": len([p for p in pubs if p.get("linea") == l]),
            "promedios": {
                "views": promedio("views", de_linea),
                "avg_watch_pct": promedio("avg_watch_pct", de_linea),
                "shares": promedio("shares", de_linea),
                "suscriptores_ganados": promedio("suscriptores_ganados", de_linea),
            },
            # Doctrina §2: hacen falta >= 5 publicaciones de la misma linea
            # antes de hablar de tendencia.
            "suficiente_para_tendencia": len(de_linea) >= 5,
            "faltan_para_tendencia": max(0, 5 - len(de_linea)),
        }

    hay_evidencia = len(reales) > 0

    return {
        "hay_evidencia_real": hay_evidencia,
        "advertencia": None if hay_evidencia else (
            "CERO metricas reales en el canal. Todas las cifras disponibles son "
            "simuladas (bug de random, pre 2026-08-01) o estan pendientes. "
            "Mr. You NO puede emitir DATO ni PATRON: solo HIPOTESIS y BEST "
            "PRACTICE EXTERNA, y debe declararlo."
        ),
        "conteos": {
            "reales": len(reales),
            "simuladas": len(simuladas),
            "pendientes": len(pendientes),
            "total": len(pubs),
        },
        "por_linea": por_linea,
        "promedios_globales_NO_INTERPRETABLES": {
            "aviso": (
                "Mezcla HUMANOS y LAB IA, que son productos distintos. "
                "Doctrina de canal §1: no usar para concluir nada. "
                "Usa `por_linea`."
            ),
            "views": promedio("views"),
            "avg_watch_pct": promedio("avg_watch_pct"),
        },
        "publicaciones": pubs,
    }


def imprimir_resumen():
    r = resumen_para_mr_you()
    print("\n" + "=" * 72)
    print(" CAPA DE CANAL — Jota Growth")
    print("=" * 72)
    c = r["conteos"]
    print(f"  Publicaciones registradas : {c['total']}")
    print(f"    con datos REALES        : {c['reales']}")
    print(f"    simuladas (bug random)  : {c['simuladas']}")
    print(f"    pendientes              : {c['pendientes']}")
    for linea, v in r["por_linea"].items():
        p = v["promedios"]
        ret = f"{p['avg_watch_pct']*100:.1f}%" if p["avg_watch_pct"] else "s/d"
        print(f"  {linea:<8} -> {v['publicaciones_con_datos_reales']} reales "
              f"de {v['total_registradas']} | retencion media {ret}")
        if not v["suficiente_para_tendencia"]:
            print(f"           faltan {v['faltan_para_tendencia']} publicaciones "
                  f"para poder hablar de tendencia (doctrina §2)")
    if r["advertencia"]:
        print("\n  AVISO:")
        # Envuelto a mano: partir por ". " rompia "Mr. You" en dos lineas.
        palabras, linea = r["advertencia"].split(), ""
        for w in palabras:
            if len(linea) + len(w) + 1 > 66:
                print(f"    {linea}")
                linea = w
            else:
                linea = f"{linea} {w}".strip()
        if linea:
            print(f"    {linea}")
    else:
        print(f"\n  Promedios (solo reales): {r['promedios_solo_reales']}")
    print("=" * 72 + "\n")
    return r


if __name__ == "__main__":
    n = importar_metrics_history()
    print(f"[canal] {n} entradas importadas de metrics_history.json (marcadas simulated).")
    imprimir_resumen()
