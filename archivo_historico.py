"""
archivo_historico — buscador de material de archivo para HUMANOS.

El problema que resuelve: buscar imagenes de archivo a mano es el cuello de
botella de la produccion. Moore ya deja escritas las `manual_search_queries`
de cada gap, pero alguien tiene que ir a googlearlas una por una, evaluar
licencias, y bajar los archivos.

Esto consulta seis archivos historicos a la vez, deduplica, y escribe una
HOJA DE CONTACTOS en HTML: una sola pagina con todas las miniaturas, la
licencia de cada una y el enlace directo. Se abre en el navegador y se
marca lo que sirve.

Ninguna de estas fuentes cobra. Cero creditos de Apify, cero de Kling.
Apify y Kling quedan para lo que estas no cubren.

Fuentes, en orden de utilidad para HUMANOS:

  Europeana        Agrega los archivos publicos europeos, incluido el
                   Istituto Luce Cinecitta: el archivo de noticiarios de
                   la Italia de posguerra. Para EP0004 es LA fuente.
                   Requiere una wskey gratuita: https://pro.europeana.eu/page/get-api
  Internet Archive Cine, noticiarios, revistas digitalizadas. Sin clave.
  Wikimedia Commons Lo que el pipeline ya usaba. Sin clave.
  Library of Congress  Fotografia documental del siglo XX. Sin clave.
  Openverse        Agregador de material con licencia abierta. Sin clave.
  Flickr Commons   Archivos institucionales en dominio publico.
                   Requiere FLICKR_API_KEY (gratuita).

Uso:

    # probar que hay red y que responden las fuentes
    python archivo_historico.py --test

    # buscar sobre los gaps que dejo Moore en un episodio
    python archivo_historico.py --episodio personajes/Ferruccio_Lamborghini/EP0004_Ferruccio_Lamborghini

    # buscar una consulta suelta
    python archivo_historico.py --buscar "Lamborghini trattori 1950" "Enzo Ferrari Maranello 1962"

    # buscar METRAJE, no fotos: solo las fuentes con fondo en movimiento y
    # solo los gaps que Moore marco como video_archivo
    python archivo_historico.py --episodio <ruta> --video

Salida:
    <episodio>/01_RESEARCH/archivo/hoja_de_contactos.html
    <episodio>/01_RESEARCH/archivo/resultados.json
    (con --video, los mismos con sufijo _video)

Sobre el video: ocho minutos de documental no se sostienen con stills. El modo
--video acota Europeana a TYPE:VIDEO (que es como se llega al fondo filmico
del Istituto Luce), Internet Archive a mediatype:movies, Commons a
filetype:video, y anade el catalogo de cine de la Library of Congress. Los
catalogos que no publican API — el propio Luce, British Pathe, AP Archive —
salen como enlaces de busqueda ya compuestos en la hoja, para navegarlos a
mano. Lo que esas agencias tienen casi nunca es gratis: la hoja lo dice, no lo
disimula.
"""

import os
import re
import sys
import json
import html
import time
import argparse
import urllib.parse
import urllib.request
import urllib.error
from concurrent.futures import ThreadPoolExecutor

try:
    import env_boot  # carga .env si esta disponible
except Exception:
    pass

UA = "HUMANOS-archivo/1.0 (canal editorial; contacto: jota)"
TIMEOUT = 25


# ---------------------------------------------------------------------------
# infraestructura
# ---------------------------------------------------------------------------

def _get(url, headers=None, timeout=TIMEOUT):
    h = {"User-Agent": UA}
    if headers:
        h.update(headers)
    req = urllib.request.Request(url, headers=h)
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.read().decode("utf-8", errors="ignore")


def _json(url, headers=None):
    return json.loads(_get(url, headers))


def _q(s):
    return urllib.parse.quote(str(s))


# ---------------------------------------------------------------------------
# semaforo de licencias
# ---------------------------------------------------------------------------
#
# Dos familias de licencia parecen libres y no lo son:
#
#   ND (no derivatives)  - prohibe la obra derivada. Recortar un clip y
#                          montarlo en una edicion ES una obra derivada.
#                          Es el que mas se cuela porque "parece" permisivo.
#                          NO depende de si hay anuncios: rojo siempre.
#
#   NC (non commercial)  - prohibe el uso comercial. Con el canal todavia sin
#                          monetizar se puede tolerar (--sin-monetizacion lo
#                          baja a ambar), pero con dos matices que conviene
#                          tener presentes:
#                            1. El dia que se monetice hay que reemplazar ese
#                               material y volver a editar los episodios.
#                            2. Creative Commons define NC como uso "dirigido
#                               principalmente a ventaja comercial". Un canal
#                               que promociona productos de pago puede caer
#                               ahi aunque no tenga AdSense todavia.
#
# Esto no es asesoria legal: es un primer filtro para no perder tiempo
# marcando material que despues hay que tirar. La ficha de la institucion
# manda siempre.

def clasificar_licencia(txt, tolerar_nc=False):
    """Devuelve (semaforo, explicacion). verde / ambar / rojo.

    `tolerar_nc=True` baja las licencias NC de rojo a ambar. Se activa con
    --sin-monetizacion. ND e In Copyright NO se mueven: no dependen de si hay
    anuncios, dependen de si haces una obra derivada, y una edicion lo es.
    """
    t = (txt or "").lower()

    if not t.strip() or t in ("verificar", "sin dato", "sin licencia declarada"):
        return "ambar", "sin licencia declarada: abri la ficha antes de usar"

    # ND e In Copyright: rojo siempre, monetizado o no.
    if "-nd" in t or "noderiv" in t or "no derivative" in t:
        return "rojo", "sin obras derivadas: montarlo en una edicion ya es derivada"
    if "/inc/" in t or "in copyright" in t or "incopyright" in t:
        return "rojo", "en copyright: hace falta permiso del titular"
    if "rr-r" in t or "all rights reserved" in t:
        return "rojo", "todos los derechos reservados"

    # NC: depende del uso.
    if "-nc" in t or "noncommercial" in t or "non-commercial" in t:
        if tolerar_nc:
            return "ambar", ("no comercial: hoy pasa, pero si monetizas el canal "
                             "o promocionas tus productos hay que reemplazarlo")
        return "rojo", "no comercial: no sirve para un canal monetizado"

    # Lo que si se puede usar
    if "publicdomain" in t or "public domain" in t or "dominio publico" in t \
       or "/pdm/" in t or "cc0" in t or "nokc" in t or "sin restricciones" in t:
        return "verde", "dominio publico: uso libre, atribucion recomendada"
    if "by-sa" in t or "by sa" in t:
        return "verde", "CC BY-SA: se puede, con atribucion"
    if re.search(r"\bby\b", t) or "attribution" in t:
        return "verde", "CC BY: se puede, con atribucion"

    return "ambar", "licencia no reconocida: verifica en la ficha"


TOLERAR_NC = False  # lo activa --sin-monetizacion

# Que tipo de material se busca. Lo fija --video / --imagen.
#
# Por que hace falta el interruptor: un documental de ocho minutos no se
# sostiene con fotos. Ken Burns sobre un still aguanta cinco segundos, no
# cuatrocientos sesenta. Pero las mismas fuentes que sirven para foto
# devuelven casi solo foto si no se las filtra: Wikimedia y Openverse son
# catalogos de imagen fija, y Europeana mezcla los dos fondos en la misma
# respuesta. Sin filtro explicito, buscar video devuelve fotos y uno cree que
# no hay metraje cuando lo que pasa es que no lo pidio.
MEDIA = "todo"  # todo | video | imagen


def _item(fuente, titulo, url_pagina, url_directo, miniatura, licencia,
          fecha=None, institucion=None, tipo="imagen"):
    """Forma canonica de un resultado. Todo lo demas se normaliza a esto."""
    semaforo, nota = clasificar_licencia(licencia, TOLERAR_NC)
    return {
        "fuente": fuente,
        "titulo": (titulo or "").strip()[:220],
        "url_pagina": url_pagina,
        "url_directo": url_directo,
        "miniatura": miniatura,
        "licencia": licencia or "verificar",
        "semaforo": semaforo,
        "nota_licencia": nota,
        "fecha": fecha,
        "institucion": institucion,
        "tipo": tipo,
    }


# ---------------------------------------------------------------------------
# fuentes
# ---------------------------------------------------------------------------

VIDEO_EXT = (".ogv", ".webm", ".mp4", ".mpg", ".mpeg", ".mov", ".avi", ".mkv")


def buscar_wikimedia(consulta, limite=12):
    # Commons guarda video (ogv/webm) en el mismo namespace 6 que las fotos.
    # `filetype:video` es lo unico que los separa.
    q = ("filetype:video " + consulta) if MEDIA == "video" else consulta
    url = ("https://commons.wikimedia.org/w/api.php?action=query&format=json"
           "&generator=search&gsrnamespace=6&gsrlimit=%d&gsrsearch=%s"
           "&prop=imageinfo&iiprop=url|extmetadata&iiurlwidth=320"
           % (limite, _q(q)))
    d = _json(url)
    out = []
    for p in (d.get("query", {}).get("pages", {}) or {}).values():
        ii = (p.get("imageinfo") or [{}])[0]
        meta = ii.get("extmetadata", {}) or {}
        lic = (meta.get("LicenseShortName", {}) or {}).get("value", "")
        fecha = (meta.get("DateTimeOriginal", {}) or {}).get("value", "")
        nombre = p.get("title", "").replace("File:", "")
        es_video = nombre.lower().endswith(VIDEO_EXT)
        out.append(_item(
            "Wikimedia Commons",
            nombre,
            ii.get("descriptionurl"), ii.get("url"),
            ii.get("thumburl") or ii.get("url"),
            lic or "ver ficha",
            re.sub("<[^>]+>", "", fecha or "")[:40] or None,
            None,
            "video" if es_video else "imagen",
        ))
    return out


def buscar_europeana(consulta, limite=12):
    """Europeana agrega el Istituto Luce. Para Italia de posguerra no hay
    nada mejor y es gratis.

    Nota importante: Europeana cataloga en el idioma de la institucion que
    aporta el material. Para archivo italiano hay que consultar EN ITALIANO.
    Buscar "Italian tractors postwar" devuelve cero; "trattori agricoltura"
    devuelve el Luce entero. De eso se ocupa expandir_consultas().

    Tampoco se filtra por media/thumbnail: ese filtro descarta la mayor parte
    del fondo historico, que esta catalogado sin preview.
    """
    key = os.environ.get("EUROPEANA_KEY", "").strip()
    if not key:
        raise RuntimeError(
            "falta EUROPEANA_KEY en el .env. Se pide gratis en "
            "https://pro.europeana.eu/page/get-api y es la fuente mas util "
            "para archivo italiano.")
    # qf=TYPE:VIDEO es lo que separa el fondo filmico del fotografico. Sin el,
    # una consulta al Istituto Luce devuelve mayoritariamente fotogramas
    # sueltos catalogados como imagen, que es justo lo que ya tenemos.
    filtro = ""
    if MEDIA == "video":
        filtro = "&qf=TYPE:VIDEO"
    elif MEDIA == "imagen":
        filtro = "&qf=TYPE:IMAGE"
    url = ("https://api.europeana.eu/record/v2/search.json?wskey=%s"
           "&query=%s&rows=%d&profile=rich%s"
           % (_q(key), _q(consulta), limite, filtro))
    d = _json(url)
    out = []
    for it in d.get("items", []) or []:
        titulo = (it.get("title") or [""])[0]
        es_video = (it.get("type") == "VIDEO")
        edm = (it.get("edmIsShownBy") or it.get("edmIsShownAt") or [None])[0]
        if es_video and edm:
            # edmIsShownBy varia por institucion que aporta el fondo: a veces
            # es el archivo real, a veces la pagina del visor del proveedor
            # (para el Istituto Luce, patrimonio.archivioluce.com/.../detail/
            # o un manifiesto de streaming .mpd que urlopen no puede guardar
            # como video reproducible). No hay forma de saber cual es sin
            # abrirlo: se avisa en vez de arriesgar una descarga corrupta.
            titulo = f"[VERIFICAR ANTES DE BAJAR — puede ser la pagina del visor, no el archivo] {titulo}"
        out.append(_item(
            "Europeana",
            titulo,
            it.get("guid"), edm,
            (it.get("edmPreview") or [None])[0],
            it.get("rights", [None])[0] or "ver ficha",
            (it.get("year") or [None])[0],
            (it.get("dataProvider") or [None])[0],
            "video" if es_video else "imagen",
        ))
    return out


_IA_EXT_DESCARTAR = (".xml", ".sqlite", ".torrent", "_meta.txt", "_files.xml")
_IA_EXT_VIDEO_BUENA = (".mp4", ".webm", ".ogv", ".mpg", ".mpeg", ".mov", ".mkv")
_IA_EXT_IMAGEN_BUENA = (".jpg", ".jpeg", ".png", ".gif", ".webp", ".tif", ".tiff")


def _ia_archivo_directo(identificador, quiere_video):
    """El item de un `identifier` de Internet Archive casi siempre tiene
    VARIOS archivos (original + derivados + miniaturas + metadatos). Un item
    con dos peliculas ("...#1.mp4" y "...#2.mp4") no tiene UN archivo, tiene
    dos: `archive.org/download/<identifier>` sin nombre de archivo devuelve
    el listado de la carpeta, no un video. Eso es lo que se descargaba antes.

    Esto pide el metadato real del item y elige el mejor archivo: el mas
    pesado entre los que tienen la extension correcta, evitando derivados
    "_ia.mp4"/miniaturas cuando hay original. Si no se puede resolver (item
    caido, sin archivos del tipo pedido), devuelve None: mejor no ofrecer
    nada que ofrecer el listado de carpeta disfrazado de archivo.
    """
    try:
        d = _json(f"https://archive.org/metadata/{_q(identificador)}")
    except Exception:
        return None
    archivos = d.get("files") or []
    buenas = _IA_EXT_VIDEO_BUENA if quiere_video else _IA_EXT_IMAGEN_BUENA
    candidatos = [
        f for f in archivos
        if str(f.get("name", "")).lower().endswith(buenas)
        and not str(f.get("name", "")).lower().endswith(_IA_EXT_DESCARTAR)
    ]
    if not candidatos:
        return None
    # Entre varios, el mas pesado suele ser el original sin recomprimir.
    mejor = max(candidatos, key=lambda f: int(f.get("size") or 0))
    nombre = mejor.get("name")
    if not nombre:
        return None
    return f"https://archive.org/download/{identificador}/{urllib.parse.quote(nombre)}"


def buscar_internet_archive(consulta, limite=12):
    if MEDIA == "video":
        consulta = f"mediatype:(movies) AND ({consulta})"
    elif MEDIA == "imagen":
        consulta = f"mediatype:(image) AND ({consulta})"
    url = ("https://archive.org/advancedsearch.php?q=%s"
           "&fl%%5B%%5D=identifier&fl%%5B%%5D=title&fl%%5B%%5D=year"
           "&fl%%5B%%5D=mediatype&fl%%5B%%5D=licenseurl"
           "&rows=%d&page=1&output=json" % (_q(consulta), limite))
    d = _json(url)
    out = []
    for doc in d.get("response", {}).get("docs", []) or []:
        ident = doc.get("identifier")
        if not ident:
            continue
        t = doc.get("title")
        if isinstance(t, list):
            t = t[0] if t else ""
        es_video = doc.get("mediatype") == "movies"

        # Resolver el archivo real cuesta una peticion extra por resultado,
        # pero la alternativa es un enlace que "abrir" descarga como HTML
        # disfrazado de video sin que nadie lo note hasta reproducirlo.
        directo = _ia_archivo_directo(ident, es_video)
        if directo is None:
            directo = f"https://archive.org/details/{ident}"
            # El prefijo va en el TITULO, no en la licencia: tocar el campo
            # de licencia le rompe la clasificacion de semaforo a
            # clasificar_licencia(), que compara el texto exacto.
            t = f"[SOLO FICHA, NO ARCHIVO — abrir y elegir a mano] {t}"

        # Internet Archive aloja tanto dominio publico como material con
        # derechos. Sin `licenseurl` explicito NO se puede asumir nada: el
        # fondo incluye peliculas comerciales recientes subidas por usuarios.
        out.append(_item(
            "Internet Archive", t,
            f"https://archive.org/details/{ident}",
            directo,
            f"https://archive.org/services/img/{ident}",
            doc.get("licenseurl") or "sin licencia declarada",
            doc.get("year"), None,
            "video" if es_video else "imagen",
        ))
    return out


def buscar_loc(consulta, limite=12):
    url = ("https://www.loc.gov/photos/?q=%s&fo=json&c=%d"
           % (_q(consulta), limite))
    d = _json(url)
    out = []
    for r in d.get("results", []) or []:
        img = r.get("image_url") or []
        out.append(_item(
            "Library of Congress", r.get("title"),
            r.get("id") or r.get("url"),
            ("https:" + img[-1]) if img and img[-1].startswith("//") else (img[-1] if img else None),
            ("https:" + img[0]) if img and img[0].startswith("//") else (img[0] if img else None),
            "dominio publico (verificar ficha)",
            (r.get("date") or None), "Library of Congress",
        ))
    return out


def buscar_loc_video(consulta, limite=12):
    """El fondo filmico de la Library of Congress, que es otro catalogo que el
    de fotografia: noticiarios, documentales y cine mudo digitalizados.

    La API de busqueda de loc.gov no publica un campo de archivo descargable
    para audiovisual (a diferencia de `buscar_loc`, que si tiene `image_url`
    resuelto a un JPG real): `r["url"]` es la pagina del item. Se avisa en el
    titulo en vez de ofrecerlo como si fuera el archivo, que es lo que
    generaba el link que se descargaba como HTML disfrazado de video."""
    url = ("https://www.loc.gov/film-and-videos/?q=%s&fo=json&c=%d"
           % (_q(consulta), limite))
    d = _json(url)
    out = []
    for r in d.get("results", []) or []:
        img = r.get("image_url") or []
        mini = img[0] if img else None
        if mini and mini.startswith("//"):
            mini = "https:" + mini
        titulo = f"[SOLO FICHA, NO ARCHIVO — abrir y descargar a mano] {r.get('title')}"
        out.append(_item(
            "LOC — film & video", titulo,
            r.get("id") or r.get("url"), r.get("url"), mini,
            "dominio publico (verificar ficha)",
            (r.get("date") or None), "Library of Congress", "video",
        ))
    return out


def buscar_openverse(consulta, limite=12):
    url = ("https://api.openverse.org/v1/images/?q=%s&page_size=%d"
           % (_q(consulta), limite))
    d = _json(url)
    out = []
    for r in d.get("results", []) or []:
        out.append(_item(
            "Openverse", r.get("title"),
            r.get("foreign_landing_url"), r.get("url"),
            r.get("thumbnail") or r.get("url"),
            (r.get("license") or "").upper() + " " + (r.get("license_version") or ""),
            None, r.get("source"),
        ))
    return out


def buscar_flickr_commons(consulta, limite=12):
    key = os.environ.get("FLICKR_API_KEY", "").strip()
    if not key:
        raise RuntimeError("falta FLICKR_API_KEY en el .env (gratuita).")
    url = ("https://api.flickr.com/services/rest/?method=flickr.photos.search"
           "&api_key=%s&text=%s&is_commons=true&per_page=%d"
           "&extras=url_l,url_m,license,date_taken,owner_name"
           "&format=json&nojsoncallback=1" % (_q(key), _q(consulta), limite))
    d = _json(url)
    out = []
    for p in d.get("photos", {}).get("photo", []) or []:
        out.append(_item(
            "Flickr Commons", p.get("title"),
            f"https://www.flickr.com/photos/{p.get('owner')}/{p.get('id')}",
            p.get("url_l") or p.get("url_m"), p.get("url_m"),
            "Flickr Commons: sin restricciones conocidas de copyright",
            p.get("datetaken"), p.get("ownername"),
        ))
    return out


FUENTES = {
    "europeana": buscar_europeana,
    "internet_archive": buscar_internet_archive,
    "wikimedia": buscar_wikimedia,
    "loc": buscar_loc,
    "loc_video": buscar_loc_video,
    "openverse": buscar_openverse,
    "flickr": buscar_flickr_commons,
}

# Fuentes que tienen fondo en movimiento. Openverse, Flickr Commons y el
# catalogo de fotografia de la LOC son de imagen fija: preguntarles por video
# gasta tiempo y devuelve cero.
FUENTES_VIDEO = ["europeana", "internet_archive", "loc_video", "wikimedia"]

# El Istituto Luce se consulta via Europeana porque su catalogo propio no
# publica API. Pero la ficha de Europeana no siempre trae el clip: para eso
# esta el catalogo original, que se navega a mano. Estos enlaces salen en la
# hoja de contactos para que la busqueda manual sea un clic y no una
# expedicion.
CATALOGOS_MANUALES = [
    ("Istituto Luce — Patrimonio",
     "https://patrimonio.archivioluce.com/luce-web/search/result.html?query={q}",
     "Noticiarios del estado italiano. Es EL fondo para la Italia de posguerra. "
     "Uso editorial: hay que pedir licencia, no es dominio publico."),
    ("Internet Archive — solo peliculas",
     "https://archive.org/search?query={q}&and[]=mediatype%3A%22movies%22",
     "Noticiarios y cine. Comprobar la licencia item por item: el fondo mezcla "
     "dominio publico con material subido sin derechos."),
    ("British Pathe",
     "https://www.britishpathe.com/search/query/{q}",
     "Noticiarios britanicos con cobertura del motor italiano. De pago, con "
     "preview marcado al agua."),
    ("AP Archive",
     "https://www.aparchive.com/search?st={q}",
     "Agencia. Caro, pero tiene lo que nadie mas filmo."),
]

# Idioma en el que conviene consultar cada fuente. Un archivo cataloga en el
# idioma de la institucion que aporta el fondo: Europeana e Istituto Luce en
# italiano, Library of Congress en ingles. Wikimedia responde mejor a nombres
# propios pelados que a frases.
IDIOMA_FUENTE = {
    "europeana": ["it", "en"],
    "internet_archive": ["en", "it"],
    "wikimedia": ["entidades", "en"],
    "loc": ["en"],
    "loc_video": ["en"],
    "openverse": ["en"],
    "flickr": ["en"],
}


# ---------------------------------------------------------------------------
# expansion de consultas
# ---------------------------------------------------------------------------
#
# El problema real que resuelve esta seccion:
#
# Moore escribe las `manual_search_queries` como frases descriptivas pensadas
# para que un humano las googlee: "Ferruccio Lamborghini tractor production
# post-war Italy". Google entiende eso. Un archivo historico no: busca
# palabras clave sobre fichas de catalogo, y una frase de seis conceptos
# devuelve cero en todas las fuentes.
#
# Ademas cada archivo cataloga en su idioma. El fondo del Istituto Luce sobre
# la mecanizacion agricola italiana esta descrito con "trattori" y
# "agricoltura", no con "tractors".
#
# Asi que antes de buscar, cada gap se traduce a un ramillete de consultas
# cortas de catalogo, en italiano, ingles y nombres propios sueltos.

TERMINOS_IT = {
    # ingles
    "tractor": "trattore", "tractors": "trattori",
    "factory": "fabbrica", "farm": "agricoltura", "farming": "agricoltura",
    "postwar": "dopoguerra", "post-war": "dopoguerra",
    "car": "automobile", "cars": "automobili", "engine": "motore",
    "workshop": "officina", "industry": "industria",
    "reconstruction": "ricostruzione", "worker": "operaio",
    "workers": "operai", "clutch": "frizione", "machinery": "macchinari",
    # espanol, que es como escribe Moore
    "tractor": "trattore", "tractores": "trattori",
    "fabrica": "fabbrica", "fábrica": "fabbrica",
    "agricola": "agricoltura", "agrícola": "agricoltura",
    "posguerra": "dopoguerra", "embrague": "frizione",
    "motor": "motore", "coche": "automobile", "auto": "automobile",
    "automovil": "automobile", "automóvil": "automobile",
    "taller": "officina", "montaje": "catena di montaggio",
    "industrial": "industria", "obrero": "operaio", "obreros": "operai",
    "maquinaria": "macchinari", "oficina": "ufficio",
}

# Ruido de produccion: describe el ENCARGO, no el contenido. Si entra en la
# consulta, la mata. Moore siempre abre con "Metraje de archivo o recreacion
# IA de...", y sin este filtro eso termina siendo la palabra buscada.
_STOP = set("""a an the of in on at to for with and or from by his her its this that
un una el la los las de del en con y o para por su sus lo al es ser un una
production visual reenactment footage historical image images photo photos
metraje recreacion recreación archivo visualizacion visualización plano planos
escena escenas imagen imagenes imágenes video clip secuencia toma tomas
idealmente debe transmitir mostrar mostrarse capture capturar asociado
fuertemente entorno ambiente estilo cinematografico cinematográfico dramatica
dramática realista detallada clara similitud demostracion demostración
proceso descubrimiento pistas alternativamente crear usar utilizar
graficos gráficos motion combinacion combinación existe sobre entre entorno
primer plano camara cámara""".split())


def _entidades(texto):
    """Nombres propios y anos. Es lo que mejor funciona en Wikimedia.

    Se descartan los que caen en _STOP: una frase en espanol empieza con
    mayuscula, asi que "Metraje" y "Recreacion" parecen nombres propios y no
    lo son.
    """
    props = re.findall(r"\b[A-Z][\w'À-ſ]+(?:\s+[A-Z][\w'À-ſ]+)*", texto or "")
    limpios = []
    for p in props:
        partes = [w for w in p.split() if w.lower() not in _STOP]
        if partes and len(" ".join(partes)) > 3:
            limpios.append(" ".join(partes))
    anos = re.findall(r"\b(1[89]\d{2}|20\d{2})\b", texto or "")
    return limpios + anos


def _expandir_determinista(consulta):
    """Sin IA: recorta a palabras utiles y traduce lo que sepa al italiano."""
    ents = _entidades(consulta)
    palabras = [w for w in re.findall(r"[\wÀ-ſ'-]+", (consulta or "").lower())
                if w not in _STOP and len(w) > 2]
    it = [TERMINOS_IT[w] for w in palabras if w in TERMINOS_IT]
    variantes = {"entidades": [], "it": [], "en": [], "es": []}
    if ents:
        variantes["entidades"] = [ents[0]] + ([" ".join(ents[:2])] if len(ents) > 1 else [])
    if it:
        variantes["it"] = [" ".join(it[:2])] + ([it[0]] if len(it) > 1 else [])
        if ents:
            variantes["it"].append(f"{ents[0]} {it[0]}")
    variantes["en"] = [" ".join(palabras[:3])] if palabras else []
    if ents and palabras:
        variantes["en"].append(f"{ents[0]} {palabras[0]}")
    return variantes, True, "expansion deterministica (sin IA)"


PROMPT_EXPANSION = """Sos documentalista de archivo audiovisual. Trabajas buscando
material historico en catalogos institucionales (Istituto Luce, Europeana,
Internet Archive, Library of Congress, Wikimedia Commons).

Te doy la descripcion de un plano que falta en un documental. Tenes que
convertirla en consultas de CATALOGO, no en frases descriptivas.

Reglas duras:
- De 1 a 4 palabras por consulta. Nunca frases largas.
- Terminos que un archivista habria escrito en la ficha, no lo que se ve en pantalla.
- En italiano usa los terminos con los que un archivo italiano cataloga su fondo.
- Los nombres propios van solos o con un termino, nunca dentro de una frase.
- Nada de palabras como "footage", "visual", "reenactment", "historical".

Ademas decidime si este plano PUEDE existir como material de archivo real.
Una escena intima, privada o sin camara presente (una conversacion a puerta
cerrada, un pensamiento, una reaccion emocional de alguien sin prensa delante)
NO existe en ningun archivo: hay que recrearla. Se honesto con eso, porque
mandar a buscar lo que no existe hace perder horas.

PLANO QUE FALTA:
{descripcion}

Responde solo con este JSON:
{{
  "archivable": true o false,
  "motivo": "una frase corta explicando por que existe o no existe en archivo",
  "it": ["consulta corta en italiano", "..."],
  "en": ["consulta corta en ingles", "..."],
  "es": ["consulta corta en espanol", "..."],
  "entidades": ["Nombre Propio", "..."]
}}"""


def expandir_consultas(descripcion, usar_ia=True):
    """Devuelve (variantes_por_idioma, archivable, motivo)."""
    if usar_ia and os.environ.get("OPENROUTER_API_KEY"):
        try:
            from openrouter_client import OpenRouterClient
            d = OpenRouterClient().complete_json(
                PROMPT_EXPANSION.format(descripcion=descripcion),
                "Sos documentalista de archivo. Respondes solo JSON valido.")
            variantes = {k: [str(x) for x in (d.get(k) or [])][:4]
                         for k in ("it", "en", "es", "entidades")}
            if any(variantes.values()):
                return variantes, bool(d.get("archivable", True)), d.get("motivo", "")
        except Exception as e:
            print(f"  [expansion] La IA fallo ({type(e).__name__}), uso el metodo simple.")
    return _expandir_determinista(descripcion)


def _consultas_para(fuente, variantes):
    """Ordena las variantes segun el idioma que le sirve a esa fuente."""
    out = []
    for idioma in IDIOMA_FUENTE.get(fuente, ["en"]):
        out.extend(variantes.get(idioma) or [])
    for resto in variantes.values():
        out.extend(resto)
    vistos, limpio = set(), []
    for c in out:
        c = (c or "").strip()
        if c and c.lower() not in vistos:
            vistos.add(c.lower())
            limpio.append(c)
    return limpio


# ---------------------------------------------------------------------------
# orquestacion
# ---------------------------------------------------------------------------

def buscar_todo(planos, limite_por_fuente=12, fuentes=None, usar_ia=True):
    """`planos` es una lista de dicts {descripcion, gap}.

    Para cada plano se generan variantes de consulta y cada fuente prueba las
    suyas EN CASCADA: si la primera devuelve cero, sigue con la siguiente. Se
    para en cuanto hay resultados. Asi una consulta mal formulada no deja el
    gap vacio.

    Una fuente caida no tumba la corrida: se registra el fallo y se sigue.
    """
    fuentes = fuentes or list(FUENTES)
    resultados, fallos, diagnostico = [], [], []

    print("Traduciendo los gaps de Moore a consultas de catalogo...\n")
    for p in planos:
        p["variantes"], p["archivable"], p["motivo"] = expandir_consultas(
            p["descripcion"], usar_ia)
        marca = "ARCHIVO" if p["archivable"] else "SOLO RECREACION"
        print(f"  {p.get('gap') or '-'}  [{marca}] {p['motivo'][:70]}")
        muestra = _consultas_para(fuentes[0] if fuentes else 'en', p["variantes"])[:4]
        print(f"      -> {' | '.join(muestra)}\n")
        diagnostico.append({"gap": p.get("gap"), "archivable": p["archivable"],
                            "motivo": p["motivo"], "variantes": p["variantes"]})

    trabajos = [(f, p) for p in planos if p["archivable"]
                for f in fuentes if f in FUENTES]
    if not trabajos:
        print("Ningun gap es archivable. Todo va a recreacion.\n")
        return [], fallos, diagnostico

    def _uno(par):
        nombre, plano = par
        intentos = _consultas_para(nombre, plano["variantes"])
        for consulta in intentos:
            try:
                r = FUENTES[nombre](consulta, limite_por_fuente)
            except Exception as e:
                return ("error", nombre, consulta, f"{type(e).__name__}: {e}", plano)
            if r:
                for it in r:
                    it["consulta"] = consulta
                    it["gap"] = plano.get("gap")
                return ("ok", nombre, consulta, r, plano)
        return ("vacio", nombre, " / ".join(intentos[:3]), [], plano)

    print("Buscando...\n")
    with ThreadPoolExecutor(max_workers=8) as ex:
        for estado, nombre, consulta, payload, plano in ex.map(_uno, trabajos):
            etiqueta = plano.get("gap") or "-"
            if estado == "ok":
                resultados.extend(payload)
                print(f"  [{nombre:17}] {len(payload):3d}  {etiqueta}  <- \"{consulta[:45]}\"")
            elif estado == "vacio":
                print(f"  [{nombre:17}]   0  {etiqueta}  (probe: {consulta[:45]})")
            else:
                fallos.append({"fuente": nombre, "consulta": consulta, "error": payload})
                print(f"  [{nombre:17}] FALLO {etiqueta}: {str(payload)[:60]}")

    # Filtro final por tipo de medio. Los parametros de cada API acotan, pero
    # ninguno garantiza: Europeana devuelve fotogramas dentro de registros
    # marcados como VIDEO, y Commons responde a filetype:video con la ficha
    # de la miniatura. La comprobacion se repite aqui sobre el resultado real.
    if MEDIA in ("video", "imagen"):
        antes = len(resultados)
        resultados = [r for r in resultados if r.get("tipo") == MEDIA]
        if antes != len(resultados):
            print(f"\n  {antes - len(resultados)} resultados descartados por no ser {MEDIA}.")

    # dedupe por url directo, y si no hay, por titulo normalizado
    vistos, unicos = set(), []
    for r in resultados:
        clave = r.get("url_directo") or ("t:" + re.sub(r"\W+", "", (r.get("titulo") or "").lower())[:60])
        if clave and clave not in vistos:
            vistos.add(clave)
            unicos.append(r)

    return unicos, fallos, diagnostico


# ---------------------------------------------------------------------------
# epoca del personaje
# ---------------------------------------------------------------------------
#
# Buscar por nombre propio trae a los homonimos vivos. En EP0004, un cuarto de
# los resultados estaban fechados despues de 1993 (ano en que murio Ferruccio):
# entre ellos una foto de 2019 de un directivo de Tonino Lamborghini, que se
# llama Ferruccio como el abuelo. Cualquier episodio sobre una figura historica
# va a arrastrar a sus descendientes.
#
# El rango se saca de la timeline que ya escribio Borges. No hay que
# configurarlo a mano.

def rango_epoca(ep_path, margen=5):
    """(desde, hasta) segun la timeline del episodio, o None."""
    p = os.path.join(ep_path, "01_RESEARCH", "timeline.json")
    if not os.path.exists(p):
        return None
    try:
        d = json.load(open(p, encoding="utf-8"))
    except Exception:
        return None
    entradas = d.get("timeline") if isinstance(d, dict) else d
    anios = []
    for e in entradas or []:
        for m in re.findall(r"\b(1[6-9]\d{2}|20\d{2})\b", str(e.get("date", ""))):
            anios.append(int(m))
    if not anios:
        return None
    return min(anios) - margen, max(anios) + margen


def _anio(item):
    m = re.search(r"\b(1[6-9]\d{2}|20\d{2})\b", str(item.get("fecha") or ""))
    return int(m.group(1)) if m else None


def marcar_epoca(items, rango):
    """Marca cada item como dentro / fuera / sin fecha respecto a la epoca."""
    for i in items:
        a = _anio(i)
        i["anio"] = a
        if not rango or a is None:
            i["epoca"] = "sin_fecha"
        elif rango[0] <= a <= rango[1]:
            i["epoca"] = "dentro"
        else:
            i["epoca"] = "fuera"
    return items


def leer_gaps(ep_path, archivo=None, solo_media=None):
    """Convierte los gaps de Moore en planos a buscar.

    Se usa `missing_asset` (la descripcion rica del plano) como material para
    la expansion, no las `manual_search_queries`: esas ya vienen escritas como
    frases de Google y son justo lo que no funciona en un catalogo. Se anexan
    igual por si aportan un nombre propio que la descripcion no tenga.

    `solo_media` filtra por el `media_type` que declara Moore largo. Buscar
    video para un gap que pide un retrato fijo es tiempo tirado: el retrato no
    se mueve en ningun archivo del mundo.
    """
    candidatos = [archivo] if archivo else [
        os.path.join(ep_path, "03_STORYBOARD", "asset_gaps_locutado.json"),
        os.path.join(ep_path, "03_STORYBOARD", "asset_gaps.json"),
    ]
    p = next((c for c in candidatos if c and os.path.exists(c)), None)
    if not p:
        raise SystemExit(
            f"No encuentro asset_gaps_locutado.json ni asset_gaps.json en "
            f"{os.path.join(ep_path, '03_STORYBOARD')}. Corre Moore primero.")
    print(f"Gaps: {os.path.basename(p)}")
    gaps = json.load(open(p, encoding="utf-8"))

    if solo_media:
        con_tipo = [g for g in gaps if g.get("media_type")]
        if con_tipo:
            gaps = [g for g in gaps if g.get("media_type") == solo_media]
            print(f"  {len(gaps)} de {len(con_tipo)} gaps piden {solo_media}.")
        else:
            print("  Estos gaps no declaran media_type (son del Moore viejo): "
                  "se buscan todos.")

    planos = []
    for g in gaps:
        desc = g.get("missing_asset") or ""
        pistas = " ".join(g.get("manual_search_queries", []) or [])
        planos.append({
            "gap": g.get("gap_id"),
            "descripcion": (desc + "\n\nPistas: " + pistas).strip(),
            "criticidad": g.get("criticality"),
            "prompt_ia": g.get("ai_generation_prompt"),
        })
    return planos, gaps


# ---------------------------------------------------------------------------
# hoja de contactos
# ---------------------------------------------------------------------------

CSS = """
:root{--bg:#090909;--panel:#141414;--acc:#01C9C7;--tx:#EDEDED;--mut:#8A8A8A}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);
 font-family:Inter,-apple-system,Segoe UI,sans-serif;padding:32px}
h1{font-family:Montserrat,Inter,sans-serif;font-size:26px;margin:0 0 4px}
.sub{color:var(--mut);font-size:13px;margin-bottom:24px}
.barra{position:sticky;top:0;background:var(--bg);padding:12px 0;
 border-bottom:1px solid #222;margin-bottom:20px;z-index:5}
.barra input,.barra select{background:var(--panel);border:1px solid #2a2a2a;
 color:var(--tx);padding:8px 12px;border-radius:6px;font-size:13px;margin-right:8px}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(240px,1fr));gap:16px}
.card{background:var(--panel);border:1px solid #222;border-radius:10px;
 overflow:hidden;display:flex;flex-direction:column}
.card.pick{border-color:var(--acc);box-shadow:0 0 0 1px var(--acc)}
.card img{width:100%;height:160px;object-fit:cover;background:#000;display:block;cursor:pointer}
.meta{padding:10px 12px;font-size:12px;flex:1;display:flex;flex-direction:column;gap:6px}
.t{font-weight:600;line-height:1.35}
.f{color:var(--acc);font-size:10px;letter-spacing:.06em;text-transform:uppercase}
.l{color:var(--mut);font-size:11px}
.lic{font-size:10px;padding:3px 7px;border-radius:4px;align-self:flex-start;
 font-weight:600;letter-spacing:.03em}
.verde{background:#0d2b1a;color:#4ade80;border:1px solid #1d5c36}
.ambar{background:#2e2408;color:#fbbf24;border:1px solid #6b520f}
.rojo{background:#2e0f0f;color:#f87171;border:1px solid #6b1f1f}
.card.rojo-b img{opacity:.4;filter:grayscale(.6)}
.ep{font-size:10px;padding:3px 7px;border-radius:4px;align-self:flex-start;font-weight:600}
.ep-fuera{background:#2a1633;color:#c084fc;border:1px solid #5b2d73}
.ep-sinfecha{background:#1a1a1a;color:#8A8A8A;border:1px solid #2a2a2a}
.card.fuera-b img{opacity:.45;filter:grayscale(.5)}
.aviso{background:#2e0f0f;border:1px solid #6b1f1f;color:#f87171;padding:12px 16px;
 border-radius:8px;font-size:13px;margin-bottom:20px;line-height:1.5}
.acc{display:flex;gap:8px;padding:0 12px 12px}
.acc a,.acc button{flex:1;text-align:center;text-decoration:none;font-size:11px;
 padding:6px;border-radius:5px;border:1px solid #2a2a2a;background:#0d0d0d;
 color:var(--tx);cursor:pointer}
.acc a:hover,.acc button:hover{border-color:var(--acc);color:var(--acc)}
.gap{color:var(--mut);font-size:10px}
#sel{color:var(--acc);font-weight:600}
"""

JS = """
function filtrar(){
 const t=document.getElementById('q').value.toLowerCase();
 const f=document.getElementById('fu').value;
 const g=document.getElementById('gp').value;
 const l=document.getElementById('li').value;
 const e=document.getElementById('ep').value;
 let vis=0;
 document.querySelectorAll('.card').forEach(c=>{
  let okl=true;
  if(l==='usable') okl=(c.dataset.sem==='verde');
  else if(l==='revisar') okl=(c.dataset.sem!=='rojo');
  else if(l) okl=(c.dataset.sem===l);
  let oke=true;
  if(e==='dentro') oke=(c.dataset.ep!=='fuera');
  else if(e==='solo') oke=(c.dataset.ep==='dentro');
  const ok=(!t||c.dataset.txt.includes(t))&&(!f||c.dataset.fuente===f)
           &&(!g||c.dataset.gap===g)&&okl&&oke;
  c.style.display=ok?'flex':'none'; if(ok)vis++;});
 document.getElementById('vis').textContent=vis+' visibles';
}
function marcar(c){
 if(c.dataset.ep==='fuera'&&!c.classList.contains('pick')){
  if(!confirm('Esta pieza es de '+c.dataset.anio+', fuera de la epoca del personaje ('+c.dataset.rango+').\\n\\nProbablemente sea un homonimo o material moderno. Marcarla igual?'))return;}
 if(c.dataset.sem==='rojo'&&!c.classList.contains('pick')){
  if(!confirm('Esta pieza es '+c.dataset.nota+'.\\n\\nTu canal esta monetizado. Marcarla igual?'))return;}
 c.classList.toggle('pick');cuenta();}
function cuenta(){
 const p=document.querySelectorAll('.card.pick');
 const r=[...p].filter(c=>c.dataset.sem==='rojo').length;
 document.getElementById('sel').textContent=p.length+' marcadas'+(r?' ('+r+' en rojo)':'');}
function exportar(){
 const p=[...document.querySelectorAll('.card.pick')];
 if(!p.length){alert('No marcaste nada.');return;}
 const txt=p.map(c=>c.dataset.dl+'  # '+c.dataset.sem.toUpperCase()+' | '+c.dataset.lic).join('\\n');
 navigator.clipboard.writeText(txt);
 alert(p.length+' URLs copiadas, cada una con su licencia al lado.');
}
window.addEventListener('load',filtrar);
"""


def panel_manual(consultas):
    """Enlaces directos a los catalogos que no tienen API.

    El Istituto Luce es el fondo mas util para este episodio y hay que
    navegarlo a mano. Dejarlo fuera de la hoja significaba que Jota tenia que
    acordarse de la URL y componer la busqueda; asi es un clic.
    """
    if not consultas:
        return ""
    filas = []
    for nombre, plantilla, nota in CATALOGOS_MANUALES:
        enlaces = " · ".join(
            f'<a href="{html.escape(plantilla.format(q=urllib.parse.quote(c)))}" '
            f'target="_blank">{html.escape(c)}</a>' for c in consultas[:8])
        filas.append(f"<li><b>{html.escape(nombre)}</b> — {html.escape(nota)}"
                     f"<div style='margin:4px 0 10px'>{enlaces}</div></li>")
    return (f'<details style="margin:0 0 20px"><summary style="cursor:pointer;'
            f'color:#01C9C7">Catalogos sin API — buscar a mano ({len(CATALOGOS_MANUALES)})'
            f'</summary><ul class="sub" style="line-height:1.6">{"".join(filas)}</ul></details>')


def escribir_hoja(items, fallos, destino, titulo="Hoja de contactos", rango=None,
                  consultas_manuales=None):
    fuentes = sorted({i["fuente"] for i in items})
    gaps = sorted({i.get("gap") for i in items if i.get("gap")})

    ETIQUETA = {"verde": "USABLE", "ambar": "VERIFICAR", "rojo": "NO USAR"}
    cards = []
    for i in items:
        txt = html.escape(((i.get("titulo") or "") + " " + (i.get("consulta") or "") + " " + (i.get("institucion") or "")).lower(), quote=True)
        mini = i.get("miniatura") or ""
        dl = i.get("url_directo") or i.get("url_pagina") or ""
        sem = i.get("semaforo") or "ambar"
        ep = i.get("epoca") or "sin_fecha"
        clases = " ".join(x for x in ('rojo-b' if sem == 'rojo' else '',
                                      'fuera-b' if ep == 'fuera' else '') if x)
        anio = i.get("anio") or "?"
        rango_txt = f"{rango[0]}-{rango[1]}" if rango else "sin dato"
        if ep == "fuera":
            badge_ep = f'<div class="ep ep-fuera">FUERA DE ÉPOCA · {anio}</div>'
        elif ep == "sin_fecha":
            badge_ep = '<div class="ep ep-sinfecha">SIN FECHA</div>'
        else:
            badge_ep = ""
        badge_video = ('<div class="ep" style="background:#0d2b2b;color:#01C9C7;'
                       'border-color:#0f4747">VIDEO</div>'
                       if i.get("tipo") == "video" else "")
        cards.append(f"""
<div class="card {clases}" data-txt="{txt}" data-ep="{ep}" data-tipo="{i.get('tipo') or 'imagen'}"
     data-anio="{anio}" data-rango="{rango_txt}"
     data-fuente="{html.escape(i['fuente'])}" data-sem="{sem}"
     data-nota="{html.escape(i.get('nota_licencia') or '', quote=True)}"
     data-lic="{html.escape(str(i.get('licencia') or ''), quote=True)[:70]}"
     data-gap="{html.escape(i.get('gap') or '')}" data-dl="{html.escape(dl)}">
  <img src="{html.escape(mini)}" loading="lazy" onclick="marcar(this.parentNode)"
       onerror="this.style.opacity=.25">
  <div class="meta">
    <div class="f">{html.escape(i['fuente'])}{' · ' + html.escape(i['gap']) if i.get('gap') else ''}</div>
    <div class="lic {sem}">{ETIQUETA[sem]}</div>
    {badge_video}
    {badge_ep}
    <div class="t">{html.escape(i.get('titulo') or 'sin titulo')}</div>
    <div class="l">{html.escape(i.get('nota_licencia') or '')}</div>
    <div class="gap">{html.escape(str(i.get('licencia') or ''))[:60]}</div>
    <div class="gap">{html.escape(str(i.get('fecha') or ''))} {html.escape(str(i.get('institucion') or ''))}</div>
  </div>
  <div class="acc">
    <a href="{html.escape(i.get('url_pagina') or '#')}" target="_blank">ficha</a>
    <a href="{html.escape(dl)}" target="_blank">abrir</a>
  </div>
</div>""")

    n_fuera = sum(1 for i in items if i.get("epoca") == "fuera")
    n_rojo = sum(1 for i in items if i.get("semaforo") == "rojo")
    n_verde = sum(1 for i in items if i.get("semaforo") == "verde")
    n_ambar = len(items) - n_rojo - n_verde

    aviso = ""
    if n_rojo:
        aviso = (f'<div class="aviso"><b>{n_rojo} de {len(items)} piezas no se pueden '
                 f'usar en un canal monetizado.</b> Son licencias NC (no comercial) o '
                 f'ND (sin obras derivadas). Recortar un clip y montarlo en una edicion '
                 f'cuenta como obra derivada, asi que ND queda fuera aunque parezca '
                 f'permisivo. Salen atenuadas y el filtro arranca en "usable". '
                 f'Esto es un primer filtro, no asesoria legal: la ficha de la '
                 f'institucion manda.</div>')

    if n_fuera and rango:
        aviso += (f'<div class="aviso" style="background:#2a1633;border-color:#5b2d73;'
                  f'color:#c084fc"><b>{n_fuera} piezas estan fechadas fuera de la epoca '
                  f'del personaje ({rango[0]}-{rango[1]}).</b> Buscar por nombre propio '
                  f'arrastra a los homonimos vivos: descendientes, empresas que llevan '
                  f'el apellido, homenajes modernos. Salen atenuadas y el filtro de '
                  f'epoca arranca excluyendolas.</div>')

    if fallos:
        det = "".join(f"<li>{html.escape(f['fuente'])}: {html.escape(str(f['error'])[:140])}</li>" for f in fallos[:12])
        aviso += f'<div class="sub" style="color:#c98a01">Fuentes que no respondieron:<ul>{det}</ul></div>'

    doc = f"""<!doctype html><meta charset="utf-8"><title>{html.escape(titulo)}</title>
<style>{CSS}</style>
<h1>{html.escape(titulo)}</h1>
<div class="sub">{len(items)} resultados de {len(fuentes)} fuentes &nbsp;·&nbsp;
 <span style="color:#4ade80">{n_verde} usables</span> ·
 <span style="color:#fbbf24">{n_ambar} a verificar</span> ·
 <span style="color:#f87171">{n_rojo} no usar</span>. Clic en una imagen para marcarla.</div>
{aviso}
{panel_manual(consultas_manuales or [])}
<div class="barra">
  <input id="q" placeholder="filtrar por texto..." oninput="filtrar()" size="24">
  <select id="li" onchange="filtrar()">
    <option value="usable">solo usables</option>
    <option value="revisar">usables + a verificar</option>
    <option value="">todas, incluidas las bloqueadas</option>
  </select>
  <select id="ep" onchange="filtrar()">
    <option value="dentro">de la época{f' ({rango[0]}-{rango[1]})' if rango else ''} + sin fecha</option>
    <option value="solo">solo con fecha de la época</option>
    <option value="">todas, incluidas las modernas</option>
  </select>
  <select id="fu" onchange="filtrar()"><option value="">todas las fuentes</option>
  {''.join(f'<option>{html.escape(f)}</option>' for f in fuentes)}</select>
  <select id="gp" onchange="filtrar()"><option value="">todos los gaps</option>
  {''.join(f'<option>{html.escape(g)}</option>' for g in gaps)}</select>
  <button onclick="exportar()">copiar URLs marcadas</button>
  <span id="sel">0 marcadas</span> &nbsp;<span id="vis" style="color:#8A8A8A"></span>
</div>
<div class="grid">{''.join(cards)}</div>
<script>{JS}</script>"""

    os.makedirs(os.path.dirname(destino), exist_ok=True)
    with open(destino, "w", encoding="utf-8") as f:
        f.write(doc)
    return destino


# ---------------------------------------------------------------------------
# cli
# ---------------------------------------------------------------------------

# Termino de control: tiene que existir en cualquier archivo del mundo. Si una
# fuente responde 0 a esto, no es que no tenga el material: es que algo esta
# mal en la consulta o en la clave.
CONTROL = "Ferrari"


def autotest():
    print(f"Probando fuentes con el termino de control \"{CONTROL}\"...\n")
    vivas = 0
    for nombre, fn in FUENTES.items():
        t0 = time.time()
        try:
            r = fn(CONTROL, 3)
            seg = time.time() - t0
            if r:
                print(f"  OK      {nombre:17} {len(r):2d} resultados  ({seg:.1f}s)")
                vivas += 1
            else:
                print(f"  RARO    {nombre:17}  0 resultados con \"{CONTROL}\" "
                      f"({seg:.1f}s). Responde pero no devuelve nada: revisa la clave.")
        except Exception as e:
            print(f"  FALLO   {nombre:17} {type(e).__name__}: {str(e)[:90]}")

    print(f"\n{vivas}/{len(FUENTES)} fuentes devolviendo material.")
    if not os.environ.get("OPENROUTER_API_KEY"):
        print("Sin OPENROUTER_API_KEY: las consultas se traducen con el metodo simple.")
    else:
        print("Con OPENROUTER_API_KEY: los gaps se traducen a consultas de catalogo con IA.")
    if vivas == 0:
        print("Ninguna devolvio nada. Revisa la conexion o el proxy.")
    return vivas


def main():
    ap = argparse.ArgumentParser(description="Buscador de archivo historico para HUMANOS")
    ap.add_argument("--episodio", help="ruta al episodio (usa los gaps de Moore)")
    ap.add_argument("--buscar", nargs="+", help="consultas sueltas")
    ap.add_argument("--limite", type=int, default=12, help="resultados por fuente y consulta")
    ap.add_argument("--fuentes", nargs="+", choices=list(FUENTES), help="restringir fuentes")
    ap.add_argument("--test", action="store_true", help="probar conectividad de las fuentes")
    ap.add_argument("--sin-ia", action="store_true",
                    help="no usar OpenRouter para traducir las consultas")
    ap.add_argument("--sin-monetizacion", action="store_true",
                    help="el canal no esta monetizado: baja las NC de rojo a ambar")
    ap.add_argument("--video", action="store_true",
                    help="buscar metraje en movimiento (Istituto Luce via Europeana, "
                         "Internet Archive, LOC film, Commons)")
    ap.add_argument("--imagen", action="store_true",
                    help="buscar solo imagen fija (comportamiento clasico)")
    ap.add_argument("--gaps", help="archivo de gaps concreto, si no se usa el del episodio")
    a = ap.parse_args()

    globals()["TOLERAR_NC"] = a.sin_monetizacion
    globals()["MEDIA"] = "video" if a.video else ("imagen" if a.imagen else "todo")
    if a.video:
        print("Modo VIDEO: metraje en movimiento.")
        print("Fuentes de imagen fija (Openverse, Flickr, LOC fotografia) quedan fuera.\n")
    if a.sin_monetizacion:
        print("Modo sin monetizacion: las licencias NC pasan a AMBAR.")
        print("ND e In Copyright siguen en ROJO: no dependen de los anuncios.\n")

    if a.test:
        return 0 if autotest() else 1

    destino_dir, titulo = "salida_archivo", "Hoja de contactos"

    rango = None
    sufijo = "_video" if a.video else ("_imagen" if a.imagen else "")
    if a.episodio:
        planos, gaps = leer_gaps(a.episodio, a.gaps,
                                 solo_media=("video_archivo" if a.video else
                                            "foto_archivo" if a.imagen else None))
        if not planos:
            print("Ningun gap pide este tipo de material. Nada que buscar.")
            return 0
        rango = rango_epoca(a.episodio)
        if rango:
            print(f"Epoca del personaje segun la timeline de Borges: {rango[0]}-{rango[1]}.")
            print("Lo fechado fuera de ese rango se marca aparte.\n")
        destino_dir = os.path.join(a.episodio, "01_RESEARCH", "archivo")
        titulo = (f"Archivo{' en VIDEO' if a.video else ''} — "
                  f"{os.path.basename(a.episodio)} ({len(gaps)} gaps)")
        print(f"{len(gaps)} gaps de Moore.\n")
    elif a.buscar:
        planos = [{"gap": None, "descripcion": c} for c in a.buscar]
        print(f"{len(planos)} consultas.\n")
    else:
        ap.error("indica --episodio o --buscar (o --test)")

    fuentes = a.fuentes or (FUENTES_VIDEO if a.video else None)
    items, fallos, diagnostico = buscar_todo(
        planos, a.limite, fuentes, usar_ia=not a.sin_ia)
    marcar_epoca(items, rango)

    # Consultas que valen para el panel manual: las mejores variantes que se
    # generaron, para poder repetirlas en los catalogos sin API.
    manuales = []
    for d in diagnostico:
        for idioma in ("it", "entidades", "en"):
            manuales.extend((d.get("variantes") or {}).get(idioma) or [])
    manuales = list(dict.fromkeys(manuales))[:8]

    os.makedirs(destino_dir, exist_ok=True)
    ruta_json = os.path.join(destino_dir, f"resultados{sufijo}.json")
    with open(ruta_json, "w", encoding="utf-8") as f:
        json.dump({"media": MEDIA, "diagnostico": diagnostico,
                   "items": items, "fallos": fallos},
                  f, ensure_ascii=False, indent=2)

    ruta_html = escribir_hoja(items, fallos,
                              os.path.join(destino_dir, f"hoja_de_contactos{sufijo}.html"),
                              titulo, rango, manuales)

    solo_recreacion = [d for d in diagnostico if not d["archivable"]]
    con_material = {i.get("gap") for i in items if i.get("gap")}
    vacios = [d["gap"] for d in diagnostico
              if d["archivable"] and d["gap"] not in con_material]

    print(f"\n{len(items)} resultados unicos tras deduplicar.")
    print(f"  JSON : {ruta_json}")
    print(f"  HOJA : {ruta_html}")

    fuera = [i for i in items if i.get("epoca") == "fuera"]
    if fuera and rango:
        print(f"\n{len(fuera)} piezas fechadas fuera de {rango[0]}-{rango[1]}: "
              f"probables homonimos o material moderno. Van atenuadas en la hoja.")

    if solo_recreacion:
        print("\nEstos gaps no existen como archivo. Van directo a recreacion:")
        for d in solo_recreacion:
            print(f"  {d['gap']}: {d['motivo']}")
    if vacios:
        print(f"\nEstos gaps son archivables pero no aparecio nada: {', '.join(map(str, vacios))}")
        print("  Vale mirar la hoja igual y, si sigue vacio, mandarlos a recreacion.")

    print("\nAbri la hoja en el navegador, marca lo que sirva y usa")
    print("'copiar URLs marcadas'.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
