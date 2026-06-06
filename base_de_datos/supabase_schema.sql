# Base de Datos Supabase — Esquema HUMANOS

## Proyecto Supabase: `humanos-content`

---

## Schema SQL completo

```sql
-- Tabla principal de personajes HUMANOS
CREATE TABLE humanos_personajes (

  -- Identificadores
  id                    UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  notion_id             TEXT UNIQUE,
  nombre                TEXT NOT NULL,

  -- Campos heredados de Notion
  historia_breve        TEXT,
  hook_inicial          TEXT,
  admirable_por         TEXT,
  categoria             TEXT,
  referencias           TEXT,
  url_referencia        TEXT,

  -- Clasificación HUMANOS
  nivel                 SMALLINT DEFAULT 1,
  area                  TEXT,
  frase_narrativa       TEXT,

  -- Ficha narrativa (entregable de Borges)
  origen                TEXT,
  conflicto             TEXT,
  decision              TEXT,
  riesgo                TEXT,
  transformacion        TEXT,
  por_que_importa       TEXT,
  hooks_borges          TEXT,
  estructura_episodios  TEXT,
  advertencias          TEXT,
  fuentes_sugeridas     TEXT,
  potencial_serie       BOOLEAN DEFAULT FALSE,

  -- Estado de producción
  estado                TEXT DEFAULT 'backlog',
  recomendacion         TEXT,

  -- Guion (entregable de Gabo)
  guion_principal       TEXT,
  guion_corto           TEXT,
  guion_largo           TEXT,
  texto_en_pantalla     TEXT,
  indicaciones_visuales TEXT,
  cierre_recomendado    TEXT,
  copy_descripcion      TEXT,
  comentario_fijado     TEXT,
  version_newsletter    TEXT,

  -- Publicación y métricas
  plataformas           TEXT,
  fecha_publicacion     TIMESTAMPTZ,
  url_video_ig          TEXT,
  url_video_tiktok      TEXT,
  url_video_youtube     TEXT,
  vistas                INTEGER,
  retencion_pct         NUMERIC(5,2),
  comentarios           INTEGER,
  compartidos           INTEGER,
  guardados             INTEGER,
  merece_serie          BOOLEAN DEFAULT FALSE,
  notas_metricas        TEXT,

  -- Control
  created_at            TIMESTAMPTZ DEFAULT NOW(),
  updated_at            TIMESTAMPTZ DEFAULT NOW()
);

-- Índices
CREATE INDEX idx_humanos_estado    ON humanos_personajes(estado);
CREATE INDEX idx_humanos_nivel     ON humanos_personajes(nivel);
CREATE INDEX idx_humanos_notion_id ON humanos_personajes(notion_id);

-- Trigger updated_at
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_updated_at
BEFORE UPDATE ON humanos_personajes
FOR EACH ROW EXECUTE FUNCTION update_updated_at();
```

---

## Valores de estado

| Estado | Significado | Agente responsable |
|---|---|---|
| `backlog` | En lista | — |
| `investigar` | Jota lo activa | → Borges |
| `borges_listo` | Ficha lista | → Jota aprueba |
| `aprobado` | Jota aprobó ficha | → Gabo |
| `gabo_listo` | Guion listo | → Jota graba |
| `grabado` | Voz grabada | → CapCut |
| `editando` | En edición | — |
| `publicado` | Publicado | → Métricas |
| `premium` | Guardado | — |

---

## Integración n8n

### Credencial Postgres en n8n
- **Host:** `db.[project-ref].supabase.co`
- **Port:** `5432`
- **Database:** `postgres`
- **User:** `postgres`
- **SSL:** Required

### API REST (para Hermoso / consultas rápidas)
- **Base URL:** `https://[project-ref].supabase.co/rest/v1/humanos_personajes`
- **Headers:**
  ```
  apikey: [anon-key]
  Authorization: Bearer [service-role-key]
  Content-Type: application/json
  ```

### Ejemplos de queries frecuentes

**Obtener personajes listos para investigar:**
```sql
SELECT id, nombre, historia_breve, categoria
FROM humanos_personajes
WHERE estado = 'investigar'
ORDER BY created_at ASC;
```

**Actualizar estado después de Borges:**
```sql
UPDATE humanos_personajes
SET estado = 'borges_listo',
    origen = $1,
    conflicto = $2,
    decision = $3,
    riesgo = $4,
    transformacion = $5,
    por_que_importa = $6,
    hooks_borges = $7,
    advertencias = $8,
    fuentes_sugeridas = $9,
    nivel = $10,
    recomendacion = $11,
    frase_narrativa = $12
WHERE id = $13;
```

**Obtener ficha aprobada para Gabo:**
```sql
SELECT *
FROM humanos_personajes
WHERE estado = 'aprobado'
ORDER BY updated_at ASC
LIMIT 1;
```
