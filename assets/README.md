# ORGANIZACIÓN DE ASSETS (assets/README.md)

Este directorio centraliza todos los recursos multimedia (imágenes, videos, audios y elementos de branding) organizados bajo una estructura de **estudio de producción cinematográfico** para **HUMANOS**.

---

## 1. ESTRUCTURA DE CARPETAS DE ESTUDIO

La organización interna debe seguir estrictamente este árbol de directorios:

```
assets/
│
├── branding/                      # Recursos visuales y clips globales de marca
│   └── video/                     # Elementos exportados de Remotion para CapCut
│       ├── character_card/        # Assets editables de la tarjeta de personaje
│       └── intro/                 # Clips de intros exportadas
│
├── camas_sonido_cinematic/        # Pistas de fondo instrumentales (documental, tensión)
│
├── cierres_sonido/                # Efectos de audio y marcas musicales para el Outro
│
├── heart_beat/                    # Efectos de sonido del latido cinematográfico oficial
│
├── transiciones_whosh/            # Efectos de sonido de aire/desplazamiento (whoosh)
│
├── personajes/                    # Recursos específicos de cada protagonista
│   ├── [nombre_normalizado]/      # Nombre en minúsculas y snake_case (ej. jan_koum)
│   │   ├── imagenes/              # Fotografías del personaje (alto contraste, B/N)
│   │   ├── videos/                # Clips de video históricos o B-roll específicos
│   │   └── audio/                 # Voz grabada (Jota) para el episodio
│   │
│   ├── jan_koum/                  # Ejemplo práctico: WhatsApp
│   └── brian_chesky/              # Ejemplo práctico: Airbnb
│
├── broll/                         # Biblioteca global de B-roll genérico de stock
│   ├── tecnologia/                # Tomas de servidores, código, pantallas, etc.
│   ├── startups/                  # Oficinas, pizarras, equipos trabajando, etc.
│   └── ciencia/                   # Laboratorios, planos abstractos, etc.
│
└── thumbnails/                    # Diseños y assets de portadas para Reels/Shorts/YouTube
```

---

## 2. REGLA DE NOMBRES PARA CARPETAS DE PERSONAJES
Los agentes (Borges, Gabo, Moore, Codex) deben usar el valor del campo `normalized_name` de la tabla `humanos_stories` de Supabase para nombrar la carpeta del personaje.
* **Fórmula:** `assets/personajes/[normalized_name]/`

---

## 3. AUTOMATIZACIÓN DE CARPETAS
La carpeta del personaje se creará de forma automática en el sistema local:
1. **Flujo de n8n (Borges):** Al pasar el estado a `researched`, n8n ejecutará un comando para estructurar las carpetas locales en el volumen compartido.
2. **Script CLI (jota-os):** Script integrado que escucha los webhooks de Supabase y genera la carpeta cuando Jota aprueba un protagonista.
