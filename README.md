# HUMANOS

> **En época de inteligencia artificial, HUMANOS es un homenaje a las personas que construyeron lo extraordinario.**

---

## La Regla Editorial

**La empresa es el escenario. La persona es la historia.**

La tecnología es el escenario. La persona es la historia.
La innovación es el escenario. La persona es la historia.
La ciencia es el escenario. La persona es la historia.

---

## Qué es HUMANOS

Una biblioteca de microdramas reales sobre personas extraordinarias.

No estamos construyendo un canal de curiosidades.
No estamos construyendo un canal de motivación.
No estamos construyendo resúmenes de Wikipedia.

Estamos construyendo una propiedad intelectual basada en historias humanas reales narradas como entretenimiento.

---

## Audiencia

Emprendedores, builders, creadores, personas curiosas interesadas en tecnología, ciencia, arte, innovación y liderazgo.

Personas que admiran a quienes construyen cosas desde cero.

La audiencia debe terminar pensando:

> *"Esto parece una película. Pero pasó de verdad."*

---

## Slogan en exploración

- Historias extraordinarias de personas reales.
- Detrás de cada imperio hubo un humano.
- Microdramas reales sobre personas que cambiaron el mundo.
- En época de IA, un homenaje a lo humano.

---

## Estructura del repositorio

```
humanos/
│
├── agents/
│   ├── borges/               # Cazador de Protagonistas
│   │   ├── personality.md
│   │   └── prompts/
│   │       └── system_prompt.md
│   ├── veritas/              # Auditor de Confianza (Quality Gate)
│   │   ├── SOUL.md
│   │   ├── personality.md
│   │   └── prompts/
│   │       └── system_prompt.md
│   ├── gabo/                 # Story Architect
│   │   ├── personality.md
│   │   └── prompts/
│   │       └── system_prompt.md
│   ├── curie/                # Memoria Editorial / Bibliotecaria RAG
│   │   ├── personality.md
│   │   └── prompts/
│   │       └── system_prompt.md
│   ├── mark/                 # Performance Analytics & Optimización
│   │   └── prompts/
│   │       └── system_prompt.md
│   └── hermoso/              # Socio de Operaciones (Alter-ego)
│       └── SOUL.md
│
├── personajes/
│   ├── plantilla_ficha_personaje.md
│   └── PRODUCTION_METRICS_DASHBOARD.md  # Generado automáticamente por Mark
│
├── guiones/
│   └── plantilla_guion.md
│
├── research/
│   ├── plantilla_fact_check.md
│   └── plantilla_approved_claims.md
│
├── backlog/
│   └── backlog_personajes.md
│
├── produccion/
│   ├── checklist_capcut.md
│   ├── familias_de_apertura.md
│   └── cierres_de_marca.md
│
├── assets/
│   └── README.md
│
├── base_de_datos/
│   ├── supabase_schema.sql
│   └── curie_library/        # Base de conocimiento vectorial administrada por Curie (TurboVec)
│
└── n8n/
    ├── borges_flow.md
    └── gabo_flow.md
```

---

## Fases del proyecto

| Fase | Objetivo | Estado |
|---|---|---|
| 1 | Publicar los primeros 3 pilotos (Jan Koum, Ehud Shabtai, Adidas vs Puma) | 🟡 En curso |
| 2 | Validar con 15-30 videos | ⬜ Pendiente |
| 3 | Biblioteca de personajes con métricas | ⬜ Pendiente |
| 4 | Serialización de miniseries | ⬜ Pendiente |
| 5 | Producción avanzada + voz clonada | ⬜ Pendiente |

---

## Primeros 3 pilotos (Lote Fundacional)

1. **Jan Koum** — El inmigrante de Ucrania que creó WhatsApp y lo vendió por $19B.
2. **Ehud Shabtai** — El programador de Israel que desafió a los gigantes del GPS con Waze.
3. **Adidas vs Puma** — La encarnizada rivalidad familiar alemana que fundó dos imperios deportivos.

---

## Agentes del sistema

| Agente | Nivel | Rol | Herramienta / Implementación |
|---|---|---|---|
| **Hermoso** | Estratégico | Socio de Operaciones | Alter-ego / Telegram / n8n |
| **Borges** | Editorial | Cazador de Protagonistas | n8n + Tavily |
| **Veritas** | Editorial | Auditor de Confianza | n8n + OpenAI (Fact Checker) |
| **Gabo** | Editorial | Story Architect | n8n + OpenAI |
| **Curie** | Editorial | Memoria Editorial / Bibliotecaria RAG | Python (`curie.py`) + TurboVec local (1536d / 4-bit) |
| **Mark** | Operativo | Performance Analytics | Python (`mark.py`) + Dashboard Conceptual |
| **Moore** | Operativo | Documentary Producer | Cruce de assets locales y storyboard |

---

## Lineamientos de Branding (Identidad de HUMANOS)

Los entregables y videos de **HUMANOS** deben seguir estrictas pautas de identidad visual, sonora y narrativa para asegurar una calidad cinematográfica premium:

### Filosofía Narrativa
* **Autenticidad Absoluta (Authenticity is Key):** Fidelidad histórica total. Prohibido inventar o alucinar anécdotas (Veritas actúa como filtro).
* **Foco en lo Humano (Human-Centric):** La historia se enfoca en las decisiones difíciles, los conflictos existenciales, pérdidas y el impacto en la persona. La tecnología/negocio es solo el escenario.
* **Matices sobre Simplificaciones (Nuance over Simplification):** Evitar caracterizaciones planas; el personaje tiene grises, contradicciones y decisiones polémicas.

### Estética y Edición Visual
* **Ritmo Contemplativo:** Cortes de video pausados y transiciones suaves (fundidos lentos, cortes directos). Pausas estratégicas y silencios de reflexión.
* **Paleta de Color Documental:** Tonos oscuros, grises cálidos, negros suaves y blancos desaturados. Acentos sutiles en verde esmeralda y ámbar oscuro para branding.
* **Tipografía:** Montserrat o Open Sans en negrita para secciones e impacto; Roboto Light o Lato Regular para créditos e información; tipografía serif clásica modernizada para citas en pantalla.

### Identidad Sonora
* **Música Minimalista y Ambiental:** Sonidos electrónicos/orquestales reflexivos e inspiradores.
* **Efectos de Sonido (SFX) Orgánicos:** Muy sutiles y realistas (tecleo suave de máquina de escribir, hum de servidores, clics discretos).

---

## 🧪 Pruebas RAG y Curie

El archivo `test_curie.py` permite verificar el funcionamiento de **Curie** de forma local. En este script, Curie indexa documentos textuales de prueba, calcula sus embeddings de forma determinista y realiza búsquedas de similitud en la biblioteca local (`base_de_datos/curie_library/`) usando la tecnología de compresión vectorial **TurboVec**.

---

*Jota Ochoa — Colombia 🇨🇴*
