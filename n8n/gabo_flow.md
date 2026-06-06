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
FROM humanos_personajes
WHERE estado = 'aprobado'
ORDER BY updated_at ASC
LIMIT 1;
```

---

## Nodo 3: OpenAI — Generar guion completo

**Modelo:** GPT-4o o equivalente
**System Prompt:** [Pegar el system_prompt.md de Gabo v4]

**User Prompt:**
```
PERSONAJE: {{$node["Supabase"].json["nombre"]}}
NIVEL: {{$node["Supabase"].json["nivel"]}}
CATEGORÍA: {{$node["Supabase"].json["categoria"]}}

FICHA NARRATIVA DE BORGES:

Frase de potencial narrativo: {{frase_narrativa}}
¿Quién era antes?: {{origen}}
Conflicto principal: {{conflicto}}
Decisión clave: {{decision}}
Riesgo: {{riesgo}}
Transformación: {{transformacion}}
¿Por qué importa hoy?: {{por_que_importa}}
Hooks sugeridos por Borges: {{hooks_borges}}
Advertencias de verificación: {{advertencias}}

Genera los 12 entregables completos según tu system prompt.
Optimiza para voz humana de Jota (no ElevenLabs todavía).
Usa [PAUSA] para pausas naturales, no puntuación mecánica.
```

---

## Nodo 4: Supabase — Guardar guion

**Tipo:** Postgres
**Operation:** Update

```sql
UPDATE humanos_personajes
SET
  estado = 'gabo_listo',
  guion_principal = '{{guion_principal}}',
  guion_corto = '{{guion_corto}}',
  guion_largo = '{{guion_largo}}',
  texto_en_pantalla = '{{texto_en_pantalla}}',
  indicaciones_visuales = '{{indicaciones_visuales}}',
  cierre_recomendado = '{{cierre_recomendado}}',
  copy_descripcion = '{{copy_descripcion}}',
  comentario_fijado = '{{comentario_fijado}}',
  version_newsletter = '{{version_newsletter}}'
WHERE id = '{{id}}';
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
