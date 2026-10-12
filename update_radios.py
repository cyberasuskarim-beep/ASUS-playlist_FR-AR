import os
import requests

# URL de votre playlist originale sur GitHub
M3U_URL = "https://raw.githubusercontent.com/cyberasuskarim-beep/ASUS-playlist_FR-AR/refs/heads/main/ASUS-playlist_FR-AR.m3u"
OUTPUT_FILENAME = "ASUS-playlist_FR-AR.m3u"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# Table de correspondance exacte des flux directs qui fonctionnent
MAPPING_RADIOS = {
    "06 - Bejaia": "https://radiobejaia.ice.infomaniak.ch/bejaia.mp3",
    "15 - Tizi Ouzou": "https://radiotiziouzou.ice.infomaniak.ch/tiziouzou.mp3",
    "35 - Boumerdes": "https://radioboumerdes.ice.infomaniak.ch/boumerdes.mp3",
    "16 - Alger": "https://radioelbahdja.ice.infomaniak.ch/elbahdja.mp3",
    "18 - Jijel": "https://radiojijel.ice.infomaniak.ch/jijel.mp3",
    "10 - Bouira": "https://radiobouira.ice.infomaniak.ch/bouira.mp3",
    "19 - Setif": "https://radiosetif.ice.infomaniak.ch/setif.mp3",
}


def update_m3u():
  print("1. Téléchargement de la playlist M3U...")
  try:
    res = requests.get(M3U_URL, headers=HEADERS)
    res.raise_for_status()
    content = res.text
  except Exception as e:
    print(f"Erreur de téléchargement : {e}")
    return

  lines = content.splitlines()
  new_lines = []
  i = 0
  total_lines = len(lines)
  radios_mises_a_jour = 0

  while i < total_lines:
    line = lines[i]
    new_lines.append(line)

    # Si c'est la ligne #EXTINF d'une radio
    if line.startswith("#EXTINF"):
      for radio_name, stream_url in MAPPING_RADIOS.items():
        if radio_name in line:
          # Si la ligne suivante existe et est l'ancienne URL (pas un autre #EXTINF)
          if i + 1 < total_lines and not lines[i + 1].startswith("#"):
            new_lines.append(stream_url)
            i += 1  # On saute l'ancienne URL
            radios_mises_a_jour += 1
            break

    i += 1

  # Écriture du fichier final
  with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines) + "\n")

  print(f"Terminé ! {radios_mises_a_jour} radio(s) mise(s) à jour avec succès.")


if __name__ == "__main__":
  update_m3u()
