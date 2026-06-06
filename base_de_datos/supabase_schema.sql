-- ============================================================
-- HUMANOS — Arquitectura de Base de Datos v2
-- Sala Editorial Completa
-- ============================================================

-- Limpiar tabla anterior si existe
DROP TABLE IF EXISTS humanos_personajes CASCADE;

-- ============================================================
-- FUNCIÓN: updated_at automático
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ LANGUAGE plpgsql;


-- ============================================================
-- TABLA 1: humanos_stories
-- La sala editorial principal. Una fila = una historia.
-- ============================================================
CREATE TABLE humanos_stories (
  id                      UUID DEFAULT gen_random_uuid() PRIMARY KEY,

  -- Identidad del protagonista
  protagonist_name        TEXT NOT NULL,
  normalized_name         TEXT,
  known_for               TEXT,
  associated_company      TEXT,
  country                 TEXT,
  region                  TEXT,
  era                     TEXT,
  story_subject_type      TEXT DEFAULT 'individual',
  -- individual / duo / team / family / company_case / movement

  -- Clasificación editorial
  domain_category         TEXT,
  -- business / technology / science / art / sports / entertainment /
  -- creator_economy / finance / space / social_impact / invention / culture
  protagonist_type        TEXT,
  -- founder / inventor / scientist / artist / builder / engineer /
  -- operator / creator / investor / explorer / leader / athlete
  story_level             TEXT DEFAULT 'microstory',
  -- microstory / extended_story / miniseries / premium_season
  format_recommendation   TEXT,
  -- single_short / two_part_short / three_part_story /
  -- mini_series / premium_series / newsletter_only / research_thread
  publish_timing          TEXT DEFAULT 'needs_research',
  -- publish_now / soon / hold_for_series / premium_reserve /
  -- needs_research / discard
  editorial_status        TEXT DEFAULT 'idea',
  -- idea → researching → researched → approved →
  -- scripted → voice_recorded → edited → scheduled →
  -- published → measured → archived
  production_status       TEXT DEFAULT 'not_started',

  -- Protección editorial
  protect_from_burning    BOOLEAN DEFAULT FALSE,
  burn_risk               TEXT DEFAULT 'low',
  -- low / medium / high / legendary

  -- Narrativa (Borges llena estos campos)
  one_line_story          TEXT,
  human_angle             TEXT,
  human_before_success    TEXT,
  central_conflict        TEXT,
  key_decision            TEXT,
  main_risk               TEXT,
  turning_point           TEXT,
  transformation          TEXT,
  legacy_today            TEXT,
  reflection_line         TEXT,

  -- Hooks (Borges propone, Gabo desarrolla)
  hook_family             TEXT,
  -- sabias_que / lo_que_nadie_sabe / antes_de /
  -- contradiccion / humano_detras / todo_comenzo / a_punto_de
  primary_hook            TEXT,
  alternative_hooks       JSONB DEFAULT '[]'::JSONB,
  closing_angle           TEXT,

  -- Serialización
  series_potential        BOOLEAN DEFAULT FALSE,
  estimated_episode_count INT,
  episode_outline         JSONB DEFAULT '[]'::JSONB,
  suggested_episode_titles JSONB DEFAULT '[]'::JSONB,

  -- Scoring 1-10 (todos opcionales — Borges los completa)
  narrative_score         INT,  -- Qué tan buena es la historia
  familiarity_score       INT,  -- Qué tan conocido es el personaje
  surprise_score          INT,  -- Factor sorpresa para la audiencia
  emotional_score         INT,  -- Conexión emocional humana
  research_confidence     INT,  -- Qué tan verificable está
  production_difficulty   INT,  -- Qué tan difícil es producir visualmente
  strategic_value         INT,  -- Encaje con la marca HUMANOS
  priority_score          INT,  -- Score final editorial
  series_score            INT,  -- Score si fuera serie/temporada

  -- Producción
  asset_needs             JSONB DEFAULT '[]'::JSONB,
  visual_style_notes      TEXT,
  music_mood              TEXT,
  capcut_template_version TEXT,

  -- Publicación
  platforms               JSONB DEFAULT '[]'::JSONB,
  scheduled_date          TIMESTAMPTZ,
  published_date          TIMESTAMPTZ,
  instagram_url           TEXT,
  youtube_url             TEXT,
  tiktok_url              TEXT,

  -- Aprendizaje post-publicación
  audience_reaction       TEXT,
  should_expand           BOOLEAN DEFAULT FALSE,
  expansion_notes         TEXT,

  -- Fuentes y verificación
  source_links            JSONB DEFAULT '[]'::JSONB,
  source_notes            TEXT,
  fact_check_status       TEXT DEFAULT 'pending',
  -- pending / verified / partial / failed
  fact_check_notes        TEXT,

  -- Sistema
  notion_id               TEXT UNIQUE,
  created_by              TEXT DEFAULT 'manual',
  assigned_to_agent       TEXT,
  created_at              TIMESTAMPTZ DEFAULT NOW(),
  updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_stories_editorial_status  ON humanos_stories(editorial_status);
CREATE INDEX idx_stories_publish_timing    ON humanos_stories(publish_timing);
CREATE INDEX idx_stories_story_level       ON humanos_stories(story_level);
CREATE INDEX idx_stories_domain_category   ON humanos_stories(domain_category);
CREATE INDEX idx_stories_priority_score    ON humanos_stories(priority_score DESC NULLS LAST);
CREATE INDEX idx_stories_notion_id         ON humanos_stories(notion_id);

CREATE TRIGGER trg_stories_updated_at
BEFORE UPDATE ON humanos_stories
FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================================
-- TABLA 2: humanos_scripts
-- Un historia puede tener N guiones (30s, 60s, 90s, newsletter...)
-- ============================================================
CREATE TABLE humanos_scripts (
  id                       UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  story_id                 UUID REFERENCES humanos_stories(id) ON DELETE CASCADE,

  script_type              TEXT,
  -- short_30 / short_60 / short_90 / episode /
  -- newsletter / caption / thread
  version                  INT DEFAULT 1,
  status                   TEXT DEFAULT 'draft',
  -- draft / review / approved / rejected / archived

  title                    TEXT,
  hook                     TEXT,
  narration                TEXT,
  on_screen_text           JSONB DEFAULT '[]'::JSONB,
  scene_breakdown          JSONB DEFAULT '[]'::JSONB,
  closing_line             TEXT,
  caption                  TEXT,
  pinned_comment           TEXT,

  estimated_duration_seconds INT,
  voice_notes              TEXT,
  pacing_notes             TEXT,
  visual_notes             TEXT,

  created_by               TEXT DEFAULT 'Gabo',
  approved_by_jota         BOOLEAN DEFAULT FALSE,

  created_at               TIMESTAMPTZ DEFAULT NOW(),
  updated_at               TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_scripts_story_id   ON humanos_scripts(story_id);
CREATE INDEX idx_scripts_status     ON humanos_scripts(status);
CREATE INDEX idx_scripts_type       ON humanos_scripts(script_type);

CREATE TRIGGER trg_scripts_updated_at
BEFORE UPDATE ON humanos_scripts
FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================================
-- TABLA 3: humanos_episodes
-- Para historias serializadas. Zhou Qunfei = 7 filas aquí.
-- ============================================================
CREATE TABLE humanos_episodes (
  id               UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  story_id         UUID REFERENCES humanos_stories(id) ON DELETE CASCADE,

  episode_number   INT NOT NULL,
  episode_title    TEXT NOT NULL,
  episode_hook     TEXT,
  episode_conflict TEXT,
  episode_summary  TEXT,
  cliffhanger      TEXT,
  status           TEXT DEFAULT 'idea',
  -- idea / scripted / recorded / edited / published

  script_id        UUID REFERENCES humanos_scripts(id),
  scheduled_date   TIMESTAMPTZ,
  published_date   TIMESTAMPTZ,

  created_at       TIMESTAMPTZ DEFAULT NOW(),
  updated_at       TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_episodes_story_id ON humanos_episodes(story_id);
CREATE INDEX idx_episodes_status   ON humanos_episodes(status);

CREATE TRIGGER trg_episodes_updated_at
BEFORE UPDATE ON humanos_episodes
FOR EACH ROW EXECUTE FUNCTION update_updated_at();


-- ============================================================
-- TABLA 4: humanos_metrics
-- Métricas por plataforma, no globales.
-- ============================================================
CREATE TABLE humanos_metrics (
  id                  UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  story_id            UUID REFERENCES humanos_stories(id) ON DELETE CASCADE,
  episode_id          UUID REFERENCES humanos_episodes(id) ON DELETE SET NULL,

  platform            TEXT NOT NULL,
  -- instagram / tiktok / youtube / linkedin / twitter
  post_url            TEXT,
  published_date      TIMESTAMPTZ,

  views               INT DEFAULT 0,
  likes               INT DEFAULT 0,
  comments            INT DEFAULT 0,
  shares              INT DEFAULT 0,
  saves               INT DEFAULT 0,
  followers_gained    INT DEFAULT 0,

  avg_watch_time      NUMERIC,
  retention_rate      NUMERIC,
  completion_rate     NUMERIC,
  click_through_rate  NUMERIC,

  qualitative_notes   TEXT,
  measured_at         TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_metrics_story_id  ON humanos_metrics(story_id);
CREATE INDEX idx_metrics_platform  ON humanos_metrics(platform);


-- ============================================================
-- VISTAS EDITORIALES
-- El cerebro operativo de la sala editorial.
-- ============================================================

-- Vista 1: Listas para publicar ya
CREATE VIEW v_publish_now AS
SELECT
  id, protagonist_name, known_for, story_level,
  format_recommendation, burn_risk, priority_score,
  editorial_status, fact_check_status
FROM humanos_stories
WHERE publish_timing = 'publish_now'
  AND editorial_status IN ('idea', 'researched', 'approved', 'scripted')
  AND protect_from_burning = FALSE
ORDER BY priority_score DESC NULLS LAST;

-- Vista 2: Historias premium protegidas
CREATE VIEW v_premium_reserve AS
SELECT
  id, protagonist_name, known_for, story_level,
  burn_risk, series_score, protect_from_burning, publish_timing
FROM humanos_stories
WHERE protect_from_burning = TRUE
   OR publish_timing IN ('hold_for_series', 'premium_reserve')
ORDER BY series_score DESC NULLS LAST;

-- Vista 3: Listas para que Gabo escriba el guion
CREATE VIEW v_ready_for_gabo AS
SELECT
  id, protagonist_name, known_for, story_level,
  format_recommendation, priority_score,
  hook_family, primary_hook, human_angle,
  central_conflict, key_decision, transformation
FROM humanos_stories
WHERE editorial_status = 'researched'
  AND fact_check_status IN ('verified', 'partial')
ORDER BY priority_score DESC NULLS LAST;

-- Vista 4: Listas para grabar voz (guion aprobado por Jota)
CREATE VIEW v_ready_for_voice AS
SELECT
  s.id, s.protagonist_name, s.known_for,
  sc.id AS script_id, sc.script_type, sc.narration,
  sc.hook, sc.closing_line, sc.voice_notes
FROM humanos_stories s
JOIN humanos_scripts sc ON sc.story_id = s.id
WHERE sc.status = 'approved'
  AND sc.approved_by_jota = TRUE
  AND s.production_status != 'voice_recorded';

-- Vista 5: Candidatas a serie
CREATE VIEW v_series_candidates AS
SELECT
  id, protagonist_name, known_for, story_level,
  estimated_episode_count, series_score,
  suggested_episode_titles, burn_risk
FROM humanos_stories
WHERE series_potential = TRUE
   OR story_level IN ('miniseries', 'premium_season')
ORDER BY series_score DESC NULLS LAST;


-- ============================================================
-- CONFIRMACIÓN
-- ============================================================
SELECT
  'humanos_stories'  AS tabla, COUNT(*) AS columnas FROM information_schema.columns WHERE table_name = 'humanos_stories'
UNION ALL SELECT
  'humanos_scripts', COUNT(*) FROM information_schema.columns WHERE table_name = 'humanos_scripts'
UNION ALL SELECT
  'humanos_episodes', COUNT(*) FROM information_schema.columns WHERE table_name = 'humanos_episodes'
UNION ALL SELECT
  'humanos_metrics', COUNT(*) FROM information_schema.columns WHERE table_name = 'humanos_metrics';
