"""
marca — carga la constitución de marca para cualquier agente.

Por qué existe
--------------
Hasta el 2026-08-01 cada agente tenía su propio system prompt y ninguno leía
los documentos de marca de Jota (`C:\\JotaOS\\vision\\`). El resultado previsible:
Mr. You operaba con una tesis de canal ("Jota Ochoa construye cosas con IA")
que la estrategia de marca v1.0 contradice de forma explícita.

Este módulo es el punto único desde donde todos los agentes cargan el mismo
criterio. Un solo archivo que cambiar cuando la marca evoluciona.

Uso:
    import marca
    system = marca.anteponer(mi_system_prompt, agente="Mr. You")
"""

import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
CONSTITUCION = os.path.join(BASE_DIR, "agents", "_MARCA", "constitucion_marca.md")

# Documentos fuente. Si cambian, hay que regenerar la constitución.
FUENTES = [
    r"C:\JotaOS\vision\Jota Ochoa Personal Brand Strategy v1.0.md",
    r"C:\JotaOS\vision\Entrevista de definición de marca personal — Jota Ochoa.md",
]

# Recordatorio comprimido, para inyectar donde no cabe el documento entero.
NUCLEO = """[MARCA — JOTA OCHOA · lente de trabajo, no reglamento]
Pregunta filtro: ¿Esto contribuye de alguna manera a la expansion humana?
Verbo nuclear: APRENDER. Patron: aprender > probar > construir > conectar > criterio > compartir.
Lente editorial: las historias detras de las historias.

DURABLE (la postura): criterio sin dogma, conectar disciplinas, construir para
comprender, admitir incertidumbre, seguir aprendiendo.
IMPERMANENTE (el territorio): que herramienta usa hoy, que tema toca este año.

Posturas a vigilar — son POSTURAS, no temas prohibidos: guru que ya llego,
divulgador que resena sin construir, vendedor de humo, fanatico afiliado en vez
de con criterio, creador que fabrica polarizacion, perseguidor de metricas.
Jota usa las olas (e-commerce, growth, podcasting, IA) sin ser definido por
ninguna: no es "Jota Manychat" ni "Jota GoHighLevel" ni sera "Jota IA".
Usar la IA y no ser divulgador de IA NO son excluyentes.

Si una propuesta roza una postura: NO la descartes. Señalala y ofrece una
version que consiga lo mismo sin ella. Casi siempre existe.

Las metricas informan; no deciden. Pero observar que funciona no es perseguir
metricas.

Esto evoluciona. Si algo aca te impide hacer un buen trabajo, proponé la
enmienda en tu salida en vez de obedecer a regañadientes o saltartela callado.
Un sistema que solo puede obedecer no tiene criterio: tiene miedo."""


def leer_constitucion():
    if not os.path.exists(CONSTITUCION):
        return ""
    with open(CONSTITUCION, "r", encoding="utf-8") as f:
        return f.read()


def anteponer(system_prompt, agente="", compacta=False):
    """Devuelve el system prompt con la constitución por delante.

    `compacta=True` inyecta solo el nucleo — para agentes con prompts ya
    largos donde el documento completo desplazaria el contexto util.
    """
    texto = NUCLEO if compacta else leer_constitucion()
    if not texto:
        print(f"[marca] AVISO: no encuentro la constitucion en {CONSTITUCION}. "
              f"{agente or 'El agente'} opera SIN criterio de marca.")
        return system_prompt

    encabezado = (
        "# CONSTITUCION DE MARCA — el lente con el que trabajas\n"
        "# Derivada de los documentos de marca de Jota (2026-07-27).\n"
        "#\n"
        "# Usala para PENSAR MEJOR, no para obedecer. Si tu rol de mas abajo la\n"
        "# contradice, señala el conflicto en tu salida y seguí trabajando con\n"
        "# criterio: no te bloquees. Si algo aca te impide hacer un buen trabajo,\n"
        "# proponé la enmienda. Esto es un documento vivo.\n\n"
    )
    return f"{encabezado}{texto}\n\n---\n\n# TU ROL ESPECIFICO\n\n{system_prompt}"


def verificar():
    """Chequeo de salud: ¿existe la constitución? ¿cambiaron las fuentes?"""
    print("\n" + "=" * 70)
    print(" ALINEACION DE MARCA")
    print("=" * 70)
    ok = os.path.exists(CONSTITUCION)
    print(f"  [{'OK ' if ok else 'NO '}] constitucion_marca.md")
    if ok:
        print(f"        {len(leer_constitucion())} caracteres")
    for f in FUENTES:
        existe = os.path.exists(f)
        print(f"  [{'OK ' if existe else 'NO '}] {os.path.basename(f)}")
    if ok:
        mt_c = os.path.getmtime(CONSTITUCION)
        desactualizada = [f for f in FUENTES
                          if os.path.exists(f) and os.path.getmtime(f) > mt_c]
        if desactualizada:
            print("\n  AVISO: los documentos de marca son MAS NUEVOS que la")
            print("  constitucion. Hay que regenerarla:")
            for f in desactualizada:
                print(f"    {os.path.basename(f)}")
        else:
            print("\n  La constitucion esta al dia con los documentos fuente.")
    print("=" * 70 + "\n")
    return ok


if __name__ == "__main__":
    verificar()
