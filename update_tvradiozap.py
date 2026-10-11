import re
import requests

URL = "https://tvradiozap.eu/live/x/vlc-mus/d/tvzeu.m3u"
OUTPUT_FILE = "tvradiozap.m3u"

def parse_m3u(content):
    """ Extrait les chaînes sous la forme {Nom_de_la_chaîne: (Entête_EXTINF, URL_flux)} """
    channels = {}
    lines = content.strip().splitlines()
    current_extinf = None
    
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            current_extinf = line
        elif line and not line.startswith("#"):
            if current_extinf:
                # Extrait le nom de la chaîne après la dernière virgule
                channel_name = current_extinf.split(",")[-1].strip()
                channels[channel_name] = (current_extinf, line)
                current_extinf = None
    return channels

def update_playlist():
    print(f"Téléchargement de la source distante depuis {URL}...")
    try:
        response = requests.get(URL, timeout=30)
        response.raise_for_status()
        remote_channels = parse_m3u(response.text)
        
        # Tente de lire le fichier local existant
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                local_channels = parse_m3u(f.read())
        except FileNotFoundError:
            local_channels = {}

        # Si le fichier local n'existe pas encore, on prend la liste distante entière
        if not local_channels:
            print("Aucun fichier local trouvé. Création de la liste initiale...")
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"Succès : {OUTPUT_FILE} a été créé.")
            return

        # Mise à jour des URL selon le nom de la chaîne
        updated_content = ["#EXTM3U"]
        updated_count = 0

        for name, (extinf, local_url) in local_channels.items():
            if name in remote_channels:
                remote_extinf, remote_url = remote_channels[name]
                if local_url != remote_url:
                    print(f"URL mise à jour pour : {name}")
                    updated_count += 1
                updated_content.append(extinf)
                updated_content.append(remote_url)
            else:
                # Conserve l'ancienne URL si la chaîne n'est plus dans la source distante
                updated_content.append(extinf)
                updated_content.append(local_url)

        # Enregistrement du fichier mis à jour
        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(updated_content) + "\n")
            
        print(f"Succès : {OUTPUT_FILE} mis à jour ({updated_count} URL de flux modifiées).")

    except Exception as e:
        print(f"Erreur : {e}")
        exit(1)

if __name__ == "__main__":
    update_playlist()
