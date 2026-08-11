"""
env_boot — arranque de entorno para HUMANOS.

Por qué existe
--------------
El 2026-08-01 se descubrió que EP0004 (Ferruccio Lamborghini) se "produjo"
sin que corriera un solo agente. La causa fueron dos fallos encadenados:

  1. `.env` no contenía OPENROUTER_API_KEY.
  2. `run_ferruccio_pilot.py` comprobaba `os.environ.get("OPENROUTER_API_KEY")`
     en la línea 26, pero el `.env` recién se cargaba en la línea 33, dentro
     de `TaleseAgent.__init__`. La comprobación siempre daba falso.

El resultado no fue un crash: fue una degradación silenciosa a los guiones
de fallback escritos a mano dentro del propio script. El sistema entregó un
episodio completo, un EPISODE_REVIEW y siete paquetes de distribución sin
haber pensado una sola frase.

Este módulo garantiza que las claves estén en os.environ ANTES de que
cualquier agente decida si instancia su cliente. Importarlo es suficiente.

Uso:
    import env_boot          # carga el .env al importar
    env_boot.exigir("OPENROUTER_API_KEY")   # aborta si falta, en vez de degradar

Regla de diseño: es aditivo. No modifica ni reemplaza el `load_env` que ya
tiene talese.py; solo se adelanta a él.
"""

import os
import sys

BASE_DIR = os.path.dirname(os.path.abspath(__file__))


def cargar(base_dir: str = None) -> int:
    """Vuelca el .env en os.environ sin pisar variables ya definidas.

    Devuelve cuántas claves nuevas se cargaron.
    """
    base_dir = base_dir or BASE_DIR
    env_path = os.path.join(base_dir, ".env")
    if not os.path.exists(env_path):
        return 0

    cargadas = 0
    with open(env_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            clave, valor = line.split("=", 1)
            clave = clave.strip()
            valor = valor.strip().strip("'").strip('"')
            if clave and clave not in os.environ:
                os.environ[clave] = valor
                cargadas += 1
    return cargadas


def hay(clave: str) -> bool:
    return bool(os.environ.get(clave, "").strip())


def exigir(*claves: str, contexto: str = "") -> None:
    """Aborta si falta alguna clave. Preferimos el crash a la degradación.

    Un pipeline que se cae es un problema de diez minutos.
    Un pipeline que degrada en silencio es un episodio falso publicado.
    """
    faltan = [c for c in claves if not hay(c)]
    if not faltan:
        return

    sufijo = f" ({contexto})" if contexto else ""
    print("", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    print(f" ABORTADO: faltan claves de entorno{sufijo}", file=sys.stderr)
    for c in faltan:
        print(f"   - {c}", file=sys.stderr)
    print("", file=sys.stderr)
    print(" No se continua con datos simulados. Anadi las claves a:", file=sys.stderr)
    print(f"   {os.path.join(BASE_DIR, '.env')}", file=sys.stderr)
    print("=" * 72, file=sys.stderr)
    sys.exit(2)


def avisar_degradacion(agente: str, motivo: str) -> None:
    """Grita cuando un agente se queda sin cerebro.

    Cualquier ruta de fallback debe pasar por aca. Si un guion sale de un
    fallback y no de un modelo, tiene que quedar constancia en pantalla y
    en el log del episodio.
    """
    print("", file=sys.stderr)
    print("!" * 72, file=sys.stderr)
    print(f"!! DEGRADACION: {agente} corre SIN modelo.", file=sys.stderr)
    print(f"!! Motivo: {motivo}", file=sys.stderr)
    print("!! Lo que produzca a partir de aca es contenido de relleno,", file=sys.stderr)
    print("!! NO salida de un agente. No lo publiques.", file=sys.stderr)
    print("!" * 72, file=sys.stderr)


# Se carga al importar. Ese es el punto.
_CARGADAS = cargar()
