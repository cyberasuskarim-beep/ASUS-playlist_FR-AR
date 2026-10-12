import os
import requests

# URL de votre playlist originale sur GitHub (en secours si le fichier local n'existe pas)
M3U_URL = "https://raw.githubusercontent.com/cyberasuskarim-beep/ASUS-playlist_FR-AR/refs/heads/main/ASUS-playlist_FR-AR.m3u"
OUTPUT_FILENAME = "ASUS-playlist_FR-AR.m3u"

# Dictionnaire exact de vos radios et de leurs flux directs
FRESH_RADIOS_STREAMS = {
    "bejaia": "https://radiobejaia.ice.infomaniak.ch/bejaia.mp3",
    "tizi ouzou": "https://radiotiziouzou.ice.infomaniak.ch/tiziouzou.mp3",
    "boumerdes": "https://radioboumerdes.ice.infomaniak.ch/boumerdes.mp3",
    "jijel": "https://radiojijel.ice.infomaniak.ch/jijel.mp3",
    "bouira": "https://radiobouira.ice.infomaniak.ch/bouira.mp3",
    "setif": "https://radiosetif.ice.infomaniak.ch/setif.mp3",
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
  print(" [1/2] Téléchargement de la playlist propre depuis GitHub...")
  try:
    res = requests.get(M3U_URL, headers=HEADERS)
    res.raise_for_status()
    content = res.text
  except Exception as e:
    print(f"Erreur lors du téléchargement : {e}")
    return

  lines = content.splitlines()
  new_lines = []
  i = 0
  radios_updated = 0

  print(" [2/2] Injection propre des flux radios...")
  while i < len(lines):
    line = lines[i]

    # Si c'est une ligne de métadonnées
    if line.startswith("#EXTINF"):
      matched_url = None
      line_lower = line.lower()

      # Vérifier si c'est l'une de nos radios
      for keyword, stream_url in FRESH_RADIOS_STREAMS.items():
        if keyword in line_lower:
          matched_url = stream_url
          break

      if matched_url:
        # 1. On garde la ligne EXTINF originale (avec nom et logo)
        new_lines.append(line)
        # 2. On ajoute immédiatement le flux direct
        new_lines.append(matched_url)

        # 3. On passe à la ligne suivante dans l'ancien fichier
        i += 1
        # Si la ligne suivante était l'ancienne URL (ne commence pas par #), on l'ignore (on la saute)
        if i < len(lines) and not lines[i].startswith("#"):
          i += 1

        radios_updated += 1
        continue

    # Pour toutes les autres lignes (TV, etc.), on les recopie normalement
    new_lines.append(line)
    i += 1

  # Sauvegarde finale
  with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines) + "\n")

  print(
      f"\nMise à jour terminée ! {radios_updated} radio(s) mise(s) à jour avec"
      " succès."
  )


if __name__ == "__main__":
  update_m3u_playlist()
