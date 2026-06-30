# Guía de Edición en CapCut - Adidas_vs_Puma

## Estilo Visual y Ritmo
- **Estilo General:** Color gradado cálido, textura de grano de película analógica
- **Estilo de Música:** Documental tension / piano minimalista
- **Horas de Edición Estimadas:** 12.0 horas

## Estructura de Edición de Escenas:

### Escena 1 (Duración: 6.0s)
- **Locución (Voiceover):** "¿Sabías que Adidas y Puma nacieron de la furia entre dos hermanos? Adi y Rudolf Dassler iniciaron una fábrica de calzado en 1924."
- **Efecto de Transición/Cámara:** cut
- **Texto en Pantalla (Caption):** "1924: Hermanos Dassler, Una sociedad que cambió el calzado"
- **Estado de Asset:** MISSING
- **Estrategia Fallback (Visual):** Mostrar el logo de Adidas original y luego el de Puma original, alternándolos rápidamente. Para los hermanos jóvenes, buscar fotos de Adi y Rudolf Dassler jóvenes juntos.
- **ID de Vacío Crítico (Gap):** gap_001

### Escena 2 (Duración: 8.0s)
- **Locución (Voiceover):** "Su éxito fue brutal: Jesse Owens ganó cuatro oros olímpicos en 1936 con sus zapatillas, disparando su fama."
- **Efecto de Transición/Cámara:** slow_zoom
- **Texto en Pantalla (Caption):** "1936: 4 Oros Olímpicos, El Mundo los Conoce"
- **Estado de Asset:** MISSING
- **Estrategia Fallback (Visual):** Ya que el video de Jesse Owens no ha sido descargado, usar el asset 'Rudolf Dassler portrait older' como un plano de contexto mientras se narran los logros de Owens para establecer la fama de la marca familiar.
- **ID de Vacío Crítico (Gap):** gap_002

### Escena 3 (Duración: 7.0s)
- **Locución (Voiceover):** "Pero la hermandad se pudrió con la Segunda Guerra Mundial, por diferencias personales y políticas. El quiebre fue total."
- **Efecto de Transición/Cámara:** text_overlay
- **Texto en Pantalla (Caption):** "Segunda Guerra Mundial: La Fractura"
- **Estado de Asset:** MISSING
- **Estrategia Fallback (Visual):** Mientras no tengamos el material específico de tensión entre los hermanos o el archivo de la SGM, mostrar una toma de las zapatillas Adidas tempranas (asset '007') como un recordatorio del objeto de su conflicto, con una superposición de texto que indique 'Tensión Creciente'.
- **ID de Vacío Crítico (Gap):** gap_003

### Escena 4 (Duración: 8.0s)
- **Locución (Voiceover):** "En 1948, dividieron la empresa sin miramientos. Adi fundó Adidas; Rudolf, Puma."
- **Efecto de Transición/Cámara:** animation
- **Texto en Pantalla (Caption):** "1948: La División, Nace una Rivalidad Eterna"
- **Estado de Asset:** AVAILABLE
- **Estrategia Fallback (Visual):** None

### Escena 5 (Duración: 12.0s)
- **Locución (Voiceover):** "Herzogenaurach, su ciudad natal, se partió en dos. Literalmente. Los habitantes elegían uno u otro, y las tiendas, los bares, se dividieron por lealtades."
- **Efecto de Transición/Cámara:** pan_right
- **Texto en Pantalla (Caption):** "Herzogenaurach: Dividida"
- **Estado de Asset:** MISSING
- **Estrategia Fallback (Visual):** Mostrar el logo de Adidas y Puma (asset_id '004') lado a lado sobre un fondo neutro para ilustrar la división. Crear una animación donde los logos se alejan uno del otro.
- **ID de Vacío Crítico (Gap):** gap_004

### Escena 6 (Duración: 13.0s)
- **Locución (Voiceover):** "Cada uno invirtió millones en eclipsar al otro. La guerra fría de las zapatillas convirtió a los hermanos en gigantes globales. Nunca se reconciliaron. Sus imperios crecieron desde una herida que jamás cerró."
- **Efecto de Transición/Cámara:** mountage
- **Texto en Pantalla (Caption):** "Guerra Fría de las Zapatillas, Una Herida Abierta"
- **Estado de Asset:** MISSING
- **Estrategia Fallback (Visual):** Usar los logos '003' y '004' en un montaje rápido intercalado con imágenes abstractas de competencia o clips de deportes genéricos (si están disponibles), finalizando con un texto en pantalla que diga 'Nunca se reconciliaron'
- **ID de Vacío Crítico (Gap):** gap_005

### Escena 7 (Duración: 10.0s)
- **Locución (Voiceover):** "Yo soy Jota y esto es HUMANOS: historias de personas que construyeron desde una herida, una obsesión o una contradicción. Nos vemos en la próxima historia."
- **Efecto de Transición/Cámara:** fade
- **Texto en Pantalla (Caption):** "None"
- **Estado de Asset:** MISSING
- **Estrategia Fallback (Visual):** Mostrar una placa con el logo de HUMANOS y el nombre 'Jota', con música de cierre.
- **ID de Vacío Crítico (Gap):** gap_006
