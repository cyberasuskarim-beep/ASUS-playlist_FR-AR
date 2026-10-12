import os
import requests

# URL de votre playlist originale sur GitHub
M3U_URL = "https://raw.githubusercontent.com/cyberasuskarim-beep/ASUS-playlist_FR-AR/refs/heads/main/ASUS-playlist_FR-AR.m3u"
OUTPUT_FILENAME = "ASUS-playlist_FR-AR.m3u"

# Dictionnaire complet de vos radios
FRESH_RADIOS_STREAMS = {
    "bejaia": "https://radiobejaia.ice.infomaniak.ch/bejaia.mp3",
    "tizi ouzou": "https://radiotiziouzou.ice.infomaniak.ch/tiziouzou.mp3",
    "boumerdes": "https://radioboumerdes.ice.infomaniak.ch/boumerdes.mp3",
    "jijel": "https://radiojijel.ice.infomaniak.ch/jijel.mp3",
    "bouira": "https://radiobouira.ice.infomaniak.ch/bouira.mp3",
    "setif": "https://radiosetif.ice.infomaniak.ch/setif.mp3",
    # Mots-clés élargis pour Alger / El Bahdja
    "alger": "https://radioelbahdja.ice.infomaniak.ch/elbahdja.mp3",
    "bahdja": "https://radioelbahdja.ice.infomaniak.ch/elbahdja.mp3",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def update_m3u_playlist():
  print(" [1/2] Lecture de la playlist originale sur GitHub...")
  if os.path.exists(OUTPUT_FILENAME):
    with open(OUTPUT_FILENAME, "r", encoding="utf-8") as f:
      content = f.read()
  else:
    try:
      res = requests.get(M3U_URL, headers=HEADERS)
      res.raise_for_status()
      content = res.text
    except Exception as e:
      print(f"Erreur lors du téléchargement de la playlist : {e}")
      return

  lines = content.splitlines()
  new_lines = []
  i = 0
  radios_updated = 0

  print(" [2/2] Mise à jour des flux de toutes les radios...")
  while i < len(lines):
    line = lines[i]

    # Détection des lignes #EXTINF
    if line.startswith("#EXTINF"):
      matched_url = None
      line_lower = line.lower()

      # On cherche quel mot-clé correspond à cette ligne
      for keyword, stream_url in FRESH_RADIOS_STREAMS.items():
        if keyword in line_lower:
          matched_url = stream_url
          break

      if matched_url:
        # Conserver la ligne #EXTINF d'origine intacte (logos et titres)
        new_lines.append(line)

        # Injecter le flux direct vérifié
        new_lines.append(matched_url)

        # Sauter l'ancienne ligne d'URL ou d'option sous jacente
        if i + 1 < len(lines):
          if lines[i + 1].startswith("#EXTVLCOPT"):
            i += 1
          if (
              i + 1 < len(lines)
              and not lines[i + 1].startswith("#")
              and not lines[i + 1].startswith("$")
          ):
            i += 1

        radios_updated += 1
        i += 1
        continue

    # Conserver toutes les autres chaînes TV et lignes sans modification
    new_lines.append(line)
    i += 1

  # Écriture du fichier final
  with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines) + "\n")

  print(
      f"\nMise à jour réussie ! {radios_updated} radio(s) mise(s) à jour (y"
      " compris Alger)."
  )


if __name__ == "__main__":
  update_m3u_playlist()
