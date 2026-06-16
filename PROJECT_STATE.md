# ESTADO DEL PROYECTO (PROJECT_STATE)

## Qué hicimos esta semana
* **Arquitectura de Base de Datos v2:** Consolidación de tablas en Supabase (`humanos_stories`, `humanos_scripts`, `humanos_episodes`, `humanos_metrics`) y creación de vistas clave (`v_ready_for_gabo`, `v_ready_for_voice`, etc.).
* **Prompts de Borges y Gabo v4:** Optimización de prompts para mejorar el factor humano y evitar alucinaciones corporativas.
* **Fichas de Pilotos:** Definición del trío de pilotos iniciales actualizados (**Jan Koum**, **Brian Chesky**, **Ehud Shabtai**).
* **Definición de Alma de Veritas (SOUL.md) y Hermoso (SOUL.md):** Consolidación de filosofías y reglas de calidad para la automatización.
* **Sistema visual HUMANOS v1:** Implementación del primer sistema Remotion para identidad documental vertical: categorías, reveal de marca, transition pulse, Character Card, End Card y assets separados para CapCut Pro.

## Qué hicimos hoy
* **Dirección creativa aprobada:** Se consolidó la dirección `ARCHIVO HUMANO`: documental premium, minimalista, cinematográfica, humana y contemporánea.
* **Setup Remotion + TypeScript:** Se agregó la base técnica para renderizar componentes visuales reutilizables en 1080x1920 a 30 FPS.
* **Componentes Remotion creados:** `HumanosBrandReveal`, `HumanosLogoReveal`, `HumanosCharacterCard`, `HumanosTransition`, `HumanosEndCard`.
* **Character Card real:** Se creó la primera tarjeta documental de **Jan Koum** usando su retrato, con arquetipo `BUILDER`, nombre, descriptor y estilo B/N de alto contraste.
* **Sistema editable para CapCut:** Se exportaron clips separados y overlays para montar un template editable en CapCut Pro.
* **Assets de branding exportados:** Se guardaron clips en `assets/branding/video`, incluyendo categorías largas, logo, línea cian, background loop, transition pulse, card de Jan Koum y End Card.
* **Sets editoriales de categorías:** Se generaron sets A/B/C de categorías como capas de pensamiento, listos para editar timing en CapCut.

## Qué haremos después
* **Sonido HUMANOS:** Definir y probar firma sonora: latido grave, textura documental, drones sutiles y transiciones mínimas.
* **Template CapCut Pro:** Armar el proyecto base editable con foto, textos, overlays y audio por capas.
* **Generación de personajes:** Crear flujo para producir nuevas Character Cards desde configuración JSON por personaje.
* **Integración completa de Veritas en n8n:** Automatizar el paso intermedio de fact checking para generar `fact_check.json` y actualizar `fact_check_status`.
* **Automatización por Webhooks/Triggers en Supabase:** Eliminar la activación manual de n8n para Gabo mediante Postgres Triggers.
* **Implementación de Curie:** Desarrollar el agente de memoria editorial e índice de contenidos a largo plazo.
* **Pipeline de Moore:** Acoplar la validación de assets multimedia locales para sugerencias de B-roll.

## Archivos clave de la jornada
* `src/Root.tsx` — Registro de composiciones Remotion.
* `src/components/HumanosBrandReveal.tsx` — Categorías editoriales / Archivo Humano.
* `src/components/HumanosLogoReveal.tsx` — Reveal independiente del logo HUMANOS.
* `src/components/HumanosCharacterCard.tsx` — Character Card reusable.
* `src/components/HumanosTransition.tsx` — Pulse transition.
* `src/components/HumanosEndCard.tsx` — End Card ritual.
* `src/components/capcut/CharacterCardOverlays.tsx` — Overlays y referencia para template editable en CapCut.
* `src/components/capcut/BrandingUtilityAssets.tsx` — Background loop, línea cian larga y assets utilitarios.
* `src/components/capcut/SlowCategoryThoughts.tsx` — Sets de categorías como pensamientos flotantes.
* `assets/branding/video/` — Clips finales para CapCut Pro.
* `assets/branding/video/character_card/` — Paquete editable de Character Card.
