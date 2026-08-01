# DASHBOARD V2 — Spec de Arquitectura de Navegación (HUMANOS)

**Estado:** propuesta congelada, sin implementar.
**Autor:** Jota Ochoa (arquitectura) + Claude (spec y validación).
**Fecha:** 2026-08-01
**Regla que gobierna todo este documento:**

> ## 🛡️ REGLA CERO — LA V2 ES ADITIVA, NO DESTRUCTIVA
> Nada se elimina. Primero se añade una capa superior de navegación y operación **sobre** las capacidades existentes. Solo después de varios episodios usando la V2 se decide si alguna vista vieja sobra.
> Esto protege: la base histórica, los logs, los copies completos y la capacidad de entrar al detalle.

---

## 1. Qué estaba mal en mi propuesta original

Autocrítica antes del diseño, porque el error importa:

| Fallo del mockup v1 | Por qué falla | Corrección |
|---|---|---|
| El Kanban pretendía ser la vista de todo | Con 50/100/500 historias, un Kanban es inmanejable | El Kanban muestra **solo lo que está en vuelo**. El backlog sigue siendo vista tipo base de datos. |
| El rail de 760px como lugar donde hacés todo | `width:min(760px,94vw)` no sirve para editar guion largo, comparar documentos extensos, analizar 30 claims o trabajar 7 copies | El rail **inspecciona y enruta**. Para trabajar → "Abrir workspace completo". |
| "7 paquetes generados en `11_DIST/`" como sustituto del copy | Un contador no reemplaza el copy real de YouTube/IG/TikTok | En Sala de Control es resumen; el clic lleva a Publisher con el copy completo. |
| Reemplazar las 5 pestañas | Perdías base histórica, logs y detalle | Las pestañas se conservan y se **orquestan** desde arriba. |

---

## 2. Arquitectura de 3 niveles

```
                  HUMANOS

           ┌─────────────────┐
           │ SALA DE CONTROL │   NIVEL 1 — Portfolio
           │ ¿Qué pasa hoy?  │   Presente. Operar.
           └────────┬────────┘
                    │ clic en una tarjeta (ej. Lamborghini)
           ┌────────▼────────┐
           │ CARRIL EPISODIO │   NIVEL 2 — Episode Workspace
           │ Estado completo │   Contexto. Entender. Resúmenes + acciones.
           └────────┬────────┘
                    │ "Ver completo →"
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    BORGES        MARK         TALESE       NIVEL 3 — Deep Dive / Database
   Dossier       Copies      Learnings      Trabajar. Vistas actuales conservadas.
```

**Cada nivel responde una sola pregunta.** Si un nivel intenta responder dos, está mal diseñado.

| Nivel | Pregunta que responde | NO hace |
|---|---|---|
| 1 · Sala de Control | ¿Qué está ocurriendo ahora y dónde tengo que intervenir? | No es la base de datos. |
| 2 · Carril de episodio | ¿En qué estado está esta historia y qué falta? | No es donde se edita/trabaja. |
| 3 · Vistas especializadas | Búsqueda, filtrado, histórico, edición real, copies completos | No es el resumen operativo. |

---

## 3. Navegación: de 5 tabs horizontales a lateral permanente

```
HUMANOS
────────────────────────────────────────

◉ SALA DE CONTROL          ← nuevo Home

BIBLIOTECA
  Historias                ← hoy: Backlog
  Guiones                  ← hoy: Guiones pendientes
  Episodios                ← hoy: Finalizados

DISTRIBUCIÓN
  Copies & Publicación     ← hoy: Publisher

INTELIGENCIA
  Aprendizaje              ← hoy: Talese
  Métricas                 ← nuevo (Mark captura → Mr. You lee)

────────────────────────────────────────
```

**Renombrado propuesto** (para que deje de sentirse como "un frontend para unos scripts" y se sienta software editorial):

| Actual (técnico) | V2 (editorial) | Contenido |
|---|---|---|
| `tabBacklog` | **Historias** | Base completa, buscable y filtrable. Todas las historias, publicadas o no. |
| `tabReview` | **Guiones** | Drafts, versiones, aprobados. |
| `tabFinalized` | **Episodios** | Producciones terminadas e histórico. |
| `tabPublisher` | **Distribución** | Todos los copies de Mark por plataforma + estado de publicación. |
| `tabTalese` | **Aprendizaje** | Talese + (futuro) Postmortems de Mr. You. |
| — | **Métricas** | Nueva. Captura de Mark → agregado de canal para Mr. You. |

El renombrado es **cosmético y reversible**; no toca los IDs internos en la primera iteración.

---

## 4. Nivel 1 — Sala de Control (nuevo Home)

Dos bloques, en este orden:

### 4.1 Hoy necesita tu atención
```
2 guiones esperando edición · 1 Greenlight · 3 assets pendientes · 2 aprendizajes
```
Cada contador es un enlace directo a la acción. Se calcula del estado que **ya existe**:
- guiones esperando → `pipeline_state.json.status === "script_pending_review"`
- assets pendientes → `03_STORYBOARD/asset_gaps.json`
- aprendizajes → entradas `status: "PROPOSED"` en `_LAB/creator_learnings.json`
- greenlight → historias en `humanos_stories` con `editorial_status` de entrada

### 4.2 Pipeline actual (Kanban)
```
Greenlight → Research → Veritas → Guion → Producción → Distribución → Publicado
```
- Usa las **etapas reales** de `pipeline_state.json`. Cero estados inventados.
- Muestra **solo episodios en vuelo**. Los publicados con más de N días salen del tablero y viven en *Episodios*.
- Clic en tarjeta → Nivel 2.

**Lo que esta vista NO hace:** no lista las 500 historias del backlog. Eso es *Historias*.

---

## 5. Nivel 2 — Carril de episodio (resúmenes + acciones)

Regla de diseño: **cada bloque muestra un resumen de una línea y un botón que lleva al Nivel 3.** Nada de contenido extenso embebido.

| Agente | Resumen en el carril | Acción |
|---|---|---|
| Borges | Dossier resumido (3 líneas) | `[Ver dossier completo]` |
| Veritas | Score 86 · 9/11 claims aprobados | `[Ver auditoría]` |
| Gabo | Draft vs tu versión (diff resumido) | `[Abrir editor]` |
| Mr. You | Estado de packaging / dirección de canal | `[Ver criterio]` |
| Moore | 3 asset gaps | `[Abrir producción]` |
| Mark | 7 copies generados | `[Ver copies]` |
| Talese | 2 aprendizajes propuestos | `[Ver historial]` |

Ancho del rail: sigue siendo panel lateral (~760px) **porque ya no pretende ser el workspace**. Cada `[Ver/Abrir …]` abre la vista completa a ancho total.

---

## 6. Nivel 3 — Vistas especializadas (las actuales, conservadas)

Se conservan **tal cual funcionan hoy**, con dos cambios mínimos:
1. Reciben un parámetro de episodio para abrirse ya filtradas (ej. Distribución abre directo en Lamborghini).
2. Un breadcrumb para volver: `Sala de Control › Lamborghini › Distribución`.

Requisitos que NO se negocian en estas vistas:
- **Historias** conserva búsqueda, filtro, orden y estados — es tu base de datos.
- **Distribución** muestra el **copy completo** de YouTube / Instagram / TikTok / Facebook / X / LinkedIn / Newsletter. Nunca un contador.
- **Aprendizaje** conserva el log completo de `creator_learnings.json` y `CREATOR_CHANGELOG.md`.

---

## 7. Plan de implementación (aditivo, por fases)

| Fase | Qué se hace | Riesgo | Reversible |
|---|---|---|---|
| **F1** | Añadir nav lateral + Sala de Control como nueva vista. Las 5 pestañas siguen intactas y accesibles. | Bajo — solo se añade | Sí, borrando una vista |
| **F2** | Kanban leyendo `pipeline_state.json` + contadores de atención. Sin escribir nada. | Bajo — solo lectura | Sí |
| **F3** | Carril de episodio con resúmenes + botones que enrutan a las vistas existentes. | Medio — routing | Sí |
| **F4** | Renombrado editorial de las vistas (cosmético). | Bajo | Sí |
| **F5** | Vista Métricas nueva (Mark captura → agregado canal → Mr. You). Requiere primero arreglar el bug de métricas `random`. | Medio | — |
| **F6** | *Solo después de varios episodios en uso:* evaluar si alguna pestaña vieja sobra. | — | — |

**Precondición técnica para F1:** `public/editorial-dashboard.html` son 1.440 líneas / 78 KB en un solo archivo. Antes de añadir una vista más conviene separarlo en módulos, o cada cambio siguiente será cirugía sobre un monolito.

---

## 8. Criterios de aceptación de la V2

1. Puedo entrar y saber en 5 segundos qué necesita mi atención hoy.
2. Puedo ver una historia moverse por el pipeline sin abrir 5 pestañas.
3. **No perdí** ni una sola capacidad actual: base histórica, logs, copies completos, filtros del backlog.
4. Desde el carril llego al copy real de cualquier plataforma en 1 clic.
5. Ninguna vista intenta responder dos preguntas a la vez.

---

*Sin implementar. Este documento es el contrato antes de tocar una línea de `editorial-dashboard.html`.*
