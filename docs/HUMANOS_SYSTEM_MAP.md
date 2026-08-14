# HUMANOS — Mapa de sistema (handoff canónico)

Documento operativo para continuar HUMANOS **sin el contexto de una conversación previa**.

Cualquier agente (Codex, Claude, Cursor, Antigravity u otro) debe leer, en este orden:

1. Este archivo: `docs/HUMANOS_SYSTEM_MAP.md`
2. `AGENTS.md` (roster y lagunas)
3. El working tree (`git status -sb`), **sin** borrar ni hacer clean

Fecha de redacción: 2026-08-13 (America/Bogota).
Rama al redactar: `migration/preserve-2026-08-10`
Commit de referencia (roster en AGENTS.md): `44a087b`
Este archivo se añade en un commit posterior en la misma rama.

Si un hecho no está comprobado en disco o en Git, se marca **REQUIERE REVISIÓN**. No se inventa.

---

## 1. Identidad del proyecto

**HUMANOS** es una biblioteca de microdramas reales sobre personas extraordinarias que cambiaron el mundo.

- **Slogan:** *En época de IA, un homenaje a lo humano.*
- **Regla de oro:** la empresa es el escenario; la persona es la historia.
- **Dirección editorial:** no biografías ni imperios. El instante psicológico de no retorno, anclas mentales (escenas dibujables) y cambio de identidad. No es canal de curiosidades, motivación barata, frases, negocios planos ni Wikipedia recortada.
- **Rol de Jota:** voz del canal y director creativo. Aprueba. Los agentes reducen carga mecánica; no sustituyen esa aprobación.
- **Qué problema resuelve el sistema de agentes:** investigar, verificar, guionar, humanizar, visualizar, producir, publicar y aprender con trazabilidad, sin que Jota tenga que rehacer el pipeline a mano en cada episodio.

Repositorio de producción (única ruta de código viva):

`C:\Users\Jota Ochoa\Antigravity\02_Projects\humanos`

Queda prohibido operar en `C:\Users\Jota Ochoa\.gemini\antigravity\scratch\humanos-mvp` (carpeta histórica / muerta).

---

## 2. Fuentes de verdad

| Superficie | Qué es | Canónica para |
|---|---|---|
| GitHub `jotaochoa07/humanos` | Copia versionada del sistema | Historia, handoff, backup remoto |
| Rama `migration/preserve-2026-08-10` | Rama de preservación activa | Trabajo actual. **No es `main`.** |
| Commit `44a087b` | Roster documental en `AGENTS.md` + snapshot previo `4919aea` | Punto de partida de este mapa |
| Disco local (ruta de arriba) | Working tree vivo | Código, episodios, untracked |
| JotaOS | Vault / sistema personal | Acceso y organización; **no** es el Git de HUMANOS |
| Antigravity | Entorno de trabajo (IDE / runtime de Jota) | Ejecución local. **No es fuente canónica.** |
| Scratch histórico | Residuo de Antigravity | Archivo muerto. No escribir. |

### GitHub

- URL: https://github.com/jotaochoa07/humanos
- Rama de trabajo: `migration/preserve-2026-08-10`
- `main` **no** se modifica ni se le hace merge desde esta preservación hasta decisión explícita de Jota.
- Commits de esta línea (orden): preservación selectiva `4919aea` → alineación de roster `44a087b` → este mapa (commit siguiente).

### Local

- Repo vivo: `C:\Users\Jota Ochoa\Antigravity\02_Projects\humanos`
- Está físicamente bajo el árbol de Antigravity porque ahí se desarrolló. Eso **no** convierte a Antigravity en fuente de verdad. El remoto GitHub + esta rama sí.

### JotaOS

Dos junctions de Windows apuntan al repo vivo (verificado 2026-08-13):

- `C:\JotaOS\100 - Proyectos\Humanos`
- `C:\JotaOS\projects\Humanos`

Ambos deben seguir apuntando a `C:\Users\Jota Ochoa\Antigravity\02_Projects\humanos`. **No recrear ni borrar junctions** sin procedimiento (usar `rmdir` + `mklink /J`; nunca `Remove-Item -Recurse` sobre un junction).

Backup verificado del rescate:

`C:\JotaOS\backups\HUMANOS-rescue-2026-08-14\`

Contiene copia del scratch (`00_scratch_Humanos`), del repo (`01_repo_humanos`, sin `node_modules`/`.next`, con `.git` y `.env` **privado**) y de dos markdown únicos del scratch (`02_unicos_scratch`).

### Scratch histórico

- Intacta: `C:\Users\Jota Ochoa\.gemini\antigravity\scratch\Humanos`
- También existe: `...\scratch\humanos-mvp` — **no tocar**
- No es el repo. No commitear desde ahí. No usarla como cwd.

### Qué está fuera de GitHub

Ver sección 7. Resumen: videos de Camilo (`Manual_assets`), proyectos Audacity (`.aup4` y temps), generados Kling, `05_VIDEO` pesado, logs, backups de Claude, `.env` y tokens. Permanecen en disco local y/o en el backup de JotaOS. **No copiarlos al repo.**

---

## 3. Arquitectura del sistema

JotaOS (junctions) apunta al repo vivo en disco, que se versiona en GitHub en esta rama.

Piezas:

- `AGENTS.md`: roster, precedencia, contradicciones, decisiones pendientes de agentes
- Código runtime (`gabo.py`, `humanizer_agent.py`, `veritas.py`, `run_humanos_mvp.py`, etc.): lo que se ejecuta hoy
- `agents/<nombre>/`: fichas de voz/ética (`personality.md`, `SOUL.md`) y `prompts/system_prompt.md`
- `marca.py` + `agents/_MARCA/`: lente de marca inyectable; no es un episodio
- Scripts `.bat`, `capturar_canal.py`, `youtube_oauth.mjs`: operación de canal (tokens fuera del repo)
- `editorial-dashboard-server.mjs`: panel editorial local
- `personajes/<Nombre>/EP####_.../`: unidades de episodio
- Assets multimedia: intros livianos en Git; bruto de Camilo/Kling/video fuera
- `tests/`: incluye `tests/test_recovery_pipeline.py`
- JotaOS: punto de entrada humano; junctions, no un segundo Git de HUMANOS

### Precedencia (obligatoria)

código runtime  >  AGENTS.md  >  fichas y prompts antiguos

Esta precedencia no autoriza cambios automáticos. Si código y ficha discrepan:

1. Registrar la contradicción (ya está en `AGENTS.md` sección 9).
2. Ejecutar el runtime reciente.
3. No revertir el `.py` para cuadrar una ficha de julio.
4. Pedir aprobación a Jota antes de cambiar arquitectura, roster o `main`.

Ejemplo comprobado: `gabo.py` y `humanizer_agent.py` (agosto 2026) contienen Gate 3B / Camilo; las fichas en `agents/gabo/` son de julio y más genéricas. Manda el runtime.

---

## 4. Roster de agentes

Estados: ACTIVO = hay runtime cableado. ACTIVO CON REVISIÓN = runtime o ficha real, con deuda. DOCUMENTAL = ficha sin `.py`. EXPERIMENTAL = variante paralela. REQUIERE DECISIÓN = Jota debe elegir alcance. Antigravity y Codex son entornos, no agentes.

| Agente | Función | Archivo principal | Estado | Dependencias | Decisiones pendientes |
|---|---|---|---|---|---|
| Borges | Investigación / dossier / claims | `borges.py` | ACTIVO | OpenRouter; salida a Veritas | — |
| Veritas | Fact-check, scores, fuentes A–F | `veritas.py` | ACTIVO | Claims de Borges; `agents/veritas/SOUL.md` | — |
| Gabo | Guion de microdrama | `gabo.py` | ACTIVO CON REVISIÓN | Claims aprobados; en recovery, creative_lock + evidencia humana | ¿Gate 3B es del agente o del episodio? ¿Actualizar ficha? |
| Humanizer | Humaniza guion sin añadir claims | `humanizer_agent.py` | ACTIVO CON REVISIÓN | Salida de Gabo; mismo contexto Gate 3B | ¿Carpeta `agents/humanizer/`? Gate 3B (igual que Gabo) |
| Curie | Memoria editorial / índice / RAG | `curie.py` | ACTIVO | Ficha `agents/curie/`; RAG turbovec según ficha | Confirmar si turbovec sigue cableado (REQUIERE REVISIÓN) |
| Moore | Storyboard / dirección visual | `moore.py` | ACTIVO CON REVISIÓN | Tras guion; ficha `agents/moore/` | Relación con `moore_largo.py` |
| Talese | Aprendizaje editorial | `talese.py` | ACTIVO | `agents/talese/SOUL.md`; evalúa episodios | — |
| Hermoso | Orquestación del loop | `hermoso_core.py` | ACTIVO | Estado, logs, I/O de episodio | Telegram/n8n: descrito en ficha, no re-verificado aquí |
| Leonardo | Marca visual / brand bible | `leonardo.py` | ACTIVO CON REVISIÓN | `agents/leonardo/brand_bible.md` | Encaje con `_MARCA` y Moore |
| Mark | Distribución (YT, IG, X, …) | `mark.py` | ACTIVO CON REVISIÓN | Skills en `agents/mark/skills/` | ¿Crear `personality.md`? |
| Mr. You | Doctrina / tesis de canal | `mr_you.py` | ACTIVO CON REVISIÓN | `agents/mr-you/doctrina_canal.md`; `marca.py` | Alineación con `_MARCA` |
| Dali | Ficha visual | `agents/dali/personality.md` | DOCUMENTAL | Prompt en `agents/dali/prompts/` | ¿Runtime `dali.py` o se queda ficha? |
| BuilderJota | Ficha de construcción | `agents/builderjota/personality.md` | REQUIERE DECISIÓN | Solo ficha + prompt; no hay `.py` en raíz | ¿HUMANOS o agente transversal JotaOS? |
| _MARCA | Constitución de marca (lente) | `agents/_MARCA/constitucion_marca.md` | ACTIVO CON REVISIÓN | Cargada por `marca.py` | Relación con Mr. You |

Variante experimental (no es un agente aparte): `moore_largo.py` junto a `moore.py`. No se declara canónica.

No son agentes: Antigravity, Codex, Claude Code, Cursor. Son plataformas.

---

## 5. Flujo editorial actual

Flujo estándar observado (no organigrama de mando):

investigación (Borges) → verificación (Veritas) → guion (Gabo) → humanización (Humanizer) → storyboard/assets (Moore, Leonardo, branding) → producción (Remotion / locución / edición; en parte manual) → revisión (Jota + panel `editorial-dashboard-server.mjs`) → publicación (Mark, cuando hay pieza) → aprendizaje (Talese, Curie)

Hermoso orquesta estado (`pipeline_state.json`) y logs. `_MARCA` / `marca.py` pueden anteponerse al system prompt; no son un paso de episodio.

### Gate 3B / recovery (excepción documentada, no regla general)

Comprobado en `run_humanos_mvp.py`, `gabo.py`, `humanizer_agent.py` y en `personajes/Camilo_Cifuentes/EP0001_Camilo_Cifuentes/`:

- Fuente canónica de research: `01_RESEARCH_RECOVERY` (no `01_RESEARCH` legado).
- Agentes permitidos en ese despacho: Gabo, Humanizer.
- Agentes prohibidos en ese despacho: Borges, Veritas, Moore.
- Gabo escribe `script_short` como partitura audiovisual, VO Jota máximo 80 palabras.
- Humanizer debe conservar esa partitura, no convertirla en prosa.
- Estado observado de Camilo: `script_pending_review` (archivo trackeado `pipeline_state.json`).

No se documentan CapCut, Audacity o Kling como etapas automáticas del pipeline: son trabajo local, no agentes.

---

## 6. Estado de los proyectos y episodios

Los números EP0001 no son únicos en el árbol (hay varios EP0001 y muchos EP0002). Tratar el identificador como `personajes/<Nombre>/EP####_...`, no como número global. REQUIERE REVISIÓN si se quiere una numeración canónica.

### Camilo Cifuentes — EP0001_Camilo_Cifuentes

- Estado: `script_pending_review`. Modo recovery / Gate 3B.
- En GitHub: research, `01_RESEARCH_RECOVERY`, scripts (revisiones gate 3a/3b), `episode_config.json`, `pipeline_state.json`, `human_editorial_provenance.json`, branding spec, character card, `earthquake_asset_manifest.json`, checklist y links en la raíz.
- Solo local: `Manual_assets` mp4 (uno ~148 MB), `Audio/*.aup4` (~450 MB) + wav + shm/wal, `agent_runs.log`.
- Riesgos: material primario no está en Git. No subir mp4/aup4.

### Ferruccio Lamborghini — EP0004_Ferruccio_Lamborghini

- Estado: `storyboard_done`. Locutado e informe de cierre versionados en `4919aea`.
- En GitHub: research (locutado y `archivo/`), scripts long, storyboard locutado, stills FER, character cards, `asset_registry.json`, `INFORME_CIERRE_EP0004.html`, learning v3 vs locutado, branding spec.
- Solo local: `04_IMAGES/kling/`, `05_VIDEO/`, `06_AUDIO/*.aup4`, `.bak` de claims.
- Riesgos: Kling y video de archivo no versionados. `run_ferruccio_pilot.py` ahora exige env_boot / no publicar fallbacks como si fueran Gabo.

### Dashboard editorial

- Archivo: `editorial-dashboard-server.mjs` (en Git).
- Sabe de `recovery_ready` / `input_mode=recovery` (cambio en `4919aea`).
- Cómo se lanza día a día (puerto, npm): REQUIERE REVISIÓN.

### Intros y branding

En Git (livianos, menos de 2 MB): `assets/branding/video/HUMANOS_Intro_*.mp4`, `src/components/HumanosLandscapeIntro.tsx`, `HumanosPortraitIntro.tsx`, `src/Root.tsx`, `public/humanos/intro-heartbeat.mp3`.

Audio bajo `assets/branding/audio/` y `MEDIA_LIBRARY/BRANDING/audio/` está en `.gitignore`.

### Otros episodios (pipeline_state.json trackeado)

| Personaje / carpeta | EP | status | Nota |
|---|---|---|---|
| Jan_Koum | EP0001 | script_pending_review | Piloto histórico |
| Margaret_Hamilton | EP0001 | idea | |
| Ehud_Shabtai | EP0002 | storyboard_done | Piloto histórico |
| hedy_lamarr | EP0002 | storyboard_done | |
| Adidas_vs_Puma | EP0003 | storyboard_done | |
| james_dyson | EP0003 | storyboard_done | |
| ricardo_semler | EP0004 | script_pending_review | Convive con EP0002 vacío de status |
| guillermo_rauch, lisa_su, ricardo_semler EP0002, sara_blakely, tobias_lutke, yvon_chouinard | EP0002 | status vacío | REQUIERE REVISIÓN |
| Lummia | raíz, sin EP | status vacío | REQUIERE REVISIÓN |

No se afirma el contenido interno más allá del pipeline_state leído.

---

## 7. Custodia de assets excluidos

No copiar ninguno de estos al repositorio. GitHub rechaza más de 100 MB. El `.gitignore` cubre `.env*`, `*_tokens.json`, `*.aup4`, shm/wal, `_LAB/*.log`, `node_modules`, `.next`.

| Asset o categoría | Ubicación | Por qué está fuera de GitHub | Riesgo | Backup existente | Acción futura |
|---|---|---|---|---|---|
| Videos Camilo Manual_assets | `personajes/Camilo_Cifuentes/EP0001_.../Manual_assets/` | Tamaño (hasta ~148 MB) | Pérdida del bruto | Backup JotaOS HUMANOS-rescue-2026-08-14 (copia anterior a algunos untracked: REQUIERE REVISIÓN) | Disco externo / DVC / LFS, no Git normal |
| Audacity Camilo | `.../Audio/*.aup4` (~450 MB) + shm/wal | DAW enorme | VO no versionado | Idem | Ignorar temps; archivar aup4 fuera |
| Audacity Lamborghini | `EP0004/.../06_AUDIO/*.aup4` | Igual | Locución no en Git | Idem | Igual |
| Kling | `EP0004/.../04_IMAGES/kling/` | Generado, pesado | Perder takes | REQUIERE REVISIÓN | Decidir stills a FER |
| `05_VIDEO` | `EP0004/.../05_VIDEO/` | ogv/webm pesados | Material de corte | REQUIERE REVISIÓN | Custodia fuera de Git |
| Logs agent_runs.log, `_LAB/*.log` | episodio y `_LAB/` | Reconstruibles | Ruido / posible dato sensible | No versionar | Dejar untracked |
| `_LAB/*.json` métricas/mapa YT | `_LAB/` | Operacional | Perder métricas locales | No | Export si Jota las necesita |
| Backups Claude `claude_improvement/_BACKUP_*` | raíz | Incluye `_BACKUP_env_*.bak` (secreto) | Fuga si se hace git add | Disco | Nunca git add |
| `.env` y `.env*` | raíz | Secretos | Fuga | Privado en `01_repo_humanos` del backup JotaOS | gitignored |
| Tokens YouTube | `_LAB/youtube_tokens.json` | OAuth | Fuga | Local | `youtube_oauth.mjs` sí está en Git; el secret no |
| `node_modules`, `.next`, `__pycache__` | varias | Caches | Hinchazón | Regenerables | Ignorar |
| Scratch histórico | `.gemini/antigravity/scratch/Humanos` | No es el repo | Confusión de cwd | `00_scratch_Humanos` | Solo lectura |

---

## 8. Cómo continuar el trabajo (runbook)

Para el próximo agente, en este orden:

1. Rama: `git branch --show-current` debe ser `migration/preserve-2026-08-10`. Si no, parar.
2. No checkout a `main`. No merge a `main`. No force push. No `git reset --hard`. No `git clean`. No `git checkout --` que tire trabajo.
3. Estado: `git status -sb` y `git log -1`. Comparar con `origin/migration/preserve-2026-08-10`.
4. Leer `docs/HUMANOS_SYSTEM_MAP.md` (este archivo) y `AGENTS.md`.
5. Working tree: habrá untracked (mp4, aup4, kling, `_LAB`, backups Claude). Es esperado. No hacer `git add .`.
6. No tocar: scratch histórico, junctions JotaOS, `humanos-mvp`, SAI WATER, `.env`, tokens.
7. No subir: secretos, `node_modules`, caches, logs, `.aup4`, shm/wal, mp4 de Camilo.
8. Código productivo: no modificarlo en una tarea solo docs. Si hay que cambiar runtime, pedir aprobación y un commit aparte, con diff.
9. Arquitectura / roster / `main`: pedir aprobación a Jota antes.
10. Tests seguros: `python tests/test_recovery_pipeline.py` con PYTHONPATH = raíz del repo. No limpiar el árbol para que pasen.
11. YouTube: usar `youtube_oauth.mjs`; no copiar `client_secret` al repo.
12. Si algo no está en este mapa ni en `AGENTS.md`, marcar REQUIERE REVISIÓN y preguntar. No rellenar el hueco con una hipótesis.

---

## 9. Decisiones pendientes

No resueltas a propósito:

1. ¿Dali debe tener runtime (`dali.py`) o permanecer ficha visual?
2. ¿Mark necesita `agents/mark/personality.md`?
3. ¿`moore_largo.py` reemplaza a `moore.py`, convive, o se archiva?
4. Relación Mr. You / `_MARCA` (¿subordinación, fusión, mandatos distintos?).
5. ¿BuilderJota es agente de HUMANOS o transversal (JotaOS / infra)?
6. ¿Gate 3B pertenece al agente (Gabo/Humanizer) o al episodio (Camilo / recovery)?
7. ¿Cuándo (si alguna vez en el corto plazo) mergear esta rama a `main`?
8. Numeración global de episodios (hoy hay varios EP0001/EP0002).
9. Custodia a largo plazo de `Manual_assets` de Camilo y de Kling/`05_VIDEO`.
10. ¿Humanizer gana carpeta `agents/humanizer/`?

Hasta que Jota decida: ejecutar el código reciente; no pisarlo con fichas viejas; no fusionar a `main`.

---

## 10. Próxima fase recomendada

Secuencia prudente, en este orden:

1. Estabilizar `migration/preserve-2026-08-10` como rama de verdad (este mapa + `AGENTS.md` + snapshot `4919aea`). No más commits mezclando docs con mp4.
2. JotaOS: confirmar que los dos junctions siguen al repo vivo; no reescribir el vault entero.
3. Auditar agentes pendientes (Dali, Mark personality, Moore largo, Mr. You/_MARCA, BuilderJota) — una decisión por commit, documental primero.
4. Decidir assets externos (Camilo video, Audacity, Kling): dónde viven si no es GitHub.
5. Probar el sistema en el repo vivo: recovery Camilo (ya `script_pending_review`), dashboard, tests de recovery, un piloto antiguo en `storyboard_done` sin reescribirlo.
6. Solo después evaluar merge a `main`. No es el siguiente paso. Es el último de esta lista.

Fuera de alcance: SAI WATER, scratch, junctions, `humanos-mvp`, cualquier force push.

---

## Apéndice — archivos de arranque

| Archivo | Para qué |
|---|---|
| `docs/HUMANOS_SYSTEM_MAP.md` | Este mapa |
| `AGENTS.md` | Roster y contradicciones |
| `run_humanos_mvp.py` | Pipeline / recovery |
| `recovery_pipeline.py` | Preflight recovery |
| `editorial-dashboard-server.mjs` | Panel |
| `gabo.py` / `humanizer_agent.py` | Gate 3B |
| `marca.py` | Lente `_MARCA` |
| `tests/test_recovery_pipeline.py` | Test de recovery |
| `.gitignore` | Bloquea `.env*`, tokens, aup4, logs `_LAB` |

Handoff 2026-08-13. No altera código, episodios, AGENTS.md, main, junctions ni scratch.
