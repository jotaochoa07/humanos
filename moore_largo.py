"""
moore_largo — Moore para el documental largo, no para el short.

Por que existe un modulo aparte:

`moore.execute_production` esta escrito para el formato corto. Espera
`scripts_data['scenes']` (las escenas de Gabo) y un `script_short`, y obliga a
la estructura de 8 actos canonicos del vertical. El documental largo de HUMANOS
tiene otra forma: 5 actos, ocho minutos, y sobre todo una locucion YA GRABADA.
Eso cambia el problema. En el corto Moore propone duraciones; aqui la duracion
ya existe, es un wav de 468 segundos, y el storyboard tiene que caber dentro.

Dos decisiones de diseno que vienen de ahi:

1. LAS DURACIONES NO LAS INVENTA EL MODELO. El LLM solo decide donde cortar.
   La duracion de cada plano se calcula por regla de tres sobre el largo del
   texto locutado y se escala al largo real del wav. Un LLM estimando segundos
   se equivoca por un factor de dos; la proporcion de caracteres no.

2. SE VERIFICA LA COBERTURA. Al terminar se comprueba que la concatenacion de
   los planos reconstruye el guion locutado. Si el modelo se comio un parrafo,
   sale un aviso con el fragmento perdido en vez de un storyboard que parece
   bien y deja tres frases sin imagen.

Y una tercera, de produccion: cada gap declara `media_type`. Un plano de una
cadena de montaje quiere VIDEO de archivo; un retrato quiere FOTO. El buscador
de archivo (`archivo_historico.py --video`) lee ese campo para saber que buscar
y donde.
"""

import os
import re
import json
import unicodedata

SYSTEM_PROMPT = (
    "Eres MOORE, Visual Director del proyecto HUMANOS. Estas disenando el "
    "storyboard de un DOCUMENTAL LARGO cuya voz en off YA ESTA GRABADA.\n\n"
    "Reglas duras:\n"
    "1. No reescribes ni una palabra de la locucion. El texto es intocable: solo "
    "decides donde cortar de un plano al siguiente.\n"
    "2. Cada plano cubre un fragmento CONTIGUO y LITERAL del guion. La "
    "concatenacion de todos los planos, en orden, tiene que dar el guion entero. "
    "Ni una frase fuera, ni una frase repetida.\n"
    "3. Prioridad de material, en este orden: archivo historico real en VIDEO, "
    "archivo historico real en FOTO, grafico/motion, y solo como ultimo recurso "
    "recreacion con IA. Este no es un canal faceless de IA: el material real "
    "manda.\n"
    "4. Solo puedes asignar un asset_id que exista en el registro que se te "
    "pasa. Si no existe, deja null y declara el gap.\n"
    "5. Una escena intima o sin prensa delante (una conversacion a puerta "
    "cerrada, un pensamiento) NO existe en ningun archivo. Marcala como "
    "recreacion y se honesto: mandar a buscar lo que no existe hace perder horas."
)


# ---------------------------------------------------------------------------
# normalizacion y cobertura
# ---------------------------------------------------------------------------

def _norm(t):
    """Texto comparable: sin marcadores, sin tipografia, sin espacios dobles."""
    t = (t or "").replace("\r", "")
    t = re.sub(r"`\[[^\]]*\]`", " ", t)
    t = re.sub(r"\[(IMAGEN|SONIDO|GR[ÁA]FICO|GRAFICO|VIDEO)[^\]]*\]", " ", t)
    t = re.sub(r"^#.*$", " ", t, flags=re.M)
    t = re.sub(r"^-{3,}$", " ", t, flags=re.M)
    t = re.sub(r"^\*\*.*?\*\*.*$", " ", t, flags=re.M)
    t = unicodedata.normalize("NFKC", t)
    for a, b in (("“", '"'), ("”", '"'), ("’", "'"),
                 ("‘", "'"), ("—", "-"), ("–", "-")):
        t = t.replace(a, b)
    t = re.sub(r"[^\w\s'\"\.,;:¿?¡!-]", " ", t)
    return re.sub(r"\s+", " ", t).strip()


def solo_locucion(script_md):
    """El guion sin cabeceras ni marcadores: lo que efectivamente se oye.

    Se descarta todo lo anterior al primer `### Acto`: la cabecera del archivo
    (titulo, nota de version, lista de assets) es documentacion para nosotros,
    no esta en el wav, y si se cuenta como locucion la cobertura sale mal.
    """
    corte = re.search(r"^###\s+", script_md or "", flags=re.M)
    return _norm(script_md[corte.start():] if corte else script_md)


def _base(ruta):
    """basename que funciona con rutas de Windows aunque se corra en Linux."""
    return re.split(r"[\\/]", str(ruta or ""))[-1]


def cobertura(planos, script_md):
    """Compara lo que cubren los planos contra la locucion real.

    Devuelve un dict con el porcentaje cubierto y los fragmentos perdidos.
    No corrige nada: informa. La correccion es decision de quien mira.
    """
    objetivo = solo_locucion(script_md)
    cubierto = _norm(" ".join(p.get("texto") or "" for p in planos))

    pal_obj = objetivo.split(" ")
    pal_cub = set(cubierto.split(" "))

    import difflib
    sm = difflib.SequenceMatcher(None, objetivo.split(" "), cubierto.split(" "))
    iguales = sum(b.size for b in sm.get_matching_blocks())
    pct = round(100.0 * iguales / max(1, len(pal_obj)), 1)

    perdidos = []
    for tag, i1, i2, _, _ in sm.get_opcodes():
        if tag in ("delete", "replace") and (i2 - i1) >= 4:
            perdidos.append(" ".join(pal_obj[i1:i2])[:220])

    return {
        "palabras_locucion": len(pal_obj),
        "palabras_cubiertas": iguales,
        "porcentaje": pct,
        "fragmentos_sin_plano": perdidos,
        "veredicto": ("OK" if pct >= 97 else
                      "REVISAR" if pct >= 90 else "INSUFICIENTE"),
    }


# ---------------------------------------------------------------------------
# duraciones
# ---------------------------------------------------------------------------

def duracion_wav(ruta):
    """Segundos reales del wav locutado, o None. Sin dependencias externas."""
    try:
        import wave
        with wave.open(ruta, "rb") as w:
            return w.getnframes() / float(w.getframerate())
    except Exception:
        return None


def repartir_duracion(planos, total_seg, minimo=1.8):
    """Duracion por plano proporcional a los caracteres de su locucion.

    Un LLM estimando segundos se equivoca por un factor de dos. La velocidad
    de habla, en cambio, es practicamente constante dentro de un mismo
    episodio grabado de una sentada.
    """
    largos = [max(1, len(_norm(p.get("texto") or ""))) for p in planos]
    suma = float(sum(largos)) or 1.0
    for p, L in zip(planos, largos):
        p["duracion_seg"] = round(max(minimo, total_seg * L / suma), 2)

    # el redondeo y el minimo desajustan el total: se corrige sobre el plano
    # mas largo, que es el que menos nota un ajuste de decimas.
    desvio = round(total_seg - sum(p["duracion_seg"] for p in planos), 2)
    if planos and abs(desvio) > 0.01:
        idx = max(range(len(planos)), key=lambda i: planos[i]["duracion_seg"])
        planos[idx]["duracion_seg"] = round(
            max(minimo, planos[idx]["duracion_seg"] + desvio), 2)

    t = 0.0
    for p in planos:
        p["inicio_seg"] = round(t, 2)
        t += p["duracion_seg"]
        p["fin_seg"] = round(t, 2)
    return planos


def tc(seg):
    """Segundos a mm:ss.d, que es como se marca en la linea de tiempo."""
    m, s = divmod(float(seg), 60)
    return f"{int(m):02d}:{s:04.1f}"


# ---------------------------------------------------------------------------
# agente
# ---------------------------------------------------------------------------

class MooreLargo:
    def __init__(self, client):
        self.client = client

    def storyboard(self, character_name, script_md, beat_sheet, registry,
                   approved_claims=None, duracion_total=None, por_acto=True):
        """Devuelve (planos, gaps, informe).

        `por_acto=True` trocea la llamada al LLM acto por acto. Un guion de
        ocho minutos entero en un solo prompt es lo que hace que el modelo se
        salte parrafos: la cobertura cae al 70% y hay que rehacerlo. Acto por
        acto la cobertura sube y ademas se puede reintentar solo el acto que
        fallo.
        """
        disponibles = [{
            "asset_id": r.get("asset_id"),
            "archivo": _base(r.get("storage_path")),
            "titulo": r.get("titulo_origen"),
            "licencia": r.get("licencia"),
            "semaforo": r.get("semaforo"),
        } for r in (registry or [])]

        actos = self._trocear(script_md, beat_sheet)
        planos = []
        for acto in actos:
            print(f"[Moore largo] {acto['id']} — {len(acto['texto'])} caracteres de locucion")
            planos.extend(self._planos_de_acto(character_name, acto, disponibles,
                                               approved_claims))

        planos = self._validar(planos, registry or [])

        total = duracion_total or 0.0
        if total:
            repartir_duracion(planos, total)

        gaps = self._gaps(planos)
        informe = cobertura(planos, script_md)
        informe.update({
            "planos": len(planos),
            "gaps": len(gaps),
            "con_asset": sum(1 for p in planos if p.get("asset_id")),
            "duracion_total_seg": round(sum(p.get("duracion_seg", 0) for p in planos), 2),
            "duracion_wav_seg": total,
        })
        return planos, gaps, informe

    # -- troceo -----------------------------------------------------------

    def _trocear(self, script_md, beat_sheet):
        """Parte el .md por las cabeceras `### Acto N`, o cae al beat_sheet."""
        partes = re.split(r"^###\s+", script_md, flags=re.M)
        actos = []
        for i, bloque in enumerate(partes[1:], 1):
            titulo, _, cuerpo = bloque.partition("\n")
            actos.append({
                "id": f"act_{i}",
                "titulo": titulo.strip(),
                "texto": cuerpo.strip(),
            })
        if actos:
            return actos
        return [{"id": b.get("id", f"act_{i}"), "titulo": b.get("title", ""),
                 "texto": b.get("script_text", "")}
                for i, b in enumerate(beat_sheet or [], 1)]

    # -- llamada por acto --------------------------------------------------

    def _planos_de_acto(self, character_name, acto, disponibles, approved_claims):
        prompt = f"""
Documental largo de HUMANOS sobre {character_name}.
Acto: {acto['id']} — {acto['titulo']}

LOCUCION YA GRABADA DE ESTE ACTO (literal, no la toques). Es todo lo que
queda entre las dos marcas de abajo:
<<<LOCUCION>>>
{acto['texto']}
<<<FIN>>>

ASSETS QUE YA ESTAN DESCARGADOS Y CON LICENCIA REGISTRADA
(solo puedes referenciar estos asset_id; cualquier otro es invento):
{json.dumps(disponibles, ensure_ascii=False, indent=1)}

CLAIMS AUDITADOS (lo que se puede afirmar en pantalla):
{json.dumps((approved_claims or {}).get('approved_claims', []), ensure_ascii=False, indent=1)}

Trocea este acto en planos de entre 4 y 12 segundos de locucion.
El campo `texto` de cada plano debe ser una porcion LITERAL y CONTIGUA del
texto de arriba, sin los marcadores entre corchetes. Concatenados en orden y
sin solapes tienen que reconstruir el acto completo.

Responde solo con este JSON:
{{
  "planos": [
    {{
      "acto": "{acto['id']}",
      "texto": "fragmento literal de la locucion",
      "descripcion_visual": "que se ve, encuadre y composicion, en una frase concreta",
      "media_type": "video_archivo | foto_archivo | motion_graphic | recreacion_ia",
      "asset_id": "id del registro si hay uno que sirva de verdad, si no null",
      "movimiento": "estatico | slow_zoom_in | slow_zoom_out | pan_left | pan_right | tilt | corte_seco",
      "archivable": true,
      "motivo_no_archivable": "solo si archivable es false: por que no existe en ningun archivo",
      "consultas_archivo": ["consulta corta de catalogo 1", "consulta corta 2"],
      "prompt_ia": "prompt de generacion, SOLO si media_type es recreacion_ia",
      "rotulo": "texto en pantalla si hace falta, o null"
    }}
  ]
}}"""
        try:
            out = self.client.complete_json(prompt, SYSTEM_PROMPT)
        except Exception as e:
            print(f"  [Moore largo] fallo el acto {acto['id']}: {type(e).__name__}: {e}")
            return [{"acto": acto["id"], "texto": acto["texto"],
                     "descripcion_visual": "SIN DISENAR — el modelo fallo en este acto",
                     "media_type": "foto_archivo", "asset_id": None,
                     "movimiento": "estatico", "archivable": True,
                     "consultas_archivo": [], "error": str(e)}]
        return out.get("planos", []) or []

    # -- validacion --------------------------------------------------------

    def _validar(self, planos, registry):
        """Ningun asset_id inventado, ningun plano sin estado, gaps numerados.

        Es la misma regla dura de `moore.execute_production`: el modelo tiende
        a referenciar archivos plausibles que no estan descargados.
        """
        registrados = {str(r.get("asset_id")): r for r in registry}
        limpios = []
        for n, p in enumerate(planos, 1):
            p["plano"] = n
            aid = p.get("asset_id")
            aid = str(aid) if aid not in (None, "", "null") else None

            if aid and aid in registrados:
                r = registrados[aid]
                p["asset_id"] = aid
                p["archivo"] = _base(r.get("storage_path"))
                p["licencia"] = r.get("licencia")
                p["semaforo"] = r.get("semaforo")
                p["estado"] = "disponible"
                p["gap"] = None
            else:
                if aid:
                    p["nota_validacion"] = f"el modelo propuso asset_id {aid}, que no esta en el registro"
                p["asset_id"] = None
                p["archivo"] = None
                p["estado"] = "falta"
                p["gap"] = f"gapL_{n:03d}"

            p.setdefault("media_type", "foto_archivo")
            p.setdefault("movimiento", "estatico")
            p.setdefault("archivable", p["media_type"] != "recreacion_ia")
            p["consultas_archivo"] = [c for c in (p.get("consultas_archivo") or []) if c][:4]
            limpios.append(p)
        return limpios

    def _gaps(self, planos):
        """Los gaps en el formato que ya lee `archivo_historico.leer_gaps`,
        mas `media_type` para que el buscador sepa si va a por video o foto."""
        gaps = []
        for p in planos:
            if p.get("estado") != "falta":
                continue
            gaps.append({
                "gap_id": p["gap"],
                "scene": p["plano"],
                "acto": p.get("acto"),
                "media_type": p.get("media_type"),
                "missing_asset": p.get("descripcion_visual") or "",
                "criticality": "high" if p.get("media_type") == "video_archivo" else "medium",
                "reason": (p.get("texto") or "")[:180],
                "archivable": bool(p.get("archivable", True)),
                "motivo_no_archivable": p.get("motivo_no_archivable"),
                "suggested_solution": ("buscar en archivo historico"
                                       if p.get("archivable", True)
                                       else "no existe en archivo: recreacion"),
                "manual_search_queries": p.get("consultas_archivo") or [],
                "ai_generation_allowed": not bool(p.get("archivable", True)),
                "ai_generation_prompt": p.get("prompt_ia") or "",
            })
        return gaps


# ---------------------------------------------------------------------------
# salidas legibles
# ---------------------------------------------------------------------------

ETIQUETA_MEDIA = {
    "video_archivo": "VIDEO de archivo",
    "foto_archivo": "FOTO de archivo",
    "motion_graphic": "Motion graphic",
    "recreacion_ia": "Recreacion IA",
}


def shotlist_md(character_name, planos, informe):
    L = [f"# Shot list — {character_name} (documental largo, locucion grabada)",
         "",
         f"{informe['planos']} planos · {informe['duracion_total_seg']}s "
         f"({informe['duracion_total_seg']/60:.1f} min) · "
         f"{informe['con_asset']} con material, {informe['gaps']} por conseguir.",
         f"Cobertura de la locucion: {informe['porcentaje']}% ({informe['veredicto']}).",
         ""]
    acto_actual = None
    for p in planos:
        if p.get("acto") != acto_actual:
            acto_actual = p.get("acto")
            L += ["", f"## {acto_actual}", ""]
        estado = p.get("archivo") or ("POR CONSEGUIR — " + (p.get("gap") or ""))
        L += [f"**{p['plano']:03d}** `{tc(p.get('inicio_seg', 0))} → {tc(p.get('fin_seg', 0))}` "
              f"({p.get('duracion_seg', 0)}s) · {ETIQUETA_MEDIA.get(p.get('media_type'), p.get('media_type'))} "
              f"· {p.get('movimiento')}",
              f"> {(p.get('texto') or '').strip()}",
              f"- Visual: {p.get('descripcion_visual')}",
              f"- Material: {estado}"]
        if p.get("consultas_archivo"):
            L.append(f"- Buscar: {', '.join(p['consultas_archivo'])}")
        if p.get("prompt_ia"):
            L.append(f"- Prompt IA: {p['prompt_ia']}")
        L.append("")
    if informe.get("fragmentos_sin_plano"):
        L += ["", "## Fragmentos de locucion que quedaron sin plano", ""]
        L += [f"- «{f}»" for f in informe["fragmentos_sin_plano"]]
    return "\n".join(L)
