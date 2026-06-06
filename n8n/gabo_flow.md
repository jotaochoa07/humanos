# Flujo n8n — Gabo (Guionista)

## Descripción

Workflow independiente para que Gabo tome la Ficha Narrativa aprobada de Borges y genere los 12 entregables del guion completo.

**Se activa:** Manualmente por Jota después de aprobar la ficha de Borges.

---

## Arquitectura del flujo

```
[Trigger manual de Jota]
    ↓
[Supabase — Leer ficha aprobada]
    ↓
[OpenAI — Generar 12 entregables del guion]
    ↓
[Supabase — Guardar guion → estado: "gabo_listo"]
    ↓
[Hermoso — Telegram: "Guion de [Nombre] listo para grabar"]
    ↓
[Opcional: Exportar guion a archivo .md local]
```

---

## Nodo 1: Trigger

**Tipo:** Manual (Jota activa cuando aprueba la ficha de Borges)

**Flujo de aprobación:**
1. Hermoso notifica: "Ficha lista: [Nombre]"
2. Jota revisa la ficha en Supabase (Table Editor)
3. Jota cambia el campo `estado` a `aprobado` manualmente
4. Jota activa el workflow de Gabo manualmente

*Futuro: automatizar con trigger en Supabase cuando estado = 'aprobado'*

---

## Nodo 2: Supabase — Leer ficha aprobada

**Tipo:** Postgres
**Query:**
```sql
SELECT *
FROM humanos_stories
WHERE editorial_status = 'approved'
ORDER BY updated_at ASC
LIMIT 1;
```

---

## Nodo 3: OpenAI — Generar guion completo

**Modelo:** GPT-4o o equivalente
**System Prompt:** [Pegar el system_prompt.md de Gabo v4]

**User Prompt:**
```
PERSONAJE: {{$node["Supabase"].json["protagonist_name"]}}
NIVEL DE HISTORIA: {{$node["Supabase"].json["story_level"]}}
CATEGORÍA: {{$node["Supabase"].json["domain_category"]}}

FICHA NARRATIVA DE BORGES:
Frase de potencial narrativo: {{$node["Supabase"].json["one_line_story"]}}
¿Quién era antes?: {{$node["Supabase"].json["human_before_success"]}}
Conflicto principal: {{$node["Supabase"].json["central_conflict"]}}
Decisión clave: {{$node["Supabase"].json["key_decision"]}}
Riesgo: {{$node["Supabase"].json["main_risk"]}}
Transformación: {{$node["Supabase"].json["transformation"]}}
¿Por qué importa hoy?: {{$node["Supabase"].json["legacy_today"]}}
Familia de hook recomendada: {{$node["Supabase"].json["hook_family"]}}
Hook principal sugerido: {{$node["Supabase"].json["primary_hook"]}}
Hooks alternativos: {{$node["Supabase"].json["alternative_hooks"]}}
Cierre sugerido: {{$node["Supabase"].json["closing_angle"]}}
Notas de verificación: {{$node["Supabase"].json["fact_check_notes"]}}

Genera los 12 entregables completos según tu system prompt.
Optimiza para voz humana de Jota (no ElevenLabs todavía).
Usa [PAUSA] para pausas naturales, no puntuación mecánica.
```

---

## Nodo 4: Supabase — Guardar guiones y actualizar historia

**Tipo:** Postgres
**Operation:** Multiple Queries / Transactions

```sql
-- 1. Actualizar el estado editorial de la historia
UPDATE humanos_stories
SET editorial_status = 'scripted'
WHERE id = '{{story_id}}';

-- 2. Insertar el guion principal (short_60)
INSERT INTO humanos_scripts (
  story_id,
  script_type,
  version,
  status,
  title,
  hook,
  narration,
  on_screen_text,
  scene_breakdown,
  closing_line,
  caption,
  pinned_comment,
  visual_notes,
  created_by
) VALUES (
  '{{story_id}}',
  'short_60',
  1,
  'draft',
  '{{title}}',
  '{{hook}}',
  '{{narration}}',
  '{{on_screen_text}}'::jsonb,
  '{{scene_breakdown}}'::jsonb,
  '{{closing_line}}',
  '{{caption}}',
  '{{pinned_comment}}',
  '{{visual_notes}}',
  'Gabo'
);

-- 3. Insertar el guion corto (short_30)
INSERT INTO humanos_scripts (
  story_id,
  script_type,
  version,
  status,
  hook,
  narration,
  created_by
) VALUES (
  '{{story_id}}',
  'short_30',
  1,
  'draft',
  '{{short_hook}}',
  '{{short_narration}}',
  'Gabo'
);
```

---

## Nodo 5: Hermoso — Notificación Telegram

**Mensaje:**
```
✍️ GABO TERMINÓ

Personaje: [NOMBRE]
Nivel: [1/2/3/4]

El guion está listo para grabar.
Tienes: guion 30s, guion 45-75s, texto en pantalla, copy e indicaciones visuales.

Revisa en Supabase o pídeme que te lo mande aquí.
```

---

## Nodo 6 (Opcional): Exportar guion a archivo local

**Tipo:** Write Binary File o similar

Guarda el guion completo como:
```
humanos/guiones/[nombre_personaje]_v1.md
```

Usando la plantilla `guiones/plantilla_guion.md` como base.

---

## Tiempo estimado por personaje

- Generación OpenAI (12 entregables): ~30-60 segundos
- Escritura en Supabase: ~2 segundos
- Total del flujo: ~1 minuto por personaje

---

## Diferencia clave con el flujo de Borges

| | Borges | Gabo |
|---|---|---|
| **Input** | Solo el nombre | Ficha completa de 15 campos |
| **Proceso** | 4 búsquedas web + síntesis | 1 generación creativa |
| **Output** | Ficha Narrativa (investigación) | Guion listo para grabar |
| **Aprobación Jota** | Antes de pasar a Gabo | Antes de grabar |
| **Duración** | ~1-2 minutos | ~1 minuto |
