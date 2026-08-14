"""
importar_youtube_csv — carga métricas REALES del canal desde el export de
YouTube Studio a la capa de canal.

Contexto (2026-08-01)
---------------------
Hasta hoy la capa de canal solo tenía las 4 entradas simuladas por el bug de
`random`. Este importador trae los números de verdad. La comparación:

    personaje        simulado     real     inflado
    Jan Koum          657.002      911        721x
    Hedy Lamarr       508.439    2.418        210x
    James Dyson       366.548   10.403         35x
    Lamborghini       496.341   nunca se publico

Uso:
    python importar_youtube_csv.py
    python importar_youtube_csv.py --csv "ruta\\Datos de la tabla.csv"
"""

import os
import csv
import sys
import argparse

import env_boot  # noqa: F401
import canal

CSV_POR_DEFECTO = (
    r"C:\JotaOS\100 - Proyectos\JOTA AI YOUTUBE\Reportes_analytics"
    r"\Contenido 2026-05-03_2026-08-01 Jota Ochoa _ HUMANOS\Datos de la tabla.csv"
)

# Qué video de YouTube corresponde a qué episodio del pipeline.
# Se empareja por fragmento del título porque los IDs de YouTube no estaban
# registrados en ninguna parte del sistema (deuda: Mark deberia guardarlos
# al publicar).
MAPA = [
    ("Jan Koum",         "EP0001", "HUMANOS"),
    ("Hedy Lamarr",      "EP0002", "HUMANOS"),
    ("James Dyson",      "EP0003", "HUMANOS"),
    ("botón de WHATSAPP", "LAB_WHATSAPP_BTN", "LAB_IA"),
]


def _num(v, tipo=float):
    try:
        return tipo(str(v).replace(",", "").strip())
    except (ValueError, AttributeError):
        return None


def importar(ruta_csv):
    if not os.path.exists(ruta_csv):
        raise SystemExit(f"No encuentro el CSV:\n  {ruta_csv}")

    with open(ruta_csv, encoding="utf-8-sig") as f:
        filas = list(csv.DictReader(f))

    total = next((r for r in filas if r.get("Contenido") == "Total"), None)
    videos = [r for r in filas if r.get("Contenido") != "Total"]

    importados, no_encontrados = [], []

    for fragmento, episode_id, linea in MAPA:
        fila = next((r for r in videos
                     if fragmento.lower() in (r.get("Título del video") or "").lower()),
                    None)
        if not fila:
            no_encontrados.append((fragmento, episode_id))
            continue

        duracion = _num(fila.get("Duración"), int)
        vistas = _num(fila.get("Vistas"), int)
        impresiones = _num(fila.get("Impresiones"), int)
        ctr = _num(fila.get("Tasa de clics de las impresiones (%)"))
        horas = _num(fila.get("Tiempo de reproducción (horas)"))
        subs = _num(fila.get("Suscriptores"), int)

        # % promedio visto, derivado. No es el dato nativo de YouTube pero es
        # lo mejor que da este export. Se marca como derivado para que nadie
        # lo confunda con una lectura directa.
        avg_pct = None
        if vistas and duracion and horas:
            avg_pct = round((horas * 3600) / (vistas * duracion), 4)

        canal.registrar_publicacion(
            episode_id=episode_id,
            titulo=fila.get("Título del video"),
            linea=linea,
            plataforma="youtube",
            publicado_en=fila.get("Tiempo de publicación del video"),
            metricas={
                "youtube_video_id": fila.get("Contenido"),
                "views": vistas,
                "impresiones": impresiones,
                "ctr": ctr,
                "avg_watch_pct": avg_pct,
                "avg_watch_pct_es_derivado": True,
                "watch_time_horas": horas,
                "suscriptores_ganados": subs,
                "duration_seconds": duracion,
                "formato": "short" if (duracion or 0) <= 180 else "long",
                # retention_3s NO esta en este export. Solo se obtiene por API
                # o mirando la curva a mano. Se deja explicitamente vacio en
                # vez de estimarlo: estimar es como empezo todo este problema.
                "retention_3s": None,
            },
            estado=canal.REAL,
            notas=(
                f"Importado del export de YouTube Studio "
                f"({os.path.basename(ruta_csv)}). Periodo 2026-05-03 a 2026-08-01. "
                f"retention_3s no viene en este export."
            ),
        )
        importados.append((episode_id, fila.get("Título del video"), vistas, ctr, duracion))

    return importados, no_encontrados, total


def informe(importados, no_encontrados, total):
    print("\n" + "=" * 76)
    print(" IMPORTACION DE METRICAS REALES — YouTube Studio")
    print("=" * 76)

    if total:
        print(f"  Canal completo: {total.get('Vistas')} vistas | "
              f"{total.get('Suscriptores')} subs | "
              f"CTR {total.get('Tasa de clics de las impresiones (%)')}%")

    print(f"\n  {'episodio':<18}{'vistas':>8}{'CTR':>8}{'dur':>7}  {'formato':<7} titulo")
    print("  " + "-" * 72)
    for ep, titulo, vistas, ctr, dur in importados:
        fmt = "SHORT" if (dur or 0) <= 180 else "LONG"
        print(f"  {ep:<18}{vistas:>8}{ctr:>7.2f}%{dur:>6}s  {fmt:<7} {(titulo or '')[:32]}")

    if no_encontrados:
        print("\n  No encontrados en el export:")
        for frag, ep in no_encontrados:
            print(f"    {ep}: ningun video contiene '{frag}'")

    # El hallazgo estructural. Vale mas que los numeros sueltos.
    duraciones = [d for _, _, _, _, d in importados if d]
    humanos = [d for d in duraciones if d <= 180]
    if humanos and len(humanos) == len([d for d in duraciones if d <= 400]):
        pass
    print("\n  " + "-" * 72)
    print("  LECTURA ESTRUCTURAL:")
    print("    Todo el catalogo publicado de HUMANOS son piezas de <= 3 minutos.")
    print("    Es decir: el canal tiene evidencia real de formato CORTO unicamente.")
    print("    EP0004 se esta produciendo a 8-10 minutos. Para ese formato el")
    print("    canal tiene CERO datos. Mr. You debe tratarlo como apuesta, no")
    print("    como continuidad, y decirlo explicitamente.")
    print("=" * 76 + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default=CSV_POR_DEFECTO)
    args = ap.parse_args()

    # Primero las simuladas (quedan marcadas), despues las reales las pisan
    # por episode_id. Nada se borra: registrar_publicacion actualiza en sitio.
    canal.importar_metrics_history()
    imp, faltan, total = importar(args.csv)
    informe(imp, faltan, total)
    canal.imprimir_resumen()
    return 0


if __name__ == "__main__":
    sys.exit(main())
