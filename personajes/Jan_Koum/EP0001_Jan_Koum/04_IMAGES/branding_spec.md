# Reporte de Dirección de Arte: JAN KOUM - HUMANOS

**Proyecto:** HUMANOS
**Sujeto:** Jan Koum
**Fecha:** 24 de mayo de 2023

---

## 1. Introducción

Este reporte detalla la dirección de arte y las especificaciones visuales para el contenido relacionado a Jan Koum, cofundador de WhatsApp. El objetivo es mantener la coherencia estética premium, editorial y minimalista definida por el HUMANOS Design System v1.0, asegurando que cada elemento visual refuerce la narrativa y la marca.

---

## 2. Dirección de Arte General

La narrativa de Jan Koum se centra en su viaje desde Ucrania hasta el éxito en el mundo tecnológico, destacando la resiliencia y la profunda transformación personal y social. La dirección de arte debe reflejar esta trayectoria a través de un contraste visual marcado entre sus orígenes y su logro. El blanco y negro, el alto contraste y el minimalismo serán pilares fundamentales.

---

## 3. Especificaciones de Entregables

### 3.1. Miniatura (Thumbnail)

*   **Composición y Justificación:** Se ha optado por un primer plano de Jan Koum, ocupando el 75% del encuadre, con una mirada directa a cámara. Este encuadre maximiza la conexión emocional y la presencia del personaje, cumpliendo con la regla del 60-80% de ocupación, lo que garantiza que el protagonista sea el foco absoluto. El fondo negro absoluto proporciona el espacio negativo necesario para aislar al personaje y transmitir la seriedad inherente a su historia.
*   **Texto:**
    *   Titular: "De cupones a miles de **millones**"
    *   Palabra clave resaltada: "**millones**" en cian (`#01C9C7`).
    *   El resto del texto en blanco (`#FFFFFF`).
*   **Tipografía:** Inter para el texto principal. La palabra destacada en cian no solo sigue la guía de marca, sino que enfatiza el logro financiero, un punto clave de su trayectoria. La elección de "millones" en cian es una decisión estratégica para captar la atención sin recurrir a elementos de clickbait.

### 3.2. Character Card

*   **Composición y Justificación:** Se utilizará un retrato documental a sangre, ocupando aproximadamente el 80% del espacio, alineado con la propuesta de la especificación. La escasez de elementos visuales y el fondo negro profundo aseguran la máxima legibilidad y un impacto estético elevado, priorizando la identidad de Jan Koum. El abundante espacio negativo superior e inferior es crucial para la respiración visual y la sensación de producción premium.
*   **Texto:**
    *   Categoría superior: "PIONERO" en gris suave (`#A7A7A7`).
    *   Nombre: "JAN KOUM" en Satoshi ExtraBold, utilizando el cian (`#01C9C7`) como color de énfasis para la marca.
    *   Descripción/Cargo: "cofundador de whatsapp" en gris suave (`#666666`) y un tamaño menor.
*   **Tipografía:** Satoshi ExtraBold para el nombre proporciona la fuerza visual y el carácter distintivo requerido para los títulos principales, alineándose perfectamente con la marca HUMANOS.

---

## 4. Prompts de IA para Generación de Contenido Visual

La generación de prompts se rige por la fórmula editorial premium, buscando consistentemente la estética HUMANOS:

*   **Prompt para Miniatura / Retrato Principal:**
    ```
    Jan Koum, co-founder of WhatsApp, serious expression, intense gaze, framed in a dramatic journalistic portrait, high contrast black and white, deep shadows, shot on 85mm lens, subtle 35mm film grain, editorial magazine style page --ar 16:9
    ```
    *   **Justificación:** Este prompt se enfoca en capturar la esencia documental y seria de Koum. La elección de un retrato periodístico de revista (estilo *Esquire*), alto contraste en blanco y negro, el uso de una lente de retrato clásica (85mm) y un toque de grano de película de 35mm buscan evocar autenticidad, intimidad y una calidad editorial superior. Evita cualquier connotación de stock artificial.

*   **Prompt para B-roll Fotografía Infancia Ucrania:**
    ```
    Exterior shot of Soviet-era apartment blocks (Plattenbau), cold, overcast sky, stark atmosphere, with a single vintage Soviet-era telephone booth in the foreground, minimal saturation, high contrast black and white, cinematic documentary style --ar 16:9
    ```
    *   **Justificación:** Representa visualmente el origen de Koum. Los bloques de apartamentos soviéticos, el cielo nublado y la atmósfera austera, junto al teléfono antiguo como único elemento, refuerzan la idea de un entorno limitado y de una era pasada. El blanco y negro de alto contraste y la baja saturación evocan la dureza y la realidad de la época, sin sentimentalismos.

*   **Prompt para B-roll Fotografía Estados Unidos - Asistencia Social:**
    ```
    Interior shot of a bleak, utilitarian government assistance office in 1990s USA, with people queuing, harsh fluorescent lighting, subtle grain, high contrast black and white, documentary realism, evoking struggle and anonymity --ar 16:9
    ```
    *   **Justificación:** Este prompt ilustra el período inicial de lucha y adaptación en Estados Unidos. El entorno austero, la iluminación artificial cruda y la representación de personas en una fila transmiten la sensación de anonimato y las dificultades de la integración y el acceso a servicios básicos. La estética documental realista y el alto contraste son clave para mantener la narrativa sombría pero honesta.

*   **Prompt para Representación Conceptual de WhatsApp:**
    ```
    Clean, minimalist composition of two simple speech bubbles in white against a deep black background, conveying direct communication, subtle hint of the cyan accent color (#01C9C7) as a single dividing line, stark, editorial, high contrast --ar 16:9
    ```
    *   **Justificación:** Para representar la esencia de WhatsApp de forma conceptual, se opta por una composición extremadamente minimalista. Dos burbujas de diálogo blancas sobre negro profundo comunican simplicidad y comunicación directa, pilares de la aplicación. El uso sutil del cian como línea divisoria es un guiño a nuestra identidad de marca, utilizado de forma funcional y no decorativa. Es una imagen que respira y comunica el concepto central de la plataforma de manera elegante.

---

## 5. Especificaciones de Motion Design

*   **Velocidad de Cámara:** `slow_zoom`
    *   **Justificación:** Un zoom lento sobre Jan Koum o los elementos de b-roll permitirá al espectador absorber la información visual y emocional de la imagen, manteniendo la cadencia pausada y reflexiva que define a HUMANOS. Evita la sensación de urgencia o de contenido rápido.
*   **Transición por Defecto:** `subtle_fade` (fundido suave)
    *   **Justificación:** La fundición suave entre escenas o imágenes es la opción más limpia y editorial. Minimiza las distracciones y mantiene un flujo visual coherente y premium, en línea con la prohibición de transiciones abruptas o llamativas.
*   **Uso del Color de Marca:** El cian (`#01C9C7`) se aplicará de forma puntual y estratégica, principalmente en elementos de transición de texto (como el logo "HUMANOS" o la mención del nombre de Jan Koum en la Character Card), asegurando que no compita visualmente sino que sirva como un distintivo funcional y reconocible.
*   **Fuentes de Títulos:** Satoshi (Bold/ExtraBold), para mantener la jerarquía y el carácter editorial de los títulos principales.
*   **Fuentes de Subtítulos:** Inter, por su legibilidad y neutralidad, ideal para texto informativo y descripciones.

---

## 6. Conclusión

Hemos diseñado la dirección de arte para Jan Koum con una atención meticulosa a los principios del HUMANOS Design System. La sobriedad, el contraste y el enfoque en la narrativa testimonial son la base de todas las piezas visuales, asegurando que el contenido no solo informe sino que también ofrezca una experiencia estética premium y memorable. Cada decisión, desde la composición fotográfica hasta la elección tipográfica y los prompts de IA, está orientada a responder la pregunta fundamental: "¿Esto parece HUMANOS?".