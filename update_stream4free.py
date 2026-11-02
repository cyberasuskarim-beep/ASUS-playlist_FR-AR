import re
import requests

# Nom du fichier M3U dédié exclusivement à la source stream4free
OUTPUT_FILE = "stream4free.m3u"

# L'URL exacte de la page web de la chaîne
SOURCE_URL = "https://www.stream4free.tv/national-geographic"

def get_fresh_url():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Referer": "https://www.stream4free.tv/"
    }
    try:
        response = requests.get(SOURCE_URL, headers=headers, timeout=10)
        if response.status_code == 200:
            match = re.search(r'(https?://[^\s\'"]+\.m3u8[^\s\'"]*)', response.text)
            if match:
                return match.group(1)
    except Exception as e:
        print(f"Erreur lors de la récupération du flux : {e}")
    return None

def create_isolated_playlist():
    new_url = get_fresh_url()
    if not new_url:
        print("Impossible de récupérer un nouveau flux stream4free.")
        return

    # Création du contenu M3U autonome
    m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="" tvg-name="National Geographic" group-title="Stream4Free",National Geographic
{new_url}
"""

    # Enregistrement exclusivement dans stream4free.m3u
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(m3u_content)
    
    print(f"Fichier {OUTPUT_FILE} généré et mis à jour avec succès !")

if __name__ == "__main__":
    create_isolated_playlist()
