# HUMANOS Production Bible
**Version:** 1.0  
**Status:** ACTIVE  
**Owner:** Jota Ochoa

---

# Filosofía
* **HUMANOS** no es un canal de curiosidades.
* Es un canal de documentales cortos sobre las personas detrás de las empresas, inventos e ideas que cambiaron el mundo.
* Cada decisión creativa debe responder una sola pregunta: **"¿Esto ayuda a contar mejor la historia?"**. Si no ayuda, se elimina.
* El objetivo nunca es impresionar con edición; el objetivo es que el espectador no pueda dejar de mirar.

---

# Referencias
* **40%** Johnny Harris
* **30%** Apple Keynote
* **20%** Netflix Documentary
* **10%** MagnatesMedia
* **Jamás:** Parecer TikTok genérico ni plantilla de CapCut.

---

# Identidad Visual

### Color Principal
* **HEX:** `#01C9C7` (Cian)
* **RGB:** `1, 201, 199`
* **Regla de uso:** Es el único color de acento del canal. Usarlo únicamente para el nombre del personaje, palabras clave o elementos gráficos muy importantes. Nunca abusar del cian: *si todo es cian, nada es cian.*

### Tipografía
* **Principal (Montserrat Bold):** Usar exclusivamente para el nombre del personaje y títulos principales.
* **Secundaria (Inter SemiBold):** Usar para categorías, cargos, datos en pantalla y subtítulos.

---

# Configuración del Proyecto
* **Formato:** 9:16 (Vertical)
* **Resolución:** 1080x1920
* **FPS:** 30
* **Espacio de Color:** Rec709 SDR

---

# Flujo de Producción
```
Borges → Veritas → Gabo → Moore → Narración → CapCut → Revisión → Publicación
```

---

# Beat Sheet
* Antes de editar: toda narración debe dividirse en bloques narrativos (Escenas), nunca editar directamente por segundos de línea de tiempo de forma ad-hoc.
* **Flujo ejemplo:** `Hook` → `Infancia` → `Problema` → `Empresa` → `Éxito` → `Legado`

---

# Audio
* **Voz:** La narración manda, todo lo demás acompaña.
* **Velocidad de narración:** 1.16x recomendada (siempre que mantenga calidad natural).
* **Música:** Muy sutil, nunca debe competir con el rango de la voz.
* **FX:** Risers, impacts, whooshes y ambientes. Siempre discretos.

---

# Intro
* **Duración:** 2-3 segundos.
* **Regla:** Siempre debe ir después del Hook. Nunca abrir un video con el logotipo del canal.

---

# Character Card
* **Duración:** 3.2 segundos aproximadamente.
* **Fotografía:** Escala de grises (B/N) ajustando saturación inicial entre `-40` y `-70` según la imagen original (nunca aplicar filtros B&N automáticos).
* **Diseño / Layout:**
  ```
  [CATEGORÍA (Inter SemiBold, Blanco)]
  [NOMBRE (Montserrat Bold, Cian #01C9C7)]
  [Cargo/Rol (Inter SemiBold, Blanco)]
  ```
  *Ejemplo:*
  ```
  INMIGRANTE
  JAN KOUM
  Fundador de WhatsApp
  ```
* **Posición:** Esquina inferior izquierda, dejando mucho aire/espacio negativo alrededor.
* **Animación:** Solo el nombre lleva animación protagonista (llenado de texto/write-on). Los demás elementos entran con fundido suave (Fade).

---

# Subtítulos
* **Estilo:** Híbrido. No palabra por palabra, no frases completas.
* **Densidad:** Bloques de 3 a 6 palabras.
* **Líneas:** Máximo 2 líneas por bloque.
* **Tipografía:** Inter SemiBold, color Blanco, contorno Negro de 5 px.
* **Palabras Clave:** Solo **una** palabra importante por bloque puede ir en color cian. Nunca destacar dos en el mismo bloque.
* **Posición:** Ubicados al **75-80% de la altura** de la pantalla para evitar que los oculte la interfaz nativa de Shorts, Reels o TikTok.

---

# Movimiento
* **Regla de oro:** Nunca usar efectos automáticos de CapCut. Todo movimiento se hace de forma controlada mediante Keyframes.
* **Movimientos Oficiales:**
  * **Push In:** `100%` → `108%`
  * **Push Out:** `108%` → `100%`
  * **Paneo Horizontal:** Izquierda → Derecha
  * **Paneo Vertical:** Arriba → Abajo
  * **Reveal:** Mostrar detalle → Abrir plano
* **Regla:** Un solo movimiento por plano. Nunca combinar Zoom + Paneo + Rotación en la misma toma.

---

# Transiciones
* **80%:** Corte directo.
* **20%:** Disolver (duración de `0.2` a `0.3` segundos).
* **Prohibido:** Usar transiciones tipo Flip, Cube, Glitch, Zoom Transition, Página o efectos llamativos similares.

---

# Timeline (Pistas de Edición)
### Video
* **V5:** Subtítulos
* **V4:** Character Card
* **V3:** Overlays / Textos adicionales
* **V2:** Intro / Elementos de Motion Graphics
* **V1:** Video principal / Archivo de fondo

### Audio
* **A3:** FX (Efectos de sonido)
* **A2:** Música
* **A1:** Narración (Voz en off principal)

---

# Organización del Proyecto
La organización estructurada del material vive en Windows (directorio raíz `Studio_CapCut`), no en la base de datos interna de CapCut.

### Carpeta Studio_CapCut
* `Templates/`
* `Projects/`
* `Assets/`
* `Music/`
* `SFX/`
* `Exports/`

---

# Assets y Versionado
* La Intro, la Character Card y el Outro son assets independientes y se manejan versionados (ej. `Intro_v1`, `Outro_v1`). Nunca se renderizan pre-unidos en un mismo archivo de video de stock.

---

# Parámetros de Exportación
* **Formato:** Vertical (1080x1920)
* **FPS:** 30 FPS
* **Codec:** H.264
* **Bitrate:** Alto

---

# Regla Editorial de Contenido
* Cada recurso visual debe reforzar la historia.
* Nunca llenar espacios vacíos con material irrelevante.
* Nunca mover una imagen de forma arbitraria; cada movimiento de cámara lenta debe tener intención narrativa clara.

---

# Checklist de Producción
* [ ] Guion aprobado
* [ ] Veritas (Fact check aprobado)
* [ ] Beat Sheet definido
* [ ] Narración / Locución grabada
* [ ] Estructura de Hook lista
* [ ] Intro y Outro integrados
* [ ] Character Card renderizada
* [ ] Selección de Imágenes
* [ ] Animación de Keyframes aplicada
* [ ] Música sutil mezclada
* [ ] FX de sonido agregados
* [ ] Subtítulos posicionados y corregidos
* [ ] Revisión final de branding
* [ ] Exportación
* [ ] Miniatura (Thumbnail) diseñada
* [ ] Publicación en plataformas

---

# Principio Final
> La audiencia no debe recordar la edición. Debe recordar la historia.
> Si el espectador nota los efectos, los efectos son demasiado fuertes.
> La edición perfecta es invisible.
