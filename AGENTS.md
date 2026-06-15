# MANUAL DE AGENTES (AGENTS.md)

Este documento centraliza las reglas de juego, arquitectura y convenciones para agentes autónomos (Codex, Claude Code, Antigravity y otros) que interactúan con el proyecto **HUMANOS**.

---

## 1. VISIÓN DEL PROYECTO
HUMANOS es una biblioteca de microdramas reales sobre personas extraordinarias que cambiaron el mundo.
* **Slogan:** *"En época de IA, un homenaje a lo humano."*
* **Regla de oro:** La empresa es el escenario. La persona es la historia.

---

## 2. REGLAS DE TRABAJO (REGLAMENTO OPERATIVO)
1. **No inventar información:** Si un dato o anécdota no tiene fuentes verificadas, Veritas debe marcarlo como `UNVERIFIED` o `REJECTED`.
2. **Priorizar el factor humano sobre el corporativo:** El foco está en el conflicto existencial, las pérdidas, las decisiones difíciles y la transformación del individuo.
3. **Optimización del tiempo del fundador:** Toda automatización debe reducir la carga operativa de Jota (voz de HUMANOS y director creativo), dándole control de aprobación pero liberándolo de tareas mecánicas.
4. **Validación antes de la narración:** Ningún guion puede pasar a Gabo sin antes ser auditado y aprobado por Veritas.

---

## 3. ARQUITECTURA DE AGENTES
El ecosistema de HUMANOS está estructurado en niveles de responsabilidad:

### Nivel Estratégico
* **Hermoso:** Socio de operaciones de Jota. Actúa como director del loop operativo. Se comunica mediante Telegram y n8n.
* **SOUL (Alma):** Los archivos `SOUL.md` definen la ética operativa, el tono y la voz de los agentes.

### Nivel Editorial
* **Borges (Cazador de Protagonistas):** Agente de investigación. Usa la API de Tavily para recopilar datos de origen, conflicto, decisiones y legado.
* **Veritas (Auditor de Confianza):** Fact checker. Evalúa evidencia, asigna scores de confianza y clasifica fuentes de A a F.
* **Gabo (Story Architect):** Guionista de microdramas. Escribe guiones en formato vertical (30s, 60s, 90s) estructurados en 7 actos.
* **Curie (Memoria Editorial):** Diseñado para administrar el índice de contenido histórico, evitar repeticiones de historias/hooks y sugerir arcos narrativos. *(Estado: Diseño avanzado. Próxima fase de implementación)*.

### Nivel Operativo
* **Moore (Documentary Producer):** Encargado de procesar y validar assets multimedia locales.

### Nivel Desarrollo
* **Antigravity / Codex:** Diseñan, desarrollan y mantienen la infraestructura de software, la base de datos Supabase, los flujos en n8n y los componentes de Remotion.

---

## 4. CONVENCIONES Y RESTRICCIONES EDITORIALES
* **Estructura de 7 Actos:** Personaje → Conflicto → Decisión → Riesgo → Resultado → Transformación → Reflexión.
* **Estilo de escritura:** Frases cortas (10-12 palabras), uso de `[PAUSA]` para ritmo conversacional, MAYÚSCULAS en 1-3 palabras clave por párrafo para indicar énfasis, y cero emojis.
* **Lo que HUMANOS NO es:**
  * No es un canal de curiosidades genéricas.
  * No es un canal motivacional / autoayuda barata.
  * No es un canal de frases inspiracionales.
  * No es un canal de negocios plano.
  * No es un canal de biografías de Wikipedia simplificadas.

---

## 5. CONVENCIONES DE DISEÑO (VISUALES Y REMOTION)
Para el desarrollo y renderizado de componentes con Remotion:
* **Nunca:** Usar neones exagerados, glitches, efectos gamer, transiciones dinámicas chillonas o animaciones TikTok genéricas.
* **Siempre:** Estilo documental premium, movimiento lento y paneos suaves (Ken Burns), fondos oscuros (negro absoluto/carbón), tipografías fuertes (Bebas Neue, Anton, Montserrat ExtraBold) y minimalismo elegante.
* **Remotion Core:** Componentes reutilizables parametrizados por configuración JSON que permitan branding centralizado y soporte dinámico para futuros personajes.

---

## 6. ROADMAP DE 12 MESES
* **Fase 1: Validación de Formato:** Publicar los primeros 10 videos pilotos (Jan Koum, Brian Chesky, Ehud Shabtai).
* **Fase 2: Automatización Editorial:** Implementación de pipelines semiautomáticos de investigación (Borges) y guiones (Gabo).
* **Fase 3: Biblioteca Humana:** Llegar a los 100 personajes históricos documentados y publicados.
* **Fase 4: Archivo Humano:** Lanzamiento de la newsletter, plataforma web interactiva y contenido extendido.
* **Fase 5: Sistema de IP:** Producción de miniseries premium, documentales interactivos y licenciamiento de la propiedad intelectual.

---

## 7. KPIs DE ÉXITO
1. **Retención de 3 segundos** (Hook rate) - *Máxima prioridad*
2. **Shares / Compartidos** - *Indica valor de marca*
3. **Saves / Guardados** - *Indica utilidad y profundidad*
4. **Likes / Me gusta**
5. **Completion Rate** (Tasa de finalización)
