# Flujo n8n — Borges (Investigación)

## Descripción

Workflow independiente para que Borges investigue un personaje y entregue la Ficha Narrativa completa en Supabase.

**Se activa:** Manualmente por Jota, o automáticamente cuando un personaje cambia a estado `investigar` en Supabase.

---

## Arquitectura del flujo

```
[Trigger]
    ↓
[Supabase — Leer personaje]
    ↓
[Tavily — Búsqueda 1: Origen y contexto]
    ↓
[Tavily — Búsqueda 2: Conflicto y fracasos]
    ↓
[Tavily — Búsqueda 3: Decisión y riesgo]
    ↓
[Tavily — Búsqueda 4: Legado e impacto actual]
    ↓
[OpenAI — Sintetizar en Ficha Narrativa (15 ítems)]
    ↓
[Supabase — Guardar ficha → estado: "borges_listo"]
    ↓
[Hermoso — Telegram: "Ficha lista: [Nombre]. ¿Apruebo?"]
```

---

## Nodo 1: Trigger

**Tipo:** Manual (por ahora) o Postgres Trigger en el futuro.

**Configuración manual:**
- Activar cuando Jota quiera investigar un personaje
- Input esperado: `nombre` o `id` del personaje en Supabase

---

## Nodo 2: Supabase — Leer personaje

**Tipo:** Postgres
**Query:**
```sql
SELECT id, protagonist_name, known_for, primary_hook, domain_category, source_notes
FROM humanos_stories
WHERE editorial_status = 'researching'
ORDER BY updated_at ASC
LIMIT 1;
```

---

## Nodos 3-6: Tavily — 4 búsquedas paralelas

**Nodo 3 — Origen:**
```
Query: "[NOMBRE] early life childhood family background origin poverty
```

**Nodo 4 — Conflicto:**
```
Query: "[NOMBRE] failures obstacles rejection struggles difficulties
```

**Nodo 5 — Decisión:**
```
Query: "[NOMBRE] key decision turning point risk bet everything
```

**Nodo 6 — Legado:**
```
Query: "[NOMBRE] legacy impact why important today 2024 2025
```

---

## Nodo 7: OpenAI — Sintetizar Ficha Narrativa

**Modelo:** GPT-4o o equivalente
**System Prompt:** [Pegar el system_prompt.md de Borges v4]

**User Prompt:**
```
Personaje: {{$node["Supabase"].json["protagonist_name"]}}
Historia breve conocida: {{$node["Supabase"].json["known_for"]}}

Investigación recopilada:
ORIGEN: {{$node["Tavily_Origen"].json["results"]}}
CONFLICTO: {{$node["Tavily_Conflicto"].json["results"]}}
DECISIÓN: {{$node["Tavily_Decision"].json["results"]}}
LEGADO: {{$node["Tavily_Legado"].json["results"]}}

Con base en esta información, entrega la Ficha Narrativa completa con los 15 ítems.
```

---

## Nodo 8: Supabase — Guardar ficha

**Tipo:** Postgres
**Operation:** Update
**Query:**
```sql
UPDATE humanos_stories
SET
  editorial_status = 'researched',
  one_line_story = '{{one_line_story}}',
  human_before_success = '{{human_before_success}}',
  central_conflict = '{{central_conflict}}',
  key_decision = '{{key_decision}}',
  main_risk = '{{main_risk}}',
  transformation = '{{transformation}}',
  legacy_today = '{{legacy_today}}',
  hook_family = '{{hook_family}}',
  primary_hook = '{{primary_hook}}',
  alternative_hooks = '{{alternative_hooks}}'::jsonb,
  closing_angle = '{{closing_angle}}',
  story_level = '{{story_level}}',
  publish_timing = '{{publish_timing}}',
  series_potential = {{series_potential}},
  estimated_episode_count = {{estimated_episode_count}},
  suggested_episode_titles = '{{suggested_episode_titles}}'::jsonb,
  narrative_score = {{narrative_score}},
  familiarity_score = {{familiarity_score}},
  surprise_score = {{surprise_score}},
  emotional_score = {{emotional_score}},
  research_confidence = {{research_confidence}},
  production_difficulty = {{production_difficulty}},
  strategic_value = {{strategic_value}},
  priority_score = {{priority_score}},
  series_score = {{series_score}},
  fact_check_status = '{{fact_check_status}}',
  fact_check_notes = '{{fact_check_notes}}',
  source_notes = '{{source_notes}}'
WHERE id = '{{id}}';
```

---

## Nodo 9: Hermoso — Notificación Telegram

**Tipo:** HTTP Request a Hermes AI Agent / Telegram Bot

**Mensaje:**
```
🔍 BORGES TERMINÓ

Personaje: [NOMBRE]
Nivel: [1/2/3/4]
Recomendación: [Publicar ahora / Guardar para serie / Premium / Verificar]

⚠️ Advertencias: [Si hay alguna]

¿Aprobás la ficha para pasarla a Gabo?
Responde: /aprobar [id] o /rechazar [id]
```

---

## Tiempo estimado por personaje

- Búsquedas Tavily: ~10-15 segundos
- Síntesis OpenAI: ~20-30 segundos
- Total del flujo: ~1-2 minutos por personaje
