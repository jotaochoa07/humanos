import os
import re
import json
import urllib.request
import urllib.parse
import sys

# Formato de duración ISO 8601 a legible (ej: PT1M30S -> 1:30)
def parse_iso_duration(duration_str):
    if not duration_str:
        return "N/A"
    match = re.match(r'PT(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', duration_str)
    if not match:
        return duration_str
    hours, minutes, seconds = match.groups()
    parts = []
    if hours:
        parts.append(hours)
    parts.append(minutes if minutes else "00" if hours else "0")
    parts.append(seconds.zfill(2) if seconds else "00")
    return ":".join(parts)

def get_video_duration_api(video_id, api_key):
    try:
        url = f"https://www.googleapis.com/youtube/v3/videos?part=contentDetails&id={video_id}&key={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "HUMANOS-Agent-System/1.0"})
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            items = res.get("items", [])
            if items:
                raw_duration = items[0].get("contentDetails", {}).get("duration", "")
                return parse_iso_duration(raw_duration)
    except Exception:
        pass
    return "N/A"

def search_youtube_api(query, api_key, max_results=3):
    try:
        encoded_query = urllib.parse.quote(query)
        url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={encoded_query}&maxResults={max_results}&type=video&key={api_key}"
        req = urllib.request.Request(url, headers={"User-Agent": "HUMANOS-Agent-System/1.0"})
        with urllib.request.urlopen(req) as response:
            res = json.loads(response.read().decode('utf-8'))
            candidates = []
            for item in res.get("items", []):
                video_id = item.get("id", {}).get("videoId", "")
                snippet = item.get("snippet", {})
                title = snippet.get("title", "")
                channel = snippet.get("channelTitle", "")
                description = snippet.get("description", "")
                duration = get_video_duration_api(video_id, api_key)
                
                candidates.append({
                    "id": video_id,
                    "url": f"https://www.youtube.com/watch?v={video_id}",
                    "title": title,
                    "channel": channel,
                    "duration": duration,
                    "description": description
                })
            return candidates
    except Exception as e:
        print(f"[YouTube Searcher] Error con API Oficial: {e}. Usando fallback de raspado...")
        return search_youtube_scraping(query, max_results)

def search_youtube_scraping(query, max_results=3):
    encoded_query = urllib.parse.quote(query)
    url = f"https://www.youtube.com/results?search_query={encoded_query}"
    # Encabezados de agente de usuario simulando un navegador real
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36",
        "Accept-Language": "es-419,es;q=0.9,en;q=0.8"
    }
    req = urllib.request.Request(url, headers=headers)
    try:
        with urllib.request.urlopen(req) as response:
            html = response.read().decode('utf-8')
            
            # Buscar el bloque de datos JSON ytInitialData que contiene todos los resultados de búsqueda
            data_match = re.search(r"var ytInitialData\s*=\s*({.*?});", html)
            if data_match:
                try:
                    data = json.loads(data_match.group(1))
                    videos = []
                    
                    # Navegar la estructura anidada de YouTube para extraer la información
                    contents = data.get("contents", {}).get("twoColumnSearchResultsRenderer", {}).get("primaryContents", {}).get("sectionListRenderer", {}).get("contents", [])
                    for content in contents:
                        item_contents = content.get("itemSectionRenderer", {}).get("contents", [])
                        for item in item_contents:
                            if "videoRenderer" in item:
                                vr = item["videoRenderer"]
                                title = vr.get("title", {}).get("runs", [{}])[0].get("text", "")
                                video_id = vr.get("videoId", "")
                                channel = vr.get("ownerText", {}).get("runs", [{}])[0].get("text", "")
                                duration = vr.get("lengthText", {}).get("simpleText", "N/A")
                                
                                # Extraer la descripción
                                description = ""
                                if "detailedMetadataSnippets" in vr:
                                    description = vr["detailedMetadataSnippets"][0].get("snippetText", {}).get("runs", [{}])[0].get("text", "")
                                if not description and "descriptionSnippet" in vr:
                                    description = "".join([r.get("text", "") for r in vr["descriptionSnippet"].get("runs", [])])
                                
                                if video_id:
                                    videos.append({
                                        "id": video_id,
                                        "url": f"https://www.youtube.com/watch?v={video_id}",
                                        "title": title,
                                        "channel": channel,
                                        "duration": duration,
                                        "description": description[:150] + "..." if len(description) > 150 else description
                                    })
                    if videos:
                        return videos[:max_results]
                except Exception as ex:
                    print(f"[YouTube Searcher] Error al decodificar JSON ytInitialData: {ex}")
            
            # Fallback regex en caso de que cambie la estructura de ytInitialData
            video_ids = re.findall(r"\"videoId\":\"([^\"]+)\"", html)
            seen = set()
            unique_ids = [x for x in video_ids if not (x in seen or seen.add(x))][:max_results]
            
            candidates = []
            for vid in unique_ids:
                candidates.append({
                    "id": vid,
                    "url": f"https://www.youtube.com/watch?v={vid}",
                    "title": f"Candidato de Video {vid}",
                    "channel": "YouTube",
                    "duration": "N/A",
                    "description": "Extraído mediante fallback regex."
                })
            return candidates
    except Exception as e:
        print(f"[YouTube Searcher] Error de red en raspado: {e}")
        return []

def main():
    print("="*60)
    print("[YouTube Searcher Engine] Buscando referencias visuales de video...")
    print("="*60)
    
    ep_path = "C:/Users/Jota Ochoa/Antigravity/02_Projects/humanos/personajes/Jan_Koum/EP0001_Jan_Koum"
    shotlist_path = os.path.join(ep_path, "03_STORYBOARD", "asset_shotlist.md")
    output_md_path = os.path.join(ep_path, "03_STORYBOARD", "youtube_candidates.md")
    output_json_path = os.path.join(ep_path, "03_STORYBOARD", "youtube_candidates.json")
    
    if not os.path.exists(shotlist_path):
        print(f"[ERROR] No se encontró el shotlist en: {shotlist_path}")
        sys.exit(1)
        
    with open(shotlist_path, "r", encoding="utf-8") as f:
        shotlist_content = f.read()
        
    # Extraer las escenas y sus términos de búsqueda en inglés
    scenes = re.findall(r"## Escena (\d+)\n(?:[^\n]*\n)*?- Términos de Búsqueda \(Inglés\): (.*?)\n", shotlist_content)
    
    if not scenes:
        print("[Advertencia] No se encontraron escenas con 'Términos de Búsqueda (Inglés)'.")
        sys.exit(0)
        
    api_key = os.environ.get("YOUTUBE_API_KEY")
    results_map = {}
    
    markdown_report = []
    markdown_report.append("# EP001 - Candidatos de Video de YouTube\n")
    markdown_report.append("Este archivo contiene los videos de archivo recomendados y encontrados automáticamente según los términos del Shot List.\n")
    
    for scene_num, query_list in scenes:
        queries = [q.strip() for q in query_list.split(",") if q.strip()]
        # Usar el término principal (o combinación de los dos primeros)
        search_query = " ".join(queries[:2])
        print(f"Buscando para Escena {scene_num} con término: '{search_query}'...")
        
        if api_key:
            videos = search_youtube_api(search_query, api_key)
        else:
            videos = search_youtube_scraping(search_query)
            
        results_map[f"escena_{scene_num}"] = {
            "query_used": search_query,
            "candidates": videos
        }
        
        markdown_report.append(f"## Escena {scene_num}")
        markdown_report.append(f"*Términos usados: `{search_query}`*\n")
        
        if not videos:
            markdown_report.append("  *No se encontraron candidatos.*")
        else:
            for idx, vid in enumerate(videos, 1):
                markdown_report.append(f"{idx}. **[{vid['title']}]({vid['url']})**")
                markdown_report.append(f"   - **Canal:** {vid['channel']}")
                markdown_report.append(f"   - **Duración:** {vid['duration']}")
                if vid.get('description'):
                    markdown_report.append(f"   - **Descripción:** {vid['description']}")
                markdown_report.append("")
        markdown_report.append("---")
        
    # Guardar reporte JSON
    with open(output_json_path, "w", encoding="utf-8") as f:
        json.dump(results_map, f, ensure_ascii=False, indent=2)
        
    # Guardar reporte Markdown
    with open(output_md_path, "w", encoding="utf-8") as f:
        f.write("\n".join(markdown_report))
        
    print(f"[YouTube Searcher Engine] Reportes generados exitosamente:")
    print(f"  - Markdown: {output_md_path}")
    print(f"  - JSON: {output_json_path}")
    print("="*60)

if __name__ == "__main__":
    main()
