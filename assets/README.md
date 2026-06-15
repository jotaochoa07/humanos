# ORGANIZACIÓN DE ASSETS (assets/README.md)

Este directorio centraliza todos los recursos multimedia (imágenes, videos, audios y elementos de branding) utilizados para la producción de los videos de **HUMANOS**.

---

## 1. ESTRUCTURA DE CARPETAS

La organización interna debe seguir estrictamente este árbol de directorios:

```
assets/
├── branding/                      # Recursos globales de marca e identidad visual
│   ├── intro.mp4                  # Intro oficial de HUMANOS
│   ├── transition.mp4             # Transición de latido oficial
│   ├── outro.mp4                  # Cierres de marca en video
│   ├── logos/                     # Logotipos vectoriales e isotipos (.png, .svg)
│   └── audio/                     # Efectos de sonido globales (latido, transiciones)
│
├── musica/                        # Biblioteca de música aprobada para los videos
│   └── tension_documental_1.mp3
│
└── personajes/                    # Recursos específicos de cada protagonista
    ├── [nombre_normalizado]/      # Nombre en minúsculas y snake_case (ej. jan_koum)
    │   ├── imagenes/              # Fotografías del personaje (alto contraste, B/N)
    │   ├── videos/                # Clips de video de stock o históricos (B-roll)
    │   └── audio/                 # Grabación de voz del episodio (Jota) y audio local
    │
    └── brian_chesky/              # Ejemplo práctico
        ├── imagenes/
        ├── videos/
        └── audio/
```

---

## 2. REGLA DE NOMBRES PARA CARPETAS DE PERSONAJES
Los agentes (Borges, Gabo, Moore, Codex) deben usar el valor del campo `normalized_name` de la tabla `humanos_stories` de Supabase para nombrar la carpeta del personaje.
* **Fórmula:** `assets/personajes/[normalized_name]/`
* **Ejemplos:**
  * `assets/personajes/jan_koum/`
  * `assets/personajes/brian_chesky/`
  * `assets/personajes/ehud_shabtai/`

---

## 3. AUTOMATIZACIÓN DE CARPETAS
La carpeta específica del personaje se creará de forma automática en el sistema local a través de los siguientes métodos:
1. **Flujo de n8n (Borges):** Al pasar el estado a `researched`, n8n ejecutará un script local (`mkdir` recursivo) usando el `normalized_name`.
2. **Script CLI (jota-os):** Un script que escuche los webhooks de Supabase y monte la estructura de subcarpetas en el disco local de producción del creador.
