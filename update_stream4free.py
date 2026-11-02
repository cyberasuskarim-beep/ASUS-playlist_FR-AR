import re
import requests

# URL brute de votre liste principale exacte
RAW_PLAYLIST_URL = "https://raw.githubusercontent.com/cyberasuskarim-beep/ASUS-playlist_FR-AR/refs/heads/main/ASUS-playlist_FR-AR.m3u"
PLAYLIST_FILE = "ASUS-playlist_FR-AR.m3u"

# L'URL exacte de la page web de la chaîne sur stream4free
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

def update_main_playlist():
    new_url = get_fresh_url()
    if not new_url:
        print("Impossible de récupérer un nouveau flux stream4free.")
        return

    # Télécharger la liste actuelle depuis GitHub
    response = requests.get(RAW_PLAYLIST_URL)
    if response.status_code != 200:
        print("Impossible de télécharger la playlist principale.")
        return
    
    lines = response.text.splitlines()

    updated_lines = []
    updated = False
    i = 0
    while i < len(lines):
        line = lines[i]
        updated_lines.append(line)
        
        # Cible la ligne correspondante dans votre liste principale
        if "#EXTINF" in line and ("National Geographic" in line or "stream4free" in line.lower()):
            if i + 1 < len(lines):
                # Remplace l'ancien lien par le nouveau flux frais
                updated_lines.append(new_url)
                i += 1  # Sauter l'ancien lien
                updated = True
        i += 1

    if updated:
        # Enregistre directement dans ASUS-playlist_FR-AR.m3u
        with open(PLAYLIST_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(updated_lines) + "\n")
        print("Fichier ASUS-playlist_FR-AR.m3u mis à jour avec succès !")
    else:
        print("Chaîne introuvable dans la playlist.")

if __name__ == "__main__":
    update_main_playlist()
