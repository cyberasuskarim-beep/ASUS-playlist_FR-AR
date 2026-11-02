import os
import requests

# Nom et chemin direct du fichier à la racine du dépôt
OUTPUT_FILE = "stream4free.m3u"

# Lien de secours direct garanti pour National Geographic
stream_url = "https://sv1.data-stream.top/1c0f141aa5b01f9075e25609dcb27f45102ddf02b1a27ea3950afe2049e76041/hls/natgeo.m3u8"

# Contenu de la playlist M3U isolée
m3u_content = f"""#EXTM3U
#EXTINF:-1 tvg-id="" tvg-name="National Geographic" group-title="Stream4Free",National Geographic
{stream_url}
"""

# Écriture forcée du fichier sur le disque
print(f"Création en cours du fichier : {OUTPUT_FILE}")
with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    f.write(m3u_content)

# Vérification immédiate que le fichier existe bien
if os.path.exists(OUTPUT_FILE):
    print(f"SUCCÈS : Le fichier {OUTPUT_FILE} a été créé avec une taille de {os.path.getsize(OUTPUT_FILE)} octets.")
else:
    print("ERREUR CRITIQUE : Le fichier n'a pas pu être créé.")
