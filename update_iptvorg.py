import requests

URL = "https://iptv-org.github.io/iptv/index.m3u"
OUTPUT_FILE = "iptv-org.m3u"

def update_playlist():
    print(f"Téléchargement depuis {URL}...")
    try:
        response = requests.get(URL, timeout=60)
        response.raise_for_status()
        
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write(response.text)
            
        print(f"Succès : {OUTPUT_FILE} mis à jour.")
    except Exception as e:
        print(f"Erreur : {e}")
        exit(1)

if __name__ == "__main__":
    update_playlist()
