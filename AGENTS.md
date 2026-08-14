# MANUAL DE AGENTES (AGENTS.md)

Este documento describe el sistema editorial **HUMANOS** tal como existe en el repositorio vivo.

No inventa jerarquías. No declara canónico un rol que todavía requiere decisión humana. Las fichas, los prompts y el código pueden divergir; cuando lo hacen, este archivo registra el hecho en lugar de resolverlo.

Repositorio de producción: `C:\Users\Jota Ochoa\Antigravity\02_Projects\humanos`
Rama de preservación documentada: `migration/preserve-2026-08-10`

Queda prohibido a cualquier agente leer, escribir, compilar o ejecutar scripts en la carpeta histórica `C:\Users\Jota Ochoa\.gemini\antigravity\scratch\humanos-mvp`. Esa ruta no es el sistema vivo.

---

## 1. Propósito del sistema HUMANOS

HUMANOS es una biblioteca de microdramas reales sobre personas extraordinarias que cambiaron el mundo.

- Slogan: *"En época de IA, un homenaje a lo humano."*
- Regla de oro: la empresa es el escenario. La persona es la historia.
- Voz y dirección creativa: Jota. Los agentes reducen carga operativa; no sustituyen la aprobación humana.

### Núcleo editorial

1. **El punto de no retorno.** No se cuentan biografías ni imperios. Se cuenta el instante psicológico del que ya no hubo regreso.
2. **Anclas mentales.** Las personas recuerdan escenas, no fechas. Cada episodio orbita una escena dibujable de memoria.
3. **Cambio de identidad.** Antes de cambiar el mundo, algo cambió a esta persona.

Estructura narrativa de referencia: Estado estable → escena de ruptura → cambio de identidad → consecuencia.

HUMANOS no es un canal de curiosidades, motivación barata, frases inspiracionales, negocios planos ni biografías de Wikipedia.

### Convenciones visuales (Remotion)

Nunca: neones exagerados, glitches, efectos gamer, transiciones chillonas o plantillas TikTok genéricas.

Siempre: documental premium, movimiento lento, Ken Burns, fondos oscuros, tipografías fuertes, minimalismo.

Documentos de apoyo (no sustituyen este roster): `production_bible.md`, `thumbnail_bible.md`, `agents/leonardo/brand_bible.md`.

### Reglamento operativo vigente

1. No inventar información. Si un dato no tiene fuente verificada, Veritas lo marca `UNVERIFIED` o `REJECTED`.
2. Priorizar el factor humano sobre el corporativo.
3. Optimizar el tiempo del fundador.
4. En el flujo estándar, ningún guion pasa a Gabo sin auditoría de Veritas. El modo recovery (Camilo / Gate 3B) es una excepción documentada, no una anulación silenciosa de esa regla.

---

## 2. Principio de precedencia entre código, fichas y documentos

Orden de lectura cuando hay conflicto:

1. **Código de runtime en la raíz** (`gabo.py`, `humanizer_agent.py`, `veritas.py`, etc.): describe lo que el sistema ejecuta hoy.
2. **Este archivo (`AGENTS.md`)**: describe el roster, el flujo observado y las lagunas conocidas.
3. **Fichas y prompts en `agents/`** (`personality.md`, `SOUL.md`, `prompts/system_prompt.md`): describen voz, ética y consigna. Son fuente de carácter, no de pipeline.
4. **Documentos de marca** (`agents/_MARCA/constitucion_marca.md`, `marca.py`): lente transversal. Su relación con Mr. You no está cerrada.

Reglas:

- Las fichas antiguas **no** sobrescriben automáticamente el comportamiento más reciente del código.
- Un nombre de archivo no basta para declarar un agente canónico.
- Gabo y Humanizer contienen lineamientos más recientes (Gate 3B y episodio Camilo) que algunas fichas de julio. Mientras no se unifiquen, el runtime manda en ejecución y la ficha se trata como documentación de voz.
- Si una ficha y un `.py` discrepan, se registra aquí como contradicción. No se "arregla" el código desde este documento.

---

## 3. Roster completo de agentes

| Agente | Función | Archivo principal | Estado | Observaciones |
|---|---|---|---|---|
| Borges | Investigación y dossier editorial | `borges.py` | ACTIVO | Ficha: `agents/borges/`. Decisión → conflicto → consecuencias. |
| Veritas | Auditoría de evidencia y fact-check | `veritas.py` | ACTIVO | Ficha y `SOUL.md` en `agents/veritas/`. Clasifica fuentes A–F. |
| Gabo | Arquitectura de guion (microdrama) | `gabo.py` | ACTIVO CON REVISIÓN | Ficha en `agents/gabo/`. El `.py` (ago 2026) incluye Gate 3B / Camilo; las fichas de julio no. |
| Humanizer | Humanización del guion ya escrito | `humanizer_agent.py` | ACTIVO CON REVISIÓN | Runtime activo. No tiene carpeta `agents/humanizer/`. Gate 3B también vive aquí. |
| Curie | Memoria editorial / índice / RAG | `curie.py` | ACTIVO | Ficha en `agents/curie/`. Integrada con RAG local (turbovec), según ficha previa. |
| Moore | Dirección visual / storyboard | `moore.py` | ACTIVO CON REVISIÓN | Existe variante `moore_largo.py`. No se declara cuál es canónica. Ficha: `agents/moore/`. |
| Talese | Aprendizaje editorial longitudinal | `talese.py` | ACTIVO | `SOUL.md` en `agents/talese/`. Mide delta editorial y anclas mentales. |
| Hermoso | Orquestación del loop operativo | `hermoso_core.py` | ACTIVO | Ficha en `agents/hermoso/`. Telegram / n8n según documentación previa. |
| Leonardo | Dirección de marca visual / brand bible | `leonardo.py` | ACTIVO CON REVISIÓN | Ficha, prompt y `agents/leonardo/brand_bible.md`. No figuraba en el AGENTS.md anterior. |
| Mark | Distribución (YouTube, IG, X, etc.) | `mark.py` | ACTIVO CON REVISIÓN | Skills en `agents/mark/skills/`. **No existe** `agents/mark/personality.md`. |
| Mr. You | Tesis / doctrina de canal | `mr_you.py` | ACTIVO CON REVISIÓN | Ficha, prompt y `agents/mr-you/doctrina_canal.md`. Relación con `_MARCA` pendiente de alineación. |
| Dali | Ficha visual | `agents/dali/personality.md` | DOCUMENTAL | Prompt en `agents/dali/prompts/system_prompt.md`. **No existe** `dali.py`. Alcance por confirmar. |
| BuilderJota | Ficha de infraestructura / construcción | `agents/builderjota/personality.md` | REQUIERE DECISIÓN | Prompt en `agents/builderjota/prompts/system_prompt.md`. No hay runtime `.py` en la raíz. ¿HUMANOS o agente transversal? |
| _MARCA | Constitución de marca (lente transversal) | `agents/_MARCA/constitucion_marca.md` | ACTIVO CON REVISIÓN | Cargada por `marca.py`. No es un agente de episodio. Relación con Mr. You pendiente. |

Humanizer, Dali, Mark (sin personality), Moore (dos runtimes), Mr. You / `_MARCA` y BuilderJota quedan explícitos para que el roster deje de omitirlos.

---

## 4. Flujo editorial actual

Flujo **estándar** observado en código y documentos (no es un organigrama de autoridad):

1. Borges investiga y arma dossier / claims.
2. Veritas audita evidencia. Nada de esto es narración todavía.
3. Gabo escribe el guion a partir de claims aprobados.
4. Humanizer reescribe el texto para voz humana, sin añadir claims.
5. Moore produce storyboard / guía visual cuando el episodio lo pide.
6. Talese evalúa el episodio contra el manifiesto (aprendizaje, no producción).
7. Curie registra memoria para no repetir ganchos ni arcos.
8. Hermoso orquesta estado, logs y handoff operativo.
9. Mark publica cuando hay pieza lista (rol de distribución; ficha incompleta).
10. Leonardo / `_MARCA` informan criterio visual y de marca; no sustituyen a Moore.

Excepción **documentada**, no generalizada: el modo recovery (Gate 3B, episodio Camilo) despacha Gabo + Humanizer sobre `01_RESEARCH_RECOVERY` y **prohíbe** en ese despacho a Borges, Veritas y Moore. Esa excepción vive en el código (`run_humanos_mvp.py`, `gabo.py`, `humanizer_agent.py`). No reescribe el flujo estándar para el resto de episodios.

Mr. You y Dali no forman parte de ese pipeline de episodio. BuilderJota tampoco.

---

## 5. Agentes activos

Ejecutan o están cableados en el runtime actual:

- Borges (`borges.py`)
- Veritas (`veritas.py`)
- Gabo (`gabo.py`)
- Humanizer (`humanizer_agent.py`)
- Curie (`curie.py`)
- Moore (`moore.py`; la variante larga no se da por activa en su lugar)
- Talese (`talese.py`)
- Hermoso (`hermoso_core.py`)
- Leonardo (`leonardo.py`)
- Mark (`mark.py`)
- Mr. You (`mr_you.py`)
- `_MARCA` vía `marca.py` (lente, no episodio)

"Activo" aquí significa: hay código o carga real en el repo vivo. No significa "canónico" ni "sin deuda documental".

---

## 6. Agentes que requieren revisión

- **Gabo y Humanizer:** el código tiene Gate 3B / Camilo; las fichas de `agents/gabo/` y la ausencia de ficha de Humanizer no lo reflejan.
- **Moore:** dos runtimes. Ver sección 7.
- **Leonardo:** existe runtime y brand bible, pero el AGENTS.md anterior no lo listaba.
- **Mark:** runtime y skills; falta `personality.md`.
- **Mr. You:** runtime y doctrina de canal; tensión con `_MARCA`.
- **Dali:** solo ficha visual. Ver sección 10.
- **BuilderJota:** solo ficha. Ver sección 10.
- **`_MARCA`:** constitución cargada por `marca.py`; alineación con Mr. You pendiente.

---

## 7. Variantes experimentales

| Variante | Relación | Estado | Qué no se decide aquí |
|---|---|---|---|
| `moore_largo.py` | Paralela a `moore.py` | EXPERIMENTAL | Si reemplaza, convive o se retira `moore.py`. |

No hay otras variantes de runtime con nombre propio identificadas en la raíz para el resto del roster. Los `prompts/system_prompt.md` no se tratan como forks experimentales; son consignas de ficha.

---

## 8. Roles de plataforma

**Antigravity** y **Codex** (y, por extensión, otros entornos como Claude Code o Cursor) son **plataformas / entornos de ejecución**. No son agentes del sistema editorial HUMANOS.

No tienen ficha en `agents/`. No entran al flujo Borges → Veritas → Gabo. No se listan en el roster.

El AGENTS.md anterior los colocaba en un "Nivel Desarrollo". Esa clasificación se retira: el desarrollo ocurre *en* esas plataformas; el sistema editorial son los agentes de la tabla.

---

## 9. Contradicciones conocidas

1. El AGENTS.md anterior omitía a Humanizer, Leonardo, Mark, Mr. You, Dali, BuilderJota y `_MARCA`.
2. Gabo/Humanizer en código (Gate 3B, partitura audiovisual, límite de VO, Camilo) vs fichas de julio, más genéricas.
3. `marca.py` documenta que Mr. You operaba una tesis de canal que la estrategia de marca v1.0 contradice. `_MARCA` existe precisamente para unificar el criterio; la unificación no está cerrada.
4. Moore: `moore.py` y `moore_largo.py` coexisten sin nota de precedencia en código.
5. Dali tiene personalidad y prompt, no runtime.
6. Mark tiene runtime y skills, no `personality.md`.
7. BuilderJota tiene ficha de "construcción" mientras Antigravity/Codex cubren infra como plataformas: el solape no está resuelto.
8. Talese aparece en el manifiesto editorial histórico, pero no estaba en el "Nivel Editorial" del organigrama anterior.

---

## 10. Decisiones pendientes

Estas decisiones **no** se resuelven en este documento:

1. ¿Dali debe convertirse en agente ejecutable (`dali.py`) o permanecer como ficha visual?
2. ¿Mark necesita `agents/mark/personality.md`?
3. ¿`moore_largo.py` reemplaza a `moore.py`, convive, o es un experimento a archivar?
4. ¿Mr. You queda subordinado a `_MARCA`, se fusionan, o conservan mandatos distintos?
5. ¿BuilderJota permanece dentro de HUMANOS o se documenta como agente transversal (JotaOS / infra)?
6. ¿Humanizer debe ganar carpeta `agents/humanizer/` (ficha + prompt) para igualar al resto del roster?
7. ¿Las fichas de Gabo deben actualizarse para Gate 3B, o Gate 3B es una excepción de episodio y no de agente?

Hasta que Jota decida, el código reciente se ejecuta; las fichas no lo pisan.

---

## 11. Regla para actualizar agentes

1. Cambiar un agente es un cambio documental **y**, si aplica, de runtime. Nunca solo de nombre.
2. Antes de editar una ficha: leer el `.py` correspondiente y anotar si el comportamiento real ya divergió.
3. Si el código es más reciente que la ficha (caso Gabo / Humanizer / Gate 3B), actualizar primero este roster y, en un commit aparte, la ficha. No revertir el `.py` para "cuadrar" la ficha.
4. No añadir un agente al flujo editorial sin archivo de runtime, salvo que se marque DOCUMENTAL.
5. No borrar fichas ni variantes (`moore_largo.py`, `agents/dali/`) para "limpiar". Se archivan o se deciden en un commit explícito.
6. Secretos, `.env`, tokens, logs y caches no entran en este documento ni en commits de agentes.
7. Este archivo se actualiza cuando cambia el roster, el flujo o una decisión de la sección 10. No se usa para publicar episodios.

---

## Apéndice A. Roadmap y KPIs (sin cambio de fondo)

Conservado del documento anterior, como contexto de producto, no como lista de agentes.

Roadmap de 12 meses (histórico): validación de formato → automatización editorial → biblioteca humana → archivo humano → sistema de IP.

KPIs: retención a 3 segundos, shares, saves, likes, completion rate.

---

*Última alineación documental: 2026-08-14. Commit de roster: `docs(agents): align HUMANOS roster and known architecture gaps`. No altera código, assets ni episodios.*
