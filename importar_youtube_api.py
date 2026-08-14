"""
importar_youtube_api — trae métricas REALES del canal vía la YouTube
Analytics API y las carga en la capa de canal.

Cierra el bucle que estaba roto desde el principio:

    YouTube (verdad)
        -> API (OAuth solo lectura, dentro del panel)
        -> canal.py (capa de agregación)
        -> Mr. You (dirección del canal)

Antes de esto, ese primer eslabón era `random.randint(300000, 800000)`.

Qué aporta sobre el CSV
-----------------------
El export de YouTube Studio no trae retención. Este sí:
  - averageViewPercentage : % real que la gente ve. Dato nativo, no derivado.
  - averageViewDuration   : segundos vistos en promedio.
  - shares / likes        : señal de propagación, ausente en el export.

Requisito: el panel tiene que estar corriendo y el canal conectado
(`Abrir HUMANOS Dashboard.bat` y luego /api/auth/youtube).

Uso:
    python importar_youtube_api.py
    python importar_youtube_api.py --desde 2026-05-01
"""

import os
import sys
import json
import argparse
import urllib.request
import urllib.error

import env_boot  # noqa: F401
import canal

PANEL = os.environ.get("HUMANOS_PANEL", "http://localhost:3100")
MAPA_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                         "_LAB", "youtube_video_map.json")

# Qué video de YouTube es qué episodio del pipeline.
# Esto debería escribirlo Mark al publicar. Hoy no lo hace: es deuda abierta
# y por eso el mapa vive acá, a mano. Ver CLAUDE_AUDIT.md.
MAPA_INICIAL = {
    "ksGK8pmgIvI": {"episode_id": "EP0001", "titulo": "Jan Koum",              "linea": "HUMANOS"},
    "ewDlJO-aFfQ": {"episode_id": "EP0002", "titulo": "Hedy Lamarr",           "linea": "HUMANOS"},
    "7MAvFSAI8mY": {"episode_id": "EP0003", "titulo": "James Dyson",           "linea": "HUMANOS"},
    "wiDRwcgXR6U": {"episode_id": "LAB_WHATSAPP_BTN",
                    "titulo": "El error del boton de WhatsApp",                "linea": "LAB_IA"},
}


def cargar_mapa():
    """El mapa en disco manda; el inicial solo rellena lo que falte."""
    mapa = dict(MAPA_INICIAL)
    if os.path.exists(MAPA_FILE):
        try:
            with open(MAPA_FILE, encoding="utf-8") as f:
                mapa.update(json.load(f))
        except (json.JSONDecodeError, OSError):
            pass
    os.makedirs(os.path.dirname(MAPA_FILE), exist_ok=True)
    with open(MAPA_FILE, "w", encoding="utf-8") as f:
        json.dump(mapa, f, indent=2, ensure_ascii=False)
    return mapa


def pedir_metricas(desde=None, hasta=None):
    q = []
    if desde:
        q.append(f"desde={desde}")
    if hasta:
        q.append(f"hasta={hasta}")
    url = f"{PANEL}/api/youtube/metrics" + ("?" + "&".join(q) if q else "")
    try:
        with urllib.request.urlopen(url, timeout=60) as r:
            return json.loads(r.read().decode())
    except urllib.error.URLError as e:
        raise SystemExit(
            f"No pude hablar con el panel en {PANEL}.\n"
            f"  {type(e).__name__}: {e}\n\n"
            f"Arranca 'Abrir HUMANOS Dashboard.bat' y volve a intentar."
        )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", help="YYYY-MM-DD")
    ap.add_argument("--hasta", help="YYYY-MM-DD")
    args = ap.parse_args()

    d = pedir_metricas(args.desde, args.hasta)
    if d.get("error"):
        raise SystemExit(
            f"La API devolvio un error:\n  {d['error']}\n\n"
            f"Si dice 'SIN_CONEXION', entra a {PANEL}/api/auth/youtube y conecta el canal."
        )

    mapa = cargar_mapa()
    videos = d.get("videos", [])
    periodo = d.get("periodo", {})

    print("\n" + "=" * 78)
    print(f" METRICAS REALES VIA API — {periodo.get('desde')} a {periodo.get('hasta')}")
    print("=" * 78)
    print(f"  {'episodio':<18}{'vistas':>8}{'reten.':>8}{'vistos':>8}{'subs':>6}{'shares':>8}  titulo")
    print("  " + "-" * 74)

    cargados, sin_mapear = 0, []

    for v in videos:
        vid = v.get("video")
        info = mapa.get(vid)
        if not info:
            sin_mapear.append((vid, v.get("views")))
            continue

        retencion = v.get("averageViewPercentage")
        canal.registrar_publicacion(
            episode_id=info["episode_id"],
            titulo=info["titulo"],
            linea=info["linea"],
            plataforma="youtube",
            publicado_en=None,
            metricas={
                "youtube_video_id": vid,
                "views": v.get("views"),
                "avg_watch_pct": round(retencion / 100, 4) if retencion else None,
                "avg_watch_pct_es_derivado": False,   # dato nativo de YouTube
                "avg_view_duration_s": v.get("averageViewDuration"),
                "watch_time_min": v.get("estimatedMinutesWatched"),
                "suscriptores_ganados": v.get("subscribersGained"),
                "likes": v.get("likes"),
                "shares": v.get("shares"),
                # retention_3s sigue sin estar: la API no la expone en este
                # reporte. Se obtiene con el reporte audienceWatchRatio.
                # Se deja vacia en vez de estimarla.
                "retention_3s": None,
            },
            estado=canal.REAL,
            notas=(
                f"YouTube Analytics API, periodo {periodo.get('desde')}..{periodo.get('hasta')}. "
                f"averageViewPercentage es dato nativo, no derivado."
            ),
        )
        cargados += 1
        print(f"  {info['episode_id']:<18}{v.get('views', 0):>8}"
              f"{(retencion or 0):>7.1f}%{v.get('averageViewDuration', 0):>7}s"
              f"{v.get('subscribersGained', 0):>6}{v.get('shares', 0):>8}  {info['titulo'][:24]}")

    if sin_mapear:
        print(f"\n  {len(sin_mapear)} videos del canal sin mapear a un episodio.")
        print(f"  Si alguno es de HUMANOS, agregalo a:\n    {MAPA_FILE}")
        for vid, vistas in sin_mapear[:8]:
            print(f"    {vid}  ({vistas} vistas)")

    print("=" * 78)
    print(f"  {cargados} episodios actualizados con datos REALES.")
    canal.imprimir_resumen()
    return 0


if __name__ == "__main__":
    sys.exit(main())
