import os

OUTPUT_FILE = "stream4free.m3u"

# Dictionnaire contenant vos chaînes : "Nom de la chaîne": "Lien direct ou lien de secours m3u8"
# Vous pouvez en rajouter autant que vous voulez ici !
CHANNELS = {
    "National Geographic": "https://sv1.data-stream.top/1c0f141aa5b01f9075e25609dcb27f45102ddf02b1a27ea3950afe2049e76041/hls/natgeo.m3u8",
    # Exemple pour ajouter une autre chaîne (remplacez le nom et le lien par les vôtres) :
    # "National Geographic Wild": "VOTRE_LIEN_M3U8_ICI",
}

def generate_playlist():
    # En-tête obligatoire d'un fichier M3U
    m3u_content = "#EXTM3U\n"

    # Boucle pour ajouter chaque chaîne proprement au format M3U
    for name, url in CHANNELS.items():
        m3u_content += f'#EXTINF:-1 tvg-id="" tvg-name="{name}" group-title="Stream4Free",{name}\n'
        m3u_content += f"{url}\n"

    # Écriture du fichier final
    print(f"Création en cours du fichier : {OUTPUT_FILE}")
    with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
        f.write(m3u_content)

    if os.path.exists(OUTPUT_FILE):
        print(f"SUCCÈS : Le fichier {OUTPUT_FILE} a été mis à jour avec {len(CHANNELS)} chaîne(s).")
    else:
        print("ERREUR : Le fichier n'a pas pu être créé.")

if __name__ == "__main__":
    generate_playlist()
