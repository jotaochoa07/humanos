# CLAUDE_AUDIT.md — Auditoría Arquitectónica del Sistema Editorial HUMANOS + Jota OS

**Auditor:** Claude (Senior Product / Architecture / Editorial Workflow)
**Fecha:** 2026-08-01
**Alcance:** `C:\JotaOS\` (spec declarativa), `C:\Users\Jota Ochoa\Antigravity\02_Projects\humanos\` (pipeline canónico ejecutable), `C:\Users\Jota Ochoa\.gemini\antigravity\scratch\humanos-mvp\` (copia archivo).
**Restricción respetada:** no se modificó ni ejecutó código de producción. Esto es diagnóstico.

> Nota de método: cada diagnóstico fuerte cita archivo y línea. Donde no tuve evidencia directa lo marco como HIPÓTESIS. No inventé certeza (regla de Veritas aplicada al propio informe).

---

## 0. Hallazgo maestro (léelo aunque no leas nada más)

Tenés **dos sistemas que no son el mismo sistema**, y ninguno de los dos es el que creés que tenés:

1. **El sistema que está escrito** (JotaOS): 12 agentes con constituciones sofisticadas, Mr. You con su Protocolo de Greenlight de 10 puntos, Talese cerrando el bucle de aprendizaje, Antigravity orquestando. Es una arquitectura hermosa y madura **en markdown**.

2. **El sistema que corre** (pipeline Python + dashboard Node): una cadena lineal de 6 agentes (`Borges → Veritas → Gabo → [pausa humana] → Moore → Leonardo → Mark`) disparada por un script monolítico de 403 líneas (`run_humanos_mvp.py`) y un servidor Node de 714 líneas. **Mr. You no existe en el código. La mitad de Talese está rota. Las métricas que alimentan todo el aprendizaje son `random.randint()`.**

La brecha entre "lo escrito" y "lo que corre" es la deuda central del proyecto. No tenés un problema de arquitectura; tenés un problema de **sincronización entre la constitución y la ejecución**. Todo lo demás en este informe es consecuencia de eso.

---

## 1. Mapa de la Arquitectura Actual

### 1.1 Quién orquesta de verdad

El brief dice que **Antigravity** es el orquestador central. En la práctica, Antigravity es tu **IDE/entorno de desarrollo** (donde codeás con agentes), no un runtime que orquesta el pipeline editorial. El orquestador real en ejecución son **dos piezas**:

- **`editorial-dashboard-server.mjs`** (Node, puerto 3100): es el orquestador de cara al humano. Expone la API, lee el estado de los episodios desde disco, lee `humanos_stories` de Supabase, y hace `spawn("python", ["run_humanos_mvp.py", ...])` (líneas 346, 487). Es lo que abrís con `npm run editorial` / `Abrir HUMANOS Dashboard.bat`.
- **`run_humanos_mvp.py`** (Python, 403 líneas): es el orquestador real del pipeline. Importa cada agente y los llama en secuencia hard-coded (líneas 9-18, 51-338).

**Hermoso, que en `JotaOS/AGENTS.md` (§1, línea 21) es el "Executive Producer / Orquestador operativo", en el código es `hermoso_core.py`: 108 líneas de utilidades de sistema de archivos** (crear 10 carpetas, escribir JSON, loggear, actualizar `pipeline_state.json`). No orquesta nada. La orquestación que su spec promete la hace el script monolítico.

### 1.2 Flujo end-to-end real (reconstruido desde el código)

```
                            ┌─────────────────────────────────────────────┐
                            │  PANEL EDITORIAL (editorial-dashboard.html)  │
                            │  Tabs: Backlog · Guiones · Finalizados ·     │
                            │        Publisher · Aprendizaje Talese        │
                            └───────────────┬─────────────────────────────┘
                                            │ HTTP :3100
                            ┌───────────────▼─────────────────────────────┐
                            │  editorial-dashboard-server.mjs (Node)       │
                            │  lee Supabase.humanos_stories + estado disco │
                            └───────┬───────────────────────┬─────────────┘
                                    │ spawn python          │ spawn python (produce)
                                    ▼ (stage=write)          ▼
   IDEA ──────────────────────────────────────────────────────────────────────────►
   (Supabase humanos_stories:                run_humanos_mvp.py  (orquestador real)
    editorial_status=idea/                          │
    needs_research)                                 │
                                                    ▼
   ① HERMOSO CORE ── crea 10 carpetas (01_RESEARCH…10_EXPORTS) + MEDIA_LIBRARY
                                                    ▼
   ② BORGES (borges.py + OpenRouter) ── research.json, timeline, claims, dossier, asset_manifest
                                                    ▼
   ②' ASSET COLLECTOR ── descarga assets de Wikimedia Commons
                                                    ▼
   ③ VERITAS (gate #1) ── fact_check.json ; si score < 80 → vuelve a research (STOP)
                                                    ▼
   ④ GABO (gabo.py) ── script_short, script_long, newsletter, twitter_thread
                                                    ▼
   ═══════════ PAUSA HUMANA (status: script_pending_review) ═══════════
              Jota edita el guion en el panel → botón "Guardar y Producir"
              → dispara Talese "immediate retro" (background) + stage=produce
                                                    ▼
   ④' VERITAS (gate #2) ── audita el guion editado a mano ; si score < 80 → STOP
                                                    ▼
   ⑤ CURIE ── lee asset_registry (indexación física, rol mínimo en ejecución)
                                                    ▼
   ⑥ MOORE (moore.py) ── storyboard.json, shotlist, asset_gaps, editing_notes
                                                    ▼
   ⑥' YouTube searcher + automated_asset_gatherer (scripts/)
                                                    ▼
   ⑦ LEONARDO (leonardo.py) ── branding_spec.json/.md (dirección de arte)
                                                    ▼
   ⑧ MARK (mark.py) ── 11_DIST/ (copy por plataforma) + checklist + métricas SIMULADAS (random)
                                                    ▼
   ═══════════ status: storyboard_done ═══════════   ◄── EL PIPELINE TERMINA AQUÍ
                                                    ▼
   [MANUAL / FUERA DEL PIPELINE]
   · Render de branding en REMOTION (npm run render:*) — compositions React
   · Edición/ensamblado en CAPCUT (capcut_packager.py existe pero NO se invoca)
   · Publicación en YouTube (manual; skill youtube_publish.md sin ejecutor)
   · Carga manual de métricas 48h en el panel (save-metrics) → metrics_history.json
                                                    ▼
   [APRENDIZAJE]
   · Talese immediate retro (delta Gabo vs Jota) → EPISODE_REVIEW.md ✅ funciona
   · Talese performance retro (métricas 48h → learnings) → ❌ ROTO (bug)
   · Mark dashboard conceptual → PRODUCTION_METRICS_DASHBOARD.md
```

### 1.3 Dónde está Mr. You en este mapa

**En ningún lado del runtime.** Mr. You vive completo en `C:\JotaOS\agents\mr-you\` (personality.md, system_prompt.md, prediction-log.md) y en `Brand/YouTube Vision & Strategy.md` §5. Su `prediction-log.md` tiene una entrada real ("El error del botón de WhatsApp", 2026-07-28) — pero es de la **línea Marca Personal / Lab IA**, no de HUMANOS, y se llenó a mano. **No hay ni una línea de código que ejecute el Greenlight de 10 puntos, ni que congele un Prediction Snapshot, ni que lo conecte al pipeline de HUMANOS.** Es el agente más elaborado que tenés y el más desconectado.

---

## 2. Matriz de Agentes y Diagnóstico

| Agente | Rol (spec JotaOS) | ¿Corre en código? | Evidencia | Diagnóstico |
|---|---|---|---|---|
| **Hermoso** | Executive Producer / Orquestador | Parcial — solo utilidades FS | `hermoso_core.py` (108 líneas, sin orquestación) | La orquestación real la hace `run_humanos_mvp.py`. Hermoso está degradado a "creador de carpetas". Brecha spec↔código grande. |
| **Borges** | Research + Cazador de Protagonistas | Sí (2 veces) | `borges.py` (19.7KB, OpenRouter) **Y** `n8n/workflows/borges_workflow.json` (Tavily) | **Doble cerebro.** Dos implementaciones paralelas de Borges. El n8n no está cableado al flujo actual. Fuente de verdad ambigua. |
| **Veritas** | Fact Checker / Quality Gate | Sí — bien integrado | `run_humanos_mvp.py` gate #1 (L89) y gate #2 (L222) | **El agente mejor implementado.** Doble compuerta con umbral 80. Diseño sólido. NO TOCAR. |
| **Gabo** | Story Architect (guion 7 actos) | Sí | `gabo.py` (15.8KB), llamado en L98-101 | Bien integrado. Genera 4 formatos (short/long/newsletter/twitter). Su spec (3 variantes) no se refleja del todo en el output. |
| **Curie** | Memoria Editorial / RAG semántico | Casi no | L231-235: solo `len(registry_data)` | Curie está **subutilizado al extremo**. Su promesa (deduplicación de historias, sugerir cruces temáticos a Gabo) no se ejecuta. Solo cuenta assets. |
| **Moore** | Documentary Producer / Storyboard | Sí | `moore.py` (205 líneas), L239-251 | Bien integrado. Genera gaps de producción (dato valioso, ver §6). |
| **Leonardo** | Creative Director / Branding | Sí | `leonardo.py` (92 líneas), L269-277 | Integrado pero delgado. Genera spec de arte, no ejecuta miniaturas. |
| **Mark** | CMO / CDO / Distribución + Métricas | Sí, con bugs | `mark.py` (331 líneas) | Genera 7 paquetes de plataforma. **Bug crítico** (§4). Checklist hard-coded a Jan Koum. Métricas simuladas. |
| **Mr. You** | Chief YouTube Officer / Greenlight | **NO** | Solo markdown en `C:\JotaOS\agents\mr-you\` | El agente más sofisticado, **cero ejecución**. Ver §2.1. |
| **Talese** | Director de Aprendizaje Editorial | Mitad sí, mitad rota | `talese.py` (421 líneas) | Immediate retro ✅ (L57-157). Performance retro ❌ (`self.learnings_file` indefinido). Gates 1/2 definidos pero no llamados. |
| **Dali** | Frontend Architect | Fuera del pipeline HUMANOS | `JotaOS/agents/dali/` | Pertenece a la línea Lab IA / webs, no a HUMANOS. Correcto que no esté. |
| **BuilderJota** | Lead Vibecoder | Fuera del pipeline HUMANOS | `JotaOS/agents/builderjota/` | Línea Lab IA. Correcto que no esté. |

### 2.1 La frontera Mr. You ↔ Mark (el punto que pediste clarificar)

Hoy la frontera está **conceptualmente clara en la spec pero colapsada en el código**, porque uno de los dos no existe en ejecución.

**Definición limpia (cómo DEBERÍA ser):**

| Dimensión | **Mr. You** (Chief YouTube Officer) | **Mark** (Chief Distribution Officer) |
|---|---|---|
| **Momento** | ANTES de producir (decisión de luz verde) | DESPUÉS de producir (empaquetar y publicar) |
| **Pregunta** | "¿Este video merece existir y con qué packaging?" | "¿Cómo distribuyo este video ya aprobado en cada canal?" |
| **Output** | Veredicto GO/REWORK/NO-GO + 2-3 hipótesis de título/miniatura + Prediction Snapshot | Copy por plataforma (`11_DIST/`), hashtags, pinned comment, thumbnail |
| **Unidad de análisis** | El **portfolio** (¿qué necesita el catálogo hoy?) | El **episodio** (¿cómo maximizo su alcance?) |
| **Métricas** | CTR, retención, returning viewers → Postmortem vs predicción | Likes/shares/saves por plataforma → recomendaciones a Gabo/Leonardo |

**El solapamiento real que existe hoy:** ambos reclaman "análisis de métricas y aprendizaje". Mark ya lo hace en código (`analyze_performance`, `generate_conceptual_dashboard`, `mark.py` L46-131). Mr. You lo reclama en spec (Postmortem, Fase 5). **Y Talese también reclama el aprendizaje** (regla de oro "mide evolución"). Son **tres agentes peleando por el bucle de métricas.**

**Frontera corregida por Jota (2026-08-01) — la jerarquía real es de CANAL vs PRODUCTO:**

El error de mi primera lectura fue tratar a Mr. You como un gate editorial de HUMANOS. No lo es. La estructura correcta:

```
              CANAL (Jota Growth)  ──► Mr. You = Chief YouTube Officer / "gran jefe del canal"
                     │                 Dirección general: qué publicar, cuándo, con qué packaging.
        ┌────────────┴────────────┐    Lee las métricas GENERALES de todo el canal.
        ▼                         ▼
   🧪 LAB IA                  🎬 HUMANOS
   (detrás de cámara:         (producto editorial que VIVE DENTRO del canal;
    agentes, automatiza-       tiene su propia dirección editorial y sus
    ciones, productos)         propios agentes: Borges·Veritas·Gabo·Moore·Talese)
```

- **Mr. You — nivel CANAL.** Asesora la dirección general: qué conviene publicar, en qué orden, con qué packaging, cómo se equilibra Lab IA vs HUMANOS en el portfolio. **No interviene en la cocina editorial de HUMANOS** — eso ya lo gobierna la constitución editorial y sus agentes. Consume las métricas agregadas de todo el canal (Lab IA + HUMANOS) y devuelve dirección.
- **Talese — nivel PRODUCTO (HUMANOS).** Aprendizaje cualitativo del oficio editorial: delta de guion, patrones narrativos, `creator_learnings.json`. No mide vistas; mide evolución. Es el que sí toca la cocina de HUMANOS.
- **Mark — nivel EPISODIO.** Distribución: copies, descripciones y paquetes por plataforma de cada episodio. **Su segunda función, hoy inexistente, es capturar la data** de cada publicación y **entregársela a Mr. You**, que la agrega a nivel canal.

**El contrato de datos que falta construir:**

```
Mark (captura por episodio: CTR, retención, views, engagement por plataforma)
        │
        ▼
[capa de agregación de canal]  ◄── también recibe data de los videos de Lab IA
        │
        ▼
Mr. You (lee métricas GENERALES del canal → dirección: qué publicar después)
```

Hoy ese contrato no existe: Mark simula métricas (`random`), no hay capa de canal, y Mr. You no recibe nada. **Ese es el eslabón a construir**, no un gate de Greenlight dentro de HUMANOS.

Solapamiento residual a limpiar: Mark hoy también "recomienda" (`analyze_performance`, `mark.py` L46-95). Esa recomendación estratégica es competencia de Mr. You. Mark debe **capturar y entregar**, no aconsejar.

---

## 3. Componentes a Conservar (🛡️ lo que está bien diseñado)

1. **La doble compuerta de Veritas con umbral 80** (`run_humanos_mvp.py` L89, L222). Es el patrón de calidad más sólido del sistema: verifica investigación Y verifica el guion editado a mano. No lo toques.
2. **La pausa humana `script_pending_review`** (L111-113). Es exactamente la filosofía correcta: automatizás lo mecánico y le das a Jota el control de aprobación sobre lo creativo. Es tu ventaja sobre un pipeline 100% automático.
3. **La estructura de 10 carpetas por episodio + MEDIA_LIBRARY global** (`hermoso_core.py` L23-57). Convención de nombres consistente, trazable, escalable a 100 personajes. Muy bien.
4. **La arquitectura de conocimiento en 3 capas de Mr. You** (constitución / knowledge / channel-memory + prediction-log). El diseño es excelente; solo hay que ejecutarlo.
5. **La constitución editorial de HUMANOS** (`AGENTS.md` §4, `README.md`): "El Punto de No Retorno", "Anclas Mentales", "antes de cambiar el mundo, algo cambió a esta persona". Es IP real y diferenciada. Es el alma del proyecto.
6. **Talese como concepto** (mide evolución, no vanidad; propone con `status: PROPOSED`, el creador aprueba). El diseño de gobernanza del aprendizaje es correcto.
7. **Remotion como capa de branding** (compositions `HumanosBrandReveal`, `CharacterCard`, `Transition`, `EndCard`). Render parametrizado por JSON, branding centralizado. Bien.

---

## 4. Matriz de Deuda (técnica y de producto)

### 4.1 Bugs concretos (deuda técnica dura)

| # | Bug | Evidencia | Impacto |
|---|---|---|---|
| B1 | `generate_distribution_package` retorna `package_manifest`, variable **nunca definida** | `mark.py` L282 | **NameError al final de cada producción.** El paso de distribución revienta justo después de generar los copies. |
| B2 | Talese performance retro usa `self.learnings_file`, **nunca definido en `__init__`** | `talese.py` L176, 222, 224, 232 | **AttributeError.** El bucle de aprendizaje a 48h (el que promueve `creator_learnings`) no corre nunca. |
| B3 | Métricas del pipeline son **`random.randint(300000,800000)`** y `random.uniform` | `run_humanos_mvp.py` L322-327 | Todo el "aprendizaje" (Mark, Talese, dashboard) puede estar entrenándose con datos inventados. Contamina `metrics_history.json`. |
| B4 | Nombres de archivo **hard-coded a Jan Koum** en el checklist | `mark.py` L156 (`cover_jan_koum.png`), L166 (`voz_off_jan_koum.wav`), L276 | El checklist de calidad da Audio/Character Card = False para **cualquier otro personaje**. Falsos negativos sistemáticos. |
| B5 | **Schema de métricas inconsistente**: dashboard escribe `retentionRate3s` (camelCase), Mark lee `retention_rate_3s` (snake_case) | `editorial-dashboard-server.mjs` L534 vs `mark.py` L26; `talese.py` L394 lee camelCase | Los datos 48h reales no se cruzan bien con el historial. Silencioso, difícil de detectar. |
| B6 | Print de cierre apunta el dashboard a `scratch/Humanos/Characters` pero Mark escribe en `humanos/personajes` | `run_humanos_mvp.py` L395 vs `mark.py` L126 | Mensaje engañoso; residuo de la migración desde la copia scratch. |
| B7 | **Dos esquemas incompatibles de `pipeline_state.json`** conviviendo en disco | 8 episodios usan `{status, last_updated}` (escrito por `hermoso_core.update_status_local()`); 6 usan `{normalized_name, editorial_status, production_status, next_steps…}` **sin la clave `status`** | **6 de 14 episodios eran invisibles para cualquier vista basada en `status`** (guillermo rauch, lisa su, ricardo semler EP0002, sara blakely, tobias lutke, yvon chouinard). Detectado al ejecutar el agregador contra datos reales, no en la lectura estática. |

### 4.2 Deuda de arquitectura

- **A1 — Split-brain de persistencia.** Tenés un schema Supabase completo (4 tablas: `humanos_stories`, `humanos_scripts`, `humanos_episodes`, `humanos_metrics` + 5 vistas: `v_ready_for_gabo`, `v_ready_for_voice`, `v_publish_now`, `v_premium_reserve`, `v_series_candidates` — `supabase_schema.sql`). **Pero el pipeline persiste todo en JSON local por episodio.** El dashboard solo usa `humanos_stories` (server L358-361, 384). Las otras 3 tablas y las 5 vistas están **diseñadas y sin usar**. Dos fuentes de verdad (disco vs Supabase) que no se sincronizan.
- **A2 — Orquestador monolítico.** `run_humanos_mvp.py` hard-codea la secuencia de agentes, el lote fundacional (L364-383) y la lógica de gates en un solo script de 403 líneas. Agregar Mr. You o reordenar el flujo obliga a cirugía en el monolito. No hay un registro de pipeline declarativo.
- **A3 — n8n huérfano.** `n8n/workflows/borges_workflow.json` y `gabo_workflow.json` (basados en Tavily) son una automatización paralela que no está cableada al flujo Python+dashboard actual. `PROJECT_STATE.md` los menciona como "próximo paso" desde hace tiempo. Deuda muerta o bifurcación sin resolver.
- **A4 — CapCut packager huérfano.** `capcut_packager.py` (273 líneas) existe pero `run_humanos_mvp.py` **no lo importa**. El ensamblado de video queda 100% manual.
- **A5 — Duplicación de repos.** `scratch/humanos-mvp/` es una copia con último commit 2026-06-10 (vs 2026-07-27 del canónico). `borges.py` ya divergió (11.5KB en scratch vs 19.7KB en canónico). Riesgo de editar el archivo equivocado.

---

## 5. Fricciones en el Workflow Editorial (dónde pierde tiempo el creador)

1. **No hay decisión de entrada.** Hoy Jota mete un personaje al backlog y arranca investigación directo. **No existe el filtro de Mr. You**: ¿este personaje merece un episodio? ¿es Tier A/B/C? ¿cuál es el ángulo de packaging? Se produce primero y se piensa el título después → retrabajo en la salida.
2. **La edición del guion es el cuello de botella real.** El pipeline se detiene en `script_pending_review` (correcto), pero Jota edita en un `<textarea>` del panel sin ver lado a lado el borrador de Gabo, el dossier de Borges y los claims aprobados de Veritas. La info existe (el server la carga en `loadEpisodePayload` L182-204) pero está repartida en pestañas.
3. **El packaging (título + miniatura) no tiene dónde vivir.** No hay paso ni pantalla donde Jota genere/elija 2-3 hipótesis de título+thumbnail antes de renderizar. La spec de Mr. You lo exige (Greenlight punto 7); el sistema no lo ofrece.
4. **Las métricas 48h se cargan a mano** y no disparan nada automático (Talese performance está roto, B2). El bucle "publico → mido → aprendo → ajusto el próximo guion" está cortado en el último eslabón.
5. **Cinco pestañas, ningún tablero.** El panel obliga a saltar entre Backlog / Guiones / Finalizados / Publisher / Talese para entender el estado global. No hay una vista "¿qué tengo en vuelo y qué necesita mi atención hoy?".

---

## 6. Data que se genera pero NO se aprovecha

Esta es tu mina de oro sin explotar. Todo esto ya se produce y se tira:

1. **`asset_gaps.json` de Moore** (`run_humanos_mvp.py` L246). Moore cataloga exactamente qué asset visual falta por escena y sugiere la búsqueda. Es una **lista de compras de producción** que hoy solo se escribe en un reporte. Debería ser una cola de tareas accionable en el panel.
2. **El delta editorial de Talese** (`EPISODE_REVIEW.md`, `EPISODE_CHANGELOG.json`). Talese ya compara el borrador de Gabo contra tu edición final y extrae qué cambiaste y por qué. Es **oro para mejorar los prompts de Gabo**, pero hoy queda en un .md que nadie relee. No retroalimenta a Gabo.
3. **`creator_learnings.json`** (3 niveles OBSERVATION→SIGNAL→PATTERN). Tenés el andamiaje conceptual perfecto (LRN-001 sobre ganchos numéricos ya está APPROVED), pero solo hay aprendizajes de **1 episodio (EP0003)** y la promoción automática está rota (B2). El sistema aprende de N=1.
4. **Prediction Log de Mr. You.** Congela predicciones ANTES de publicar para medirlas después. Es la única forma honesta de saber si tu criterio de packaging funciona. Hoy tiene 1 entrada manual y ningún Postmortem que la cierre.
5. **Los claims con score de Veritas** (`fact_check.json`, `approved_claims.json`). Veritas asigna confianza A-F por afirmación. Ese scoring podría alimentar un "índice de solidez factual" por episodio y evitar re-verificar personajes ya investigados (vía Curie).
6. **Las vistas de Supabase** (`v_ready_for_gabo`, `v_publish_now`, `v_series_candidates`). Diseñadas para dar exactamente el estado del pipeline y candidatos a serie. Cero uso.
7. **Curie / TurboVec.** Toda la memoria semántica para detectar "esta historia se parece a la de X" y sugerir cruces narrativos está construida (`base_de_datos/curie_library/`) y prácticamente sin invocar en el flujo real.

---

## 7. Automatizaciones de Alto Impacto

Ordenadas por (impacto / esfuerzo):

1. **Arreglar B2 + B3 para cerrar el bucle de aprendizaje real.** Sin métricas reales y sin Talese performance, todo lo demás es teatro. Es el desbloqueo de mayor palanca.
2. **Cablear el Prediction Snapshot de Mr. You al momento de "Guardar y Producir".** Cuando Jota aprueba un guion, que se le pidan (o autogeneren) las 2-3 hipótesis de título+miniatura y se congele la predicción. Convierte a Mr. You de markdown a función.
3. **`asset_gaps.json` → cola de tareas en el panel.** Que los gaps de Moore aparezcan como checklist accionable ("faltan estos 4 planos, buscá esto") en lugar de un reporte muerto.
4. **Talese delta → mejora de prompt de Gabo.** Un job que agregue los `EPISODE_CHANGELOG.json` y proponga ajustes al `system_prompt` de Gabo cada N episodios. El sistema aprende a escribir mejor solo.
5. **Sincronización disco↔Supabase.** Un writer que empuje research/scripts/metrics a las tablas ya diseñadas, para que las vistas funcionen y el estado sea consultable sin leer carpetas.
6. **Auto-Postmortem de Mr. You a las 48-72h.** Cuando entran métricas reales, comparar contra el Prediction Snapshot y escribir el Postmortem (esperado vs real). Esto sí es aprendizaje acumulativo del canal.

---

## 8. Rediseño del Panel Editorial (UX/UI)

### 8.1 Diagnóstico del panel actual

`public/editorial-dashboard.html`: **un solo archivo de 1.440 líneas / 78 KB** con 5 pestañas planas (`tabBacklog`, `tabReview`, `tabFinalized`, `tabPublisher`, `tabTalese`). Problemas:
- **No hay overview.** Entrás y no sabés qué necesita tu atención. Tenés que abrir pestaña por pestaña.
- **El pipeline es lineal pero la UI no lo muestra.** No ves el episodio moviéndose por etapas (research → veritas → guion → producción → distribución).
- **Mr. You no tiene lugar.** No hay Greenlight ni packaging en la interfaz.
- **Las métricas están enterradas** en Publisher, desconectadas del aprendizaje de Talese.
- **Todo el HTML/CSS/JS en un archivo** — cada cambio es cirugía en un monolito de 1.440 líneas.

### 8.2 Propuesta: de "5 pestañas" a "1 sala de control + carril de episodio"

Estructura propuesta (mockup navegable entregado aparte, `panel-redesign-mockup.html`):

```
┌───────────────────────────────────────────────────────────────────────┐
│  HUMANOS · Sala de Control Editorial            [＋ Nuevo personaje]   │
├───────────────────────────────────────────────────────────────────────┤
│  HOY NECESITA TU ATENCIÓN                                             │
│  ● 2 guiones esperando tu edición   ● 1 episodio listo para publicar  │
│  ● 3 gaps de assets sin resolver    ● Talese propuso 2 aprendizajes   │
├───────────────────────────────────────────────────────────────────────┤
│  PIPELINE (kanban por etapa — cada tarjeta es un episodio)            │
│  IDEA → 🔵GREENLIGHT → RESEARCH → VERITAS → ✍️GUION → PRODUCCIÓN →     │
│         (Mr.You)                            (Jota)     (Moore/Leo)      │
│         → 📦DISTRIB (Mark) → 📊PUBLICADO (métricas+postmortem)         │
├───────────────────────────────────────────────────────────────────────┤
│  Al hacer clic en una tarjeta → CARRIL DE EPISODIO (vista única)      │
│  Todo el contexto del episodio en scroll vertical, no en pestañas:    │
│  Dossier(Borges) · Claims+score(Veritas) · Guion editable lado a lado │
│  con el borrador de Gabo · Storyboard+gaps(Moore) · Packaging(Mr.You) │
│  · Paquete DIST(Mark) · Métricas+Postmortem · Notas de Talese         │
└───────────────────────────────────────────────────────────────────────┘
```

Principios del rediseño:
1. **Un overview que responde "¿qué hago hoy?"** antes que cualquier lista.
2. **Kanban del pipeline** como metáfora central: ves cada historia moverse por las etapas reales que ya existen en `pipeline_state.json`.
3. **Carril de episodio de scroll único**: toda la data del episodio (que el server ya carga en `loadEpisodePayload`) en una sola vista, en el orden del flujo, sin saltar pestañas. La edición del guion muestra **Gabo vs tu versión lado a lado**.
4. **Greenlight de Mr. You como primera etapa visible**, con las hipótesis de packaging.
5. **Métricas + Postmortem + aprendizajes de Talese juntos** al final del carril, cerrando el bucle visualmente.
6. **Separar el monolito HTML** en módulos (aunque sea con includes) para que sea mantenible.

---

## 9. Complementariedad con Claude (sin duplicar a Antigravity)

Antigravity sigue siendo tu orquestador y tu entorno de desarrollo. Claude no lo reemplaza; **ocupa los huecos donde hoy no hay nadie ejecutando**:

1. **Ser el motor de razonamiento de Mr. You.** El Greenlight de 10 puntos, el Prediction Snapshot y el Postmortem son tareas de juicio editorial, no de pipeline. Claude puede ejecutarlas como paso invocado (igual que hoy se invoca a Gabo vía OpenRouter), sin tocar la orquestación de Antigravity.
2. **Cerrar el bucle Talese → Gabo.** Claude puede leer los `EPISODE_CHANGELOG.json` acumulados y proponer mejoras concretas al `system_prompt` de Gabo. Aprendizaje del oficio, no del contenido.
3. **Edición de video asistida.** Mencionaste que querés editar video conmigo. El camino natural: Claude consume `storyboard.json` + `editing_notes.md` + `asset_gaps.json` de Moore y genera el **timeline/EDL o el proyecto de CapCut/Remotion** — automatizando el paso ⑨ que hoy es 100% manual. Ahí `capcut_packager.py` (hoy huérfano) es el punto de enganche.
4. **Auditoría continua de calidad** (como esta): revisar coherencia spec↔código, detectar bugs como B1-B6, mantener la sincronización que `AGENTS.md` exige pero que ningún proceso valida.
5. **Verificación factual de segundo nivel** junto a Veritas para episodios Tier A.

Regla de no-duplicación: **Antigravity orquesta y coordina; Claude razona, audita y genera en los pasos de juicio.** Claude no debe convertirse en otro dispatcher.

---

## 10. Arquitectura Objetivo — El Sistema Operativo Editorial de HUMANOS

El norte no es "más agentes". Es **cerrar los tres bucles que hoy están abiertos**: entrada (Greenlight), ejecución (que lo escrito = lo que corre) y aprendizaje (métricas reales → mejor próximo episodio).

```
        ┌──────────────────── SALA DE CONTROL (Panel rediseñado) ────────────────────┐
        │                                                                            │
   IDEA ─► ① GREENLIGHT ─► ② PRE-PRODUCCIÓN ─► ③ PAUSA HUMANA ─► ④ PRODUCCIÓN ─► ⑤ DISTRIBUCIÓN ─► ⑥ APRENDIZAJE
        │   (Mr. You)        (Borges→Veritas→     (Jota edita       (Moore→Leo→      (Mark →           (Mr.You Postmortem +
        │   GO/REWORK/       Gabo)               guion +           CapCut/          publicar)         Talese learnings →
        │   NO-GO +                              packaging)        Remotion render)                   prompt de Gabo)
        │   Prediction                                                                                        │
        │   Snapshot                                                                                          │
        └──────────────────────────────────────────────────────────────────────────────────────────────────┘
                                    ▲                                                                          │
                                    └────────── el aprendizaje del paso ⑥ alimenta el criterio del paso ① ────┘
                                                        (BUCLE CERRADO)

   CAPA DE ESTADO ÚNICA:  Supabase (fuente de verdad) ←sync→ carpetas de episodio (artefactos)
   CAPA DE ORQUESTACIÓN:  Antigravity + pipeline declarativo (reemplaza el monolito run_humanos_mvp.py)
   CAPA DE RAZONAMIENTO:  Claude (Mr. You, Postmortem, Talese→Gabo, edición asistida)
   CAPA DE MEMORIA:       Curie/TurboVec (dedupe + cruces narrativos, hoy dormida)
```

Cambios estructurales para llegar ahí:
1. **Mr. You ejecutable** como paso ① real, con veredicto y Prediction Snapshot persistidos.
2. **Registro de pipeline declarativo** (una lista de etapas en config) que reemplace la secuencia hard-coded del monolito. Agregar/reordenar agentes sin cirugía.
3. **Supabase como fuente de verdad única** con sync bidireccional a los artefactos en disco. Apagar el split-brain.
4. **Métricas reales obligatorias** (nunca `random`) y bucle Postmortem+Talese cerrado y funcionando.
5. **Curie despierta**: dedupe de historias y sugerencia de cruces a Gabo antes de escribir.
6. **Un repo único** (matar `scratch/humanos-mvp`).

---

## 11. Clasificación de Recomendaciones

### 🟢 QUICK WINS (alto impacto, bajo esfuerzo — esta semana)
- **Arreglar B1** (`mark.py` L282, `package_manifest` indefinido). Una línea. Desbloquea la distribución.
- **Arreglar B2** (`talese.py`, definir `self.learnings_file` en `__init__`). Desbloquea el bucle de aprendizaje 48h.
- **Eliminar las métricas `random`** (B3, `run_humanos_mvp.py` L322-338). Reemplazar por "pendiente de datos reales" hasta que se carguen las 48h.
- **Unificar el schema de métricas** (B5): decidir camelCase o snake_case en un solo lado.
- **Borrar/archivar `scratch/humanos-mvp`** (A5) y las carpetas vacías del vault Obsidian (`100 - Proyectos/Antigravity-Projects`, `.../Humanos`) que sugieren una ubicación de proyecto que no existe. Organización impecable empieza acá.
- **Des-hardcodear los nombres Jan Koum** en el checklist de Mark (B4).

### 🟡 NEXT (estructural, próxima iteración — este mes)
- **Cablear Mr. You al "Guardar y Producir"**: Prediction Snapshot + hipótesis de packaging al aprobar guion.
- **`asset_gaps.json` → cola de tareas** accionable en el panel.
- **Rediseñar el panel** a Sala de Control + Carril de Episodio (mockup entregado).
- **Bucle Talese → prompt de Gabo** (aprendizaje del oficio).
- **Definir y congelar la frontera Mr. You / Mark / Talese** (§2.1) en las specs y en el código.
- **Sync disco↔Supabase** para activar las tablas y vistas ya diseñadas.

### 🔴 LATER (complejo / largo plazo)
- **Registro de pipeline declarativo** que reemplace el monolito `run_humanos_mvp.py`.
- **Edición de video asistida por Claude** (storyboard → EDL/CapCut/Remotion), reactivando `capcut_packager.py`.
- **Curie en producción**: dedupe semántico + sugerencia de cruces narrativos a Gabo.
- **Auto-Postmortem de portfolio** de Mr. You con datos reales de YouTube API.
- **Resolver n8n** (A3): integrarlo de verdad o retirarlo.

### 🛡️ NO TOCAR (sólido — protegido)
- La **doble compuerta de Veritas** (umbral 80, gates #1 y #2).
- La **pausa humana `script_pending_review`** (control de aprobación del creador).
- La **estructura de 10 carpetas + MEDIA_LIBRARY** y la convención de nombres.
- La **constitución editorial de HUMANOS** (Punto de No Retorno, Anclas Mentales) y la arquitectura de 3 capas de Mr. You.
- El rol de **Antigravity como orquestador** — se extiende, no se reemplaza.

---

## 12. Preguntas abiertas / límites de esta auditoría

- No leí línea por línea `borges.py`, `gabo.py`, `moore.py`, `veritas.py`, `leonardo.py`, `curie.py` (audité sus specs + cómo los invoca el orquestador). Si querés diagnóstico interno de alguno, decímelo.
- No encontré tus archivos `SOBRE MI/` (`sobre-mi.md`, `estilo-anti-ia.md`, `mi-empresa.md`) en ninguno de los 3 repos conectados. Usé `Manual de Marca`, `brand_bible` y `YouTube Vision & Strategy` como sustituto. Si existen en otra carpeta, apuntámela y reaudito la voz.
- La coherencia de `metrics_history.json` (EP0001-EP0004) sugiere que ya cargaste métricas reales a mano por el panel — pero conviven con el logging `random` del runner. HIPÓTESIS: el historial está parcialmente contaminado. Vale una limpieza antes de confiar en el aprendizaje.

---

---

## 13. REGISTRO DE EJECUCIÓN — 2026-08-01

Las secciones anteriores son el diagnóstico. Esto es lo que efectivamente **se implementó** después, con autorización explícita de Jota.

**Backup previo:** `claude_improvement/_BACKUP_20260801_092617/` (dashboard, server, mark, talese, runner).

### 13.1 Bugs cerrados

| Bug | Archivo | Cambio |
|---|---|---|
| B1 | `mark.py` | `return package_manifest` (indefinido) → `return True`. La distribución ya no crashea al final. |
| B2 | `talese.py` | Añadidos `self.lab_dir` y `self.learnings_file` en `__init__`. La retro de desempeño a 48h ya puede correr. |
| B3 | `run_humanos_mvp.py` | **Eliminadas las métricas `random`.** Nuevo `MarkAgent.register_episode()` crea la ficha con `metrics_status: "pending"`. `analyze_performance()` excluye las pendientes: el aprendizaje ya no se entrena con datos inventados. |
| B4 | `mark.py` | Nuevo `_find_cover()`. Portada, audio y character card se detectan por patrón, no por `cover_jan_koum.png`. El checklist deja de dar falsos negativos en todo personaje que no sea Jan Koum. |
| B5 | `talese.py`, `server` | Nuevo helper `_metric()` tolerante a camelCase y snake_case. El server ya no pisa `hook_text` con las notas. |
| B6 | `run_humanos_mvp.py` | Ruta del dashboard corregida; `import random` retirado. |
| **B7** | `server` | Lectura tolerante a los dos esquemas (`status \|\| editorial_status`). **Recupera 6 episodios que estaban invisibles.** Los archivos en disco no se migraron ni se tocaron. |

### 13.2 Dashboard V2 — capa aditiva

Implementado según `DASHBOARD_V2_SPEC.md`, respetando la **regla cero**:

- **Nav lateral permanente** que *orquesta* las vistas existentes llamando a sus funciones originales (`showBacklog`, `showReview`, `showFinalized`, `showPublisher`, `showTalese`). Las 5 pestañas horizontales siguen en el DOM con sus listeners intactos, solo ocultas por CSS.
- **Sala de Control** (Nivel 1): contadores de atención + Kanban de 7 etapas leídas de `pipeline_state.json`. Es Home; para volver al comportamiento previo basta llamar `showBacklog()`.
- **Carril de episodio** (Nivel 2): resúmenes con botones que enrutan a las vistas completas. No intenta ser el workspace.
- **Endpoint `/api/control-room`**: agregador de **solo lectura**. Degrada a cero si Supabase no responde.
- **Dirección de arte de Leonardo** aplicada (`brand_bible.md` §04-05): negro `#090909`, contenedores `#141414`, blanco, grises `#A7A7A7`/`#666666`, cian `#01C9C7` como único acento y logotipo. Montserrat Bold + Inter SemiBold. **Se eliminaron los 22 usos de violeta y los degradados decorativos** que contradecían la biblia de marca.

### 13.3 Verificación ejecutada

- Sintaxis: los 3 `.py`, el server y los 2 bloques JS del panel compilan.
- **Cero funciones perdidas** (41 → 47, solo altas). **Cero endpoints perdidos** (+1). **Cero vistas perdidas.**
- **Modales intactos y verificados uno a uno:** `createManualButton`, `drawerBackdrop`, `storyForm`, `drawerTitle`, `protagonistName`, `humanAngle`, `domainCategory`, `startButton`, `closeButton`, `saveProduceButton`, `metricsForm`, `actsContainer`, `socraticContainer`.
- **Supabase: cero cambios.** Las operaciones de escritura son byte-idénticas al backup. Cero `DELETE`/`DROP`/`TRUNCATE` en el código. `supabase_schema.sql` sin tocar.
- **Datos en disco intactos:** `metrics_history.json` (4 entradas) y `creator_learnings.json` (4 aprendizajes) sin modificar.
- Prueba en vivo contra datos reales: 14/14 episodios ubicados correctamente, 29 asset gaps y scores de Veritas reales; los 4 endpoints originales responden 200.

### 13.4 Pendiente / advertencias

- **`metrics_history.json` (EP0001-EP0004) no fue tocado**, pero puede contener las métricas simuladas por el `random` anterior. No lo limpié porque es tu dato: decidí no borrar nada. Recomiendo revisarlas y marcarlas o borrarlas a mano antes de confiar en el aprendizaje.
- **`scratch/humanos-mvp` (copia muerta) NO se borró.** Eliminar un repo es destructivo y queda a tu decisión explícita.
- **Los 6 episodios con esquema antiguo** ahora se leen bien, pero conviene decidir si se normalizan a un solo esquema (tarea de migración, no de lectura).

---

*Diagnóstico: 2026-08-01. Ejecución: 2026-08-01, con backup y verificación de no-pérdida.*
