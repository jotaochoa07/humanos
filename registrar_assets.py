"""
registrar_assets — baja lo marcado en la hoja de contactos y lo INSCRIBE.

El agujero que tapa: cuando Jota bajaba una imagen a mano y la dejaba en
04_IMAGES, quedaba un archivo suelto sin rastro de origen ni licencia. A los
seis meses, ante un reclamo, no habia forma de saber de donde salio. El gate
de derechos los llama "huerfanos" y son el peor tipo de riesgo, porque son
invisibles: no aparecen como problema, aparecen como nada.

Esto cierra el ciclo: descarga, calcula hash, deduplica, nombra con el
estandar del episodio, y escribe en `asset_registry.json` con licencia,
semaforo y URL de la ficha de origen.

Uso:

    # pegar las URLs copiadas de la hoja de contactos
    python registrar_assets.py --episodio <ruta> --desde-portapapeles

    # o desde un archivo con una URL por linea
    python registrar_assets.py --episodio <ruta> --lista urls.txt

    # inscribir archivos que YA estan en 04_IMAGES sin registrar
    python registrar_assets.py --episodio <ruta> --revisar
"""

import os
import re
import sys
import json
import time
import hashlib
import argparse
import http.client
import urllib.parse
import urllib.request

try:
    import env_boot
except Exception:
    pass

from derechos import clasificar

EXT_IMG = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".tif", ".tiff", ".svg"}
EXT_VIDEO = {".mp4", ".mov", ".webm", ".ogv", ".mpg", ".mpeg", ".avi", ".mkv"}
EXT_MEDIA = EXT_IMG | EXT_VIDEO


def _basename(p):
    """basename que entiende las dos barras.

    os.path.basename en Linux no parte rutas con barra invertida, y el
    registro guarda rutas de Windows. Sin esto, una auditoria corrida fuera
    de Windows reporta como huerfano todo el episodio.
    """
    return re.split(r"[\\/]", str(p or ""))[-1]


def _hash(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for bloque in iter(lambda: f.read(65536), b""):
            h.update(bloque)
    return h.hexdigest()


def _slug(txt, largo=40):
    t = re.sub(r"[^\w\s-]", "", (txt or "asset"), flags=re.UNICODE)
    t = re.sub(r"[\s-]+", "_", t.strip()).upper()
    return (t[:largo] or "ASSET").strip("_")


def _prefijo(ep_path):
    """FER_ para Ferruccio_Lamborghini. Respeta el naming que ya usa el episodio."""
    nombre = os.path.basename(ep_path)
    m = re.match(r"EP\d+_(.+)", nombre)
    base = (m.group(1) if m else nombre).replace("_", " ")
    return re.sub(r"[^A-Z]", "", base.upper())[:3] or "AST"


def cargar_registro(ep_path):
    p = os.path.join(ep_path, "asset_registry.json")
    if os.path.exists(p):
        try:
            return json.load(open(p, encoding="utf-8")), p
        except Exception:
            pass
    return [], p


def guardar_registro(registro, path):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(registro, f, ensure_ascii=False, indent=2)


def _indice_resultados(ep_path):
    """Los metadatos de cada URL ya los tiene la hoja. Se reusan en vez de
    pedirle a Jota que copie licencias a mano.

    Se leen TODOS los `resultados*.json` de la carpeta, no solo
    `resultados.json`: `archivo_historico.py --video` escribe
    `resultados_video.json` aparte, y si solo se indexara el de imagen, una
    URL marcada en la hoja de video perdia fuente, institucion y gap_id (la
    licencia igual se rescata del comentario que copia la hoja, pero el resto
    se iba a None en silencio).
    """
    carpeta = os.path.join(ep_path, "01_RESEARCH", "archivo")
    if not os.path.isdir(carpeta):
        return {}
    idx = {}
    for nombre in sorted(os.listdir(carpeta)):
        if not (nombre.startswith("resultados") and nombre.endswith(".json")):
            continue
        try:
            d = json.load(open(os.path.join(carpeta, nombre), encoding="utf-8"))
        except Exception:
            continue
        for i in d.get("items", []):
            for k in (i.get("url_directo"), i.get("url_pagina")):
                if k:
                    idx[k.strip()] = i
                    idx[_clave_url(k)] = i   # forma normalizada, sin query ni fragmento
    return idx


def _carpeta_destino(ep_path, ext):
    """04_IMAGES para imagen, 05_VIDEO para video.

    Antes todo caia en 04_IMAGES sin mirar la extension: un .mp4 bajado desde
    la hoja de video quedaba fisicamente mezclado con las fotos. La extension
    ya viene resuelta contra EXT_MEDIA antes de llegar aca, asi que esto solo
    decide la carpeta.
    """
    carpeta = "05_VIDEO" if ext in EXT_VIDEO else "04_IMAGES"
    return os.path.join(ep_path, carpeta)


def _clave_url(u):
    """Clave estable para cruzar URLs.

    Wikimedia devuelve la misma imagen con y sin parametros utm, y Library of
    Congress anexa un fragmento #h=...&w=... con las dimensiones. Comparar la
    cadena cruda haria que casi ningun item cruzara con su metadato.
    """
    u = str(u or "").split("#")[0].split("?")[0].strip()
    return urllib.parse.unquote(u).lower()


def partir_linea(linea):
    """Separa la URL del comentario que anexa la hoja de contactos.

    El formato exportado es:  <url>  # VERDE | Public domain
    No se puede cortar por el primer '#' porque las URLs de Library of Congress
    llevan fragmento propio (#h=2693&w=3994). El separador real son dos
    espacios seguidos de almohadilla.
    """
    m = re.split(r"\s{2,}#\s*", linea.strip(), maxsplit=1)
    url = m[0].strip()
    comentario = m[1].strip() if len(m) > 1 else ""
    lic = None
    if "|" in comentario:
        lic = comentario.split("|", 1)[1].strip()
    return url, lic


# Wikimedia exige un User-Agent descriptivo CON datos de contacto y penaliza
# las rafagas con HTTP 429. Un UA generico y trece descargas seguidas sin
# pausa es exactamente el patron que bloquean.
# Ver: https://meta.wikimedia.org/wiki/User-Agent_policy
UA = ("HUMANOS-archivo/1.0 (canal editorial Jota Growth; "
      "agentejotan8n@gmail.com) python-urllib/3")

# Segundos minimos entre peticiones al mismo servidor.
FRENO = {"upload.wikimedia.org": 1.5, "commons.wikimedia.org": 1.5,
         "tile.loc.gov": 0.7, "archive.org": 0.7}
FRENO_POR_DEFECTO = 0.4

_ultima_visita = {}


def _esperar_turno(url):
    host = urllib.parse.urlparse(url).netloc
    espera = FRENO.get(host, FRENO_POR_DEFECTO)
    ultimo = _ultima_visita.get(host)
    if ultimo is not None:
        falta = espera - (time.time() - ultimo)
        if falta > 0:
            time.sleep(falta)
    _ultima_visita[host] = time.time()


class ContenidoNoEsMedia(Exception):
    """El servidor respondio con una pagina (HTML/JSON) en vez del archivo.

    Pasa cuando la URL marcada en la hoja es la ficha de un item con varios
    archivos adentro (Internet Archive sin nombre de archivo, un item de
    loc.gov, un visor de Europeana) y no el archivo en si. Sin este chequeo,
    eso se guardaba con extension .mp4 o .jpg igual: un huerfano perfecto,
    porque nadie nota que esta roto hasta que intenta reproducirlo.
    """


def _parece_pagina(datos, content_type, ext_esperada):
    """Heuristica barata: si se esperaba media y lo que llego arranca como
    HTML o es demasiado chico y con content-type de texto, es una pagina."""
    ct = (content_type or "").lower()
    if ct.startswith("text/html") or ct.startswith("application/json"):
        return True
    cabeza = datos[:200].lstrip().lower()
    if cabeza.startswith(b"<!doctype html") or cabeza.startswith(b"<html"):
        return True
    return False


def descargar(url, destino, intentos=4, ext_esperada=None):
    """Descarga con freno por servidor y reintentos con espera creciente.

    Se reintenta en dos casos:
      429 / 503      el servidor pide que bajemos el ritmo
      IncompleteRead la conexion se corto a mitad del archivo
    Un 404 no se reintenta: no va a aparecer.

    Si `ext_esperada` es de video o imagen y lo que llega es HTML, se rechaza
    con ContenidoNoEsMedia en vez de guardarlo: mejor un fallido visible que
    un asset corrupto invisible.
    """
    espera = 3
    for intento in range(1, intentos + 1):
        _esperar_turno(url)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=90) as r:
                datos = r.read()
                content_type = r.headers.get("Content-Type", "")
            if ext_esperada in EXT_MEDIA and _parece_pagina(datos, content_type, ext_esperada):
                raise ContenidoNoEsMedia(
                    f"el servidor devolvio una pagina (Content-Type: {content_type or 'desconocido'}), "
                    f"no el archivo. La URL probablemente es la ficha de un item con varios "
                    f"archivos adentro, no el archivo directo.")
            with open(destino, "wb") as out:
                out.write(datos)
            return len(datos)

        except urllib.error.HTTPError as e:
            if e.code in (429, 503) and intento < intentos:
                print(f"    HTTP {e.code}, espero {espera}s y reintento "
                      f"({intento}/{intentos - 1})...")
                time.sleep(espera)
                espera *= 2
                continue
            raise
        except (http.client.IncompleteRead, ConnectionError, TimeoutError,
                urllib.error.URLError) as e:
            if intento < intentos:
                print(f"    {type(e).__name__}, reintento en {espera}s "
                      f"({intento}/{intentos - 1})...")
                time.sleep(espera)
                espera *= 2
                continue
            raise


def procesar_urls(ep_path, urls, monetizado=False):
    registro, reg_path = cargar_registro(ep_path)
    idx = _indice_resultados(ep_path)
    hashes = {e.get("hash") for e in registro if e.get("hash")}
    prefijo = _prefijo(ep_path)
    os.makedirs(os.path.join(ep_path, "04_IMAGES"), exist_ok=True)
    os.makedirs(os.path.join(ep_path, "05_VIDEO"), exist_ok=True)

    # URLs que ya se bajaron en una corrida anterior. Se saltan SIN pedirlas:
    # volver a descargar 16 archivos para descubrir por hash que ya estaban es
    # justo lo que hace que Wikimedia devuelva 429.
    ya = set()
    for e in registro:
        for k in (e.get("url_ficha"), e.get("storage_path")):
            if k:
                ya.add(_clave_url(k))

    # Continuar la numeracion donde quedo, en vez de pisar.
    usados = [int(e["asset_id"]) for e in registro
              if str(e.get("asset_id", "")).isdigit()]
    siguiente = max(usados) + 1 if usados else 100
    if siguiente < 100:
        siguiente = 100
    nuevos, saltados, fallidos, repetidos = 0, 0, 0, 0

    for linea in urls:
        url, lic_comentario = partir_linea(linea)
        if not url or not url.lower().startswith("http"):
            continue
        if _clave_url(url) in ya:
            print(f"    ya estaba registrado, no lo pido de nuevo.")
            repetidos += 1
            continue
        meta = idx.get(url) or idx.get(_clave_url(url)) or {}
        ext = os.path.splitext(urllib.parse.urlparse(url).path)[1].lower()
        # Si la fuente ya marco el tipo (Europeana/Internet Archive lo saben
        # aunque la URL no tenga extension reconocible), se respeta eso antes
        # de caer al default de imagen.
        if ext not in EXT_MEDIA:
            ext = ".mp4" if meta.get("tipo") == "video" else ".jpg"
        etiqueta = meta.get("titulo") or _slug(os.path.basename(
            urllib.parse.urlparse(url).path) or "asset")
        nombre = f"{prefijo}_{siguiente}_{_slug(etiqueta)}{ext}"
        dest_dir = _carpeta_destino(ep_path, ext)
        ruta = os.path.join(dest_dir, nombre)

        try:
            print(f"  bajando {url[:64]}...")
            descargar(url, ruta, ext_esperada=ext)
        except ContenidoNoEsMedia as e:
            print(f"    RECHAZADO: {str(e)}")
            print(f"    Abri la ficha a mano: {meta.get('url_pagina') or url}")
            if os.path.exists(ruta):
                os.remove(ruta)
            fallidos += 1
            continue
        except Exception as e:
            print(f"    FALLO: {type(e).__name__}: {str(e)[:70]}")
            if os.path.exists(ruta):
                os.remove(ruta)
            fallidos += 1
            continue

        h = _hash(ruta)
        if h in hashes:
            os.remove(ruta)
            print("    ya estaba en el episodio (mismo hash). Saltado.")
            saltados += 1
            continue

        # Prioridad: el metadato de la busqueda; si no cruzo, la etiqueta que
        # la propia hoja anexo al copiar.
        lic = meta.get("licencia") or lic_comentario or "sin licencia declarada"
        sem, nota = clasificar(lic, monetizado)
        hashes.add(h)
        ya.add(_clave_url(url))
        registro.append({
            "asset_id": str(siguiente),
            "hash": h,
            "source": meta.get("fuente") or "descarga manual",
            "storage_path": ruta,
            "licencia": lic,
            "semaforo": sem,
            "nota_licencia": nota,
            "url_ficha": meta.get("url_pagina") or url,
            "titulo_origen": meta.get("titulo"),
            "institucion": meta.get("institucion"),
            "gap": meta.get("gap"),
        })
        marca = {"verde": "OK", "ambar": "REVISAR", "rojo": "NO USAR"}[sem]
        print(f"    {nombre}  [{marca}] {lic[:40]}")
        nuevos += 1
        siguiente += 1

    guardar_registro(registro, reg_path)
    print(f"\n  {nuevos} inscritos, {repetidos} ya estaban, "
          f"{saltados} duplicados por contenido, {fallidos} fallidos.")
    if fallidos:
        print("  Volve a correr el .bat: los que fallaron se reintentan y")
        print("  los que ya estan no se vuelven a pedir.")
    print(f"  Registro: {reg_path}")
    return nuevos


def revisar_huerfanos(ep_path, monetizado=False):
    """Inscribe lo que ya esta en disco sin registrar, preguntando la licencia."""
    registro, reg_path = cargar_registro(ep_path)
    registradas = {os.path.normcase(_basename(e.get("storage_path") or ""))
                   for e in registro}

    # 05_VIDEO se suma a la revision: desde que --video baja metraje, un
    # huerfano puede estar ahi tanto como en 04_IMAGES.
    huerfanos = []
    for carpeta in ("04_IMAGES", "05_VIDEO"):
        dest_dir = os.path.join(ep_path, carpeta)
        if not os.path.isdir(dest_dir):
            continue
        huerfanos += [(dest_dir, f) for f in sorted(os.listdir(dest_dir))
                      if os.path.splitext(f)[1].lower() in EXT_MEDIA
                      and os.path.normcase(f) not in registradas]
    if not huerfanos:
        print("No hay archivos sin registrar. Todo trazado.")
        return 0

    print(f"{len(huerfanos)} archivos sin registrar.\n")
    print("Para cada uno, pega la licencia o la URL de la ficha de origen.")
    print("Enter vacio = 'sin licencia declarada' (queda en ambar).")
    print("Escribi 'propio' si lo generaste vos o con IA.\n")

    n = 0
    for dest_dir, f in huerfanos:
        ruta = os.path.join(dest_dir, f)
        resp = input(f"  {f}\n    licencia/origen: ").strip()
        if resp.lower() in ("propio", "mio", "ia", "generado"):
            lic, fuente = "propio / generado", "generado"
            sem, nota = "verde", "material propio o generado: sin derechos de terceros"
        else:
            lic = resp or "sin licencia declarada"
            fuente = "registro retroactivo"
            sem, nota = clasificar(lic, monetizado)
        registro.append({
            "asset_id": os.path.splitext(f)[0],
            "hash": _hash(ruta),
            "source": fuente,
            "storage_path": ruta,
            "licencia": lic,
            "semaforo": sem,
            "nota_licencia": nota,
            "url_ficha": resp if resp.startswith("http") else None,
        })
        n += 1

    guardar_registro(registro, reg_path)
    print(f"\n  {n} archivos inscritos retroactivamente.")
    print(f"  Registro: {reg_path}")
    return n


def rellenar_desde_sidecars(ep_path, monetizado=False):
    """Recupera las licencias que el sistema ya tenia pero tiraba.

    `asset_collector.py` siempre escribio un sidecar por asset en
    01_RESEARCH/metadata/ con la licencia adentro. Lo que no hacia era
    llevarla al registro. Asi que para todo el material historico la licencia
    NO se perdio: esta ahi, sin leer. Esto la rescata.
    """
    registro, reg_path = cargar_registro(ep_path)
    meta_dir = os.path.join(ep_path, "01_RESEARCH", "metadata")
    if not os.path.isdir(meta_dir):
        print("No hay 01_RESEARCH/metadata en este episodio.")
        return 0

    sidecars = {}
    for f in os.listdir(meta_dir):
        if not f.endswith(".json"):
            continue
        try:
            d = json.load(open(os.path.join(meta_dir, f), encoding="utf-8"))
        except Exception:
            continue
        # el sidecar se llama <nombre_de_archivo>.json
        sidecars[os.path.normcase(f[:-5])] = d
        if d.get("hash"):
            sidecars["hash:" + d["hash"]] = d

    n = 0
    for e in registro:
        actual = (e.get("licencia") or "").strip().lower()
        if actual and actual != "sin licencia declarada":
            continue  # ya tiene licencia util
        base = os.path.normcase(_basename(e.get("storage_path") or ""))
        d = sidecars.get(base) or sidecars.get("hash:" + (e.get("hash") or ""))
        if not d or not d.get("license"):
            continue
        lic = d["license"]
        sem, nota = clasificar(lic, monetizado)
        e["licencia"] = lic
        e["semaforo"] = sem
        e["nota_licencia"] = nota
        e["url_ficha"] = e.get("url_ficha") or d.get("url")
        e["titulo_origen"] = e.get("titulo_origen") or d.get("title")
        e["source"] = d.get("source") or e.get("source")
        marca = {"verde": "OK", "ambar": "REVISAR", "rojo": "NO USAR"}[sem]
        print(f"  {base[:50]:52} [{marca}] {lic}")
        n += 1

    guardar_registro(registro, reg_path)
    print(f"\n  {n} licencias recuperadas de los sidecars.")
    return n


def main():
    ap = argparse.ArgumentParser(description="Descarga e inscribe assets con su licencia")
    ap.add_argument("--episodio", required=True)
    ap.add_argument("--rellenar", action="store_true",
                    help="recupera licencias de los sidecars de metadatos")
    ap.add_argument("--lista", help="archivo con una URL por linea")
    ap.add_argument("--desde-portapapeles", action="store_true",
                    help="lee las URLs pegadas por stdin")
    ap.add_argument("--revisar", action="store_true",
                    help="inscribe los archivos que ya estan en disco sin registrar")
    ap.add_argument("--monetizado", action="store_true")
    ap.add_argument("--sin-monetizacion", action="store_true",
                    help="el canal no esta monetizado: las NC quedan en ambar")
    a = ap.parse_args()

    if not os.path.isdir(a.episodio):
        print(f"No existe {a.episodio}")
        return 1

    if a.rellenar:
        rellenar_desde_sidecars(a.episodio, a.monetizado)
        return 0

    if a.revisar:
        # Primero se rescata lo que ya estaba escrito, y solo despues se le
        # pregunta a Jota. Preguntarle por algo que el sistema ya sabia seria
        # hacerle perder el tiempo.
        rellenar_desde_sidecars(a.episodio, a.monetizado)
        print()
        revisar_huerfanos(a.episodio, a.monetizado)
        return 0

    if a.lista:
        urls = [l.strip() for l in open(a.lista, encoding="utf-8") if l.strip()]
    elif a.desde_portapapeles:
        print("Pega las URLs (una por linea). Terminá con una linea vacia "
              "y Ctrl+Z + Enter en Windows:\n")
        urls = []
        try:
            for linea in sys.stdin:
                linea = linea.strip()
                if not linea:
                    break
                urls.append(linea)
        except KeyboardInterrupt:
            pass
    else:
        ap.error("indica --lista, --desde-portapapeles o --revisar")

    if not urls:
        print("No recibi ninguna URL.")
        return 1

    print(f"\n{len(urls)} URLs. Bajando a {a.episodio}\\04_IMAGES\n")
    procesar_urls(a.episodio, urls, a.monetizado)
    print("\nAhora corre el gate:")
    print(f"  python derechos.py --episodio \"{a.episodio}\"")
    return 0


if __name__ == "__main__":
    sys.exit(main())
