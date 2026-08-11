"""
Cierre del EP0004 Lamborghini: pasa el guion LOCUTADO por todo el pipeline.

El episodio se grabo antes de que los agentes vieran el texto final. Esto lo
corrige en el orden correcto:

  1. BORGES     investiga el Acto 4 (el debut sin motor en Turin, 1963), que
                nunca paso por investigacion. Las cifras que hay en el guion
                — 48 horas, ladrillos en el capo, 18 horas diarias — vienen de
                Gabo, no de una fuente.
  2. CLAIMS     extrae del guion locutado las afirmaciones que todavia no
                estan en approved_claims.json.
  3. VERITAS I  audita esas afirmaciones nuevas y las incorpora al catalogo de
                claims aprobados.
  4. VERITAS II audita el guion entero contra el catalogo ya ampliado.
  5. MOORE      rehace el storyboard sobre la locucion real y la duracion real
                del wav (468 s), y deja los gaps separados por tipo de medio.
  6. TALESE     compara la version de Claude con la que Jota edito y grabo, y
                saca el aprendizaje de oficio.
  7. INFORME    una sola pagina HTML con todo, para no leer seis JSON.

Cada paso escribe su salida en cuanto termina, asi que si el paso 5 se cae no
se pierde lo de los cuatro anteriores. `--desde 5` retoma donde quedo.

    python claude_improvement/_run_pipeline_ep0004.py
    python claude_improvement/_run_pipeline_ep0004.py --desde 5
    python claude_improvement/_run_pipeline_ep0004.py --solo 6
"""

import os
import re
import sys
import json
import html
import shutil
import argparse
import traceback
from datetime import datetime

BASE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
sys.path.insert(0, BASE)
os.chdir(BASE)

EP = os.path.join(BASE, "personajes", "Ferruccio_Lamborghini",
                  "EP0004_Ferruccio_Lamborghini")
RESEARCH = os.path.join(EP, "01_RESEARCH")
SCRIPT = os.path.join(EP, "02_SCRIPT")
STORY = os.path.join(EP, "03_STORYBOARD")
PERSONAJE = "Ferruccio Lamborghini"


def cargar_env():
    p = os.path.join(BASE, ".env")
    if not os.path.exists(p):
        return
    for linea in open(p, encoding="utf-8"):
        linea = linea.strip()
        if not linea or linea.startswith("#") or "=" not in linea:
            continue
        k, v = linea.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip("'").strip('"'))


cargar_env()

from openrouter_client import OpenRouterClient          # noqa: E402
from veritas import VeritasAgent                        # noqa: E402
from talese import TaleseAgent                          # noqa: E402
from moore_largo import (MooreLargo, duracion_wav,      # noqa: E402
                         shotlist_md, tc)


# ---------------------------------------------------------------------------
# utilidades
# ---------------------------------------------------------------------------

def leer(*partes, defecto=None):
    p = os.path.join(*partes)
    if not os.path.exists(p):
        if defecto is not None:
            return defecto
        raise SystemExit(f"No encuentro {p}")
    if p.endswith(".json"):
        return json.load(open(p, encoding="utf-8"))
    return open(p, encoding="utf-8").read()


def escribir(datos, *partes):
    p = os.path.join(*partes)
    os.makedirs(os.path.dirname(p), exist_ok=True)
    if os.path.exists(p):
        # Backup antes de pisar. Ya se perdio una edicion manual del panel por
        # no hacerlo; no se repite.
        shutil.copy2(p, p + f".bak_{datetime.now():%Y%m%d_%H%M%S}")
    if p.endswith(".json"):
        json.dump(datos, open(p, "w", encoding="utf-8"), ensure_ascii=False, indent=2)
    else:
        open(p, "w", encoding="utf-8").write(datos)
    print(f"    -> {os.path.relpath(p, BASE)}")
    return p


def titulo(n, txt):
    print("\n" + "=" * 68)
    print(f"PASO {n}. {txt}")
    print("=" * 68)


# ---------------------------------------------------------------------------
# pasos
# ---------------------------------------------------------------------------

def paso_1_borges(cliente):
    titulo(1, "Borges — investigacion dirigida del Acto 4 (Turin, 1963)")

    guion = leer(SCRIPT, "script_long.md")
    acto4 = re.search(r"###\s+Acto 4.*?(?=\n---|\Z)", guion, re.S)
    acto4 = acto4.group(0) if acto4 else guion

    system = (
        "Eres BORGES, Chief Researcher de HUMANOS. Investigas hechos reales y "
        "distingues con precision entre lo documentado, lo narrado por fuentes "
        "secundarias y lo que es leyenda repetida.\n"
        "Regla dura: si un dato circula solo como anecdota sin fuente primaria, "
        "lo dices. No lo adornas ni lo das por bueno. Un dato que no se puede "
        "sostener es peor que no tenerlo, porque el episodio ya esta grabado y "
        "hay que saber que se afirmo.\n"
        "Escribe en espanol neutro. Responde solo JSON."
    )
    prompt = f"""
Investiga este pasaje de un documental sobre {PERSONAJE}. Es el Acto 4: el
debut del prototipo Lamborghini 350 GTV en el Salone dell'Automobile di Torino
de 1963, presentado sin motor bajo el capo.

PASAJE TAL COMO SE GRABO:
<<<TEXTO>>>
{acto4}
<<<FIN>>>

Necesito saber, dato por dato, que esta documentado y que no. Presta atencion
especial a las cifras concretas (horas de trabajo, que se puso bajo el capo
para lastrar el coche, jornadas de los ingenieros): esas cifras entraron por
via narrativa, no por investigacion, y hay que saber si se sostienen.

Responde solo con este JSON:
{{
  "hechos": [
    {{
      "afirmacion": "el hecho tal como lo afirma el guion",
      "estado_documental": "documentado | plausible_sin_fuente_primaria | leyenda_repetida | contradicho",
      "que_dicen_las_fuentes": "que se sabe realmente, en dos frases",
      "fuentes": [{{"titulo": "...", "tipo": "libro | prensa | museo | entrevista", "fiabilidad": "alta | media | baja"}}],
      "recomendacion_editorial": "que hacer con esto en un episodio ya grabado"
    }}
  ],
  "contexto_verificado": "que se sabe con certeza del Salone di Torino 1963 y del 350 GTV",
  "riesgos": ["dato del guion que no deberia repetirse en la newsletter ni en los shorts"],
  "material_visual_probable": ["que material de archivo podria existir de este evento y donde"]
}}"""
    salida = cliente.complete_json(prompt, system)
    escribir({"generado": datetime.now().isoformat(), "acto": "act_4",
              "investigacion": salida},
             RESEARCH, "research_acto4_turin.json")

    for h in salida.get("hechos", []):
        print(f"    [{h.get('estado_documental','?'):32}] {str(h.get('afirmacion'))[:60]}")
    return salida


def paso_2_claims(cliente):
    titulo(2, "Claims — que afirma el guion locutado que aun no esta auditado")

    guion = leer(SCRIPT, "script_long.md")
    aprobados = leer(RESEARCH, "approved_claims.json")
    acto4 = leer(RESEARCH, "research_acto4_turin.json", defecto={})

    system = ("Extraes afirmaciones factuales verificables de un guion "
              "documental. No extraes juicios, metaforas ni recursos "
              "narrativos: solo lo que se puede comprobar o desmentir. "
              "Respondes solo JSON.")
    prompt = f"""
GUION LOCUTADO:
<<<TEXTO>>>
{guion}
<<<FIN>>>

YA AUDITADO (no lo repitas):
{json.dumps(aprobados.get("approved_claims", []), ensure_ascii=False, indent=1)}

INVESTIGACION DIRIGIDA DEL ACTO 4:
{json.dumps(acto4.get("investigacion", {}), ensure_ascii=False, indent=1)}

Extrae las afirmaciones factuales del guion que NO estan ya en la lista
auditada. Numeralas desde C008. Incluye fechas, nombres propios, cifras y
sucesos. Si una afirmacion es de las cifras del Acto 4, marcala igual: el
objetivo es justamente auditarlas.

Responde solo con este JSON:
{{"claims": [{{"claim_id": "C008", "claim": "...", "importance": 8,
  "acto": "act_4", "cita_del_guion": "la frase literal donde aparece"}}]}}"""
    salida = cliente.complete_json(prompt, system)
    claims = salida.get("claims", []) or []
    escribir({"extraido": datetime.now().isoformat(), "claims": claims},
             RESEARCH, "claims_locutado.json")
    print(f"    {len(claims)} afirmaciones nuevas por auditar.")
    return {"claims": claims}


def paso_3_veritas_claims(cliente):
    titulo(3, "Veritas I — auditar las afirmaciones nuevas")

    claims = leer(RESEARCH, "claims_locutado.json")
    research = leer(RESEARCH, "research.json")
    fuentes = leer(RESEARCH, "sources.json")
    acto4 = leer(RESEARCH, "research_acto4_turin.json", defecto={})

    # La investigacion dirigida del Acto 4 entra como material de auditoria:
    # sin ella, Veritas no tiene con que contrastar Turin y lo marca todo
    # UNVERIFIED por falta de datos, que no es lo mismo que por falsedad.
    research = dict(research)
    research["investigacion_acto4_turin"] = acto4.get("investigacion", {})

    veritas = VeritasAgent(cliente)
    fact_check, aprobados_nuevos, logs = veritas.execute_verification(
        PERSONAJE, claims, research, fuentes)
    print("   ", logs)

    escribir({"auditado": datetime.now().isoformat(), "fact_check": fact_check},
             RESEARCH, "fact_check_locutado.json")

    # Fusion con el catalogo existente. No se pisa: se anade lo que aprueba.
    catalogo = leer(RESEARCH, "approved_claims.json")
    existentes = {c.get("claim_id") for c in catalogo.get("approved_claims", [])}
    anadidos, bloqueados = [], []
    for c in aprobados_nuevos.get("approved_claims", []) or []:
        if c.get("claim_id") in existentes:
            continue
        if c.get("status") in ("VERIFIED", "PARTIAL"):
            catalogo["approved_claims"].append(c)
            anadidos.append(c)
        else:
            # Lo que no pasa se guarda igual, no se tira. Un claim que Veritas
            # no pudo sostener es informacion util: es exactamente lo que no
            # hay que repetir en la newsletter, el hilo ni el short, aunque ya
            # este dicho en el video.
            catalogo.setdefault("rejected_or_blocked_claims", []).append(c)
            bloqueados.append(c)
    for c in aprobados_nuevos.get("rejected_or_blocked_claims", []) or []:
        catalogo.setdefault("rejected_or_blocked_claims", []).append(c)
        bloqueados.append(c)

    catalogo["ultima_ampliacion"] = {
        "fecha": datetime.now().isoformat(),
        "origen": "guion locutado EP0004 + investigacion dirigida acto 4",
        "anadidos": len(anadidos), "bloqueados": len(bloqueados),
    }
    escribir(catalogo, RESEARCH, "approved_claims.json")
    print(f"    {len(anadidos)} claims incorporados, {len(bloqueados)} bloqueados.")
    for c in bloqueados:
        print(f"      BLOQUEADO {c.get('claim_id')}: {str(c.get('claim'))[:70]}")
    return fact_check


def paso_4_veritas_guion(cliente):
    titulo(4, "Veritas II — auditar el guion completo contra el catalogo ampliado")

    guion = leer(SCRIPT, "script_long.md")
    research = leer(RESEARCH, "research.json")
    aprobados = leer(RESEARCH, "approved_claims.json")

    veritas = VeritasAgent(cliente)
    audit, logs = veritas.verify_manual_script(
        PERSONAJE,
        {"script_short": guion, "newsletter": "", "linkedin_post": ""},
        research, aprobados)
    print("   ", logs)

    escribir({"audited_at": datetime.now().isoformat(),
              "target": "script_long.md (locutado_final)",
              "script_audit": audit},
             RESEARCH, "veritas_audit_locutado_final.json")
    for i in audit.get("detected_issues", []) or []:
        print(f"    [{i.get('severity','?'):6}] {str(i.get('issue_description'))[:80]}")
    return audit


def paso_5_moore(cliente):
    titulo(5, "Moore — storyboard sobre la locucion real")

    guion = leer(SCRIPT, "script_long.md")
    scripts = leer(SCRIPT, "scripts_long.json")
    registro = leer(EP, "asset_registry.json", defecto=[])
    aprobados = leer(RESEARCH, "approved_claims.json")

    wav = os.path.join(EP, "06_AUDIO", "lamborghini_voz-off-termindo_wav.wav")
    dur = duracion_wav(wav)
    if dur:
        print(f"    Locucion grabada: {dur:.1f}s ({dur/60:.2f} min). "
              f"El storyboard se ajusta a esa duracion.")
    else:
        print("    No pude leer el wav: las duraciones saldran sin escalar.")

    moore = MooreLargo(cliente)
    planos, gaps, informe = moore.storyboard(
        PERSONAJE, guion, scripts.get("narrative_blueprint", {}).get("beat_sheet", []),
        registro, aprobados, duracion_total=dur or 0)

    escribir({"generado": datetime.now().isoformat(),
              "fuente": "script_long.md (locutado_final)",
              "duracion_locucion_seg": dur, "informe": informe,
              "planos": planos},
             STORY, "storyboard_locutado.json")
    escribir(gaps, STORY, "asset_gaps_locutado.json")
    escribir(shotlist_md(PERSONAJE, planos, informe), STORY, "shotlist_locutado.md")

    print(f"    {informe['planos']} planos · cobertura {informe['porcentaje']}% "
          f"({informe['veredicto']}) · {informe['con_asset']} con material · "
          f"{informe['gaps']} por conseguir")
    porvideo = sum(1 for g in gaps if g.get("media_type") == "video_archivo")
    porIA = sum(1 for g in gaps if g.get("media_type") == "recreacion_ia")
    print(f"    De los gaps: {porvideo} piden VIDEO de archivo, {porIA} solo se "
          f"resuelven con recreacion.")
    if informe["veredicto"] != "OK":
        print("    AVISO: hay locucion sin plano asignado. Esta listada al final "
              "de shotlist_locutado.md.")
    return informe


def paso_6_talese(cliente):
    titulo(6, "Talese — aprendizaje entre la version de Claude y la que grabaste")

    guion = leer(SCRIPT, "script_long.md")
    scripts = leer(SCRIPT, "scripts_long.json")
    veritas = leer(RESEARCH, "veritas_audit_locutado_final.json", defecto={})
    moore = leer(STORY, "storyboard_locutado.json", defecto={})

    talese = TaleseAgent(base_dir=BASE)
    system = talese._get_system_prompt()

    historial = scripts.get("version_history", [])
    v3 = next((v for v in historial if v.get("version") == "v3_optimizado"), None)
    loc = next((v for v in historial if v.get("version") == "locutado_final"), None)

    prompt = f"""
Analiza el episodio EP0004 ({PERSONAJE}) comparando dos versiones sucesivas del
mismo guion largo documental.

VERSION ANTERIOR (v3_optimizado, escrita por Claude, nunca locutada):
{json.dumps(v3, ensure_ascii=False, indent=1)}

VERSION NUEVA (locutado_final, editada por Jota y grabada como voz en off):
{json.dumps(loc, ensure_ascii=False, indent=1)}

GUION COMPLETO DE LA VERSION GRABADA:
<<<TEXTO>>>
{guion}
<<<FIN>>>

AUDITORIA DE VERITAS SOBRE LA VERSION GRABADA:
{json.dumps(veritas.get("script_audit", {}), ensure_ascii=False, indent=1)}

DIAGNOSTICO DE PRODUCCION DE MOORE:
{json.dumps(moore.get("informe", {}), ensure_ascii=False, indent=1)}

Jota quiere aprendizaje de oficio, no un veredicto de aprobado o rechazado.
Se especifico y cita frases concretas: una observacion que no se apoya en una
frase del guion no sirve para el proximo episodio.

Responde solo con este JSON:
{{
  "creator_intent": "que buscaba Jota al editar y locutar esta version",
  "editorial_delta": "que corto, que agrego, que enfatizo. Cita las frases.",
  "what_worked": "que mejoro respecto a la version de Claude",
  "what_surprised": "la decision editorial mas inesperada y por que",
  "riesgo_no_resuelto": "que quedo sin resolver en esta version y hay que vigilar",
  "next_experiment": "una hipotesis pequena y accionable para el proximo episodio",
  "proposed_observations": [
    {{"axis": "hook_structure | pacing | tone | precision_factual | ritmo_visual",
      "title": "titulo corto",
      "description": "explicacion apoyada en evidencia del delta"}}
  ]
}}"""
    try:
        informe = cliente.complete_json(prompt, system, model=talese.model_name)
    except Exception as e:
        print(f"    Talese fallo: {type(e).__name__}: {e}")
        informe = {"error": str(e)}

    escribir({"generado": datetime.now().isoformat(),
              "compara": ["v3_optimizado", "locutado_final"], "informe": informe},
             EP, "EPISODE_LEARNING_v3_vs_locutado.json")

    md = f"""# Aprendizaje entre versiones — EP0004 {PERSONAJE}
*v3_optimizado (Claude) → locutado_final (Jota: edicion + locucion real)*
*Gay Talese, {datetime.now():%Y-%m-%d %H:%M}*

## Intencion del creador
{informe.get('creator_intent', 'N/A')}

## Delta editorial
{informe.get('editorial_delta', 'N/A')}

## Lo que funciono
{informe.get('what_worked', 'N/A')}

## Lo que sorprendio
{informe.get('what_surprised', 'N/A')}

## Riesgo sin resolver
{informe.get('riesgo_no_resuelto', 'N/A')}

## Experimento para el proximo episodio
{informe.get('next_experiment', 'N/A')}

---
*Talese no mide exito. Mide evolucion.*
"""
    escribir(md, EP, "EPISODE_LEARNING_v3_vs_locutado.md")
    return informe


# ---------------------------------------------------------------------------
# informe
# ---------------------------------------------------------------------------

CSS = """
:root{--bg:#090909;--panel:#141414;--acc:#01C9C7;--tx:#EDEDED;--mut:#8A8A8A}
*{box-sizing:border-box}
body{margin:0;background:var(--bg);color:var(--tx);
 font-family:Inter,-apple-system,Segoe UI,sans-serif;padding:36px;line-height:1.55}
h1{font-family:Montserrat,Inter,sans-serif;font-size:30px;margin:0 0 6px}
h2{font-size:19px;margin:34px 0 12px;color:var(--acc);
 border-bottom:1px solid #1f1f1f;padding-bottom:8px}
.sub{color:var(--mut);font-size:13px;margin-bottom:26px}
.tarjetas{display:flex;gap:14px;flex-wrap:wrap;margin:18px 0}
.t{background:var(--panel);border:1px solid #222;border-radius:10px;
 padding:16px 20px;min-width:158px}
.t .n{font-size:27px;font-weight:600}
.t .e{color:var(--mut);font-size:12px;text-transform:uppercase;letter-spacing:.5px}
.ok{color:#4ade80}.med{color:#fbbf24}.mal{color:#f87171}
table{width:100%;border-collapse:collapse;font-size:13.5px;margin:8px 0}
th,td{text-align:left;padding:9px 12px;border-bottom:1px solid #1c1c1c;vertical-align:top}
th{color:var(--mut);font-weight:500;font-size:11.5px;text-transform:uppercase}
.pill{display:inline-block;padding:2px 9px;border-radius:20px;font-size:11px;
 border:1px solid currentColor}
.caja{background:var(--panel);border:1px solid #222;border-radius:10px;
 padding:18px 22px;margin:12px 0}
.cita{border-left:3px solid var(--acc);padding-left:14px;color:#cfcfcf;margin:10px 0}
code{background:#1b1b1b;padding:1px 6px;border-radius:4px;font-size:12.5px}
"""


def _pill(estado):
    e = str(estado or "").upper()
    c = ("ok" if e in ("VERIFIED", "APPROVED", "OK", "DOCUMENTADO") else
         "mal" if e in ("REJECTED", "INSUFICIENTE", "CONTRADICHO", "LEYENDA_REPETIDA") else "med")
    return f'<span class="pill {c}">{html.escape(e or "?")}</span>'


def paso_7_informe():
    titulo(7, "Informe — una sola pagina con todo")

    acto4 = leer(RESEARCH, "research_acto4_turin.json", defecto={}).get("investigacion", {})
    fact = leer(RESEARCH, "fact_check_locutado.json", defecto={}).get("fact_check", {})
    audit = leer(RESEARCH, "veritas_audit_locutado_final.json", defecto={}).get("script_audit", {})
    sb = leer(STORY, "storyboard_locutado.json", defecto={})
    aprendizaje = leer(EP, "EPISODE_LEARNING_v3_vs_locutado.json", defecto={}).get("informe", {})
    aprobados = leer(RESEARCH, "approved_claims.json", defecto={})
    inf = sb.get("informe", {})
    planos = sb.get("planos", [])
    gaps = leer(STORY, "asset_gaps_locutado.json", defecto=[])

    def clase(v, bueno, medio):
        return "ok" if v >= bueno else ("med" if v >= medio else "mal")

    precision = audit.get("overall_accuracy_score", 0) or 0
    cobertura = inf.get("porcentaje", 0) or 0
    dur = inf.get("duracion_wav_seg") or 0

    tarjetas = f"""
<div class="tarjetas">
  <div class="t"><div class="n {clase(precision,90,75)}">{precision}%</div>
    <div class="e">precision Veritas</div></div>
  <div class="t"><div class="n">{len(aprobados.get('approved_claims',[]))}</div>
    <div class="e">claims aprobados</div></div>
  <div class="t"><div class="n">{inf.get('planos',0)}</div>
    <div class="e">planos</div></div>
  <div class="t"><div class="n {clase(cobertura,97,90)}">{cobertura}%</div>
    <div class="e">locucion cubierta</div></div>
  <div class="t"><div class="n">{inf.get('con_asset',0)}</div>
    <div class="e">planos con material</div></div>
  <div class="t"><div class="n mal">{inf.get('gaps',0)}</div>
    <div class="e">planos sin material</div></div>
  <div class="t"><div class="n">{dur/60:.1f} min</div>
    <div class="e">locucion grabada</div></div>
</div>"""

    # Acto 4
    filas4 = "".join(
        f"<tr><td>{html.escape(str(h.get('afirmacion','')))}</td>"
        f"<td>{_pill(h.get('estado_documental'))}</td>"
        f"<td>{html.escape(str(h.get('que_dicen_las_fuentes','')))}</td>"
        f"<td>{html.escape(str(h.get('recomendacion_editorial','')))}</td></tr>"
        for h in acto4.get("hechos", []))
    riesgos = "".join(f"<li>{html.escape(str(r))}</li>" for r in acto4.get("riesgos", []))

    # Veritas
    problemas = "".join(
        f"<tr><td>{_pill(i.get('severity'))}</td>"
        f"<td>{html.escape(str(i.get('issue_description','')))}</td>"
        f"<td>{html.escape(str(i.get('evidence_contradiction','')))}</td></tr>"
        for i in audit.get("detected_issues", []) or [])
    if not problemas:
        problemas = '<tr><td colspan="3">Veritas no marco ningun problema.</td></tr>'

    # Moore: gaps agrupados
    porte = {}
    for g in gaps:
        porte.setdefault(g.get("media_type") or "sin_tipo", []).append(g)
    bloques = ""
    for tipo, lista in sorted(porte.items(), key=lambda x: -len(x[1])):
        filas = "".join(
            f"<tr><td><code>{html.escape(str(g.get('gap_id')))}</code></td>"
            f"<td>{html.escape(str(g.get('acto') or ''))}</td>"
            f"<td>{html.escape(str(g.get('missing_asset',''))[:150])}</td>"
            f"<td>{html.escape(', '.join(g.get('manual_search_queries') or [])[:90])}</td></tr>"
            for g in lista)
        bloques += (f"<h3 style='color:#8A8A8A;font-size:14px;margin:22px 0 6px'>"
                    f"{html.escape(tipo)} · {len(lista)}</h3>"
                    f"<table><tr><th>gap</th><th>acto</th><th>que falta</th>"
                    f"<th>buscar</th></tr>{filas}</table>")

    # linea de tiempo
    tl = "".join(
        f"<tr><td><code>{tc(p.get('inicio_seg',0))}</code></td>"
        f"<td>{p.get('duracion_seg',0)}s</td>"
        f"<td>{html.escape(str(p.get('acto') or ''))}</td>"
        f"<td>{html.escape(str(p.get('texto',''))[:110])}</td>"
        f"<td>{html.escape(str(p.get('archivo') or p.get('gap') or ''))}</td></tr>"
        for p in planos)

    perdidos = "".join(f'<div class="cita">{html.escape(f)}</div>'
                       for f in inf.get("fragmentos_sin_plano", []) or [])

    doc = f"""<!doctype html><meta charset="utf-8">
<title>EP0004 Lamborghini — cierre del pipeline</title>
<style>{CSS}</style>
<h1>EP0004 · Ferruccio Lamborghini</h1>
<div class="sub">Cierre del pipeline sobre el guion locutado ·
 {datetime.now():%d/%m/%Y %H:%M}</div>
{tarjetas}

<h2>1 · Acto 4: que se sostiene y que no</h2>
<p class="sub">El debut sin motor en Turin nunca paso por investigacion. Estas
son las afirmaciones del guion contrastadas una por una. El episodio ya esta
grabado, asi que lo que importa aqui es saber que NO repetir en la newsletter,
los shorts y el hilo.</p>
<table><tr><th>afirmacion</th><th>estado</th><th>que dicen las fuentes</th>
<th>que hacer</th></tr>{filas4 or '<tr><td colspan="4">Sin datos.</td></tr>'}</table>
{f'<div class="caja"><b>No repetir fuera del video:</b><ul>{riesgos}</ul></div>' if riesgos else ''}

<h2>2 · Veritas sobre el guion completo</h2>
<div class="caja">Precision {precision}% · {_pill(audit.get('status'))}<br>
<span class="sub">{html.escape(str(audit.get('notes','')))}</span></div>
<table><tr><th>gravedad</th><th>problema</th><th>contradiccion</th></tr>
{problemas}</table>

<h2>3 · Produccion: que falta por conseguir</h2>
<p class="sub">{inf.get('gaps',0)} de {inf.get('planos',0)} planos no tienen
material. Agrupados por lo que hace falta buscar.</p>
{bloques or '<p>Sin gaps.</p>'}

<h2>4 · Linea de tiempo</h2>
<p class="sub">Duraciones proporcionales al texto locutado, escaladas a los
{dur:.0f} segundos reales del wav.</p>
<table><tr><th>entra</th><th>dura</th><th>acto</th><th>locucion</th>
<th>material</th></tr>{tl}</table>
{f'<h2>Locucion sin plano asignado</h2>{perdidos}' if perdidos else ''}

<h2>5 · Aprendizaje (Talese)</h2>
<div class="caja"><b>Intencion:</b> {html.escape(str(aprendizaje.get('creator_intent','N/A')))}</div>
<div class="caja"><b>Delta editorial:</b> {html.escape(str(aprendizaje.get('editorial_delta','N/A')))}</div>
<div class="caja"><b>Funciono:</b> {html.escape(str(aprendizaje.get('what_worked','N/A')))}</div>
<div class="caja"><b>Sorprendio:</b> {html.escape(str(aprendizaje.get('what_surprised','N/A')))}</div>
<div class="caja"><b>Riesgo sin resolver:</b> {html.escape(str(aprendizaje.get('riesgo_no_resuelto','N/A')))}</div>
<div class="caja" style="border-color:#01C9C7"><b>Proximo experimento:</b>
 {html.escape(str(aprendizaje.get('next_experiment','N/A')))}</div>

<h2>6 · Que sigue</h2>
<div class="caja">
<ol>
<li>Buscar el metraje: <code>Buscar Video Lamborghini.bat</code> — solo los gaps
 que piden video, en Istituto Luce (via Europeana), Internet Archive y el fondo
 filmico de la Library of Congress.</li>
<li>Marcar en la hoja de contactos lo que sirva y bajarlo con
 <code>Bajar Seleccion Lamborghini.bat</code>.</li>
<li>Lo que no exista en ningun archivo, y solo eso, a Kling:
 <code>Generar Video IA Lamborghini.bat</code>.</li>
<li>Volver a correr el gate de derechos antes de montar.</li>
</ol></div>
"""
    p = escribir(doc, EP, "INFORME_CIERRE_EP0004.html")
    print(f"\n    Abrelo: {p}")
    return p


# ---------------------------------------------------------------------------

PASOS = [
    (1, "Borges — Acto 4", paso_1_borges, True),
    (2, "Claims nuevos", paso_2_claims, True),
    (3, "Veritas I — claims", paso_3_veritas_claims, True),
    (4, "Veritas II — guion", paso_4_veritas_guion, True),
    (5, "Moore — storyboard", paso_5_moore, True),
    (6, "Talese — aprendizaje", paso_6_talese, True),
    (7, "Informe HTML", paso_7_informe, False),
]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--desde", type=int, default=1)
    ap.add_argument("--solo", type=int)
    a = ap.parse_args()

    if not os.environ.get("OPENROUTER_API_KEY"):
        raise SystemExit("Falta OPENROUTER_API_KEY en el .env.")

    cliente = OpenRouterClient()
    fallos = []
    for n, nombre, fn, necesita_cliente in PASOS:
        if a.solo and n != a.solo:
            continue
        if not a.solo and n < a.desde:
            continue
        try:
            fn(cliente) if necesita_cliente else fn()
        except Exception as e:
            fallos.append((n, nombre, e))
            print(f"\n    PASO {n} FALLO: {type(e).__name__}: {e}")
            traceback.print_exc(limit=2)
            if n <= 4:
                print("    Los pasos siguientes dependen de este. Paro aqui.")
                break

    print("\n" + "=" * 68)
    if fallos:
        print("Terminado con fallos:")
        for n, nombre, e in fallos:
            print(f"  paso {n} ({nombre}): {type(e).__name__}: {str(e)[:120]}")
        print(f"\nRetoma con:  python claude_improvement/_run_pipeline_ep0004.py "
              f"--desde {fallos[0][0]}")
        return 1
    print("Pipeline completo. El informe esta en:")
    print(f"  {os.path.join(EP, 'INFORME_CIERRE_EP0004.html')}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
