# Auditoría de alineación de marca

*Generada 2026-08-01 19:46 · modelo anthropic/claude-sonnet-5*

Confronta la definición de cada agente contra `agents/_MARCA/constitucion_marca.md`.

**Solo lectura: ningún prompt fue modificado.**

---

## Resumen

- **Contradicen:** 2 (gabo, mark)
- **En tensión:** 4 (mr-you, borges, leonardo, talese)
- **Alineados:** 4 (veritas, moore, curie, hermoso)

---

## 🔴 gabo

Gabo está bien alineado en su lente narrativa (persona sobre empresa, estructura de 7 actos, reglas de voz), pero su definición de propósito ('posicionar la marca personal de Jota') y su variante 'Disruptiva' ('giros narrativos polarizantes') contradicen directamente la arquitectura Jota↔HUMANOS y la anti-asociación de creador polarizante.

### Contradicción — severidad alta

**El agente dice:**
> Su propósito principal es posicionar la marca personal de Jota creando microdramas reales de alta retención (60-90 segundos) sobre personajes inspiradores, fundadores y líderes extraordinarios.

**La constitución dice:**
> HUMANOS debe funcionar **aunque el espectador no sepa quién es Jota**. No existe para promocionarlo.

**Por qué:** personality.md define el propósito nuclear de Gabo/HUMANOS como vehículo de posicionamiento de Jota, exactamente la relación 'influencer ↔ producto promocional' que la constitución excluye explícitamente en la arquitectura Jota↔HUMANOS.

**Corrección sugerida:** Su propósito es crear microdramas reales de personajes que funcionen como obra editorial independiente, con la calidad narrativa como prueba; el fortalecimiento de la marca de Jota es una consecuencia, no el fin.

### Contradicción — severidad alta

**El agente dice:**
> 3. Disruptiva: Enfocado en riesgos extremos, tensiones insólitas, giros narrativos polarizantes o decisiones arriesgadas del protagonista.

**La constitución dice:**
> No fabricar polarización para conseguir distribución. [...] ❌ Creador polarizante

**Por qué:** La variante 'Disruptiva' instruye explícitamente a construir 'giros narrativos polarizantes', chocando de frente con una anti-asociación explícita (veto, no preferencia) y con la regla de contenido §6.

**Corrección sugerida:** 3. Disruptiva: Enfocado en riesgos extremos, tensiones insólitas y giros dramáticos inesperados del protagonista (sin buscar polarizar, sino sorprender por la complejidad humana de la decisión).

### Contradicción — severidad media

**El agente dice:**
> Master System Prompt: Gabo (AI Agent) - Story Architect ... utilizado en el agente Gabo para la generación de guiones automáticos de alta retención del proyecto HUMANOS.

**La constitución dice:**
> Una métrica describe lo que pasó. No autoriza a cambiar el rumbo. [...] El canal no persigue clics: construye catálogo.

**Por qué:** Definir la especialidad del agente en términos de 'alta retención' como objetivo primario (en vez de la calidad narrativa o la pregunta filtro) instala la métrica como criterio rector del guion, en tensión con el mandato de que las métricas informan y no deciden.

**Corrección sugerida:** ...utilizado en el agente Gabo para la generación de guiones de microdramas reales de alta calidad narrativa, diseñados para sostener la atención por mérito propio, no por persecución de retención.

### Omisiones

- **Ninguna referencia a la pregunta filtro (§0) ni al Test de 7 preguntas (§9) como filtro antes de escribir o elegir ángulo de personaje.** — Gabo decide qué historia contar y con qué énfasis (p. ej. la variante Disruptiva); sin el filtro explícito, no hay salvaguarda escrita contra ángulos que prioricen drama sobre expansión humana. *(dónde: En system_prompt.md, antes de la sección de variantes, agregar una verificación: cada variante debe poder responder 'sí' a la pregunta filtro y no empujar hacia una anti-asociación.)*
- **No se menciona la distinción entre mostrar el proceso/las decisiones (§6: 'Mostrar procesos y decisiones, no solo resultados terminados') y la estructura actual, que culmina en RESULTADO/TRANSFORMACIÓN como clímax dramático.** — El riesgo es que los guiones terminen celebrando el resultado final (el 'toqué fondo y ahora gané' que el §8 asocia a un tono no deseado para Jota) aplicado ahora al personaje retratado, reforzando una épica de éxito en vez de una épica de aprendizaje continuo. *(dónde: En la sección 'FILOSOFÍA DEL PROYECTO' o en el acto 7 (REFLEXIÓN), aclarar que la reflexión debe iluminar un aprendizaje genuino y no cerrar en tono de 'llegó y triunfó'.)*

---

## 🔴 mark

El Quality Gate y el paquete de distribución de Mark están bien alineados con la marca, pero su Paso 3 contradice directamente el rol que la constitución le asigna ('no aconseja estrategia') al producir recomendaciones accionables que otros agentes deben ejecutar en el próximo episodio. Además, faltan las salvaguardas de §2 (etiquetado DATO/PATRÓN/HIPÓTESIS, umbral de tendencia, alerta de correlación por orden de publicación).

### Contradicción — severidad alta

**El agente dice:**
> Basándote en esto, debes redactar las **Lecciones** (qué funcionó y qué falló) y **Recomendaciones** accionables que serán consumidas por Gabo (para ajustar guiones) y Leonardo (para ajustar portadas) en el próximo episodio.

**La constitución dice:**
> Mark | Copy que no presume. Captura y entrega datos; **no aconseja estrategia**. (§10) / Una métrica **describe** lo que pasó. No decide qué hacer después. (§2.1)

**Por qué:** La constitución le asigna a Mark explícitamente el límite de 'capturar y entregar datos' sin aconsejar estrategia, y advierte que la sección §2 nació justo porque el sistema 'empezó a recomendar decisiones de formato basadas en la retención de tres videos'. El prompt de Mark hace exactamente eso: convierte métricas de 72hs en 'Recomendaciones accionables' que otros agentes (Gabo, Leonardo) deben aplicar en el próximo episodio, saltándose el rol de Talese (custodio de medir evolución) y transformando la métrica en decisión.

**Corrección sugerida:** Cambiar a: 'Compila el informe de rendimiento con los datos crudos (retención, CTR, interacciones) y entrégalo a Talese, quien evalúa si constituye PATRÓN o HIPÓTESIS antes de que derive en ajustes de guion o portada. Mark no redacta recomendaciones de contenido; entrega datos etiquetados y contextualizados.'

### Omisiones

- **El proceso de post-mortem no exige distinguir DATO / PATRÓN / HIPÓTESIS / BEST PRACTICE EXTERNA al reportar métricas.** — La constitución (§2.5) lo exige explícitamente para cualquier agente que lea datos, precisamente para evitar que una observación aislada se presente como conclusión sólida. *(dónde: Paso 3, antes de redactar 'Lecciones y Recomendaciones'.)*
- **No se menciona el umbral de '5+ publicaciones de la misma línea y varias capturas en el tiempo' antes de calificar algo como tendencia.** — Sin este criterio, un post-mortem de un solo episodio (72hs) puede generalizarse indebidamente como patrón de canal, algo que §2.4 pide marcar como hipótesis si hay menos evidencia. *(dónde: Paso 3, al redactar Lecciones.)*
- **No se contempla que una correlación en las métricas pueda explicarse por el orden de publicación / curva de aprendizaje del creador, en lugar de por la variable que se cree medir.** — §2.6 lo pide explícitamente para evitar atribuir causalidad falsa a un formato o gancho cuando en realidad el creador simplemente mejoró con la práctica. *(dónde: Paso 3, en el informe de rendimiento.)*

---

## 🟡 mr-you

Mr. You está mayormente alineado con la constitución: ya adoptó una tesis de canal que corrige la contradicción C1 registrada en la constitución (no ancla la identidad de Jota a la IA), y respeta la pregunta filtro y la disciplina DATO/PATRÓN/HIPÓTESIS. El punto débil real es incluir 'Reach' como Objetivo seleccionable pese a declarar que el alcance es 'solo un input de distribución', y le faltan mecanismos explícitos para el Test de 7, el checklist de anti-asociaciones y las salvaguardas contra falsos patrones.

### Contradicción — severidad media

**El agente dice:**
> Objetivo: Resonancia Profesional / Resonancia Intelectual / Reach

**La constitución dice:**
> 3. Prohibido proponer packaging que suba CTR a costa de las anti-asociaciones. El canal no persigue clics: construye catálogo.

**Por qué:** El propio system_prompt de Mr. You establece que 'el alcance (reach) es solo un input de distribución', pero luego, en el formato de salida estándar, ofrece 'Reach' como una opción de Objetivo/Strategic Objective al mismo nivel que Resonancia Profesional e Intelectual. Convertir el reach en un objetivo estratégico seleccionable abre la puerta a justificar decisiones por alcance, exactamente lo que la constitución veta bajo la anti-asociación 'Perseguidor de métricas o competidores' y la regla de que las métricas informan pero no deciden.

**Corrección sugerida:** Eliminar 'Reach' como opción de Objetivo en el formato de salida y dejar únicamente 'Resonancia Profesional / Resonancia Intelectual', registrando el reach obtenido solo como dato descriptivo en el Postmortem, nunca como objetivo perseguido.

### Omisiones

- **El Test de 7 Preguntas (§9 de la constitución) no está integrado explícitamente en el Protocolo de Greenlight de 10 puntos, aunque la propia constitución (§10) exige: 'Sus 10 puntos de Greenlight incorporan la pregunta filtro y el Test de 7'. Solo el punto 1 (Filtro de Expansión Humana) coincide; faltan preguntas clave como '¿Puedo defenderlo sin comprometer mi independencia de criterio?', '¿Respeta la inteligencia de la audiencia?' y sobre todo '¿Me sentiría orgulloso de que esto siguiera asociado a mi nombre dentro de diez años?' (el punto 6 'Longevity' solo pregunta por potencial evergreen del contenido, no por el orgullo/reputación a 10 años).** — La constitución señala este test como 'el filtro más duro y el más útil contra el clickbait'; sin él integrado, el Greenlight puede aprobar ideas que pasan el filtro de expansión humana pero fallan en independencia de criterio o en sostenibilidad reputacional a largo plazo. *(dónde: FASE 3 (Protocolo de Greenlight) de system_prompt.md, añadiendo puntos explícitos que mapeen 1:1 con las 7 preguntas de la constitución.)*
- **El listado de las 10 anti-asociaciones (gurú de IA, divulgador de novedades, vendedor de humo, fanático tecnológico, propagandista político, creador polarizante, influencer mercantilizado, persona definida por una plataforma, perseguidor de métricas o competidores, experto con todas las respuestas) no aparece como checklist explícito dentro del Greenlight o el Packaging Lab.** — La constitución exige en §10: 'Ningún packaging puede empujar hacia una anti-asociación.' Sin un chequeo explícito, la revisión queda a criterio implícito del agente en lugar de ser un veto sistemático y auditable. *(dónde: FASE 3, punto 'Packaging Potential' o como un nuevo ítem de verificación previo al veredicto GO/REWORK/NO-GO.)*
- **No se incorpora la regla de mínimo 5 publicaciones de la misma línea antes de declarar una tendencia, ni la advertencia de que una correlación puede explicarse por el orden de publicación / curva de aprendizaje del creador en lugar de por la variable medida (§2, reglas 4 y 6 de la constitución).** — Sin estas salvaguardas, el Postmortem (Fase 5) podría inducir a Mr. You a declarar patrones prematuros o atribuir mejoras de retención a una variable de formato cuando en realidad reflejan la evolución natural del creador, violando la disciplina de DATO/PATRÓN/HIPÓTESIS que el propio agente dice seguir. *(dónde: FASE 5 (Postmortem & Aprendizaje de Resonancia), como criterios adicionales antes de clasificar algo como PATRÓN.)*

---

## 🟡 borges

Borges está bien alineado en su foco central (el ser humano y no la corporación/tecnología, la historia detrás de la historia), pero su lenguaje de 'romper el scroll' y su propio ejemplo práctico se inclinan hacia datos espectaculares y ganchos de retención, en tensión con lo que la constitución le exige explícitamente en §10 y §2. No hay contradicciones graves de anti-asociaciones, pero sí omisiones claras de la pregunta filtro y del amarre vulnerabilidad-aprendizaje.

### Contradicción — severidad media

**El agente dice:**
> Entrega 3 opciones de ganchos acústicos que rompan el scroll en los primeros 3 segundos, centrados directamente en el personaje y su conflicto o contradicción inicial

**La constitución dice:**
> Prohibido proponer packaging que suba CTR a costa de las anti-asociaciones. El canal no persigue clics: construye catálogo.

**Por qué:** Pedir explícitamente ganchos que 'rompan el scroll en los primeros 3 segundos' encuadra el objetivo en retención/CTR, justo el lenguaje que la constitución busca evitar como criterio rector del packaging, aunque el resto de la ficha sí prioriza la profundidad humana.

**Corrección sugerida:** Reformular como: 'Entrega 3 opciones de apertura que planteen de inmediato la contradicción o tensión humana del personaje, sin optimizar para retención sino para claridad narrativa.'

### Contradicción — severidad media

**El agente dice:**
> Hoy en día domina la tecnología de pantallas táctiles y fabrica componentes críticos para los robots y vehículos de Elon Musk [Tesla] y Tim Cook [Apple], quienes dependen directamente de su perseverancia.

**La constitución dice:**
> Busca las particularidades humanas, no el currículum del personaje. Ángulos no evidentes sobre datos espectaculares.

**Por qué:** El ejemplo práctico de Borges cierra la historia apoyándose en nombres y marcas espectaculares (Elon Musk, Tim Cook, Tesla, Apple) como prueba de legado, exactamente lo que la constitución pide evitar a favor de un ángulo humano no evidente. Contradice la obligación específica que la propia constitución le asigna a este agente en §10.

**Corrección sugerida:** Cerrar el ejemplo con una particularidad humana no evidente (ej. cómo su ceguera del padre moldeó su meticulosidad en el pulido de vidrio) en vez de listar clientes/marcas famosas como validación del legado.

### Omisiones

- **No hay ninguna referencia explícita a la pregunta filtro (§0, '¿esto contribuye a la expansión humana?') como criterio de selección o clasificación de historias.** — Borges decide qué protagonistas avanzan hacia Gabo y la newsletter; sin este filtro, la selección puede quedar solo en 'historia de superación llamativa' y no en si expande posibilidades humanas para la audiencia. *(dónde: En la sección '📌 1. CLASIFICACIÓN DE LA HISTORIA', antes de asignar el Nivel, agregar una justificación explícita de por qué esta historia contribuye a la expansión humana.)*
- **Ningún mecanismo que ate la exposición de dificultades/infancia/pérdidas ('Detalla los momentos de mayor dificultad de la infancia/juventud') a que esa vulnerabilidad ilumine un aprendizaje concreto, tal como exige §6 ('Vulnerabilidad cuando ilumina un aprendizaje, nunca como explotación emocional').** — Sin ese amarre explícito, la sección 5 (Cronología de Quiebre) puede derivar en drama de sufrimiento por impacto emocional puro, en vez de aprendizaje transferible a la audiencia. *(dónde: En la sección '📊 5. CRONOLOGÍA DE QUIEBRE Y FACTOR HUMANO', añadir una pregunta obligatoria tipo '¿qué aprendizaje transferible ilumina este momento de dificultad?'.)*
- **No se menciona ninguna revisión contra las anti-asociaciones (ej. evitar que la historia termine glorificando la tecnología/corporación por sí misma, o el 'fanático tecnológico') antes de enviar la ficha a Gabo.** — Borges declara que evita centrarse en la tecnología/corporación, pero no hay un paso de verificación explícito, y el ejemplo interno ya se desvía hacia ese terreno. *(dónde: Al final de la metodología de investigación, agregar un checklist rápido contra las 10 anti-asociaciones de la constitución antes de entregar la ficha.)*

---

## 🟡 leonardo

Leonardo está mayormente alineado con la identidad visual editorial de HUMANOS (sobriedad, anti-clickbait, espacio negativo), pero su propia descripción de especialidad usa 'alto CTR' como objetivo, lo que choca directamente con el principio 'el canal no persigue clics: construye catálogo' de §2. Falta además que su checklist conecte con la pregunta filtro y el manejo correcto de métricas.

### Contradicción — severidad alta

**El agente dice:**
> Especialidad: Dirección de arte, identidad visual, consistencia de marca, diseño de miniaturas de alto CTR y motion design cinematográfico.

**La constitución dice:**
> El canal no persigue clics: construye catálogo.

**Por qué:** Definir el 'alto CTR' como especialidad nuclear de Leonardo instala la métrica de clics como objetivo de diseño, exactamente lo que la constitución identifica como riesgo ('el sistema... empezó a recomendar decisiones de formato basadas en la retención') y descarta explícitamente en §2. También roza la anti-asociación 'Perseguidor de métricas: Producir por ansiedad de números'.

**Corrección sugerida:** "Especialidad: Dirección de arte, identidad visual, consistencia de marca, diseño de miniaturas que sostienen la curiosidad sin depender del CTR, y motion design cinematográfico."

### Omisiones

- **Ninguna referencia a la pregunta filtro ('¿esto contribuye a la expansión humana?') ni al Test de 7 preguntas en el checklist de aprobación de Leonardo.** — La constitución dice que la leen TODOS los agentes 'antes de producir, evaluar o recomendar nada'; el checklist de Leonardo solo pregunta '¿Parece HUMANOS?' sin ningún filtro que conecte lo visual con el propósito de marca más amplio (por ejemplo, si una miniatura de alto impacto visual empuja hacia clickbait o hacia una anti-asociación como 'creador polarizante'). *(dónde: En 'El Checklist de Aprobación de Leonardo' (personality.md) y en la sección 2.A del system_prompt.md, como pregunta adicional antes de aprobar.)*
- **No se menciona cómo Leonardo debe tratar datos de retención/CTR reales cuando lleguen (distinguir DATO/PATRÓN/HIPÓTESIS de §2.5).** — Si en el futuro Talese o Mark le pasan datos de performance de miniaturas, Leonardo no tiene instrucción explícita de que esos datos informan pero no deciden el diseño, lo cual es justamente el problema que originó la sección §2 de la constitución. *(dónde: Nueva sub-sección en system_prompt.md, cerca de 'Auditoría y Revisión Visual', aclarando que las métricas de CTR no reemplazan el criterio del Design System.)*

---

## 🟡 talese

Talese está fuertemente alineado con la constitución en su principio central (medir evolución, no éxito, métricas que informan) y su prudencia de autoría (status PROPOSED). La tensión real es un umbral de evidencia más laxo (3 vs 5+) para pasar de observación a recomendación, y faltan chequeos explícitos sobre confusión por orden de publicación y sobre no empujar hacia anti-asociaciones al perseguir números.

### Contradicción — severidad media

**El agente dice:**
> SIGNAL: Empieza a repetirse entre episodios (2 evidencias). Se mantiene en observación. PATTERN: Evidencia consistente entre 3+ episodios. Puede convertirse en recomendación editorial.

**La constitución dice:**
> Antes de llamar algo "tendencia": idealmente 5+ publicaciones de la misma línea y varias capturas en el tiempo. Con menos se puede hablar igual, marcándolo como hipótesis.

**Por qué:** Talese puede promover algo a PATTERN (habilitado para 'recomendación editorial') con solo 3 episodios, mientras la constitución pide 5+ evidencias antes de tratar algo como patrón consolidado. El umbral más bajo de Talese puede producir recomendaciones que la propia constitución consideraría todavía hipótesis, tensionando el principio de §2 de que las métricas informan pero no deciden.

**Corrección sugerida:** Renombrar el nivel de 3+ evidencias como 'PATTERN (hipótesis fuerte)' y reservar 'PATTERN (recomendación editorial)' para 5+ evidencias, alineando el umbral con §2.4 de la constitución.

### Omisiones

- **No hay instrucción explícita para distinguir si una correlación observada se explica por el orden de publicación (curva de aprendizaje del creador) en vez de por la variable que se está midiendo — algo que §2.6 pide explícitamente ('Señalar cuándo una correlación puede explicarse por el orden de publicación...').** — Talese es precisamente el agente que compara episodios en el tiempo y propone PATTERNS; sin este chequeo corre el riesgo de atribuir a una técnica editorial lo que en realidad es simple mejora acumulada del creador, generando falsas 'evidencias'. *(dónde: En 'Filosofía & Principios Operativos Innegociables', como punto adicional al ítem 3 (Evidencia antes que opinión).)*
- **No se menciona el chequeo de §2.3: si la única forma de subir un número implica adoptar una de las anti-asociaciones de §1, el agente debe señalarlo en vez de proponerlo.** — Talese es quien convierte métricas en recomendaciones (Retro de Desempeño); sin este filtro explícito, una 'recomendación' basada en retención podría empujar sin querer hacia posturas como 'perseguidor de métricas' o 'divulgador de herramientas'. *(dónde: En la sección 'Salidas & Formato de Respuesta', punto 2 (Creator Changelog), como criterio de validación antes de proponer una entrada.)*
- **No usa explícitamente la distinción DATO / PATRÓN / HIPÓTESIS / BEST PRACTICE EXTERNA de §2.5, sino solo OBSERVATION / SIGNAL / PATTERN.** — Son taxonomías parcialmente solapadas pero no idénticas; sin mapear una a la otra, puede no quedar claro cuándo una recomendación se apoya en evidencia propia versus en una 'best practice externa' (p.ej. una tendencia de la industria, no del propio catálogo). *(dónde: En la sección de clasificación en tres niveles, aclarando la relación con la taxonomía de §2.5 de la constitución.)*

---

## 🟢 veritas

Veritas está bien alineado con su mandato específico en §10 (no convertir exploración en hecho, declarar incertidumbre, exigir evidencia). No se detectaron contradicciones directas con la constitución, solo una omisión de conexión explícita con el marco más amplio (pregunta filtro, anti-asociaciones, reglas de métricas).

### Omisiones

- **No hay ninguna referencia a la pregunta filtro (§0), al Test de 7 preguntas (§9), ni a las anti-asociaciones (§1) como parte de su función de quality gate. Veritas define su rol únicamente en torno a verificación factual, sin mención de que también debería señalar cuando un claim aprobado factualmente pueda estar siendo usado para construir una narrativa que ancle a Jota a una anti-asociación (p.ej. 'gurú de IA') o que viole §2 (métricas informan, no deciden).** — La constitución dice explícitamente que 'La leen TODOS' los agentes antes de producir, evaluar o recomendar nada, y asigna a Veritas la obligación específica de 'proteger el principio de no presentar exploraciones como hechos comprobados' (tabla §10). Ese mandato puntual sí está cubierto (ver VERIFIED/PARTIAL/UNVERIFIED y la filosofía de 'no sabemos todavía'), pero el resto del aparato de la constitución (pregunta filtro, anti-asociaciones, reglas de métricas §2) no aparece nunca en sus documentos, dejando ambiguo si Veritas debe aplicarlos o si su scope es puramente factual y otro agente cubre eso. *(dónde: En SOUL.md, sección 'Quality Gate' o 'Lo que NO hago', agregar una nota explícita de que Veritas opera bajo la Constitución de marca y que, si detecta que un claim verificado se usaría para reforzar una anti-asociación o para convertir una métrica de corto plazo en mandato de cambio de rumbo (§2), debe señalarlo aunque no sea estrictamente su función corregirlo.)*

---

## 🟢 moore

Moore es un agente puramente técnico de storyboard/gestión de assets, coherente con el rigor documental y anti-presunción de la constitución; no se detectan contradicciones directas, solo omisiones respecto al estándar creativo §11 y a la trazabilidad de fallbacks no-originales.

### Omisiones

- **La constitución (§10) asigna explícitamente a Moore el 'Estándar creativo de la estrategia: intención visible, sin hype vacío', pero ni el system_prompt ni personality.md mencionan ese estándar ni cómo aplicarlo al diseñar efectos, captions o estilo visual.** — Sin esa referencia, el agente puede diseñar 'caption' o 'effect' (ej. text_overlay con frases tipo 'OBSESIÓN: PRIVACIDAD') optimizados por impacto visual sin ningún chequeo contra hype vacío o anti-asociaciones como 'vendedor de humo' o 'creador polarizante'. *(dónde: En 'Instrucciones de Operación', punto 4 (Diseño de Edición), agregar una verificación explícita: los captions y efectos no deben generar hype ni polarización, deben tener intención visible.)*
- **No hay ninguna mención a que los 'fallback_strategy' (stock libre de derechos, tomas de apoyo genéricas) deban señalarse como tales ante la audiencia y no presentarse como material auténtico del archivo real.** — La constitución exige (§6) 'La obra demuestra; el copy no presume' y (Veritas, §10) 'no presentar exploraciones como hechos comprobados'. Usar un asset de stock para simular un momento histórico real sin distinguirlo podría vulnerar la fidelidad documental que el propio Moore dice proteger. *(dónde: En la 'Regla Madre de Producción' o en el punto 2 de Instrucciones de Operación, aclarar que todo fallback debe quedar trazable como no-original en el registro de edición.)*

---

## 🟢 curie

Curie está bien alineado: su función de taxonomía y deduplicación no toca ninguna anti-asociación ni la pregunta filtro directamente. Las omisiones son de matiz — podría anclar mejor sus cruces narrativos al lente §5 y a la disciplina de evidencia del §2.

### Omisiones

- **No hay mención al lente editorial §5 ('las historias detrás de las historias y los patrones detrás de las cosas') ni a la pregunta filtro §0 al generar sugerencias de cruce narrativo.** — Curie alimenta directamente a Gabo con cruces narrativos; si su taxonomía prioriza patrones temáticos genéricos (obsesión, rivalidad, resiliencia) sin conectar explícitamente con el lente §5 o la pregunta filtro §0, corre el riesgo de sugerir cruces correctos en forma pero vacíos en fondo (ej. coincidencias superficiales de tema en vez de 'la historia detrás de la historia'). *(dónde: En el punto 3 de 'Instrucciones de Operación' del system_prompt.md, al describir qué debe contener la 'propuesta de cruce narrativo'.)*
- **No se menciona la distinción DATO / PATRÓN / HIPÓTESIS / BEST PRACTICE EXTERNA (§2.5) al validar patrones temáticos cruzados entre personajes.** — Curie identifica 'patrones' entre personajes (ej. pobreza extrema en la infancia compartida por varios), y la constitución exige marcar explícitamente si algo es patrón confirmado o hipótesis con poca evidencia (menos de 5 casos). Sin esta distinción, Curie podría presentar coincidencias anecdóticas como patrones establecidos. *(dónde: En el punto 3 de 'Instrucciones de Operación', al generar la 'Sugerencia exacta de cómo entrelazar esa anécdota'.)*

---

## 🟢 hermoso

Hermoso es un agente operativo/técnico (pipeline, telemetría, alertas, verificación de evidencia) y no contradice ningún principio de marca explícito. Su ausencia es de tipo omisión: sus 'quality gates' y disparadores de alerta son puramente técnicos y no incorporan el filtro editorial de la constitución (§0 y §9) en el punto donde controla la transición a `published`.

### Omisiones

- **Hermoso controla las transiciones de estado del pipeline (incluida la transición a `published`) y define 'Quality Gates' propios ('¿Está completo? ¿Es verificable? ¿Hay fuentes o trazabilidad? ¿Hay supuestos no declarados? ¿Hay riesgo reputacional, comercial o técnico? ¿El siguiente paso está claro?'), pero ninguno de esos gates referencia el Test de 7 preguntas (§9) ni la pregunta filtro (§0) antes de marcar un episodio como listo para publicar.** — La constitución dice que la pregunta filtro y el Test de 7 se aplican 'antes de publicar, construir, asociarse o recomendar' (§9), y Hermoso es literalmente quien controla esa transición de estado hacia `published`. Si su quality gate es solo técnico (evidencia, trazabilidad, riesgo) y no editorial/de marca, puede dejar pasar contenido que roza una anti-asociación de §1 o que no responde a §0 sin que nadie lo frene en el punto donde efectivamente se decide publicar. *(dónde: En personality.md, sección 'Quality Gates', agregar un ítem tipo: '¿Este episodio pasó el Test de 7 preguntas de la constitución de marca? ¿Alguna anti-asociación de §1 quedó sin resolver en el pipeline de Borges/Gabo/Moore?')*
- **El system_prompt.md no menciona qué hace Hermoso si detecta que el guion de Gabo o el storyboard de Moore contradice explícitamente algún principio de la constitución (por ejemplo, polarización fabricada, o una postura de 'gurú de IA') antes de notificar al editor humano como 'listo para grabar'.** — La constitución pide (§10) que 'ningún packaging pueda empujar hacia una anti-asociación' para Mr. You, y espera un rol similar de contención en otros puntos del pipeline; Hermoso, como orquestador del ciclo de vida, es el lugar natural para escalar ese tipo de alerta antes de avisar al humano, no solo alertar sobre fallos técnicos o bloqueos de asset. *(dónde: En system_prompt.md, punto 2 ('Alertas y Mensajería'), añadir un cuarto disparador de notificación: 'Se detecte contenido que roce una anti-asociación o contradiga un principio vinculante de la constitución de marca (§6), aun si el pipeline técnico está completo.')*

---

## Nota

Nada se corrigió automáticamente. Cambiar el prompt de un agente cambia cómo piensa, y eso es decisión de Jota.
