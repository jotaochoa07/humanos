# Prompt para retomar — HUMANOS, EP0004 Ferruccio Lamborghini

> **Este archivo quedó viejo el 2026-08-09.** Lee
> `claude_improvement\SESION_20260809.md`, que es el estado actual.
> Lo de abajo se conserva porque explica cómo se llegó hasta aquí.

Repo: `C:\Users\Jota Ochoa\Antigravity\02_Projects\humanos`
Episodio: `personajes\Ferruccio_Lamborghini\EP0004_Ferruccio_Lamborghini`

## Qué cambió respecto a lo que dice este archivo

- El `.bat` de Veritas y Talese **nunca llegó a correrse**. Lo reemplazó
  `Cerrar Episodio Lamborghini.bat`, que hace el cierre completo: Borges sobre
  el Acto 4, extracción de claims, dos pasadas de Veritas, Moore sobre la
  locución real, Talese e informe HTML.
- El guion del repo **es** el que se grabó. Verificado carácter a carácter.
- El archivo histórico ya busca video (`--video`), y el cliente de Kling ya
  existe (`kling_client.py`).

---

## Lo que quedó cerrado el 2026-08-07

1. **Botón "Guardar Acto" arreglado.** `public/editorial-dashboard.html`: `saveAct` ahora toma la ruta de `state.selectedReviewPath` (nunca incrustada en el `onclick`) y muestra toast rojo con el error real si el servidor responde mal. Verificado con `node --check`.
2. **Guion locutado promovido a canónico.** `script_long.md` y `scripts_long.json` (beat_sheet de los 5 actos) tienen ahora el texto exacto de `C:\Users\Jota Ochoa\Claude_Cowork\GUIONES\Lamborghini largo..md`, que es lo que Jota grabó en `06_AUDIO\lamborghini_voz-off-termindo_wav.wav`. Backups en `claude_improvement\_BACKUP_*_pre-locutado.*`.
3. **Cento corregido** en `voice_sample.txt` (era "Sant'Agata", coincide con approved_claims C007). Backup guardado.
4. **Veritas + Talese: bloqueados por red del sandbox**, no ejecutados. *(Resuelto el 09/08: ver arriba.)*

## Decisión de producto tomada (video, no solo fotos)

El episodio necesita mínimo 8 minutos y hoy solo hay fotos descargadas (Ken Burns no alcanza). Orden de prioridad acordado con Jota — **documental real, no canal faceless de IA**:

1. **Archivo primario real** (prioridad más alta): `EUROPEANA_KEY` da acceso al Istituto Luce. Ferruccio Lamborghini está indexado como persona en `patrimonio.archivioluce.com` y hay cobertura extensa del Salone dell'Automobile di Torino. Falta confirmar la edición de 1963. *(Implementado el 09/08 como `archivo_historico.py --video`.)*
2. **YouTube de terceros como respaldo**, no como fuente principal: la lista debe incluir canal de origen y créditos visibles. Se descartó automatizar la descarga sin ese dato: "publicado en YouTube" no equivale a "derechos claros". **Sigue sin hacerse.**
3. **Kling es el último recurso**, no el default. *(Implementado el 09/08 como `kling_client.py`.)*

## Cómo trabaja Jota (no repetir explicaciones ya dadas)

Decisiones suyas en HTML clickeable, scripts en `.bat`, nunca prompts de terminal. Rutas completas y archivo exacto en cada instrucción. Verificar antes de afirmar — correr el código sobre datos reales, no solo leerlo. Es visual: preferí mostrarle resultados o links, no pedirle que interprete JSON crudo.
