"""
kling_client — generacion de video con Kling a traves de KIE.AI.

CUANDO USAR ESTO: cuando ya se busco archivo real y no aparecio nada. Ese es
el orden y no al reves. HUMANOS no es un canal faceless de IA; el material
generado es el ultimo recurso, para los planos que no existen en ningun
archivo del mundo (una conversacion a puerta cerrada, un pensamiento) o para
animar un still que ya esta licenciado cuando el Ken Burns se queda corto.

Dos modos:

    texto -> video   para un gap que no existe como archivo
    imagen -> video  para animar una foto que YA esta en el registro con su
                     licencia. Ojo con esto: animar una imagen crea una OBRA
                     DERIVADA. Si la licencia de la foto es ND, esta prohibido
                     aunque la foto sea gratis. El cliente lo comprueba antes
                     de gastar creditos y se planta si el semaforo esta en
                     rojo.

SOBRE LOS ENDPOINTS: KIE.AI cambia rutas cada pocos meses y no hay forma de
verificarlas sin llamar. En vez de dejar una URL fija enterrada en el codigo,
`--descubrir` prueba las rutas candidatas contra la clave real y dice cual
responde. La que funcione se fija en el .env como KIE_KLING_ENDPOINT y el
cliente la usa sin volver a adivinar.

Uso:

    # 1. comprobar la clave y encontrar la ruta buena
    python kling_client.py --descubrir

    # 2. un plano suelto, texto -> video
    python kling_client.py --texto "cadena de montaje de tractores, Italia 1950,
        blanco y negro, grano de pelicula" --segundos 5

    # 3. animar una foto ya licenciada del episodio
    python kling_client.py --episodio <ruta> --animar 007 --segundos 5

    # 4. todos los gaps que Moore marco como recreacion_ia
    python kling_client.py --episodio <ruta> --gaps-ia

Salida: <episodio>/05_VIDEO/, con su entrada en asset_registry.json marcada
como generado por IA. El gate de derechos ya reconoce "kling" como material
propio (derechos.py), asi que no rompe el semaforo.
"""

import os
import re
import sys
import json
import time
import argparse
import urllib.error
import urllib.request

try:
    import env_boot  # carga .env
except Exception:
    pass

BASE_URL = os.environ.get("KIE_BASE_URL", "https://api.kie.ai").rstrip("/")
TIMEOUT = 60

# Rutas candidatas, de la mas probable a la menos. `--descubrir` las prueba.
CANDIDATOS_GENERAR = [
    "/api/v1/kling/generate",
    "/api/v1/jobs/createTask",
    "/api/v1/veo/generate",
    "/api/v1/gpt4o-image/generate",
]
CANDIDATOS_ESTADO = [
    "/api/v1/kling/record-info?taskId={id}",
    "/api/v1/jobs/recordInfo?taskId={id}",
    "/api/v1/veo/record-info?taskId={id}",
]
CANDIDATOS_CREDITO = [
    "/api/v1/chat/credit",
    "/api/v1/common/credit",
]


def _clave():
    k = os.environ.get("KIE_API_KEY", "").strip()
    if not k:
        raise SystemExit("Falta KIE_API_KEY en el .env.")
    return k


def _pedir(ruta, payload=None, metodo=None):
    """Devuelve (codigo, cuerpo_dict_o_texto). No traga los errores: el cuerpo
    de un 4xx de KIE explica que espera la API, y es la unica documentacion
    fiable que hay."""
    url = ruta if ruta.startswith("http") else BASE_URL + ruta
    datos = json.dumps(payload).encode("utf-8") if payload is not None else None
    req = urllib.request.Request(
        url, data=datos, method=metodo or ("POST" if datos else "GET"),
        headers={"Authorization": f"Bearer {_clave()}",
                 "Content-Type": "application/json",
                 "Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            cuerpo = r.read().decode("utf-8", errors="ignore")
            codigo = r.status
    except urllib.error.HTTPError as e:
        cuerpo = e.read().decode("utf-8", errors="ignore")
        codigo = e.code
    try:
        return codigo, json.loads(cuerpo)
    except Exception:
        return codigo, cuerpo


# ---------------------------------------------------------------------------
# descubrimiento
# ---------------------------------------------------------------------------

def descubrir():
    """Prueba las rutas candidatas y dice cual sirve. Se corre una vez."""
    print(f"Base: {BASE_URL}\n")

    print("Credito:")
    for r in CANDIDATOS_CREDITO:
        c, b = _pedir(r)
        print(f"  {c}  {r}  {str(b)[:120]}")

    print("\nGeneracion (payload minimo de prueba, no llega a gastar creditos "
          "si la ruta no existe):")
    prueba = {"prompt": "test", "model": "kling-v1", "duration": 5,
              "aspect_ratio": "16:9"}
    vivas = []
    for r in CANDIDATOS_GENERAR:
        c, b = _pedir(r, prueba)
        marca = "  <-- responde" if c not in (404, 405) else ""
        print(f"  {c}  {r}  {str(b)[:160]}{marca}")
        if c not in (404, 405):
            vivas.append(r)

    print()
    if vivas:
        print("Rutas que responden:", ", ".join(vivas))
        print(f"Fija la buena en el .env:  KIE_KLING_ENDPOINT={vivas[0]}")
        print("Si devolvio un 4xx de validacion, el mensaje de arriba dice que "
              "campos espera: pegamelo y ajusto el payload.")
    else:
        print("Ninguna ruta respondio. O la clave no tiene Kling habilitado, o "
              "cambiaron la API. El cuerpo de los errores de arriba lo aclara.")
    return 0 if vivas else 1


# ---------------------------------------------------------------------------
# generacion
# ---------------------------------------------------------------------------

class Kling:
    def __init__(self, endpoint=None, modelo=None):
        self.endpoint = (endpoint or os.environ.get("KIE_KLING_ENDPOINT")
                         or CANDIDATOS_GENERAR[0])
        self.modelo = modelo or os.environ.get("KIE_KLING_MODEL", "kling-v1")

    def generar(self, prompt, imagen_url=None, segundos=5, aspecto="16:9"):
        """Lanza la tarea y devuelve su id. imagen_url activa imagen->video."""
        payload = {
            "model": self.modelo,
            "prompt": prompt,
            "duration": int(segundos),
            "aspect_ratio": aspecto,
        }
        if imagen_url:
            payload["image_url"] = imagen_url
        codigo, cuerpo = _pedir(self.endpoint, payload)
        if codigo >= 400:
            raise RuntimeError(f"KIE respondio {codigo}: {str(cuerpo)[:300]}")
        tid = self._buscar(cuerpo, ("taskId", "task_id", "id", "jobId"))
        if not tid:
            raise RuntimeError(f"No encuentro el id de tarea en: {str(cuerpo)[:300]}")
        return tid

    def esperar(self, task_id, minutos=10, cada=10):
        """Sondea hasta que la tarea termina. Devuelve la URL del video."""
        limite = time.time() + minutos * 60
        ultimo = None
        while time.time() < limite:
            for plantilla in CANDIDATOS_ESTADO:
                codigo, cuerpo = _pedir(plantilla.format(id=task_id))
                if codigo == 404:
                    continue
                ultimo = cuerpo
                url = self._buscar(cuerpo, ("videoUrl", "video_url", "resultUrl", "url"))
                if url and str(url).startswith("http"):
                    return url
                estado = str(self._buscar(cuerpo, ("status", "state", "successFlag")) or "")
                if estado.lower() in ("failed", "error", "3"):
                    raise RuntimeError(f"La tarea fallo: {str(cuerpo)[:300]}")
                break
            print(f"  ... generando ({int(limite - time.time())}s de margen)")
            time.sleep(cada)
        raise TimeoutError(f"Se agoto la espera. Ultimo estado: {str(ultimo)[:300]}")

    @staticmethod
    def _buscar(obj, claves):
        """Busca la primera clave que aparezca, a cualquier profundidad.

        KIE anida la respuesta de forma distinta segun el endpoint
        ({data:{taskId}} en unos, {taskId} pelado en otros). Buscar en
        profundidad evita tener un parser por ruta.
        """
        if isinstance(obj, dict):
            for k in claves:
                if obj.get(k) not in (None, ""):
                    return obj[k]
            for v in obj.values():
                r = Kling._buscar(v, claves)
                if r is not None:
                    return r
        elif isinstance(obj, list):
            for v in obj:
                r = Kling._buscar(v, claves)
                if r is not None:
                    return r
        return None


# ---------------------------------------------------------------------------
# integracion con el episodio
# ---------------------------------------------------------------------------

def _registro(ep):
    p = os.path.join(ep, "asset_registry.json")
    return p, (json.load(open(p, encoding="utf-8")) if os.path.exists(p) else [])


def comprobar_derivada(entrada):
    """Animar una foto crea una obra derivada. ND lo prohibe.

    Este es el error que mas caro sale: la foto es gratis, el semaforo esta en
    verde para USARLA, y aun asi animarla es ilegal. Se comprueba antes de
    gastar el credito, no despues de montar el episodio.
    """
    lic = str(entrada.get("licencia") or "").lower()
    sem = entrada.get("semaforo")
    if "nd" in re.findall(r"\bnd\b", lic) or "noderiv" in lic.replace(" ", ""):
        return False, f"licencia ND ({entrada.get('licencia')}): la obra derivada esta prohibida"
    if sem == "rojo":
        return False, f"semaforo rojo: {entrada.get('nota_licencia')}"
    return True, f"licencia {entrada.get('licencia')}: se puede derivar"


def descargar(url, destino):
    os.makedirs(os.path.dirname(destino), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": "HUMANOS-kling/1.0"})
    with urllib.request.urlopen(req, timeout=300) as r, open(destino, "wb") as f:
        f.write(r.read())
    return destino


def inscribir(ep, ruta, prompt, origen):
    """Anota el video generado en el registro para que el gate de derechos lo
    vea. Sin esto es un huerfano y `derechos.py` lo marca como no registrado."""
    p, reg = _registro(ep)
    ids = {str(e.get("asset_id")) for e in reg}
    n = 900
    while str(n) in ids:
        n += 1
    reg.append({
        "asset_id": str(n),
        "hash": None,
        "source": "Kling (KIE.AI)",
        "storage_path": os.path.abspath(ruta),
        "licencia": "Generado por IA (Kling) — material propio",
        "semaforo": "verde",
        "nota_licencia": "generado para este episodio; no hay derechos de terceros",
        "url_ficha": None,
        "titulo_origen": prompt[:120],
        "generado_de": origen,
    })
    json.dump(reg, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    return str(n)


def gaps_ia(ep):
    """Los gaps que Moore largo marco como recreacion_ia."""
    for nombre in ("asset_gaps_locutado.json", "asset_gaps.json"):
        p = os.path.join(ep, "03_STORYBOARD", nombre)
        if os.path.exists(p):
            gaps = json.load(open(p, encoding="utf-8"))
            return [g for g in gaps
                    if g.get("media_type") == "recreacion_ia"
                    or g.get("ai_generation_allowed")]
    return []


def main():
    ap = argparse.ArgumentParser(description="Kling via KIE.AI para HUMANOS")
    ap.add_argument("--descubrir", action="store_true",
                    help="probar la clave y encontrar el endpoint bueno")
    ap.add_argument("--texto", help="prompt de texto -> video")
    ap.add_argument("--animar", help="asset_id del registro para imagen -> video")
    ap.add_argument("--episodio", help="ruta del episodio")
    ap.add_argument("--gaps-ia", action="store_true",
                    help="generar todos los gaps marcados como recreacion_ia")
    ap.add_argument("--segundos", type=int, default=5)
    ap.add_argument("--aspecto", default="16:9")
    ap.add_argument("--simular", action="store_true",
                    help="no llama a la API: solo dice que haria y cuanto")
    a = ap.parse_args()

    if a.descubrir:
        return descubrir()

    k = Kling()
    trabajos = []

    if a.texto:
        trabajos.append({"prompt": a.texto, "imagen": None, "origen": "texto"})

    if a.animar:
        if not a.episodio:
            ap.error("--animar necesita --episodio")
        _, reg = _registro(a.episodio)
        e = next((x for x in reg if str(x.get("asset_id")) == str(a.animar)), None)
        if not e:
            ap.error(f"no existe el asset {a.animar} en el registro")
        ok, motivo = comprobar_derivada(e)
        print(f"{e.get('titulo_origen')}: {motivo}")
        if not ok:
            print("No se anima. Buscar otra imagen o dejar Ken Burns.")
            return 1
        trabajos.append({"prompt": a.texto or f"movimiento sutil de camara sobre {e.get('titulo_origen')}",
                         "imagen": e.get("url_ficha") or e.get("storage_path"),
                         "origen": f"asset {a.animar}"})

    if a.gaps_ia:
        if not a.episodio:
            ap.error("--gaps-ia necesita --episodio")
        for g in gaps_ia(a.episodio):
            trabajos.append({"prompt": g.get("ai_generation_prompt") or g.get("missing_asset"),
                             "imagen": None, "origen": g.get("gap_id")})

    if not trabajos:
        ap.error("indica --texto, --animar o --gaps-ia (o --descubrir)")

    print(f"\n{len(trabajos)} plano(s) a generar, {a.segundos}s cada uno.\n")
    if a.simular:
        for t in trabajos:
            print(f"  [{t['origen']}] {t['prompt'][:110]}")
        print("\nModo simulacion: no se llamo a la API ni se gastaron creditos.")
        return 0

    hechos = []
    for t in trabajos:
        print(f"[{t['origen']}] {t['prompt'][:90]}")
        try:
            tid = k.generar(t["prompt"], t["imagen"], a.segundos, a.aspecto)
            print(f"  tarea {tid}")
            url = k.esperar(tid)
            destino = os.path.join(a.episodio or ".", "05_VIDEO",
                                   f"KLING_{t['origen'].replace(' ', '_')}.mp4")
            descargar(url, destino)
            aid = inscribir(a.episodio or ".", destino, t["prompt"], t["origen"]) if a.episodio else None
            print(f"  OK -> {destino}" + (f" (asset {aid})" if aid else ""))
            hechos.append(destino)
        except Exception as e:
            print(f"  FALLO: {type(e).__name__}: {str(e)[:200]}")

    print(f"\n{len(hechos)}/{len(trabajos)} generados.")
    return 0 if hechos else 1


if __name__ == "__main__":
    sys.exit(main())
