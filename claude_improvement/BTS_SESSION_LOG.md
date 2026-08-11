# BTS — Registro de sesión

**Fecha:** 2026-08-01
**Episodio bajo prueba:** EP0004 · Ferruccio Lamborghini (formato largo, 8-10 min)
**Tesis del BTS:** *"Construí un equipo de agentes de IA para producir documentales. Entonces intenté producir uno de verdad."*

Este archivo se escribe mientras se trabaja, no después. Registra fricciones, degradaciones y decisiones — no acciones. Cada entrada es materia prima editorial.

---

## H1 · El episodio ya estaba producido

**Momento:** apertura de sesión, antes de tocar nada.

Se abrió `personajes/Ferruccio_Lamborghini/EP0004_Ferruccio_Lamborghini/` esperando una carpeta vacía. Estaba todo hecho: `status: storyboard_done`, 11 imágenes, guion largo y corto, storyboard, 7 plataformas empaquetadas en `11_DIST/`, `EPISODE_REVIEW.md` firmado por Talese y 496.341 views registradas en `metrics_history.json`.

De un video que nunca se publicó.

**Valor editorial:** es el gancho. El episodio elegido como prueba de estrés ya había pasado la prueba. En apariencia.

---

## H2 · Quién escribió el guion

**Momento:** revisión de `run_ferruccio_pilot.py`, el script que produjo EP0004.

Los cinco actos del episodio están **escritos a mano dentro del propio script**, en una lista llamada `act_fallbacks` (líneas 133-148). El diálogo socrático de Talese guarda como respuesta del creador la cadena literal `"Respuesta de prueba registrada para {act_id}"`. Los tiempos de auditoría no se miden: se fabrican con `int(time.time() * 1000) % 3000 + 1200`.

**Valor editorial:** el giro. No es que el sistema haya producido un mal episodio. Es que el sistema no produjo el episodio.

---

## H3 · Por qué nadie se dio cuenta

**Momento:** búsqueda de la causa raíz.

Dos fallos encadenados, ninguno de los cuales genera un error:

1. `.env` contenía tres variables: `SUPABASE_URL`, `SUPABASE_KEY`, `PEXELS_API_KEY`. **No contenía `OPENROUTER_API_KEY`.** Sin esa clave, `borges`, `gabo` y `moore` quedan en `None`.
2. Aunque la clave hubiera estado, el pilot la comprobaba en la **línea 26** y el `.env` recién se cargaba en la **línea 33**, dentro de `TaleseAgent.__init__`. La comprobación corría siete líneas antes que la carga. Siempre daba falso.

El pipeline no falló. **Degradó en silencio y siguió adelante con cara de éxito**: imprimió `PILOTO COMPLETADO DE PUNTA A PUNTA CON ÉXITO`.

**Valor editorial:** este es el corazón del video. La diferencia entre un sistema que se rompe y un sistema que miente. Un pipeline que crashea es un problema de diez minutos; uno que degrada en silencio es un episodio falso publicado.

**Frase para narrar en cámara:** *"Mi sistema no me falló. Me dijo que había terminado."*

---

## H4 · La decisión: qué se conserva

**Momento:** definición del alcance, antes de re-producir.

Lo producido por los fallbacks se descarta como salida de agente, pero **no se borra**: queda archivado como v1 y como evidencia. Lo que sí se conserva es la versión del guion corto escrita por Jota (`GUIONES/Ferruccio Lamborghini.md`), porque esa sí es humana y es el ADN editorial del personaje: frases cortas, la escena de Maranello dramatizada con diálogo directo, el hallazgo técnico del embrague compartido, el cierre con firma de marca.

El largo de 8-10 minutos debe **expandir esa voz, no reescribirla**.

**Valor editorial:** el momento en que el creador decide qué parte del desastre vale la pena salvar. También es la prueba de que el delta que mida Talese esta vez será real: Gabo contra Jota, no fallback contra Jota.

---

## H5 · Fail-loud como decisión de arquitectura

**Momento:** primera corrección aplicada.

Se añadió `env_boot.py`: carga el `.env` antes de cualquier comprobación y expone `exigir()` y `avisar_degradacion()`. `run_ferruccio_pilot.py` ahora **aborta** si no hay modelo, en vez de rellenar. Para correr igual con relleno hay que pedirlo explícitamente: `HUMANOS_STRICT=0`.

**Valor editorial:** la lección transferible del video. No "usá IA para producir"; sino: *cuando automatizás, el enemigo no es el error, es el fallback silencioso.*

---

## H6 · La única cosa que no se delega

**Momento:** mitad de sesión, decisión espontánea de Jota.

Se estaba verificando la clave de ElevenLabs (daba 401) cuando Jota interrumpió: *"La voz la grabo con mi voz en Audacity. No con ElevenLabs."*

No era un fallo. Era una decisión que nunca se había escrito en ninguna parte del sistema. Se eliminó la prueba y quedó documentada como `N/A` por diseño.

**Valor editorial:** en un sistema con once agentes, la voz es lo único que no se delega. Ese es el límite que el creador puso sin que nadie se lo pidiera, y explica de qué va el proyecto entero: automatizar la producción, no la autoría.

---

## H7 · Mr. You sale del papel — y lo primero que hace es admitir que no sabe

**Momento:** primera ejecución de `mr_you.py`.

Mr. You era el agente más elaborado del sistema (tres capas de conocimiento, protocolo de 10 puntos, prediction log) y el único sin una línea de código. Hoy corrió por primera vez.

Antes de evaluar nada, la capa de canal recién construida le dijo la verdad a la cara:

```
Publicaciones registradas : 4
  con datos REALES        : 0
  simuladas (bug random)  : 4
```

Su propio system prompt le prohíbe inventar certeza. Con cero métricas reales, tiene vetado marcar cualquier afirmación como DATO o PATRÓN: solo puede emitir HIPÓTESIS, y debe declararlo.

**Valor editorial:** el Chief YouTube Officer de un canal empieza su primer día de trabajo declarando que está ciego. No es un fallo del agente: es el agente funcionando bien. La alternativa —sonar seguro sin datos— es la que produjo el desastre de julio.

---

## H8 · El sistema falla, y esta vez avisa

**Momento:** primera corrida del Greenlight, con Apify cableado.

Apify devolvió HTTP 400: `sortVideosBy must be equal to one of "NEWEST", "POPULAR", "OLDEST"`. Se le estaba mandando `"popular"` en minúsculas.

Lo que pasó después es el punto entero de la jornada. En pantalla:

```
[Mr. You] Apify no respondio (ApifyError: HTTP 400 ...)
[Mr. You] Sigo SIN datos de competencia. Quedara marcado como HIPOTESIS, no como DATO.
```

**Valor editorial:** es el mismo tipo de fallo que hundió a EP0004 el 20 de julio — una integración que no responde. Pero el comportamiento es opuesto: en julio el pipeline rellenó el hueco con contenido inventado e imprimió *"COMPLETADO CON ÉXITO"*. Hoy declaró el hueco, degradó la confianza de su propia conclusión y siguió.

**Este es el final del arco.** No "construí agentes y funcionaron", sino: *aprendí a construir sistemas que me dicen cuándo no funcionan.*

**Frase para cámara:** *"Falló igual que en julio. La diferencia es que esta vez me enteré."*

---

## H9 · 721 veces

**Momento:** llegan los datos reales del canal desde YouTube Studio.

| personaje | el sistema creía | la realidad | inflado |
|---|---|---|---|
| Jan Koum | 657.002 vistas | **911** | **721×** |
| Hedy Lamarr | 508.439 | **2.418** | **210×** |
| James Dyson | 366.548 | **10.403** | **35×** |
| Ferruccio Lamborghini | 496.341 | **nunca se publicó** | — |

El canal entero tiene 13.935 vistas. El sistema creía que un solo episodio había hecho 657.000.

Durante un mes, Talese propuso aprendizajes editoriales y Mark generó recomendaciones de distribución sobre esos números. Todo el "aprendizaje acumulado" del sistema estaba calibrado contra una realidad inventada.

**Valor editorial:** el segundo golpe, y es peor que el primero. El primero fue "el episodio lo escribió un script". Este es: **"y después el sistema aprendió de él"**. El fraude no se quedó quieto: se propagó al mecanismo de mejora.

**Frase para cámara:** *"No solo produjo un episodio falso. Después estudió ese episodio falso para hacer el siguiente mejor."*

---

## H10 · El hallazgo que nadie fue a buscar

**Momento:** mirando la columna de duración del mismo export.

178 segundos. 128 segundos. 150 segundos.

Los tres episodios publicados de HUMANOS son **Shorts**. Todo el catálogo validado del proyecto es formato corto. Y hoy se está produciendo EP0004 a 8-10 minutos.

Para long-form el canal tiene cero datos. Cero. El único video largo publicado (378s, "El error del botón de WhatsApp", línea Lab IA) hizo 61 vistas.

**Valor editorial:** el dato que cambia la decisión y que no estaba en la pregunta. Nadie preguntó "¿de qué duración es mi catálogo?". Salió solo al mirar los números de verdad por primera vez.

Y plantea la tensión honesta del episodio: EP0004 no es la continuación de una racha. Es una **apuesta a un formato que este canal nunca probó**. Mr. You tiene que decirlo así, no disfrazarlo de estrategia.

**Frase para cámara:** *"Descubrí que llevo tres episodios de éxito en un formato... que no es el que estoy a punto de producir."*

---

## H11 · Conectar el canal de verdad

**Momento:** decisión de implementar OAuth en vez de seguir con exports manuales.

El CSV arregla el pasado pero no el futuro: hay que descargarlo a mano cada vez. Se implementó OAuth contra la YouTube Analytics API, dentro del panel editorial, con dos decisiones deliberadas:

- **Scopes de solo lectura.** `yt-analytics.readonly` y `youtube.readonly`. El sistema mide, no publica. Aunque el código quisiera borrar un video, Google no lo dejaría.
- **El `client_secret` nunca se copia al repo.** Se lee de su ubicación original en JotaOS. Los tokens van a `_LAB/youtube_tokens.json`, añadido al `.gitignore` antes de escribir la primera línea.

**Valor editorial:** el momento en que el sistema deja de creer lo que se le dice y empieza a mirar por sí mismo. Es el cierre del arco que abrió el `random.randint()`.

---

## H12 · Claude comete el mismo error que el sistema

**Momento:** al presentar la primera lectura de los datos reales.

Claude armó una tabla ordenando los cuatro videos **por duración** y concluyó: "cuatro puntos, todos en la misma dirección: cuanto más largo, menor la retención". Presentó eso como PATRÓN.

Jota lo frenó: HUMANOS y Lab IA son dos productos distintos, con audiencias y horizontes distintos. No se comparan.

Tenía razón, y el error era peor de lo que él señaló. Ordenados por **fecha**, que es como ocurrieron:

| 3 jul | Jan Koum | 178s | 40,6% |
| 10 jul | Hedy Lamarr | 128s | **66,4%** |
| 17 jul | James Dyson | 150s | 62,0% |

40,6% → 66,4% → 62,0%. No es "más largo, peor retención". Es la curva de aprendizaje del creador: EP0001 fue el primero, después saltó 26 puntos y se sostuvo. La correlación con la duración era un artefacto del orden que Claude eligió para contar la historia.

**Valor editorial: este es el mejor momento del día.** Todo el episodio venía siendo "la IA produjo contenido falso y sonó segura". Y en el medio de arreglarlo, la IA que lo estaba arreglando hizo exactamente lo mismo: ordenó los datos para que contaran una historia limpia y presentó como patrón lo que era ruido.

No lo detectó Claude. Lo detectó el creador, porque conocía su propio negocio.

**Frase para cámara:** *"Le pedí a la IA que auditara mi sistema por sonar seguro sin datos. Y a mitad de la auditoría tuve que corregirla por sonar segura sin datos."*

**Lo que salió de ahí:** `agents/mr-you/doctrina_canal.md`. El criterio de Jota escrito donde el sistema lo obedece — se antepone al system prompt de Mr. You y gobierna sobre los datos. Incluye una regla nacida de este error: señalar cuándo una correlación puede explicarse por el orden de publicación en vez de por la variable que se cree estar midiendo.

---

## H13 · El bucle queda cerrado y andando solo

**Momento:** 19:22:52, primera captura ejecutada por el Programador de tareas de Windows.

```
Canal: Jota Ochoa | HUMANOS | 230 subs | 15621 vistas | 17 videos
4 episodios actualizados con datos reales.
Mr. You ve ahora 4 publicaciones con datos reales. Evidencia real: True
```

Sin el panel abierto. Sin una sesión de Claude. Sin nadie mirando.

Costó cuatro fallos encadenados llegar acá, todos de Claude: comillas mal escapadas en `schtasks`, `&&` dentro de un parámetro que no lo admite, el `.bat` y el script peleándose por el mismo archivo de log, y `python` a secas en un entorno donde no existe.

**Valor editorial:** el cierre honesto de la jornada. El sistema quedó capturando su propia realidad todos los días a las 08:00 — donde a la mañana había `random.randint(300000, 800000)`.

Y el detalle que vale contar: la serie histórica arranca hoy con **1 día**. YouTube Studio muestra el presente; nadie guarda la historia de su propio canal. A partir de mañana, este sí. En tres meses Mr. You va a poder decir PATRÓN con datos propios en vez de HIPÓTESIS prestada.

**Frase para cámara:** *"El sistema ya no me cuenta lo que quiero oír. Va a buscar los números él solo, todas las mañanas, aunque yo no esté."*

---

## H14 ·

*(siguiente entrada)*
