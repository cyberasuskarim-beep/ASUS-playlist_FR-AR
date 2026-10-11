import requests

URL = "https://iptv-org.github.io/iptv/index.m3u"
OUTPUT_FILE = "iptv-org.m3u"

def parse_m3u(content):
    channels = {}
    lines = content.strip().splitlines()
    current_extinf = None
    
    for line in lines:
        line = line.strip()
        if line.startswith("#EXTINF:"):
            current_extinf = line
        elif line and not line.startswith("#"):
            if current_extinf:
                channel_name = current_extinf.split(",")[-1].strip()
                channels[channel_name] = (current_extinf, line)
                current_extinf = None
    return channels

def update_playlist():
    print(f"Téléchargement de la source IPTV-org depuis {URL}...")
    try:
        response = requests.get(URL, timeout=60)
        response.raise_for_status()
        remote_channels = parse_m3u(response.text)
        
        try:
            with open(OUTPUT_FILE, "r", encoding="utf-8") as f:
                local_channels = parse_m3u(f.read())
        except FileNotFoundError:
            local_channels = {}

        if not local_channels:
            print("Aucun fichier local trouvé. Création de la liste initiale...")
            with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
                f.write(response.text)
            print(f"Succès : {OUTPUT_FILE} a été créé.")
            return

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
                updated_content.append(extinf)
                updated_content.append(local_url)

        with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
            f.write("\n".join(updated_content) + "\n")
            
        print(f"Succès : {OUTPUT_FILE} mis à jour ({updated_count} URL de flux modifiées).")

    except Exception as e:
        print(f"Erreur : {e}")
        exit(1)

if __name__ == "__main__":
    update_playlist()
