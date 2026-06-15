# ESTADO DEL PROYECTO (PROJECT_STATE)

## Qué hicimos esta semana
* **Arquitectura de Base de Datos v2:** Consolidación de tablas en Supabase (`humanos_stories`, `humanos_scripts`, `humanos_episodes`, `humanos_metrics`) y creación de vistas clave (`v_ready_for_gabo`, `v_ready_for_voice`, etc.).
* **Prompts de Borges y Gabo v4:** Optimización de prompts para mejorar el factor humano y evitar alucinaciones corporativas.
* **Fichas de Pilotos:** Definición del trío de pilotos iniciales actualizados (**Jan Koum**, **Brian Chesky**, **Ehud Shabtai**).
* **Definición de Alma de Veritas (SOUL.md) y Hermoso (SOUL.md):** Consolidación de filosofías y reglas de calidad para la automatización.

## Qué estamos haciendo hoy
* **Dossier de Onboarding Técnico para Codex:** Creación de guías y políticas del repositorio para habilitar el desarrollo autónomo.
* **Integración del repositorio Remotion:** Configuración y estructura inicial para el renderizado automatizado de intros, lower thirds y animaciones para el formato vertical.
* **Configuración del Quality Gate de Veritas:** Preparando la conexión directa entre Borges, Veritas y Gabo en n8n.

## Qué haremos después
* **Integración completa de Veritas en n8n:** Automatizar el paso intermedio de fact checking para generar `fact_check.json` y actualizar `fact_check_status`.
* **Automatización por Webhooks/Triggers en Supabase:** Eliminar la activación manual de n8n para Gabo mediante Postgres Triggers.
* **Implementación de Curie:** Desarrollar el agente de memoria editorial e índice de contenidos a largo plazo.
* **Pipeline de Moore:** Acoplar la validación de assets multimedia locales para sugerencias de B-roll.
