# Auditoría del guion largo — EP0004 Ferruccio Lamborghini

**Fecha:** 2026-08-06
**Base auditada:** `02_SCRIPT/script_long.md` (humanizado el 4 ago 21:19)
**Salida:** `02_SCRIPT/script_long_v3_optimizado.md`

---

## Veredicto

La humanización del 4 ago funcionó en lo tonal. Reutiliza el ADN de la Versión Jota
casi literalmente ("ya era rico. Muy.", "Ahí no nació un competidor. Nació una venganza
con motor V12", el outro completo). En patrones de IA el texto está limpio: sin
em-dashes decorativos, sin "testamento a", sin regla de tres forzada, longitudes de
frase variadas.

El problema no es el tono. Es que **perdió precisión factual y perdió los marcadores
de producción.**

---

## 1. Errores de hecho

### 1.1 El taller estaba en Cento, no en Sant'Agata — CORREGIDO

El guion dice: *"Volvió a su taller en Sant'Agata y desarmó el auto"*.

El claim aprobado C007 (confianza 98, entrevista directa en *Thoroughbred & Classic
Cars*, 1991) dice explícitamente **"en su taller de Cento"**.

Sant'Agata Bolognese es donde construyó la **fábrica de autos en 1963**, un año
después. En 1962, cuando desarmó el Ferrari, su operación de tractores estaba en Cento.

Este error **no lo introdujo el Humanizer: viene de tu propia Versión Jota**, que dice
"volvió a Sant'Agata". El Humanizer hizo bien su trabajo imitando tu ADN — y copió el
error con él. Es el riesgo estructural de la calibración de voz: propaga los errores
de la muestra. Conviene corregir `voice_sample.txt` también.

### 1.2 Se perdió la fecha verificada — CORREGIDO

El claim C001 fija la reunión con Enzo **en 1962**. La versión pre-humanizer la tenía.
La humanizada la borró. Restaurada.

### 1.3 Se perdió el detalle más fuerte del episodio — CORREGIDO

C007 no dice "un embrague comercial". Dice: **un Borg & Beck**, el mismo proveedor
inglés, **vendido a diez veces su costo**. El guion humanizado lo diluyó a "el mismo
embrague comercial" y "a precio de oro".

Ese es el dato que convierte la anécdota en evidencia. Un nombre de proveedor y un
múltiplo concreto valen más que cualquier adjetivo. Restaurados los dos.

---

## 2. Claims sin verificar que el guion afirma como ciertos

**El Acto 4 completo — el debut sin motor — no está en `approved_claims.json`.**

Es el acto narrativamente más potente del episodio y Veritas nunca lo auditó. El guion
afirma tres cosas no verificadas:

| Afirmación | Estado |
|---|---|
| El capó no cerraba porque el V12 era demasiado alto | sin verificar |
| Llenó el compartimiento con **ladrillos** | sin verificar (la versión más citada dice lastre, sin especificar) |
| Faltaban **48 horas** para la presentación | sin verificar, cifra probablemente inventada por Gabo |
| Trabajaron **18 horas diarias** (Acto 3) | sin verificar, misma sospecha |

En v3 suavicé las cifras no sostenidas ("lastre" en vez de ladrillos, "faltaban horas,
no semanas" en vez de 48, "contra el reloj" en vez de 18 horas diarias) para que el
acto sobreviva sin afirmar números que no podés defender.

**Recomendación:** antes de publicar, pasá el Acto 4 por Borges para conseguir fuente.
Si aparece, restaurá los detalles concretos — son buenos. Si no aparece, quedó
narrado de forma defendible.

---

## 3. Patrones de IA que quedaban

Dos punchlines fabricadas (patrón 31 del Humanizer) y una fórmula de aforismo
(patrón 32):

| Original | Problema | v3 |
|---|---|---|
| "La revelación no le dio rabia. Le dio certidumbre." | Punchline manufacturada con negación paralela | "Le dio algo más útil que rabia. Le dio un número." |
| "Y el resto no es historia: es ingeniería." | Fórmula de aforismo, cierre débil | eliminado; cierra en "La respuesta fue no." |
| "Competía con la idea de lo que un deportivo podía ser." | Abstracción vacía | eliminado |

También quité la redundancia "Se retiró a un viñedo... Cambió el rugido de los motores
por el silencio de las vides" (dice lo mismo dos veces, la segunda en registro
publicitario) → "Se retiró a un viñedo en Umbría y se puso a hacer vino."

---

## 4. Marcadores de producción — el daño colateral

La versión pre-humanizer tenía `[IMAGEN: ...]` y `[SONIDO: ...]` en todo el texto.
**La humanizada los borró todos.**

Es un bug real del `humanizer_agent.py`: su prompt pide explícitamente "manteniendo los
actos y marcas visuales [IMAGEN: ...]" (línea 77) pero el modelo no lo respetó. Vale
reforzar esa instrucción, o mejor, extraer los marcadores antes de humanizar y
reinyectarlos después en vez de confiar en que el modelo los preserve.

En v3 los devolví, y además **los mapeé contra los assets que ya existen** en
`04_IMAGES/` (FER_01 a FER_09) y contra los tres gaps de Moore. O sea: el guion ahora
te dice qué archivo poner en cada momento y dónde falta material.

Ojo con esto: `storyboard.json` es del 20 de julio y el guion bueno es del 4 de agosto.
**El storyboard está desfasado.** Habría que volver a correr Moore sobre v3.

---

## 5. Lo que quedó intacto

Tu voz. Las frases que son tuyas siguen ahí sin tocar: "ya era rico. Muy.", "Ahí no
nació un competidor. Nació una venganza con motor V12", "un capricho costoso", el
outro entero. La estructura de cinco actos tampoco se movió.

---

## Pendientes que dejo abiertos

1. Corregir Sant'Agata → Cento en `voice_sample.txt` (si no, el error se repite en cada episodio futuro).
2. Pasar el Acto 4 por Borges para sostener o descartar el debut sin motor.
3. Reforzar la preservación de marcadores en `humanizer_agent.py`.
4. Volver a correr Moore sobre v3 — el storyboard tiene dos semanas de atraso.
