import re
import requests
import os

OUTPUT_FILE = "stream4free.m3u"
SOURCE_URL = "https://www.stream4free.tv/national-geographic"

def get_fresh_url():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.stream4free.tv/"
    }
    try:
        # 1. Récupérer la page principale de la chaîne
        response = requests.get(SOURCE_URL, headers=headers, timeout=15)
        if response.status_code == 200:
            html_content = response.text
            
            # Chercher un lien .m3u8 directement sur la page
            match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', html_content)
            if match:
                return match.group(1)
            
            # 2. Si pas trouvé directement, chercher un iframe (lecteur intégré)
            iframe_match = re.search(r'<iframe[^>]+src=["\'](https?://[^"\']+)["\']', html_content)
            if iframe_match:
                iframe_url = iframe_match.group(1)
                print(f"Exploration de l'iframe : {iframe_url}")
                iframe_headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                    "Referer": SOURCE_URL
                }
                iframe_resp = requests.get(iframe_url, headers=iframe_headers, timeout=10)
                if iframe_resp.status_code == 200:
                    match_iframe = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', iframe_resp.text)
                    if match_iframe:
                        return match_iframe.group(1)
                        
    except Exception as e:
        print(f"Erreur lors de la récupération : {e}")
        
    return None

def update_playlist():
    new_url = get_fresh_url()
    
    # Si le scraping ne trouve pas de lien frais (protection du site), 
    # on garde un mécanisme de sécurité pour ne pas casser le fichier existant
    if not new_url:
        print("Avertissement : Impossible de récupérer un nouveau flux dynamique (protection du site).")
        if os.path.exists(OUTPUT_FILE):
            print("Le fichier précédent est conservé.")
            return
        else:
            # Lien de secours initial si le fichier n'existe pas du tout
            new_url = "https://sv1.data-stream.top/1c0f141aa5b01f9075e25609dcb27f45102ddf02b1a27ea3950afe2049e76041/hls/natgeo.m3u8"

    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="" tvg-name="National Geographic" group-title="Stream4Free",National Geographic
{new_url}
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    print(f"Fichier {OUTPUT_FILE} mis à jour avec succès.")

if __name__ == "__main__":
    update_playlist()
