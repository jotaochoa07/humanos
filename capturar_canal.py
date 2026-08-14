"""
capturar_canal — la función que a Mark le faltaba.

Contexto
--------
La auditoría del 2026-08-01 definió así la frontera entre agentes:

    Mark    -> nivel EPISODIO. "Su segunda funcion, hoy inexistente, es
               capturar la data de cada publicacion y entregarsela a Mr. You."
    Mr. You -> nivel CANAL. Lee lo agregado y devuelve direccion.

Esto es esa segunda función. Corre solo, en horario, sin que nadie abra nada.

Independiente a propósito
-------------------------
No necesita el panel corriendo ni una sesión de Claude. Habla directo con
Google usando el refresh_token guardado. Puede vivir en el Programador de
tareas de Windows y funcionar durante meses sin que nadie lo mire.

Qué escribe
-----------
1. `_LAB/channel_metrics.json` — estado actual (lo lee Mr. You).
2. `_LAB/channel_daily.jsonl`  — una linea por dia, para siempre.

El segundo es el que de verdad importa a largo plazo. YouTube Studio te
muestra el presente; nadie guarda la serie historica del canal. A partir de
hoy, este archivo si. En tres meses vas a poder responder "como evoluciono
la retencion de HUMANOS" con datos propios, que es exactamente lo que
Mr. You necesita para pasar de HIPOTESIS a PATRON.

Uso:
    python capturar_canal.py
    python capturar_canal.py --dias 28
"""

import os
import sys
import json
import glob
import argparse
import urllib.parse
import urllib.request
import urllib.error
from datetime import datetime, timedelta, timezone

import env_boot  # noqa: F401
import canal

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LAB_DIR = os.path.join(BASE_DIR, "_LAB")
TOKENS = os.path.join(LAB_DIR, "youtube_tokens.json")
DIARIO = os.path.join(LAB_DIR, "channel_daily.jsonl")
LOG = os.path.join(LAB_DIR, "capturar_canal.log")

CARPETA_CREDENCIALES = os.environ.get(
    "YT_CREDENCIALES",
    r"C:\JotaOS\100 - Proyectos\JOTA AI YOUTUBE\Reportes_analytics",
)

MAPA_FILE = os.path.join(LAB_DIR, "youtube_video_map.json")


def registrar(msg):
    """Escribe al log sin poder tumbar la captura.

    El 2026-08-01 esto crasheo con PermissionError: el .bat que lanzaba el
    script tenia el mismo archivo abierto con `>>` y Windows nego el acceso.
    Un fallo al ESCRIBIR el registro no puede impedir el trabajo que el
    registro documenta. Se avisa por pantalla y se sigue.
    """
    linea = f"{datetime.now():%Y-%m-%d %H:%M:%S}  {msg}"
    print(linea, flush=True)
    try:
        os.makedirs(LAB_DIR, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as f:
            f.write(linea + "\n")
    except OSError as e:
        print(f"    [aviso] no pude escribir el log ({e.__class__.__name__}): "
              f"la captura continua igual", flush=True)


# ---------------------------------------------------------------------------
# Credenciales y token
# ---------------------------------------------------------------------------

def credenciales():
    patron = os.path.join(CARPETA_CREDENCIALES, "client_secret_*.json")
    archivos = glob.glob(patron)
    if not archivos:
        raise SystemExit(f"No hay client_secret_*.json en:\n  {CARPETA_CREDENCIALES}")
    with open(archivos[0], encoding="utf-8") as f:
        bruto = json.load(f)
    return bruto.get("web") or bruto.get("installed")


def access_token():
    """Devuelve un access token valido, refrescandolo si hace falta."""
    if not os.path.exists(TOKENS):
        raise SystemExit(
            f"No hay tokens en {TOKENS}.\n"
            "Arranca el panel y entra a http://localhost:3100/api/auth/youtube"
        )
    with open(TOKENS, encoding="utf-8") as f:
        t = json.load(f)

    ahora_ms = datetime.now(timezone.utc).timestamp() * 1000
    if ahora_ms < t.get("expira_en", 0) - 60000:
        return t["access_token"]

    if not t.get("refresh_token"):
        raise SystemExit(
            "El token expiro y no hay refresh_token. Volve a conectar el canal "
            "en http://localhost:3100/api/auth/youtube"
        )

    c = credenciales()
    datos = urllib.parse.urlencode({
        "refresh_token": t["refresh_token"],
        "client_id": c["client_id"],
        "client_secret": c["client_secret"],
        "grant_type": "refresh_token",
    }).encode()
    req = urllib.request.Request(
        c.get("token_uri", "https://oauth2.googleapis.com/token"),
        data=datos,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    with urllib.request.urlopen(req, timeout=30) as r:
        d = json.loads(r.read().decode())

    t["access_token"] = d["access_token"]
    t["expira_en"] = ahora_ms + d.get("expires_in", 3600) * 1000
    t["refrescado_en"] = datetime.now().isoformat(timespec="seconds")
    with open(TOKENS, "w", encoding="utf-8") as f:
        json.dump(t, f, indent=2, ensure_ascii=False)
    registrar("Token refrescado sin intervencion.")
    return t["access_token"]


def pedir(url, token):
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=45) as r:
            return json.loads(r.read().decode())
    except urllib.error.HTTPError as e:
        cuerpo = e.read()[:300].decode(errors="ignore")
        raise SystemExit(f"HTTP {e.code} de Google: {cuerpo}")


# ---------------------------------------------------------------------------
# Captura
# ---------------------------------------------------------------------------

def capturar(dias=365):
    token = access_token()

    canal_info = pedir(
        "https://www.googleapis.com/youtube/v3/channels"
        "?part=snippet,statistics&mine=true", token
    )
    ch = (canal_info.get("items") or [{}])[0]

    hoy = datetime.now().date()
    ini = (hoy - timedelta(days=dias)).isoformat()

    q = urllib.parse.urlencode({
        "ids": "channel==MINE",
        "startDate": ini,
        "endDate": hoy.isoformat(),
        "metrics": ("views,estimatedMinutesWatched,averageViewDuration,"
                    "averageViewPercentage,subscribersGained,likes,shares"),
        "dimensions": "video",
        "sort": "-views",
        "maxResults": "50",
    })
    rep = pedir(f"https://youtubeanalytics.googleapis.com/v2/reports?{q}", token)

    cols = [c["name"] for c in rep.get("columnHeaders", [])]
    videos = [dict(zip(cols, fila)) for fila in rep.get("rows", [])]

    return {
        "canal": {
            "titulo": ch.get("snippet", {}).get("title"),
            "suscriptores": int(ch.get("statistics", {}).get("subscriberCount", 0)),
            "vistas_totales": int(ch.get("statistics", {}).get("viewCount", 0)),
            "videos": int(ch.get("statistics", {}).get("videoCount", 0)),
        },
        "periodo": {"desde": ini, "hasta": hoy.isoformat()},
        "videos": videos,
    }


def cargar_mapa():
    if not os.path.exists(MAPA_FILE):
        return {}
    try:
        with open(MAPA_FILE, encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, OSError):
        return {}


def volcar_a_canal(datos, mapa):
    cargados, sin_mapear = 0, []
    for v in datos["videos"]:
        vid = v.get("video")
        info = mapa.get(vid)
        if not info:
            sin_mapear.append(vid)
            continue
        pct = v.get("averageViewPercentage")
        canal.registrar_publicacion(
            episode_id=info["episode_id"],
            titulo=info["titulo"],
            linea=info.get("linea", "HUMANOS"),
            plataforma="youtube",
            metricas={
                "youtube_video_id": vid,
                "views": v.get("views"),
                "avg_watch_pct": round(pct / 100, 4) if pct else None,
                "avg_watch_pct_es_derivado": False,
                "avg_view_duration_s": v.get("averageViewDuration"),
                "watch_time_min": v.get("estimatedMinutesWatched"),
                "suscriptores_ganados": v.get("subscribersGained"),
                "likes": v.get("likes"),
                "shares": v.get("shares"),
                "retention_3s": None,
            },
            estado=canal.REAL,
            notas=f"Captura automatica {datetime.now():%Y-%m-%d %H:%M}. Mark -> capa de canal.",
        )
        cargados += 1
    return cargados, sin_mapear


def anexar_diario(datos):
    """Una linea por dia. Esta es la serie historica que nadie guardaba."""
    os.makedirs(LAB_DIR, exist_ok=True)
    fila = {
        "fecha": datetime.now().date().isoformat(),
        "capturado_en": datetime.now().isoformat(timespec="seconds"),
        "canal": datos["canal"],
        "periodo": datos["periodo"],
        "videos": datos["videos"],
    }
    # Idempotente: si hoy ya se capturo, se reemplaza esa linea.
    lineas = []
    if os.path.exists(DIARIO):
        with open(DIARIO, encoding="utf-8") as f:
            lineas = [l for l in f if l.strip()
                      and json.loads(l).get("fecha") != fila["fecha"]]
    lineas.append(json.dumps(fila, ensure_ascii=False) + "\n")
    with open(DIARIO, "w", encoding="utf-8") as f:
        f.writelines(lineas)
    return len(lineas)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dias", type=int, default=365)
    args = ap.parse_args()

    registrar("=" * 60)
    registrar("Captura de canal iniciada.")
    try:
        datos = capturar(args.dias)
    except SystemExit as e:
        registrar(f"ABORTADO: {e}")
        raise

    c = datos["canal"]
    registrar(f"Canal: {c['titulo']} | {c['suscriptores']} subs | "
              f"{c['vistas_totales']} vistas | {c['videos']} videos")

    mapa = cargar_mapa()
    cargados, sin_mapear = volcar_a_canal(datos, mapa)
    registrar(f"{cargados} episodios actualizados con datos reales.")
    if sin_mapear:
        registrar(f"{len(sin_mapear)} videos sin mapear a episodio "
                  f"(agregalos a {os.path.basename(MAPA_FILE)}): "
                  f"{', '.join(sin_mapear[:6])}")

    dias_guardados = anexar_diario(datos)
    registrar(f"Serie historica: {dias_guardados} dia(s) en channel_daily.jsonl")

    r = canal.resumen_para_mr_you()
    registrar(f"Mr. You ve ahora {r['conteos']['reales']} publicaciones con "
              f"datos reales. Evidencia real: {r['hay_evidencia_real']}")
    registrar("Captura completada.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
