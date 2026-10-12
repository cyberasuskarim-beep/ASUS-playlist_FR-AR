import os
import re
from bs4 import BeautifulSoup
import requests

# URL de votre playlist originale sur GitHub
M3U_URL = "https://raw.githubusercontent.com/cyberasuskarim-beep/ASUS-playlist_FR-AR/refs/heads/main/ASUS-playlist_FR-AR.m3u"
OUTPUT_FILENAME = "ASUS-playlist_FR-AR.m3u"

# Dictionnaire associant chaque radio à sa page de lecteur officielle où se trouve le flux frais
RADIO_PLAYER_PAGES = {
    "Bejaia": "https://my.radioalgerie.dz/player/bejaia.html",
    "Tizi Ouzou": "https://my.radioalgerie.dz/player/tiziouzou.html",
    "Boumerdes": "https://my.radioalgerie.dz/player/boumerdes.html",
    "Alger": "https://my.radioalgerie.dz/player/elbahdja.html",
    "Jijel": "https://my.radioalgerie.dz/player/jijel.html",
    "Bouira": "https://my.radioalgerie.dz/player/bouira.html",
    "Setif": "https://my.radioalgerie.dz/player/setif.html",
}

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}


def fetch_fresh_streams():
  """Visite les pages de lecteur pour extraire les liens de streaming actuels"""
  fresh_streams = {}
  session = requests.Session()
  session.headers.update(HEADERS)

  for name, page_url in RADIO_PLAYER_PAGES.items():
    try:
      response = session.get(page_url, timeout=10)
      response.raise_for_status()

      soup = BeautifulSoup(response.text, "html.parser")
      stream_url = None

      # 1. Chercher dans les balises <audio> ou <source>
      audio_tag = soup.find(["audio", "source"])
      if audio_tag and audio_tag.get("src"):
        stream_url = audio_tag["src"]

      # 2. Si non trouvé, chercher via une expression régulière le lien .mp3 ou flux icecast dans la page
      if not stream_url:
        match = re.search(
            r'https?://[^\s\'"]+\.(?:mp3|aac|m3u8|stream)[^\s\'"]*',
            response.text,
        )
        if match:
          stream_url = match.group(0)

      if stream_url:
        fresh_streams[name] = stream_url
        print(f"[TROUVÉ] {name} -> {stream_url}")
      else:
        print(f"[AVERTISSEMENT] Aucun flux trouvé pour {name}")

    except Exception as e:
      print(f"[ERREUR] Impossible de récupérer {name} : {e}")

  return fresh_streams


def update_m3u_playlist():
  print(" [1/3] Récupération des nouveaux liens depuis Radio Algérie...")
  fresh_streams = fetch_fresh_streams()

  if not fresh_streams:
    print("Aucun flux récupéré, arrêt de la mise à jour.")
    return

  print("\n [2/3] Lecture de la playlist sur GitHub...")
  if os.path.exists(OUTPUT_FILENAME):
    with open(OUTPUT_FILENAME, "r", encoding="utf-8") as f:
      content = f.read()
  else:
    try:
      res = requests.get(M3U_URL, headers=HEADERS)
      res.raise_for_status()
      content = res.text
    except Exception as e:
      print(f"Erreur téléchargement M3U : {e}")
      return

  lines = content.splitlines()
  new_lines = []
  i = 0
  radios_updated = 0

  print("\n [3/3] Mise à jour des lignes dans le fichier M3U...")
  while i < len(lines):
    line = lines[i]

    if line.startswith("#EXTINF"):
      matched_radio = None
      for radio_name in fresh_streams:
        if radio_name.lower() in line.lower():
          matched_radio = radio_name
          break

      if matched_radio:
        # Conserver la ligne EXTINF originale intacte (avec logo et nom)
        new_lines.append(line)

        # Injecter le lien frais récupéré dynamiquement
        new_lines.append(fresh_streams[matched_radio])

        # Sauter l'ancienne ligne de flux s'il y en a une en dessous
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

    new_lines.append(line)
    i += 1

  with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines) + "\n")

  print(
      f"\nMise à jour terminée avec succès ! {radios_updated} radio(s) rafraîchie(s)"
      " dynamiquement."
  )


if __name__ == "__main__":
  update_m3u_playlist()
