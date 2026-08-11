# Trabajo para las próximas 2 horas — sin Claude

**Contexto:** límite de sesión alcanzado 2026-08-01. Vuelvo en ~2h.
Todo lo que sigue lo podés hacer solo, y **cada punto sube el valor de lo que hago cuando vuelva**.

Ordenado por impacto real, no por comodidad.

---

## 1. Corré otra vez el Greenlight — ya arreglé el bug de Apify (2 min)

El error que viste:

```
Field input.sortVideosBy must be equal to one of the allowed values:
"NEWEST", "POPULAR", "OLDEST"
```

Le pasaba `"popular"` en minúsculas. Ya está corregido en `apify_client.py`.

```
Greenlight Lamborghini.bat
```

Fijate en algo antes de seguir: **el sistema no mintió**. Apify falló, Mr. You lo dijo en pantalla y siguió declarando que su packaging quedaba como HIPÓTESIS y no como DATO. Eso es exactamente lo contrario de lo que pasó el 20 de julio, cuando el pipeline falló en silencio y estampó `PILOTO COMPLETADO CON ÉXITO`.

**Grabá esa comparación.** Es la prueba de que la corrección de hoy funciona, y es el cierre natural del arco del BTS.

---

## 2. Lo más valioso que podés hacer hoy: darle ojos a Mr. You (20-30 min)

Ahora mismo Mr. You está ciego. Cero métricas reales. Todo lo que diga es hipótesis.

Si EP0001 (Jan Koum), EP0002 (Hedy Lamarr) o EP0003 (James Dyson) **se publicaron de verdad**, andá a YouTube Studio y anotá los números reales. Con eso Mr. You pasa de opinar a saber.

Para cada video publicado necesito seis datos:

| Dato | Dónde está en YouTube Studio |
|---|---|
| Vistas | Analytics → Descripción general |
| CTR de impresiones | Analytics → Alcance |
| Retención a 3s | Analytics → Interacción → Retención de audiencia |
| % promedio visto | Analytics → Interacción |
| Duración del video | La ficha del video |
| Fecha de publicación | La ficha del video |

Pegámelos así, en texto plano, cuando vuelva:

```
EP0001 Jan Koum | publicado 2026-06-17 | vistas 1234 | ctr 4.2% | ret3s 61% | avg 38% | dur 47s
EP0002 Hedy Lamarr | ...
```

Yo los cargo en `canal.py` marcados como `real` y el veredicto de Mr. You cambia de raíz.

**Si ninguno se publicó**, decímelo igual: eso también es un dato, y significa que Mr. You va a operar a ciegas por un tiempo. Es honesto y hay que decirlo en el video.

---

## 3. Elegí la hipótesis de packaging (10 min)

El Greenlight te va a dar tres títulos + miniaturas: una segura, una arriesgada y una en un ángulo que la competencia no cubre.

Elegí una y anotá **por qué**. Si elegís distinto a lo que recomienda Mr. You, mejor todavía: eso es un Override Editorial, y el campo `override_de_jota` ya existe en `prediction_snapshot.json` esperándolo. Se mide contra el resultado a las 48h.

Esa tensión —el agente recomienda A, vos elegís C— es material de cámara.

---

## 4. Grabá la voz del corto en Audacity (30 min)

El guion corto ya está aprobado y es tuyo: `GUIONES\Ferruccio Lamborghini.md`, sección "Versión Jota". No hace falta esperarme.

Guardalo en:
```
personajes\Ferruccio_Lamborghini\EP0004_Ferruccio_Lamborghini\06_AUDIO\
```

Nombre libre, con que empiece por `voz` o contenga `lamborghini` alcanza — el `_find_cover()` que arreglé ayer ya no depende de que se llame `voz_off_jan_koum.wav`.

---

## 5. Mirá los 3 asset gaps y decidí qué es archivo y qué es IA (15 min)

```
personajes\Ferruccio_Lamborghini\EP0004_Ferruccio_Lamborghini\03_STORYBOARD\asset_gaps.json
```

Son 3. Por cada uno, decidí: **¿esto existe como material de archivo o hay que generarlo?**

Importa porque KIE.AI te quedan **80 créditos**. No alcanza para experimentar. Cada generación tiene que salir a la primera o casi.

Si algo es histórico y verificable (el Salón de Turín del 63, el 350 GTV, la fábrica de Sant'Agata), buscá archivo real antes de generar. Un documental que recrea con IA algo que existe fotografiado pierde autoridad, y Veritas no puede protegerte de eso porque no es un claim falso: es una decisión de producción.

---

## 6. Momentos que conviene narrar mientras trabajás

Decisiones, no acciones. Los que ya ocurrieron hoy y valen:

- **"El episodio ya estaba producido."** Abriste la carpeta esperando vacío y estaba todo hecho.
- **"Y lo escribió el propio script."** Los cinco actos estaban a mano dentro de `run_ferruccio_pilot.py`.
- **"Mi sistema no me falló. Me dijo que había terminado."** La frase del video.
- **"La voz es lo único que no delego."** Once agentes, y grabás vos en Audacity.
- **"Hoy Apify falló y el sistema me lo dijo."** El contraste que cierra el arco.

---

## Cuando vuelva, en este orden

0. **Meter a Mr. You dentro del panel editorial.** Hoy solo vive en la terminal
   y vos vas a grabar con el panel. El carril de episodio ya tiene su lugar
   reservado (`DASHBOARD_V2_SPEC.md` §5) pero está vacío. Que se vean ahí:
   el veredicto GO/REWORK/NO-GO, las 3 hipótesis de título con su miniatura,
   el prediction snapshot congelado y el botón de Override para vos.
   Eso se graba; una ventana negra de comandos no.
1. Cargo las métricas reales que hayas traído → Mr. You deja de estar ciego.
2. Gabo escribe el largo de 8-10 min partiendo de tu versión del corto como ADN, no reescribiéndola.
3. Veritas gate 2 sobre el guion largo.
4. Moore + KIE.AI para los 3 gaps.
5. Verificación con evidencia y cierre.

---

## Estado del sistema ahora mismo

| Pieza | Estado |
|---|---|
| `.env` | 5 claves añadidas, backup en `_BACKUP_20260801_092617/.env.bak` |
| `env_boot.py` | nuevo — carga entorno + fail-loud |
| `verificar_agentes.py` | nuevo — prueba de vida real |
| `canal.py` | nuevo — capa de agregación, 4 entradas marcadas `simulated` |
| `apify_client.py` | nuevo — bug de `sortVideosBy` corregido |
| `mr_you.py` | nuevo — Mr. You ejecutable |
| `requirements.txt` | nuevo — no existía |
| `run_ferruccio_pilot.py` | aborta en vez de rellenar |
| `metrics_history.json` | **sin tocar** (mtime sigue en 2026-07-20 13:48:45) |
| Supabase | **cero escrituras**, solo lectura |
| git | nada commiteado |
