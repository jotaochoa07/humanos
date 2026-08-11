"""
apify_client — cliente mínimo de Apify para HUMANOS.

Dos consumidores:

  - Mr. You : qué está publicando la competencia sobre este tema en YouTube.
              Sirve para que sus hipótesis de packaging sean DATO OBSERVADO
              y no opinión. Su system prompt exige esa distinción.

  - Borges  : bibliografía y fuentes que Tavily y Wikimedia no alcanzan.

Diseño deliberado: sin SDK, solo urllib. El repo ya funciona así
(openrouter_client.py) y una dependencia menos es una dependencia menos que
falta declarar. Ver requirements.txt.

Aviso de coste: la cuenta es plan FREE. Cada corrida de actor consume
créditos. `run_actor` limita resultados por defecto y avisa antes de gastar.
"""

import os
import json
import time
import urllib.parse
import urllib.request
import urllib.error

import env_boot  # asegura APIFY_TOKEN en os.environ

API = "https://api.apify.com/v2"


class ApifyError(RuntimeError):
    pass


class ApifyClient:
    def __init__(self, token: str = None):
        self.token = token or os.environ.get("APIFY_TOKEN", "")
        if not self.token:
            raise ApifyError(
                "APIFY_TOKEN no esta en el entorno. Anadilo al .env."
            )

    # -- infraestructura ---------------------------------------------------

    def _pedir(self, metodo, ruta, payload=None, timeout=60):
        url = f"{API}/{ruta.lstrip('/')}"
        sep = "&" if "?" in url else "?"
        url = f"{url}{sep}token={urllib.parse.quote(self.token)}"

        data = json.dumps(payload).encode("utf-8") if payload is not None else None
        headers = {"Content-Type": "application/json"} if data else {}
        req = urllib.request.Request(url, data=data, headers=headers, method=metodo)
        try:
            with urllib.request.urlopen(req, timeout=timeout) as r:
                cuerpo = r.read().decode("utf-8", errors="ignore")
                return json.loads(cuerpo) if cuerpo.strip() else {}
        except urllib.error.HTTPError as e:
            detalle = e.read()[:300].decode(errors="ignore")
            raise ApifyError(f"HTTP {e.code} en {metodo} {ruta}: {detalle}") from e

    def quien_soy(self):
        return self._pedir("GET", "users/me").get("data", {})

    def creditos(self):
        """Lectura del uso mensual. Util antes de gastar en un actor caro."""
        try:
            d = self._pedir("GET", "users/me/usage/monthly").get("data", {})
            return d.get("monthlyUsageCycle", {}), d.get("totalUsageCreditsUsd")
        except ApifyError:
            return {}, None

    # -- ejecución de actores ---------------------------------------------

    def run_actor(self, actor_id: str, entrada: dict, espera_max_s: int = 180,
                  limite_items: int = 40, confirmar: bool = False):
        """Corre un actor y devuelve los items del dataset.

        `confirmar=True` imprime la entrada y pide confirmacion antes de
        gastar creditos. En plan FREE eso importa.
        """
        if confirmar:
            print(f"\n[Apify] Voy a correr el actor '{actor_id}' con:")
            print(json.dumps(entrada, ensure_ascii=False, indent=2)[:600])
            if input("[Apify] Consume creditos. Continuar? (s/n) ").strip().lower() != "s":
                raise ApifyError("Cancelado por el operador.")

        ruta = f"acts/{actor_id.replace('/', '~')}/runs"
        run = self._pedir("POST", ruta, entrada).get("data", {})
        run_id = run.get("id")
        if not run_id:
            raise ApifyError(f"El actor no devolvio run id. Respuesta: {run}")

        print(f"[Apify] run {run_id} lanzado. Esperando (max {espera_max_s}s)...")
        t0 = time.time()
        estado = run.get("status")
        dataset_id = run.get("defaultDatasetId")

        while estado in ("READY", "RUNNING") and (time.time() - t0) < espera_max_s:
            time.sleep(5)
            d = self._pedir("GET", f"actor-runs/{run_id}").get("data", {})
            estado = d.get("status")
            dataset_id = d.get("defaultDatasetId", dataset_id)
            print(f"[Apify]   ... {estado} ({int(time.time() - t0)}s)")

        if estado != "SUCCEEDED":
            raise ApifyError(
                f"El run termino en estado {estado} tras {int(time.time() - t0)}s. "
                f"Revisar en https://console.apify.com/actors/runs/{run_id}"
            )

        items = self._pedir("GET", f"datasets/{dataset_id}/items?limit={limite_items}")
        print(f"[Apify] {len(items)} items recuperados.")
        return items


# ---------------------------------------------------------------------------
# Consulta especializada: competencia en YouTube (la usa Mr. You)
# ---------------------------------------------------------------------------

ACTOR_YOUTUBE = "streamers/youtube-scraper"


def competencia_youtube(consultas, max_por_consulta=12, confirmar=False):
    """Busca en YouTube qué existe ya sobre estos temas.

    Devuelve una lista normalizada de piezas con lo único que le importa a
    Mr. You para empaquetar: título, vistas, duración, canal, fecha y
    miniatura. No opina sobre ellas: eso es trabajo del agente.
    """
    cli = ApifyClient()
    entrada = {
        "searchQueries": list(consultas),
        "maxResults": max_por_consulta,
        "maxResultsShorts": 0,
        "maxResultStreams": 0,
        # El actor exige MAYUSCULAS. Con "popular" devuelve HTTP 400
        # invalid-input. Valores permitidos: NEWEST | POPULAR | OLDEST.
        "sortVideosBy": "POPULAR",
    }
    crudos = cli.run_actor(ACTOR_YOUTUBE, entrada,
                           limite_items=max_por_consulta * len(consultas),
                           confirmar=confirmar)

    piezas = []
    for v in crudos:
        piezas.append({
            "titulo": v.get("title"),
            "canal": v.get("channelName"),
            "vistas": v.get("viewCount"),
            "duracion": v.get("duration"),
            "publicado": v.get("date") or v.get("uploadDate"),
            "url": v.get("url"),
            "miniatura": v.get("thumbnailUrl"),
            "likes": v.get("likes"),
        })
    piezas.sort(key=lambda p: p.get("vistas") or 0, reverse=True)
    return piezas


if __name__ == "__main__":
    c = ApifyClient()
    yo = c.quien_soy()
    print(f"[Apify] Conectado como {yo.get('username')} "
          f"(plan {(yo.get('plan') or {}).get('id')})")
    ciclo, usado = c.creditos()
    print(f"[Apify] Uso del ciclo: {usado} USD")
