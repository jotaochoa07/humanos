import os
from openrouter_client import OpenRouterClient
from curie import CurieAgent

def main():
    print("=== PROBANDO AGENTE CURIE EN EL ENTORNO REAL ===")
    
    # Inicializar cliente y agente
    client = OpenRouterClient()
    curie = CurieAgent(client=client)
    
    character = "Jan Koum"
    
    # Ingestar documentos de prueba si no existen
    if not curie.has_library(character):
        print(f"\n[1] La biblioteca para {character} no existe. Creándola...")
        docs = [
            ("Jan Koum nació en Fastiv, Ucrania, en una casa sin calefacción ni agua caliente.", "Biografía Oficial"),
            ("Koum emigró a los Estados Unidos a los 16 años junto con su madre y su abuela, instalándose en Mountain View, California.", "Reportaje de Prensa"),
            ("De joven, Koum trabajó como barrendero en un supermercado mientras su madre hacía labores de niñera para subsistir.", "Entrevista WIRED"),
            ("En 2009, Koum fundó WhatsApp, enfocado obsesivamente en crear una aplicación sin publicidad ni trucos, inspirada en su deseo de privacidad tras vivir bajo la vigilancia soviética.", "Folleto Corporativo"),
            ("En 2014, Facebook adquirió WhatsApp por 19,000 millones de dólares.", "Nota Financiera Forbes")
        ]
        for text, src in docs:
            curie.ingest_document(character, text, src)
    else:
        print(f"\n[1] La biblioteca para {character} ya existe. Saltando paso de ingesta.")

    # 2. Hacer una consulta de prueba
    query = "Háblame de las dificultades de Jan Koum en su juventud y su origen humilde"
    print(f"\n[2] Realizando consulta semántica: '{query}'")
    
    results = curie.search_library(character, query, k=2)
    
    print("\nResultados encontrados por Curie:")
    for i, res in enumerate(results):
        print(f"{i+1}. [Fuente: {res['source']}] {res['text']} (Distancia: {res['distance']:.4f})")

    # 3. Probar recomendación de naming
    print("\n[3] Probando nomenclatura oficial de Curie:")
    carpeta = curie.get_episode_naming_recommendation(character, episode_num=1)
    asset = curie.get_naming_recommendation(character, index=1, description="Koum portrait", extension="jpg")
    print(f"Carpeta recomendada: {carpeta}")
    print(f"Asset recomendado: {asset}")

if __name__ == "__main__":
    main()
