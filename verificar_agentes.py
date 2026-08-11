"""
verificar_agentes — prueba de vida del sistema HUMANOS.

Responde una sola pregunta: cuando corro el pipeline, ¿piensa alguien?

No verifica que las claves "existan". Verifica que cada servicio RESPONDE
y que cada agente instancia su cliente de verdad. La diferencia entre esas
dos cosas es un episodio falso.

Uso:  python verificar_agentes.py
"""

import os
import sys
import json
import time
import urllib.request
import urllib.error

import env_boot  # carga el .env antes de nada

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ANCHO = 74

OK = "  OK  "
FALLO = " FALLO"
AUSENTE = "AUSENTE"


def _titulo(t):
    print("\n" + "=" * ANCHO)
    print(f" {t}")
    print("=" * ANCHO)


def _fila(nombre, estado, detalle=""):
    print(f"  [{estado}]  {nombre:<24} {detalle}")


def _pedir(url, headers=None, data=None, timeout=25):
    req = urllib.request.Request(url, data=data, headers=headers or {})
    with urllib.request.urlopen(req, timeout=timeout) as r:
        return r.status, r.read().decode("utf-8", errors="ignore")


# ---------------------------------------------------------------------------
# 1. Servicios externos
# ---------------------------------------------------------------------------

def probar_openrouter():
    clave = os.environ.get("OPENROUTER_API_KEY", "")
    if not clave:
        return AUSENTE, "no esta en .env"
    try:
        _, body = _pedir(
            "https://openrouter.ai/api/v1/auth/key",
            {"Authorization": f"Bearer {clave}"},
        )
        d = json.loads(body).get("data", {})
        limite = d.get("limit")
        usado = d.get("usage")
        saldo = "sin limite" if limite is None else f"limite {limite}"
        return OK, f"usado {usado} | {saldo}"
    except urllib.error.HTTPError as e:
        return FALLO, f"HTTP {e.code} — clave rechazada"
    except Exception as e:
        return FALLO, f"{type(e).__name__}: {str(e)[:60]}"


def probar_inferencia_real():
    """El unico test que importa: pedirle al modelo que piense."""
    clave = os.environ.get("OPENROUTER_API_KEY", "")
    if not clave:
        return AUSENTE, "no esta en .env"
    modelo = os.environ.get("OPENROUTER_MODEL", "google/gemini-2.5-flash-lite")
    payload = {
        "model": modelo,
        "messages": [
            {"role": "system", "content": "Responde solo JSON."},
            {"role": "user", "content": 'Devuelve {"vivo": true, "modelo": "<tu nombre>"}'},
        ],
        "response_format": {"type": "json_object"},
        "max_tokens": 100,
    }
    try:
        t0 = time.time()
        _, body = _pedir(
            "https://openrouter.ai/api/v1/chat/completions",
            {"Authorization": f"Bearer {clave}", "Content-Type": "application/json"},
            json.dumps(payload).encode("utf-8"),
            timeout=45,
        )
        ms = int((time.time() - t0) * 1000)
        r = json.loads(body)
        txt = r["choices"][0]["message"]["content"][:60].replace("\n", " ")
        return OK, f"{modelo} respondio en {ms}ms — {txt}"
    except urllib.error.HTTPError as e:
        return FALLO, f"HTTP {e.code} {e.read()[:80].decode(errors='ignore')}"
    except Exception as e:
        return FALLO, f"{type(e).__name__}: {str(e)[:60]}"


def probar_apify():
    tok = os.environ.get("APIFY_TOKEN", "")
    if not tok:
        return AUSENTE, "no esta en .env"
    try:
        _, body = _pedir(f"https://api.apify.com/v2/users/me?token={tok}")
        d = json.loads(body).get("data", {})
        plan = (d.get("plan") or {}).get("id", "?")
        return OK, f"usuario {d.get('username')} | plan {plan}"
    except urllib.error.HTTPError as e:
        return FALLO, f"HTTP {e.code} — token rechazado"
    except Exception as e:
        return FALLO, f"{type(e).__name__}: {str(e)[:60]}"


def probar_tavily():
    clave = os.environ.get("TAVILY_API_KEY", "")
    if not clave:
        return AUSENTE, "no esta en .env"
    try:
        _, body = _pedir(
            "https://api.tavily.com/search",
            {"Content-Type": "application/json"},
            json.dumps({
                "api_key": clave,
                "query": "Ferruccio Lamborghini Enzo Ferrari 1963",
                "max_results": 2,
            }).encode("utf-8"),
        )
        n = len(json.loads(body).get("results", []))
        return OK, f"{n} resultados para la consulta de prueba"
    except urllib.error.HTTPError as e:
        return FALLO, f"HTTP {e.code} — clave rechazada"
    except Exception as e:
        return FALLO, f"{type(e).__name__}: {str(e)[:60]}"


def probar_kie():
    clave = os.environ.get("KIE_API_KEY", "")
    if not clave:
        return AUSENTE, "no esta en .env"
    for url in ("https://api.kie.ai/api/v1/chat/credit",
                "https://api.kie.ai/api/v1/common/credit"):
        try:
            _, body = _pedir(url, {"Authorization": f"Bearer {clave}"})
            return OK, f"creditos: {body[:70]}"
        except urllib.error.HTTPError as e:
            ultimo = f"HTTP {e.code}"
        except Exception as e:
            ultimo = f"{type(e).__name__}"
    return FALLO, f"{ultimo} — revisar endpoint de KIE.AI"


def probar_elevenlabs():
    """No aplica. Decisión editorial de Jota (2026-08-01): la voz off se graba
    con su propia voz en Audacity, no con síntesis. En un sistema con once
    agentes, la voz es lo único que no se delega. No es un fallo: es el diseño.
    """
    return "  N/A ", "voz grabada por Jota en Audacity — no se sintetiza"


def probar_supabase():
    url = os.environ.get("SUPABASE_URL", "")
    clave = os.environ.get("SUPABASE_KEY", "")
    if not url or not clave:
        return AUSENTE, "no esta en .env"
    try:
        # Solo lectura. Cero escrituras, cero DDL.
        st, body = _pedir(
            f"{url}/rest/v1/humanos_stories?select=id&limit=1",
            {"apikey": clave, "Authorization": f"Bearer {clave}"},
        )
        return OK, f"humanos_stories responde HTTP {st} (solo lectura)"
    except urllib.error.HTTPError as e:
        return FALLO, f"HTTP {e.code}"
    except Exception as e:
        return FALLO, f"{type(e).__name__}: {str(e)[:60]}"


# ---------------------------------------------------------------------------
# 2. Agentes: ¿instancian cliente de verdad?
# ---------------------------------------------------------------------------

def probar_agentes():
    resultados = []

    def chequear(nombre, fn):
        try:
            tiene = fn()
            resultados.append((nombre, OK if tiene else FALLO,
                               "cliente instanciado" if tiene
                               else "client=None -> caeria a fallback"))
        except Exception as e:
            resultados.append((nombre, FALLO, f"{type(e).__name__}: {str(e)[:50]}"))

    try:
        from openrouter_client import OpenRouterClient
        cli = OpenRouterClient() if os.environ.get("OPENROUTER_API_KEY") else None
    except Exception as e:
        print(f"  No se pudo crear OpenRouterClient: {e}")
        cli = None

    chequear("Borges", lambda: __import__("borges").BorgesAgent(cli).client is not None)
    chequear("Gabo", lambda: __import__("gabo").GaboAgent(cli).client is not None)
    chequear("Moore", lambda: __import__("moore").MooreAgent(cli).client is not None)
    chequear("Talese", lambda: __import__("talese").TaleseAgent(base_dir=BASE_DIR).client is not None)
    return resultados


def main():
    print()
    print("#" * ANCHO)
    print("#  HUMANOS — PRUEBA DE VIDA")
    print("#  La pregunta no es si las claves existen. Es si alguien piensa.")
    print("#" * ANCHO)

    _titulo("1. Entorno")
    env_path = os.path.join(BASE_DIR, ".env")
    _fila(".env", OK if os.path.exists(env_path) else FALLO, env_path)
    claves = ["OPENROUTER_API_KEY", "APIFY_TOKEN", "KIE_API_KEY",
              "TAVILY_API_KEY", "ELEVENLABS_API_KEY",
              "SUPABASE_URL", "SUPABASE_KEY", "PEXELS_API_KEY",
              "EUROPEANA_KEY"]
    for c in claves:
        v = os.environ.get(c, "")
        _fila(c, OK if v else AUSENTE, f"{len(v)} caracteres" if v else "")

    _titulo("2. Servicios (respuesta real, no presencia de clave)")
    pruebas = [
        ("OpenRouter (auth)", probar_openrouter),
        ("OpenRouter (inferencia)", probar_inferencia_real),
        ("Apify", probar_apify),
        ("Tavily", probar_tavily),
        ("KIE.AI", probar_kie),
        ("ElevenLabs", probar_elevenlabs),   # N/A por decisión editorial
        ("Supabase", probar_supabase),
    ]
    fallos = 0
    for nombre, fn in pruebas:
        estado, detalle = fn()
        if estado == FALLO:
            fallos += 1
        _fila(nombre, estado, detalle)

    _titulo("3. Agentes — ¿tienen cerebro?")
    for nombre, estado, detalle in probar_agentes():
        if estado == FALLO:
            fallos += 1
        _fila(nombre, estado, detalle)

    _titulo("Veredicto")
    if fallos == 0:
        print("  Sistema vivo. Lo que se produzca hoy lo produjeron los agentes.")
    else:
        print(f"  {fallos} fallo(s). NO produzcas hasta cerrarlos: lo que salga")
        print("  seria relleno con formato de episodio. Ya paso el 2026-07-20.")
    print("=" * ANCHO + "\n")
    return 1 if fallos else 0


if __name__ == "__main__":
    sys.exit(main())
