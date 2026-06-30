import dotenv, json, urllib.request, os

# Cargar credenciales
env = dotenv.dotenv_values(r"C:\Users\Jota Ochoa\Antigravity\02_Projects\humanos\.env")
url = env["SUPABASE_URL"]
key = env["SUPABASE_KEY"]

# Payload para Lummia
payload = {
    "protagonist_name": "Nicolás Moreno y Julián Mora",
    "normalized_name": "nicolas_moreno_julian_mora",
    "known_for": "Fundadores de Lummia",
    "associated_company": "Lummia",
    "country": "Colombia",
    "region": "Bucaramanga, Santander",
    "era": "2020-presente",
    "story_subject_type": "duo",
    
    # Clasificación editorial
    "domain_category": "business",
    "protagonist_type": "founder",
    "story_level": "microstory",
    "format_recommendation": "two_part_short",
    "publish_timing": "soon",
    "editorial_status": "idea",
    "production_status": "not_started",
    
    # Protección editorial
    "protect_from_burning": False,
    "burn_risk": "medium",
    
    # Narrativa
    "one_line_story": "Dos amigos de la infancia invirtieron sus ahorros en máquinas de depilación láser y hoy facturan $12M sin inversionistas.",
    "human_angle": "Nicolás perdió a su mamá a los 17 años y vio quebrar a su papá poco después. Esa dolor lo motivó a crear algo que hiciera sentir bien a las mujeres.",
    "human_before_success": "Vendían máquina por máquina, financiaban cada inventario con las ventas anteriores y resolvían operaciones manualmente.",
    "central_conflict": "Apostar todo los ahorros de dos jóvenes sin experiencia ni inversionistas, confiando en un producto de belleza para mujeres.",
    "key_decision": "Decidir enfocarse solo en productos que conectaban emocionalmente y construir una marca con identidad propia.",
    "main_risk": "Perder los ahorros de toda una vida en un producto de nicho sin garantías de mercado.",
    "turning_point": "2025: Colaboración con Barbie/Mattel que validó la marca y confirmó que podían competir por deseo, no solo por funcionalidad.",
    "transformation": "De marca funcional a propuesta con identidad emocional, donde el 90% del equipo son mujeres y cada decisión pasa por el filtro de '¿respetamos y cuidamos a las mujeres?'",
    "legacy_today": "Empresa 100% colombiana con presencia en México, Ecuador y proyección regional. Muestra que se puede escalar sin capital de riesgo.",
    "reflection_line": "El mejor negocio es ese que nace del respeto hacia las personas y se mantiene por el valor que genera.",
    
    # Hooks
    "hook_family": "lo_que_nadie_sabe",
    "primary_hook": "Lo que nadie sabe: invirtieron sus ahorros en máquinas de depilación láser porque perdieron a su mamá a los 17 años",
    "alternative_hooks": [
        "Antes de Lummia, estos dos vendían máquina por máquina financiando cada inventario con las ventas anteriores",
        "El 90% del equipo de Lummia son mujeres: así construyeron una empresa que protege y valora a las mujeres",
        "Se negaron a aceptar inversionistas: hoy facturan $12M manteniendo el control total de su empresa"
    ],
    "closing_angle": "Sin inversionistas, sin estructura corporativa, solo dos amigos de la infancia que apostaron sus ahorros y hoy superan los $12 millones en facturación.",
    
    # Serialización
    "series_potential": True,
    "estimated_episode_count": 3,
    "episode_outline": [
        "Ep1: El origen — Nicolás pierde a su mamá y ve quebrar a su papá. Dos amigos de la infancia deciden apostar todo.",
        "Ep2: La validación — Venden máquina por máquina, aprenden del error, construyen identidad propia. 2025: Barbie valida la marca.",
        "Ep3: El crecimiento — $12M en facturación sin un solo dólar de inversionista. Presencia en 3 países."
    ],
    "suggested_episode_titles": [
        "Lo que nadie sabe: por qué invirtieron sus ahorros en depilación láser",
        "El momento en que Barbie validó una startup colombiana",
        "Cómo facturan $12M sin un solo inversionista"
    ],
    
    # Scoring (estimado — Borges debe completar)
    "narrative_score": 8,
    "familiarity_score": 3,
    "surprise_score": 7,
    "emotional_score": 9,
    "research_confidence": 7,
    "production_difficulty": 4,
    "strategic_value": 8,
    "priority_score": 7,
    "series_score": 8,
    
    # Producción
    "asset_needs": [
        "Foto de Nicolás Moreno y Julián Mora",
        "Foto de máquinas Lummia",
        "Foto de tienda/almacén",
        "Captura de colaboración Barbie",
        "Gráfico de crecimiento facturado"
    ],
    "visual_style_notes": "Estilo documental: planos abiertos de Bucaramanga, primeros planos de máquinas, fotos de fundadores, transiciones lentas y elegantes.",
    "music_mood": "Acústico inspirador, piano suave, ritmo moderado, sin dramatismo excesivo",
    
    # Publicación
    "platforms": ["instagram", "tiktok", "linkedin"],
    
    # Fuentes y verificación
    "source_links": [
        "https://www.portafolio.co/emprendimiento/la-historia-de-lummia-el-emprendimiento-bumangues-que-hoy-supera-los-12-millones-de-dolares-496335"
    ],
    "source_notes": "Artículo de Portafolio por Julian Andres Gonzalez Vargas, publicado 17/06/2026. Verificar con entrevista directa a fundadores para confirmar detalles financieros.",
    "fact_check_status": "pending",
    "fact_check_notes": "REQUERIDO: Entrevistar a Nicolás y Julián para confirmar: (1) monto exacto de inversión inicial, (2) fecha exacta de fundación, (3) cifra precisa de facturación 2025-2026, (4) número exacto de empleados.",
    
    # Sistema
    "created_by": "Jota",
    "assigned_to_agent": "Borges"
}

# Construir payload
data = json.dumps(payload, ensure_ascii=False, indent=2).encode("utf-8")

# Enviar a Supabase
req = urllib.request.Request(
    url + "/rest/v1/humanos_stories",
    data=data, method="POST",
    headers={
        "apikey": key,
        "Authorization": "Bearer " + key,
        "Content-Type": "application/json",
        "Prefer": "return=representation",
    }
)

try:
    with urllib.request.urlopen(req) as resp:
        result = json.loads(resp.read())
        story_id = result[0]["id"]
        print(f"✅ Historia de Lummia insertada en Supabase")
        print(f"🆔 ID: {story_id}")
        print(f"📝 Protagonistas: {payload['protagonist_name']}")
        print(f"📊 Story Level: {payload['story_level']}")
        print(f"🎯 Hook: {payload['primary_hook'][:100]}...")
        print(f"\n\n🔜 NEXT: Enviar a Borges para investigación detallada")
except Exception as e:
    print(f"❌ ERROR al insertar: {e}")
    print(f"\nRespuesta del servidor:")
    print(resp.read().decode())
