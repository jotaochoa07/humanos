# ESTADO DEL PROYECTO (PROJECT_STATE)

## Qué hicimos esta semana
* **Arquitectura de Base de Datos v2:** Consolidación de tablas en Supabase (`humanos_stories`, `humanos_scripts`, `humanos_episodes`, `humanos_metrics`) y creación de vistas clave (`v_ready_for_gabo`, `v_ready_for_voice`, etc.).
* **Prompts de Borges y Gabo v4:** Optimización de prompts para mejorar el factor humano y evitar alucinaciones corporativas.
* **Fichas de Pilotos:** Definición del trío de pilotos iniciales actualizados (**Jan Koum**, **Brian Chesky**, **Ehud Shabtai**).
* **Definición de Alma de Veritas (SOUL.md) y Hermoso (SOUL.md):** Consolidación de filosofías y reglas de calidad.
* **Base Visual en Remotion & TypeScript:**
  * Configuración del entorno de Remotion en `humanos/`.
  * Desarrollo de la intro (Brand Categories), HUMANOS Logo Reveal, Transition Pulse, Character Card (de Jan Koum) y End Card.
  * Ajuste fino: Grano cinematográfico, respiración visual, categorías en desenfoque profundo y un cierre más ritual.
  * Exportación de los primeros clips editables hacia `assets/branding/video/`.

## Qué estamos haciendo hoy
* **Dirección Creativa Oficial V1:** Aprobación del manual visual y de audio para el "Archivo Humano".
* **Organización del Estudio Audiovisual:** Definición de la estructura cinemática de carpetas en `assets/` para sonido, transiciones, B-roll y thumbnails.

## Qué haremos después
* **Integración de Veritas en n8n:** Automatizar el paso de auditoría para generar `fact_check.json` antes de habilitar a Gabo.
* **Automatización por Triggers de Supabase:** Crear webhooks para activar los agentes en n8n sin intervención manual.
* **Implementación de Curie:** Desarrollar el agente de memoria editorial para catalogar y evitar repeticiones.
