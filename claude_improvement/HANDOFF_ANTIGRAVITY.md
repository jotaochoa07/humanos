# HANDOFF → ANTIGRAVITY

**De:** Claude (sesión de auditoría + ejecución)
**Para:** Antigravity (orquestador del ecosistema)
**Fecha:** 2026-08-01
**Repo:** `C:\Users\Jota Ochoa\Antigravity\02_Projects\humanos`
**Commit base (sin tocar):** `feat(dali): update system prompt with airbnb js standards and motion budget` — 2026-07-27

> **Estado: cambios aplicados en working tree, SIN commitear.** Antigravity decide si commitea, revierte o ajusta.

---

## 1. Resumen en una línea

Se auditó el sistema completo (JotaOS + pipeline + panel), se corrigieron **7 bugs** que rompían silenciosamente la distribución y el aprendizaje, y se añadió una **capa V2 aditiva** al panel editorial (nav lateral + Sala de Control + carril de episodio) sin eliminar ninguna vista, función, dato ni listener previo.

---

## 2. Archivos modificados (6)

| Archivo | Δ reales | Naturaleza del cambio |
|---|---|---|
| `mark.py` | +108 / −15 | Bugs B1, B4, B5 + nuevo `register_episode()` y `_find_cover()` |
| `talese.py` | +148 / −5 | Bug B2 + helper `_metric()` tolerante de esquema |
| `run_humanos_mvp.py` | +70 / −14 | Bugs B3, B6 — eliminadas métricas simuladas |
| `editorial-dashboard-server.mjs` | +196 | Endpoint `/api/control-room` (solo lectura) + bug B7 |
| `public/editorial-dashboard.html` | +719 | Capa V2 + dirección de arte de Leonardo |
| `Abrir HUMANOS Dashboard.bat` | +46 / −6 | Race condition: abría el navegador antes del servidor |

**Nota para Antigravity:** el `--stat` de git infla `talese.py` y `mark.py` porque reancla hunks al insertar métodos nuevos entre existentes. **No hay funciones duplicadas** (verificado por conteo de `def`). Los cambios reales son los de la columna Δ.

## 3. Archivos creados

```
claude_improvement/
├── CLAUDE_AUDIT.md              ← informe de auditoría, 13 secciones (§13 = registro de ejecución)
├── DASHBOARD_V2_SPEC.md         ← contrato de arquitectura del panel (3 niveles + regla cero)
├── HANDOFF_ANTIGRAVITY.md       ← este documento
├── arquitectura-humanos.mermaid ← diagrama del flujo end-to-end real
├── panel-redesign-mockup.html   ← mockup navegable del rediseño
└── _BACKUP_20260801_092617/     ← backup previo a TODO cambio
    ├── editorial-dashboard.html
    ├── editorial-dashboard-server.mjs
    ├── mark.py
    ├── run_humanos_mvp.py
    └── talese.py
```

**Reversión total:** copiar los 5 archivos del backup encima de sus originales. El `.bat` no está en el backup — su versión previa está en el §7 de este documento.

---

## 4. Bugs corregidos

| ID | Archivo | Antes | Ahora |
|---|---|---|---|
| **B1** | `mark.py` | `return package_manifest` — variable indefinida → `NameError` al final de cada producción | `return True` |
| **B2** | `talese.py` | `self.learnings_file` usado en `run_performance_retro()` pero nunca definido → `AttributeError`. La retro de 48h **nunca corrió** | Definidos `self.lab_dir` y `self.learnings_file` en `__init__` |
| **B3** | `run_humanos_mvp.py` | Métricas inventadas con `random.randint(300000,800000)` contaminando `metrics_history.json` | Nuevo `MarkAgent.register_episode()` → ficha con `metrics_status: "pending"`. `analyze_performance()` **excluye** las pendientes |
| **B4** | `mark.py` | Rutas fijas `cover_jan_koum.png` / `voz_off_jan_koum.wav` → checklist daba falso negativo en todo personaje ≠ Jan Koum | Nuevo `_find_cover()` + detección por extensión en `06_AUDIO/` |
| **B5** | `talese.py`, server | `retentionRate3s` (camelCase, dashboard) vs `retention_rate_3s` (snake_case, Mark) | Helper `_metric()` lee ambos. El server ya no pisa `hook_text` con las notas |
| **B6** | `run_humanos_mvp.py` | Print apuntaba a `scratch/Humanos/Characters` (ruta muerta) | Ruta corregida; `import random` retirado |
| **B7** | server | **Dos esquemas de `pipeline_state.json` conviviendo.** 6 de 14 episodios sin clave `status` → **invisibles** para el panel | Lectura tolerante `status \|\| editorial_status`. **Sin migrar archivos.** Recupera los 6 |

### Detalle de B7 (importante para Antigravity)

Coexisten dos formatos en disco:

```jsonc
// A) escrito por hermoso_core.update_status_local()  — 8 episodios
{ "status": "script_pending_review", "last_updated": "2026-07-04 08:12:05" }

// B) fichas previas al runner                        — 6 episodios
{ "normalized_name": "lisa_su", "editorial_status": "idea",
  "production_status": "pending", "created_by": "hermoso", "next_steps": [...] }
```

Afectados por el esquema B: `guillermo_rauch/EP0002`, `lisa_su/EP0002`, `ricardo_semler/EP0002`, `sara_blakely/EP0002`, `tobias_lutke/EP0002`, `yvon_chouinard/EP0002`.

**Se resolvió solo en lectura.** Queda pendiente decidir si se normalizan a un esquema único (tarea de migración de datos, no de código).

---

## 5. Panel Editorial V2

### 5.1 Arquitectura implementada

```
NIVEL 1  Sala de Control      ← nuevo Home. Operar el presente.
NIVEL 2  Carril de episodio   ← inspeccionar y enrutar (NO es el workspace).
NIVEL 3  Vistas existentes    ← trabajar en profundidad. Intactas.
```

### 5.2 Cómo se garantizó que fuera aditivo

- La nav lateral **no reimplementa nada**: llama a las funciones originales `showBacklog()`, `showReview()`, `showFinalized()`, `showPublisher()`, `showTalese()`.
- Las 5 pestañas horizontales **siguen en el DOM con sus listeners intactos**; solo se ocultan con `body.v2 .tabs { display:none }`.
- Para volver al comportamiento anterior: quitar la clase `v2` del `<body>` y cambiar el arranque `loadStories().then(showControlRoom)` por `loadStories()`.

### 5.3 Elementos nuevos

**JS (6 funciones nuevas, 0 eliminadas — 41 → 47):**
`navGo()`, `showControlRoom()`, `loadControlRoom()`, `crCard()`, `openEpisodeRail()`, `closeEpisodeRail()`

**Endpoint nuevo (1, ninguno eliminado):**
`GET /api/control-room` — agregador de **solo lectura**. Devuelve `{episodes[], counters{}, greenlight[], supabaseOk, supabaseError}`.

Funciones de apoyo en el server: `collectControlRoom()`, `mapStatusToStage()`, `handleControlRoom()`.

**Mapeo status → columna del Kanban** (`mapStatusToStage`):

| status en disco | columna | agente responsable |
|---|---|---|
| `idea` | Greenlight | Mr. You |
| `research_pending` · `research_in_progress` · `needs_research` | Research | Borges |
| `verification_in_progress` · `research_done` | Veritas | Veritas |
| `script_pending_review` | Guion | Gabo → Jota |
| `storyboard_done` (sin copies) | Producción | Moore · Leonardo |
| `storyboard_done` (con copies en `11_DIST/`) | Distribución | Mark |
| `published` · `publicado` | Publicado | Talese · Mr. You |
| *desconocido* | Greenlight + warning en consola | — |

**Orden del carril de episodio:** Mr. You → Borges → Veritas → Gabo/Jota → Moore → Mark → Talese.
Mr. You abre porque decide a **nivel canal**; la cocina editorial de HUMANOS empieza en Borges.

### 5.4 Dirección de arte (Leonardo)

Aplicada `C:\JotaOS\agents\leonardo\brand_bible.md` §04-05 vía variables CSS:

| Token | Valor | Uso |
|---|---|---|
| `--bg` | `#090909` | Fondo (negro profundo) |
| `--panel` | `#141414` | Contenedores |
| `--text` | `#FFFFFF` | Texto principal |
| `--muted` / `--muted-deep` | `#A7A7A7` / `#666666` | Secundario y metadatos |
| `--accent` | `#01C9C7` | **Cian de marca.** Acento y logotipo HUMANOS |

Tipografías: Montserrat (600-900) para títulos, Inter (400-700) para UI. Cargadas desde Google Fonts con fallback local.
**Se eliminaron 22 usos de violeta y todos los degradados decorativos** que contradecían la biblia de marca.

---

## 6. Corrección del lanzador

**Causa raíz del "Failed to fetch"** que reportó Jota — bug preexistente, no del rediseño:

```bat
start "" "http://127.0.0.1:3100/"   REM abría el navegador PRIMERO
npm run editorial                    REM arrancaba el servidor DESPUÉS
```

Ahora el `.bat` hace polling del puerto 3100 (máx. 40 intentos) y **solo abre el navegador cuando el servidor responde**. El servidor corre en su propia ventana (`cmd /k`) para que sus logs queden visibles. Si no arranca, imprime las causas probables en vez de fallar en silencio.

**Adicional — resiliencia:** si Supabase no responde, el panel ya no muere. Muestra los episodios desde disco y un aviso con botón de reintentar. Verificado con Supabase caído: 14/14 episodios servidos.

---

## 7. Versión previa del `.bat` (para revertir)

```bat
@echo off
cd /d "C:\Users\Jota Ochoa\Antigravity\02_Projects\humanos"
set PORT=3100
start "" "http://127.0.0.1:3100/"
npm run editorial
pause
```

---

## 8. Garantías verificadas

| Verificación | Resultado |
|---|---|
| Sintaxis Python (`mark`, `talese`, `run_humanos_mvp`) | ✅ compilan |
| Sintaxis Node (server) y JS del panel | ✅ `node --check` OK |
| Funciones JS perdidas | ✅ **0** (41 → 47) |
| Endpoints perdidos | ✅ **0** (+1 nuevo) |
| Vistas perdidas | ✅ **0** (las 5 intactas) |
| Modales / acciones | ✅ verificados uno a uno (ver §9) |
| Escrituras a Supabase | ✅ **byte-idénticas al backup** |
| `DELETE` / `DROP` / `TRUNCATE` en el código | ✅ **0** |
| `supabase_schema.sql` | ✅ sin tocar (`md5 957c2766`) |
| `metrics_history.json` | ✅ 4 entradas, sin modificar |
| `_LAB/creator_learnings.json` | ✅ 4 aprendizajes, sin modificar |
| Prueba en vivo con datos reales | ✅ 14/14 episodios ubicados, 29 asset gaps, scores de Veritas reales |
| Endpoints originales | ✅ los 4 responden HTTP 200 |

## 9. Elementos de UI protegidos y verificados

`createManualButton` · `drawerBackdrop` · `storyForm` · `drawerTitle` · `protagonistName` · `humanAngle` · `domainCategory` · `startButton` · `closeButton` · `refreshButton` · `saveProduceButton` · `openSelectedButton` · `openSelectedFinalizedButton` · `metricsForm` · `actsContainer` · `socraticContainer`

Vistas: `backlogView` · `reviewView` · `finalizedView` · `publisherView` · `taleseView`

---

## 10. Pendiente — decisiones de Jota, NO ejecutadas

Estas quedaron sin hacer **a propósito** porque son destructivas o requieren su criterio:

1. **`metrics_history.json` (EP0001-EP0004)** puede contener las métricas simuladas por el `random` anterior. No se borró nada. Requiere revisión manual antes de confiar en el aprendizaje.
2. **`C:\Users\Jota Ochoa\.gemini\antigravity\scratch\humanos-mvp\`** es una copia muerta (último commit 2026-06-10 vs 2026-07-27 del canónico; `borges.py` divergido 11.5KB → 19.7KB). **No se borró.**
3. **Carpetas vacías en el vault de Obsidian**: `C:\JotaOS\100 - Proyectos\Antigravity-Projects\` y `C:\JotaOS\100 - Proyectos\Humanos\` son placeholders vacíos que sugieren una ubicación de proyecto inexistente.
4. **Normalizar los dos esquemas de `pipeline_state.json`** (B7) — hoy resuelto solo en lectura.
5. **Commitear** — nada fue commiteado.

## 11. Deuda de arquitectura pendiente (del informe, sin ejecutar)

- **Mr. You sigue sin ejecución.** Existe solo como markdown en `C:\JotaOS\agents\mr-you\`. El eslabón a construir es el **contrato de datos**: Mark captura por episodio → capa de agregación de canal (que también recibe Lab IA) → Mr. You lee métricas generales. Ver `CLAUDE_AUDIT.md` §2.1.
- **Split-brain de persistencia.** Supabase tiene 4 tablas + 5 vistas; el pipeline persiste en JSON local y el panel solo usa `humanos_stories`.
- **`run_humanos_mvp.py` sigue siendo monolítico** (secuencia de agentes hard-coded).
- **`capcut_packager.py` sigue huérfano** (existe, no se invoca).
- **Curie sigue dormido** (solo cuenta assets; su RAG no se usa).
- **n8n huérfano** (`borges_workflow.json`, `gabo_workflow.json` no cableados).

---

## 12. Contexto de entorno

- **gentle-ai instalado** y verificado en `C:\Users\Jota Ochoa\.gemini\skills\` (catálogo SDD completo: `sdd-init`, `sdd-explore`, `sdd-design`, `sdd-spec`, `sdd-tasks`, `sdd-apply`, `sdd-verify`, `sdd-archive`, `skill-registry`, `judgment-day`). Persona y reglas en `C:\Users\Jota Ochoa\.gemini\GEMINI.md`.
- **Excepción de idioma:** la regla de gentle-ai "los artefactos técnicos van en inglés" **no aplica a este repo** — HUMANOS ya está en español y el propio contrato exceptúa proyectos que usan otro idioma ("the existing project clearly uses another language and you are extending it"). Todo el código nuevo y sus comentarios están en español, coherente con el resto.
- **Arranque:** `Abrir HUMANOS Dashboard.bat` o `npm run editorial` → `http://127.0.0.1:3100/`
- **Stack:** Node HTTP server + Python (agentes, OpenRouter) + Remotion (render) + Supabase (estado de historias).

---

*Handoff generado 2026-08-01. Nada commiteado. Backup íntegro en `claude_improvement/_BACKUP_20260801_092617/`.*
