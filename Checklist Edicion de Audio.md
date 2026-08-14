# 🎙️ Limpieza de voz — HUMANOS

## Cadena maestra — Audacity 4

### 1. Reducción de ruido
- [ ] Seleccionar fragmento con solo ruido ambiente
- [ ] `Efecto → Noise removal and repair → Noise Reduction`
- [ ] Obtener perfil de ruido
- [ ] Seleccionar toda la grabación
- [ ] Aplicar Noise Reduction

> No pasarse con la reducción. Si aparecen artefactos metálicos o voz "acuosa", reducir intensidad.

---

### 2. High-Pass Filter
- [ ] `Efecto → EQ and filters → High-Pass Filter`
- [ ] Frecuencia: **80 Hz**
- [ ] Rodamiento: **24 dB/octava**
- [ ] Aplicar

---

### 3. EQ
- [ ] `Efecto → EQ and filters → Filter Curve EQ`
- [ ] Preset: **Ajuste Jota**
- [ ] Aplicar

**Objetivo:** quitar barro en graves/medios y añadir presencia y aire a la voz.

---

### 4. Compresor
- [ ] `Efecto → Volume and compression → Compressor`
- [ ] Preset: **Ajuste Jota**

Valores:

- Ataque: **5 ms**
- Liberación: **100 ms**
- Umbral: **−18 dB**
- Proporción: **3.1:1**
- Espera previa: **3 ms**
- Exportar: **0 dB**
- Liberación: **6 dB**

- [ ] Aplicar

---

### 5. De-Esser
- [ ] `De-Ess — MuseFX`
- [ ] Modo: **Male Voice**
- [ ] Intensidad: **≈ 5/11**
- [ ] Aplicar

> Solo controlar las S agresivas. No quitarle el brillo a la voz.

---

### 6. Loudness Normalization
- [ ] `Efecto → Volume and compression → Loudness Normalization`
- [ ] Normalizar vía: **Volumen percibido**
- [ ] Objetivo: **−14 LUFS**
- [ ] Normalizar canales estéreo independientemente: **OFF**
- [ ] Treat mono as dual mono: **ON**
- [ ] Aplicar

---

### 7. Limiter
- [ ] `Efecto → Volume and compression → Limiter`
- [ ] Preset: **Ajuste Jota**

Valores:

- Umbral: **−4 dB**
- Salida: **−1 dB**
- Espera previa: **1 ms**
- Exportar: **0 dB**
- Liberación: **50 ms**

- [ ] Aplicar

---

## 🔊 Control final

- [ ] Escuchar con audífonos
- [ ] Revisar que las **S** no molesten
- [ ] Revisar respiraciones y silencios
- [ ] Confirmar que la compresión no se escuche artificial
- [ ] Escuchar también en parlantes normales
- [ ] Confirmar que no haya clipping
- [ ] Exportar audio final

---

## ⚡ Orden rápido

**Noise Reduction → High-Pass 80 Hz → EQ → Compressor → De-Ess → −14 LUFS → Limiter −1 dB**

> **NO volver a normalizar después del limiter.**