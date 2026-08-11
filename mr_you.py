"""
mr_you — Chief YouTube Officer. Ejecutable.

Hasta el 2026-08-01 Mr. You era el agente más elaborado del sistema y el único
sin una sola línea de código. Vivía en `C:\\JotaOS\\agents\\mr-you\\` como
markdown: un director de canal que nunca dirigió nada.

Este módulo lo pone a trabajar. Ejecuta su Protocolo de Greenlight de 10 puntos,
produce hipótesis de packaging y congela un Prediction Snapshot que después se
contrasta contra la realidad.

Frontera de responsabilidad (auditoría §2.1) — Mr. You opera a nivel CANAL:
  - NO interviene en la cocina editorial de HUMANOS. Eso es Borges, Veritas,
    Gabo, Moore y Talese.
  - SÍ decide qué merece publicarse, con qué empaque y en qué orden, mirando
    el portfolio completo (HUMANOS + Lab IA).

Regla que hereda de su system prompt y que este código hace cumplir:
  "Nunca inventes certeza."
Toda afirmación se clasifica como DATO / PATRÓN / HIPÓTESIS / BEST PRACTICE
EXTERNA. Si la capa de canal no tiene métricas reales, Mr. You debe decir
que no sabe, en vez de sonar seguro. `canal.resumen_para_mr_you()` se lo
inyecta en el prompt para que no pueda evitarlo.

Uso:
    python mr_you.py --episodio EP0004_Ferruccio_Lamborghini
    python mr_you.py --idea "..." --expresion STORY --tier A
    python mr_you.py --episodio EP0004... --sin-apify     (no gasta creditos)
"""

import os
import re
import sys
import json
import argparse
from datetime import datetime

import env_boot
import canal
import marca

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JOTAOS_MR_YOU = r"C:\JotaOS\agents\mr-you"
REPO_MR_YOU = os.path.join(BASE_DIR, "agents", "mr-you")
PREDICTION_LOG = os.path.join(JOTAOS_MR_YOU, "prediction-log.md")

MODELO = os.environ.get("MR_YOU_MODEL", "anthropic/claude-sonnet-5")


# ---------------------------------------------------------------------------
# Carga de la identidad del agente
# ---------------------------------------------------------------------------

def _leer(*candidatos):
    for c in candidatos:
        if c and os.path.exists(c):
            with open(c, "r", encoding="utf-8") as f:
                return f.read()
    return ""


def cargar_identidad():
    """Lee personality.md y system_prompt.md. El repo manda; JotaOS respalda.

    El system_prompt.md real está dentro de un bloque ```markdown. Se extrae
    para no meterle al modelo el envoltorio de documentación.
    """
    system = _leer(
        os.path.join(REPO_MR_YOU, "prompts", "system_prompt.md"),
        os.path.join(JOTAOS_MR_YOU, "prompts", "system_prompt.md"),
    )
    m = re.search(r"```markdown\s*\n(.*?)\n```", system, re.S)
    if m:
        system = m.group(1)

    personalidad = _leer(
        os.path.join(REPO_MR_YOU, "personality.md"),
        os.path.join(JOTAOS_MR_YOU, "personality.md"),
    )
    # Doctrina de canal: la escribio Jota, gobierna sobre los datos.
    # Existe porque el sistema, apenas empezo a leer metricas reales, intento
    # optimizar el corto plazo y mezclo las dos lineas de producto en una sola
    # serie. Se antepone al system prompt para que no sea un anexo opcional.
    doctrina = _leer(
        os.path.join(REPO_MR_YOU, "doctrina_canal.md"),
        os.path.join(JOTAOS_MR_YOU, "doctrina_canal.md"),
    )
    if doctrina:
        system = (
            "# DOCTRINA DE CANAL — la escribio Jota. Gobierna sobre cualquier\n"
            "# lectura de datos. Si un dato la contradice, lo decis explicitamente\n"
            "# pero NO cambias el rumbo por tu cuenta.\n\n"
            + doctrina
            + "\n\n---\n\n# TU SYSTEM PROMPT\n\n"
            + system
        )
    else:
        print("[Mr. You] Aviso: no encuentro doctrina_canal.md. "
              "Opero solo con el system prompt.")

    if not system:
        raise SystemExit(
            "No encuentro el system prompt de Mr. You. Busque en:\n"
            f"  {REPO_MR_YOU}\\prompts\\system_prompt.md\n"
            f"  {JOTAOS_MR_YOU}\\prompts\\system_prompt.md"
        )

    # La constitucion de marca va por ENCIMA de todo, incluida la doctrina.
    # Contradiccion C1 abierta: el system prompt de Mr. You declara "Tesis del
    # Canal: Jota Ochoa construye cosas con IA", y la estrategia de marca v1.0
    # (posterior en fecha) dice que Jota NO debe construirse como marca de IA.
    # Hasta que Jota decida, manda la constitucion y el agente debe señalarlo.
    system = marca.anteponer(system, agente="Mr. You")

    return system, personalidad


# ---------------------------------------------------------------------------
# Contexto del episodio
# ---------------------------------------------------------------------------

def localizar_episodio(episode_id):
    raiz = os.path.join(BASE_DIR, "personajes")
    for personaje in os.listdir(raiz):
        d = os.path.join(raiz, personaje, episode_id)
        if os.path.isdir(d):
            return d
    return None


def contexto_episodio(episode_id):
    """Reúne lo que existe en disco. Sin inventar: lo que falta, falta."""
    d = localizar_episodio(episode_id)
    if not d:
        raise SystemExit(f"No encuentro el episodio {episode_id} en personajes/")

    def leer(*partes, limite=6000):
        p = os.path.join(d, *partes)
        if not os.path.exists(p):
            return None
        with open(p, "r", encoding="utf-8") as f:
            return f.read()[:limite]

    def leer_json(*partes):
        p = os.path.join(d, *partes)
        if not os.path.exists(p):
            return None
        try:
            with open(p, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

    gaps = leer_json("03_STORYBOARD", "asset_gaps.json") or []
    fact = leer_json("01_RESEARCH", "fact_check.json") or {}

    return {
        "episode_id": episode_id,
        "directorio": d,
        "estado": (leer_json("pipeline_state.json") or {}).get("status"),
        "dossier": leer("01_RESEARCH", "Editorial_Dossier.md", limite=8000),
        "guion_corto": leer("02_SCRIPT", "script_short.md"),
        "guion_largo": leer("02_SCRIPT", "script_long.md", limite=12000),
        "asset_gaps": len(gaps) if isinstance(gaps, list) else None,
        "veritas_score": fact.get("score") or fact.get("overall_score"),
        "imagenes": len(os.listdir(os.path.join(d, "04_IMAGES")))
                    if os.path.isdir(os.path.join(d, "04_IMAGES")) else 0,
    }


# ---------------------------------------------------------------------------
# El agente
# ---------------------------------------------------------------------------

ESQUEMA = """{
  "veredicto": "GO | REWORK | NO-GO",
  "pilar": "BUILD | STORY | BECOME | BTS",
  "tier": "A | B | C | D",
  "discovery": "Search | Browse | Hybrid",
  "objetivo": "Reach | Authority | Trust | Conversion",
  "diagnostico": "2-3 lineas: que funcion cumple esta pieza en el catalogo HOY",
  "viewer_payoff": "Despues de ver este video, el espectador ...",
  "checklist_10_puntos": [
    {"punto": "Click Reason", "respuesta": "...", "tipo_evidencia": "DATO | PATRON | HIPOTESIS | BEST_PRACTICE_EXTERNA"}
  ],
  "packaging": [
    {"id": "A", "titulo": "...", "concepto_miniatura": "...",
     "prompt_miniatura": "prompt listo para generador de imagen",
     "visual_hook": "que ocurre en los primeros 3 segundos",
     "por_que_funciona": "...", "tipo_evidencia": "DATO | PATRON | HIPOTESIS | BEST_PRACTICE_EXTERNA"}
  ],
  "riesgo_principal": "compliance, derechos, retencion...",
  "que_cambiaria_para_go": ["accion concreta"],
  "prediction_snapshot": {
    "ctr_objetivo": "rango con unidad, ej '4-6%'",
    "retencion_3s_objetivo": "rango, ej '65-75%'",
    "punto_de_abandono_esperado": "donde y por que",
    "hipotesis_estrategica": "la apuesta que este video pone a prueba",
    "base_de_la_prediccion": "DATO | HIPOTESIS | BEST_PRACTICE_EXTERNA",
    "como_se_mide": "que mirar en YouTube Studio a las 48h"
  },
  "lo_que_no_se": ["cosas que no puedo afirmar por falta de evidencia del canal"]
}"""


class MrYou:
    def __init__(self, client=None):
        env_boot.exigir("OPENROUTER_API_KEY", contexto="Mr. You necesita modelo")
        if client is None:
            from openrouter_client import OpenRouterClient
            client = OpenRouterClient()
        self.client = client
        self.system, self.personalidad = cargar_identidad()

    # -- fase 3 + 4 --------------------------------------------------------

    def greenlight(self, idea, expresion="STORY", tier="A", contexto="",
                   competencia=None, metricas_canal=None):
        metricas_canal = metricas_canal or canal.resumen_para_mr_you()

        bloque_evidencia = json.dumps({
            "hay_evidencia_real_del_canal": metricas_canal["hay_evidencia_real"],
            "advertencia": metricas_canal["advertencia"],
            "conteos": metricas_canal["conteos"],
            "promedios_solo_reales": metricas_canal["promedios_solo_reales"],
        }, ensure_ascii=False, indent=2)

        bloque_competencia = "No se consulto la competencia en esta corrida."
        if competencia:
            bloque_competencia = json.dumps(competencia[:20], ensure_ascii=False, indent=2)

        system = (
            self.system
            + "\n\n---\nRESPONDE EXCLUSIVAMENTE CON UN OBJETO JSON VALIDO que siga "
              "este esquema, sin texto alrededor:\n" + ESQUEMA
            + "\n\nOBLIGATORIO: el campo `tipo_evidencia` de cada afirmacion debe ser "
              "honesto. Si la seccion de METRICAS DEL CANAL dice que no hay evidencia "
              "real, NO puedes marcar nada como DATO ni como PATRON. Usa HIPOTESIS o "
              "BEST_PRACTICE_EXTERNA y llena `lo_que_no_se`. Sonar seguro sin datos es "
              "el peor fallo que puedes cometer."
        )

        prompt = f"""PROPUESTA DE VIDEO PARA EVALUACION:
- Idea / Concepto: {idea}
- Expresion sugerida: {expresion}
- Tier pretendido: {tier}

--- CONTEXTO Y MATERIAL DISPONIBLE ---
{contexto}

--- METRICAS DEL CANAL (capa de agregacion, {datetime.now():%Y-%m-%d}) ---
{bloque_evidencia}

--- COMPETENCIA EN YOUTUBE SOBRE ESTE TEMA (via Apify) ---
{bloque_competencia}

Ejecuta el Protocolo de Greenlight de 10 puntos y el Prediction Snapshot.
Da TRES hipotesis de packaging (A, B, C), no dos: una segura, una arriesgada
y una que ataque un angulo que la competencia listada arriba no esta usando.
"""
        print(f"[Mr. You] Evaluando con {MODELO}...")
        return self.client.complete_json(prompt, system_prompt=system, model=MODELO)

    # -- fase 4: congelar --------------------------------------------------

    def congelar_snapshot(self, veredicto, episode_id, titulo_idea, directorio=None):
        """Escribe el snapshot en el episodio y lo añade al prediction-log.

        Las predicciones se congelan y no se tocan después de publicar. Ese es
        el punto entero: si se pueden editar, no son predicciones.
        """
        snap = veredicto.get("prediction_snapshot", {})
        elegido = (veredicto.get("packaging") or [{}])[0]

        ficha = {
            "episode_id": episode_id,
            "idea": titulo_idea,
            "congelado_en": datetime.now().isoformat(timespec="seconds"),
            "congelado_por": "mr_you.py",
            "modelo": MODELO,
            "veredicto": veredicto.get("veredicto"),
            "pilar": veredicto.get("pilar"),
            "tier": veredicto.get("tier"),
            "discovery": veredicto.get("discovery"),
            "objetivo": veredicto.get("objetivo"),
            "viewer_payoff": veredicto.get("viewer_payoff"),
            "packaging_congelado": elegido,
            "packaging_alternativas": (veredicto.get("packaging") or [])[1:],
            "prediccion": snap,
            "lo_que_no_se": veredicto.get("lo_que_no_se", []),
            "override_de_jota": None,
            "resultado_real": None,
            "postmortem": None,
        }

        if directorio:
            destino = os.path.join(directorio, "prediction_snapshot.json")
            with open(destino, "w", encoding="utf-8") as f:
                json.dump(ficha, f, indent=2, ensure_ascii=False)
            print(f"[Mr. You] Snapshot congelado en {destino}")

        self._anexar_al_log(ficha)
        return ficha

    def _anexar_al_log(self, ficha):
        if not os.path.exists(PREDICTION_LOG):
            print(f"[Mr. You] Aviso: no encuentro {PREDICTION_LOG}. No anexo.")
            return
        p = ficha.get("packaging_congelado", {})
        pr = ficha.get("prediccion", {})
        bloque = f"""

---

### [{datetime.now():%Y-%m-%d}] {ficha['idea']}

* **Episodio:** `{ficha['episode_id']}`
* **Veredicto:** {ficha['veredicto']}
* **Pilar:** {ficha['pilar']} · **Tier:** {ficha['tier']} · **Discovery:** {ficha['discovery']}
* **Titulo Congelado:** `{p.get('titulo', '—')}`
* **Miniatura Congelada:** {p.get('concepto_miniatura', '—')}
* **Visual Hook:** {p.get('visual_hook', '—')}
* **Viewer Payoff:** "{ficha.get('viewer_payoff', '—')}"

#### Expectativas y Metricas a Medir
1. **CTR Esperado:** {pr.get('ctr_objetivo', '—')}
2. **Retencion 3s:** {pr.get('retencion_3s_objetivo', '—')}
3. **Punto de abandono esperado:** {pr.get('punto_de_abandono_esperado', '—')}
4. **Hipotesis Estrategica:** {pr.get('hipotesis_estrategica', '—')}
5. **Base de la prediccion:** {pr.get('base_de_la_prediccion', '—')}

#### Lo que Mr. You NO sabe todavia
{chr(10).join('* ' + x for x in ficha.get('lo_que_no_se', [])) or '* —'}

*Congelado por `mr_you.py` el {ficha['congelado_en']}. No se edita post-publicacion.*
"""
        with open(PREDICTION_LOG, "a", encoding="utf-8") as f:
            f.write(bloque)
        print(f"[Mr. You] Anexado a {PREDICTION_LOG}")


# ---------------------------------------------------------------------------
# Presentación
# ---------------------------------------------------------------------------

def imprimir(v):
    icono = {"GO": "[ GO ]", "REWORK": "[REWRK]", "NO-GO": "[NO-GO]"}
    print("\n" + "=" * 74)
    print(f" GREENLIGHT — {v.get('veredicto', '?')}")
    print("=" * 74)
    print(f"  Veredicto : {icono.get(v.get('veredicto'), '')} {v.get('veredicto')}")
    print(f"  Pilar     : {v.get('pilar')}   Tier: {v.get('tier')}   "
          f"Discovery: {v.get('discovery')}   Objetivo: {v.get('objetivo')}")
    print(f"\n  Diagnostico:\n    {v.get('diagnostico', '')}")
    print(f"\n  Viewer Payoff:\n    \"{v.get('viewer_payoff', '')}\"")

    print("\n  --- Checklist de 10 puntos ---")
    for i, p in enumerate(v.get("checklist_10_puntos", []), 1):
        print(f"  {i:>2}. {p.get('punto')}  [{p.get('tipo_evidencia')}]")
        print(f"      {p.get('respuesta', '')}")

    print("\n  --- Hipotesis de packaging ---")
    for p in v.get("packaging", []):
        print(f"\n  [{p.get('id')}] {p.get('titulo')}")
        print(f"      Miniatura : {p.get('concepto_miniatura')}")
        print(f"      Hook 3s   : {p.get('visual_hook')}")
        print(f"      Por que   : {p.get('por_que_funciona')}  [{p.get('tipo_evidencia')}]")

    print(f"\n  Riesgo principal: {v.get('riesgo_principal')}")
    if v.get("que_cambiaria_para_go"):
        print("  Para llegar a GO:")
        for a in v["que_cambiaria_para_go"]:
            print(f"    - {a}")

    print("\n  --- Prediction Snapshot (se congela) ---")
    for k, val in (v.get("prediction_snapshot") or {}).items():
        print(f"    {k:<32} {val}")

    if v.get("lo_que_no_se"):
        print("\n  --- Lo que Mr. You NO sabe ---")
        for x in v["lo_que_no_se"]:
            print(f"    - {x}")
    print("=" * 74 + "\n")


def main():
    ap = argparse.ArgumentParser(description="Mr. You — Greenlight y Packaging")
    ap.add_argument("--episodio", help="ej. EP0004_Ferruccio_Lamborghini")
    ap.add_argument("--idea", help="idea suelta, si no hay episodio en disco")
    ap.add_argument("--expresion", default="STORY",
                    choices=["BUILD", "STORY", "BECOME", "BTS"])
    ap.add_argument("--tier", default="A", choices=["A", "B", "C", "D"])
    ap.add_argument("--sin-apify", action="store_true",
                    help="no consulta la competencia (no gasta creditos)")
    ap.add_argument("--no-congelar", action="store_true",
                    help="evalua pero no escribe el prediction snapshot")
    args = ap.parse_args()

    if not args.episodio and not args.idea:
        ap.error("dame --episodio o --idea")

    # La capa de canal primero: Mr. You no opina sin saber qué sabe.
    canal.importar_metrics_history()
    metricas = canal.imprimir_resumen()

    contexto, idea, directorio = "", args.idea, None
    if args.episodio:
        ctx = contexto_episodio(args.episodio)
        directorio = ctx["directorio"]
        idea = args.idea or f"Documental HUMANOS — {args.episodio}"
        contexto = f"""Estado del pipeline: {ctx['estado']}
Score de Veritas: {ctx['veritas_score']}
Imagenes disponibles: {ctx['imagenes']} · Asset gaps abiertos: {ctx['asset_gaps']}

[DOSSIER EDITORIAL — BORGES]
{ctx['dossier'] or '(sin dossier)'}

[GUION CORTO — version final de Jota]
{ctx['guion_corto'] or '(sin guion corto)'}
"""

    competencia = None
    if not args.sin_apify:
        try:
            from apify_client import competencia_youtube
            print("[Mr. You] Consultando competencia en YouTube via Apify...")
            competencia = competencia_youtube([
                "Ferruccio Lamborghini Enzo Ferrari historia",
                "origen Lamborghini documental",
                "Lamborghini vs Ferrari rivalidad",
            ], max_por_consulta=10)
            print(f"[Mr. You] {len(competencia)} piezas de competencia recuperadas.")
        except Exception as e:
            print(f"[Mr. You] Apify no respondio ({type(e).__name__}: {e}).")
            print("[Mr. You] Sigo SIN datos de competencia. Quedara marcado "
                  "como HIPOTESIS, no como DATO.")

    agente = MrYou()
    veredicto = agente.greenlight(idea, args.expresion, args.tier,
                                  contexto, competencia, metricas)
    imprimir(veredicto)

    if not args.no_congelar and args.episodio:
        agente.congelar_snapshot(veredicto, args.episodio, idea, directorio)

    return 0


if __name__ == "__main__":
    sys.exit(main())
