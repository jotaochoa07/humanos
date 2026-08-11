"""
derechos — quality gate de derechos de uso para HUMANOS.

Por que existe:

El sistema tenia el mandato de revisar licencias escrito en dos lugares
(Mr. You FASE 4 "Risk Check", y el checklist de Mark "Copyright OK") y no lo
ejecutaba en ninguno. La razon no era negligencia: era que el dato no estaba.
`asset_collector.py` capturaba la licencia en el sidecar de metadatos de cada
asset pero la tiraba al escribir `asset_registry.json`, que es la unica vista
consolidada del episodio. Auditar derechos exigia abrir un archivo por asset.

Esto cierra el circuito. Mismo patron que Veritas, que ya es el gate en el
que Jota confia: se audita, se puntua, se emite veredicto, y el episodio no
avanza si el veredicto es RECHAZADO.

Diferencia deliberada con Veritas: aca NO hay LLM. Una licencia es un dato
categorico, no una interpretacion. Meter un modelo a "opinar" sobre si algo
es dominio publico agregaria alucinacion a una decision legal. Se clasifica
con reglas, y lo que las reglas no reconocen queda en AMBAR para que lo mire
un humano.

Uso:

    # auditar un episodio
    python derechos.py --episodio personajes/Ferruccio_Lamborghini/EP0004_Ferruccio_Lamborghini

    # auditar todos los episodios del catalogo (pasada retroactiva)
    python derechos.py --todos

    # el canal ya esta monetizado: las NC vuelven a rojo
    python derechos.py --episodio <ruta> --monetizado
"""

import os
import re
import sys
import json
import glob
import argparse

# ---------------------------------------------------------------------------
# clasificacion
# ---------------------------------------------------------------------------
#
# ND (no derivatives) e In Copyright son ROJO siempre. No dependen de si el
# canal tiene anuncios: dependen de si se produce una obra derivada, y montar
# un clip en una edicion lo es.
#
# NC (non commercial) depende del uso. Con el canal sin monetizar se tolera
# como AMBAR, con la advertencia de que es deuda: el dia que se monetice hay
# que reemplazar ese material y reeditar los episodios que lo usen.

MONETIZADO = False


def clasificar(txt, monetizado=None):
    """Devuelve (semaforo, explicacion). verde / ambar / rojo."""
    mon = MONETIZADO if monetizado is None else monetizado
    t = (txt or "").lower().strip()

    if not t or t in ("verificar", "sin dato", "none", "null",
                      "sin licencia declarada", "ver ficha"):
        return "ambar", "sin licencia declarada: hay que abrir la ficha de origen"

    if "-nd" in t or "noderiv" in t or "no derivative" in t:
        return "rojo", "sin obras derivadas: montarlo en una edicion ya es derivada"
    if "/inc/" in t or "in copyright" in t or "incopyright" in t:
        return "rojo", "en copyright: hace falta permiso del titular"
    if "rr-r" in t or "all rights reserved" in t or "todos los derechos" in t:
        return "rojo", "todos los derechos reservados"

    if "-nc" in t or "noncommercial" in t or "non-commercial" in t:
        if mon:
            return "rojo", "no comercial: el canal esta monetizado"
        return "ambar", ("no comercial: hoy pasa, pero hay que reemplazarlo "
                         "el dia que se monetice el canal")

    if ("publicdomain" in t or "public domain" in t or "dominio publico" in t
            or "dominio público" in t or "/pdm/" in t or "cc0" in t
            or "nokc" in t or "sin restricciones" in t):
        return "verde", "dominio publico: uso libre, atribucion recomendada"
    if "by-sa" in t or "by sa" in t:
        return "verde", "CC BY-SA: se puede, con atribucion"
    if re.search(r"\bby\b", t) or "attribution" in t:
        return "verde", "CC BY: se puede, con atribucion"

    return "ambar", "licencia no reconocida: verificar en la ficha"


# ---------------------------------------------------------------------------
# auditoria
# ---------------------------------------------------------------------------

def _basename(p):
    """basename que entiende las dos barras.

    os.path.basename en Linux no parte rutas con barra invertida, y el
    registro guarda rutas de Windows. Sin esto, una auditoria corrida fuera
    de Windows reporta como huerfano todo el episodio.
    """
    return re.split(r"[\\/]", str(p or ""))[-1]


EXT_MEDIA = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff",
             ".mp4", ".mov", ".webm", ".avi", ".mkv", ".svg",
             # ogv/mpg/mpeg: archivo historico de video los trae de Wikimedia
             # y de catalogos institucionales. Sin esto, un .ogv sin registrar
             # no aparece como huerfano: no es que este limpio, es que el gate
             # no lo mira.
             ".ogv", ".mpg", ".mpeg"}

# Material propio o generado: no tiene problema de derechos de terceros.
#
# Se comparan PALABRAS COMPLETAS, no subcadenas. Con subcadenas, "ia" hacia
# que "Wikimedia Commons" se clasificara como material propio, porque
# "wikimedia" termina en "ia". Un falso positivo asi es peor que no tener
# gate: da luz verde a material de terceros.
FUENTES_PROPIAS = {"generado", "generada", "generadas", "generados",
                   "kling", "kie", "leonardo", "dali", "propio", "propia",
                   "jota", "grabado", "grabada", "captura", "ai-gen", "aigen"}


def _es_propio(entrada):
    s = (str(entrada.get("source") or "") + " " +
         str(entrada.get("licencia") or "")).lower()
    palabras = set(re.findall(r"[\w-]+", s))
    return bool(palabras & FUENTES_PROPIAS)


def auditar_episodio(ep_path, monetizado=False):
    """Cruza los archivos que hay en disco contra lo registrado.

    Los dos problemas que busca son distintos:
      - asset registrado con licencia problematica  -> riesgo conocido
      - archivo en disco que NO esta en el registro -> riesgo INVISIBLE,
        que es el peor: nadie sabe de donde salio.
    """
    registry_path = os.path.join(ep_path, "asset_registry.json")
    registro = []
    if os.path.exists(registry_path):
        try:
            registro = json.load(open(registry_path, encoding="utf-8"))
        except Exception as e:
            print(f"  [aviso] no pude leer asset_registry.json: {e}")

    registradas = set()
    for e in registro:
        sp = e.get("storage_path") or ""
        if sp:
            registradas.add(os.path.normcase(_basename(sp)))

    # Archivos reales en las carpetas de medios del episodio
    en_disco = []
    for carpeta in ("04_IMAGES", "05_VIDEO", "08_BROLL", "06_AUDIO", "07_MUSIC"):
        d = os.path.join(ep_path, carpeta)
        if not os.path.isdir(d):
            continue
        for f in os.listdir(d):
            if os.path.splitext(f)[1].lower() in EXT_MEDIA:
                en_disco.append((carpeta, f))

    conteo = {"verde": 0, "ambar": 0, "rojo": 0}
    detalle, huerfanos = [], []

    for e in registro:
        if _es_propio(e):
            sem, nota = "verde", "material propio o generado: sin derechos de terceros"
        else:
            sem, nota = clasificar(e.get("licencia"), monetizado)
        conteo[sem] += 1
        detalle.append({
            "asset_id": e.get("asset_id"),
            "archivo": _basename(e.get("storage_path") or ""),
            "fuente": e.get("source"),
            "licencia": e.get("licencia") or "sin licencia declarada",
            "semaforo": sem,
            "nota": nota,
            "url_ficha": e.get("url_ficha"),
        })

    for carpeta, f in en_disco:
        if os.path.normcase(f) not in registradas:
            huerfanos.append(os.path.join(carpeta, f))

    total = len(detalle) + len(huerfanos)
    # Los huerfanos cuentan como riesgo desconocido, que es peor que ambar.
    if conteo["rojo"] > 0:
        estado = "RECHAZADO"
    elif huerfanos or conteo["ambar"] > 0:
        estado = "REVISION"
    else:
        estado = "APROBADO"

    puntaje = int(100 * conteo["verde"] / total) if total else 0

    return {
        "episodio": os.path.basename(ep_path),
        "ruta": ep_path,
        "estado": estado,
        "puntaje_limpio": puntaje,
        "conteo": conteo,
        "assets_registrados": len(detalle),
        "archivos_en_disco": len(en_disco),
        "huerfanos": huerfanos,
        "detalle": detalle,
        "monetizado": monetizado,
    }


# ---------------------------------------------------------------------------
# informe
# ---------------------------------------------------------------------------

def imprimir(r):
    c = r["conteo"]
    print(f"\n{'=' * 70}")
    print(f"  DERECHOS — {r['episodio']}")
    print(f"{'=' * 70}")
    print(f"  Veredicto: {r['estado']}   ({r['puntaje_limpio']}% limpio)")
    print(f"  Registrados: {r['assets_registrados']}   "
          f"En disco: {r['archivos_en_disco']}   Sin registrar: {len(r['huerfanos'])}")
    print(f"  verde {c['verde']}   ambar {c['ambar']}   rojo {c['rojo']}")

    rojos = [d for d in r["detalle"] if d["semaforo"] == "rojo"]
    if rojos:
        print(f"\n  NO SE PUEDEN USAR ({len(rojos)}):")
        for d in rojos:
            print(f"    {d['archivo'][:46]:48} {d['nota']}")

    ambar = [d for d in r["detalle"] if d["semaforo"] == "ambar"]
    if ambar:
        print(f"\n  A VERIFICAR ({len(ambar)}):")
        for d in ambar[:10]:
            print(f"    {d['archivo'][:46]:48} {d['nota'][:44]}")
        if len(ambar) > 10:
            print(f"    ... y {len(ambar) - 10} mas")

    if r["huerfanos"]:
        print(f"\n  SIN REGISTRAR ({len(r['huerfanos'])}) — riesgo invisible:")
        print("    Estos archivos estan en el episodio y nadie sabe de donde salieron.")
        for f in r["huerfanos"][:12]:
            print(f"    {f}")
        if len(r["huerfanos"]) > 12:
            print(f"    ... y {len(r['huerfanos']) - 12} mas")
        print("    Registralos con:  python registrar_assets.py --episodio <ruta> --revisar")

    if r["estado"] == "APROBADO":
        print("\n  Todo el material registrado esta limpio.")
    elif r["estado"] == "RECHAZADO":
        print("\n  Hay material que no se puede usar. Reemplazalo antes de publicar.")
    else:
        print("\n  Nada bloqueante, pero queda material sin verificar.")
    print()


def main():
    ap = argparse.ArgumentParser(description="Quality gate de derechos de uso")
    ap.add_argument("--episodio", help="ruta al episodio")
    ap.add_argument("--todos", action="store_true",
                    help="auditar todo el catalogo (pasada retroactiva)")
    ap.add_argument("--monetizado", action="store_true",
                    help="el canal esta monetizado: las NC pasan a rojo")
    a = ap.parse_args()

    globals()["MONETIZADO"] = a.monetizado

    if a.todos:
        rutas = sorted(glob.glob(os.path.join("personajes", "*", "EP*")))
        rutas = [r for r in rutas if os.path.isdir(r)]
        if not rutas:
            print("No encontre episodios en personajes/*/EP*")
            return 1
        print(f"Auditando {len(rutas)} episodios...\n")
        resumen, hay_rojo = [], False
        for r in rutas:
            res = auditar_episodio(r, a.monetizado)
            resumen.append(res)
            hay_rojo = hay_rojo or res["estado"] == "RECHAZADO"
            marca = {"APROBADO": "OK  ", "REVISION": "REV ", "RECHAZADO": "STOP"}[res["estado"]]
            print(f"  {marca} {res['episodio'][:40]:42} "
                  f"v{res['conteo']['verde']:3d} a{res['conteo']['ambar']:3d} "
                  f"r{res['conteo']['rojo']:3d}  sin registrar: {len(res['huerfanos'])}")
        destino = os.path.join("claude_improvement", "AUDITORIA_DERECHOS.json")
        os.makedirs("claude_improvement", exist_ok=True)
        json.dump(resumen, open(destino, "w", encoding="utf-8"),
                  ensure_ascii=False, indent=2)
        print(f"\nInforme completo: {destino}")
        return 2 if hay_rojo else 0

    if not a.episodio:
        ap.error("indica --episodio o --todos")

    r = auditar_episodio(a.episodio, a.monetizado)
    imprimir(r)
    destino = os.path.join(a.episodio, "01_RESEARCH", "auditoria_derechos.json")
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    json.dump(r, open(destino, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    print(f"  Informe: {destino}\n")
    return 2 if r["estado"] == "RECHAZADO" else 0


if __name__ == "__main__":
    sys.exit(main())
