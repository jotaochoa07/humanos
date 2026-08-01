import dotenv
import json
import urllib.request
import sys

# Load credentials
env = dotenv.dotenv_values(".env")
SUPABASE_URL = env["SUPABASE_URL"]
SUPABASE_KEY = env["SUPABASE_KEY"]

# Data to insert
candidates = [
    {
        "protagonist_name": "James Dyson",
        "normalized_name": "james_dyson",
        "known_for": "Dyson vacuum cleaners",
        "associated_company": "Dyson",
        "country": "United Kingdom",
        "region": "Europe",
        "era": "1990s-2020s",
        "story_subject_type": "individual",
        "domain_category": "technology",
        "protagonist_type": "inventor",
        "story_level": "microstory",
        "publish_timing": "soon",
        "editorial_status": "idea",
        "protect_from_burning": False,
        "burn_risk": "medium",
        "one_line_story": "Built 5,126 prototypes. Failed repeatedly. Revolutionized an industry.",
        "human_angle": "Everyone said it was impossible. He never stopped.",
        "human_before_success": "Struggling designer with no manufacturing experience",
        "central_conflict": "Thousands of failures vs. belief in the final product",
        "key_decision": "Keep building prototypes when no one would fund it",
        "main_risk": "Financial ruin and family bankruptcy",
        "turning_point": "The 5,126th prototype finally worked",
        "transformation": "From struggling inventor to industry revolutionary",
        "legacy_today": "Multibillion-dollar company known for engineering excellence",
        "hook_family": "lo_que_nadie_sabe",
        "primary_hook": "Falló 5.126 veces... y por eso terminó construyendo un imperio.",
        "alternative_hooks": ["La obsesión vence al talento"],
        "closing_angle": "Sometimes the biggest failure is just another step forward.",
        "source_links": ["https://www.dyson.com/company-history"],
        "assigned_to_agent": "Borges",
        "created_by": "Hermoso"
    },
    {
        "protagonist_name": "Sara Blakely",
        "normalized_name": "sara_blakely",
        "known_for": "Spanx foundation shapewear",
        "associated_company": "Spanx",
        "country": "United States",
        "region": "North America",
        "era": "2000s-2020s",
        "story_subject_type": "individual",
        "domain_category": "business",
        "protagonist_type": "founder",
        "story_level": "microstory",
        "publish_timing": "soon",
        "editorial_status": "idea",
        "protect_from_burning": False,
        "burn_risk": "medium",
        "one_line_story": "Sold fax machines door-to-door. Created Spanx with $5K. Became youngest self-made female billionaire.",
        "human_angle": "No fashion background. No investors. No fear.",
        "human_before_success": "Fax machine saleswoman with no clothing industry experience",
        "central_conflict": "Fashion industry rejection vs. personal product need",
        "key_decision": "Invest $5K savings and personally pitch buyers",
        "main_risk": "Losing her life savings with no fashion connections",
        "turning_point": "Neiman Marcus buyers agreed to carry the product",
        "transformation": "From struggling saleswoman to self-made billionaire",
        "legacy_today": "Category-defining brand that changed women's foundation wear",
        "hook_family": "lo_que_nadie_sabe",
        "primary_hook": "Vendía máquinas de fax puerta a puerta antes de convertirse en multimillonaria.",
        "alternative_hooks": ["Convertir un problema cotidiano en un imperio"],
        "closing_angle": "Your greatest weakness might be your unfair advantage.",
        "source_links": ["https://www.spanx.com/pages/about-spanx"],
        "assigned_to_agent": "Borges",
        "created_by": "Hermoso"
    },
    {
        "protagonist_name": "Yvon Chouinard",
        "normalized_name": "yvon_chouinard",
        "known_for": "Patagonia sustainable outdoor brand",
        "associated_company": "Patagonia",
        "country": "United States",
        "region": "North America",
        "era": "1970s-2020s",
        "story_subject_type": "individual",
        "domain_category": "business",
        "protagonist_type": "founder",
        "story_level": "microstory",
        "publish_timing": "soon",
        "editorial_status": "idea",
        "protect_from_burning": False,
        "burn_risk": "high",
        "one_line_story": "Built a billion-dollar company to fight capitalism. Gave it away to save the planet.",
        "human_angle": "All his life he built. Then he decided to give it all away.",
        "human_before_success": "Professional climber turning outdoor gear into business",
        "central_conflict": "Growth and profit vs. planetary survival",
        "key_decision": "Transfer ownership to fight climate change",
        "main_risk": "Destroying the company's mission stability",
        "turning_point": "Deciding to give away the company in 2022",
        "transformation": "From businessman to climate activist",
        "legacy_today": "Living proof that business can serve the planet",
        "hook_family": "lo_que_nadie_sabe",
        "primary_hook": "Construyó una compañía de miles de millones... y luego la regaló.",
        "alternative_hooks": ["El empresario que decidió regalar su empresa"],
        "closing_angle": "The greatest business decision was to stop trying to be a business.",
        "source_links": ["https://www.patagonia.com/our-footprint/"],
        "assigned_to_agent": "Borges",
        "created_by": "Hermoso"
    },
    {
        "protagonist_name": "James Harrison",
        "normalized_name": "james_harrison",
        "known_for": "Saving millions of babies with unique blood",
        "associated_company": "None",
        "country": "Australia",
        "region": "Oceania",
        "era": "1960s-2020s",
        "story_subject_type": "individual",
        "domain_category": "science",
        "protagonist_type": "healer",
        "story_level": "microstory",
        "publish_timing": "soon",
        "editorial_status": "idea",
        "protect_from_burning": False,
        "burn_risk": "low",
        "one_line_story": "Had a rare antibody. Donated blood for 60 years. Saved 2.4 million babies.",
        "human_angle": "Almost died from surgery. Made something life-saving from his blood.",
        "human_before_success": "Teenager who nearly died from chest surgery",
        "central_conflict": "His body could kill... or save millions",
        "key_decision": "Donate blood every week for the rest of his life",
        "main_risk": "Health complications from frequent donations",
        "turning_point": "Discovery that his plasma could treat Rhesus disease",
        "transformation": "From patient to the hero who saved millions",
        "legacy_today": "Lives on in every baby he helped bring into the world",
        "hook_family": "lo_que_nadie_sabe",
        "primary_hook": "Su sangre salvó a más de dos millones de bebés.",
        "alternative_hooks": ["Un héroe cuyo superpoder estaba en su sangre"],
        "closing_angle": "Sometimes your greatest wound becomes your greatest gift.",
        "source_links": ["https://www.giveblood.life.gov.au/about-blood-donation/history/james-harrison"],
        "assigned_to_agent": "Borges",
        "created_by": "Hermoso"
    },
    {
        "protagonist_name": "Guillermo Rauch",
        "normalized_name": "guillermo_rauch",
        "known_for": "Creating the modern web development infrastructure",
        "associated_company": "Vercel",
        "country": "Argentina",
        "region": "South America",
        "era": "2010s-2020s",
        "story_subject_type": "individual",
        "domain_category": "technology",
        "protagonist_type": "builder",
        "story_level": "microstory",
        "publish_timing": "soon",
        "editorial_status": "idea",
        "protect_from_burning": False,
        "burn_risk": "medium",
        "one_line_story": "Argentine developer built tools powering billions of webpages. Changed how the web is built.",
        "human_angle": "You use his tech every day. You probably never knew his name.",
        "human_before_success": "Self-taught programmer from Buenos Aires",
        "central_conflict": "Closed-source ecosystem vs. open-source future",
        "key_decision": "Build infrastructure that belongs to everyone",
        "main_risk": "Fighting against established tech giants",
        "turning_point": "Next.js became the standard for React development",
        "transformation": "From coder to invisible architect of the web",
        "legacy_today": "Tools powering thousands of modern websites and applications",
        "hook_family": "lo_que_nadie_sabe",
        "primary_hook": "Es posible que uses su tecnología todos los días... sin conocer su nombre.",
        "alternative_hooks": ["El latino que ayudó a construir el Internet moderno"],
        "closing_angle": "The most powerful builders are often the ones you never meet.",
        "source_links": ["https://vercel.com/company/history"],
        "assigned_to_agent": "Borges",
        "created_by": "Hermoso"
    },
    {
        "protagonist_name": "Norman Borlaug",
        "normalized_name": "norman_borlaug",
        "known_for": "Saving billions from famine with high-yield wheat",
        "associated_company": "None",
        "country": "United States",
        "region": "North America",
        "era": "1940s-2000s",
        "story_subject_type": "individual",
        "domain_category": "science",
        "protagonist_type": "scientist",
        "story_level": "microstory",
        "publish_timing": "soon",
        "editorial_status": "idea",
        "protect_from_burning": True,
        "burn_risk": "legendary",
        "one_line_story": "Developed wheat varieties that prevented mass starvation. Saved more lives than almost anyone.",
        "human_angle": "You've probably never heard his name. But you're alive because of him.",
        "human_before_success": "Young scientist obsessed with agricultural productivity",
        "central_conflict": "World population growth vs. limited food production",
        "key_decision": "Develop dwarf wheat that could grow anywhere",
        "main_risk": "Scientific failure could feed millions of deaths",
        "turning_point": "Green Revolution spread high-yield crops globally",
        "transformation": "From researcher to the man who saved humanity",
        "legacy_today": "Hundreds of millions of lives saved from starvation",
        "hook_family": "lo_que_nadie_sabe",
        "primary_hook": "Probablemente nunca escuchaste su nombre... pero salvó a más personas que casi cualquier ser humano.",
        "alternative_hooks": ["El hombre que alimentó al mundo"],
        "closing_angle": "Sometimes the greatest heroism has no movie deal.",
        "source_links": ["https://www.nobelprize.org/prizes/peace/1970/borlaug/biographical/"],
        "assigned_to_agent": "Borges",
        "created_by": "Hermoso",
        "protect_from_burning": True
    }
]

base_url = SUPABASE_URL + "/rest/v1/humanos_stories"

results = []
for story in candidates:
    try:
        req = urllib.request.Request(
            base_url,
            data=json.dumps(story, ensure_ascii=False).encode('utf-8'),
            method='POST',
            headers={
                'apikey': SUPABASE_KEY,
                'Authorization': 'Bearer ' + SUPABASE_KEY,
                'Content-Type': 'application/json',
                'Prefer': 'return=representation'
            }
        )
        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            print(f"✓ {story['protagonist_name']} → ID: {result[0]['id']}")
            results.append({'name': story['protagonist_name'], 'id': result[0]['id'], 'status': 'success'})
    except Exception as e:
        print(f"✗ {story['protagonist_name']} → ERROR: {e}")
        results.append({'name': story['protagonist_name'], 'status': 'failed', 'error': str(e)})

print(f"\nTotal: {len(results)}")
print(f"Success: {sum(1 for r in results if r.get('status') == 'success')}")
print(f"Failed: {sum(1 for r in results if r.get('status') == 'failed')}")
