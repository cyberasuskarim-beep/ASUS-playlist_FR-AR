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
        response = requests.get(SOURCE_URL, headers=headers, timeout=15)
        print(f"Code statut de la page source : {response.status_code}")
        if response.status_code == 200:
            match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', response.text)
            if match:
                flux = match.group(1)
                print(f"Flux trouvé avec succès : {flux}")
                return flux
            else:
                print("Erreur : Aucun lien .m3u8 trouvé dans le code source de la page.")
        else:
            print(f"Erreur HTTP : {response.status_code}")
    except Exception as e:
        print(f"Erreur lors de la requête : {e}")
    return None

def create_isolated_playlist():
    new_url = get_fresh_url()
    if not new_url:
        print("Abandon : Impossible de récupérer un nouveau flux.")
        return

    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="" tvg-name="National Geographic" group-title="Stream4Free",National Geographic
{new_url}
"""

    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    
    print(f"Fichier {OUTPUT_FILE} écrit avec succès.")

if __name__ == "__main__":
    create_isolated_playlist()
