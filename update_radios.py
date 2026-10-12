import os
import re
from bs4 import BeautifulSoup
import requests

# URL de votre playlist originale sur GitHub
M3U_URL = "https://raw.githubusercontent.com/cyberasuskarim-beep/ASUS-playlist_FR-AR/refs/heads/main/ASUS-playlist_FR-AR.m3u"
OUTPUT_FILENAME = "ASUS-playlist_FR-AR.m3u"

# Source officielle Radio Algérie
LIVE_PLAYER_URL = "https://radioalgerie.dz/player/fr/live-player"
BASE_URL = "https://radioalgerie.dz"

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML,"
        " like Gecko) Chrome/120.0.0.0 Safari/537.36"
    )
}

# Liste des radios à chercher/mettre à jour (expressions régulières / mots-clés)
RADIOS_KEYWORDS = [
    "chaine 1",
    "chaine 2",
    "chaine 3",
    "jil fm",
    "radio coran",
    "radio culture",
    "soummam",
    "alger chaine",
    "radio algerie",
]


def radio_est_concernee(nom_ou_ligne):
  """Vérifie si la ligne ou le nom contient un mot-clé de nos radios."""
  nom_lower = nom_ou_ligne.lower()
  return any(kw in nom_lower for kw in RADIOS_KEYWORDS)


def fetch_live_radio_streams():
  """Récupère les derniers flux audio direct depuis Radio Algérie Live."""
  session = requests.Session()
  session.headers.update(HEADERS)
  streams = {}

  try:
    print(" [1/3] Connexion au site officiel Radio Algérie...")
    res = session.get(LIVE_PLAYER_URL, timeout=15)
    res.raise_for_status()

    soup = BeautifulSoup(res.text, "html.parser")
    links = soup.find_all("a", href=True)

    for link in links:
      href = link["href"]
      if "/player/" in href and (
          "/content/" in href or "/live/" in href or "chaine" in href
      ):
        name = link.get_text(strip=True) or href.split("/")[-1]
        name_cleaned = (
            name.replace("Radio", "")
            .replace("إذاعة", "")
            .replace("chaine", "Chaine ")
            .strip()
        )

        if not name_cleaned or len(name_cleaned) < 2:
          continue

        page_url = href if href.startswith("http") else BASE_URL + href

        try:
          p_res = session.get(page_url, timeout=8)
          p_soup = BeautifulSoup(p_res.text, "html.parser")

          stream_url = None

          # 1. Recherche balise audio/source
          audio_tag = p_soup.find(["audio", "source"])
          if audio_tag and audio_tag.get("src"):
            stream_url = audio_tag["src"]

          # 2. Recherche iframes / icecast
          if not stream_url:
            for iframe in p_soup.find_all("iframe", src=True):
              iframe_src = iframe["src"]
              if (
                  "stream" in iframe_src
                  or "live" in iframe_src
                  or "icecast" in iframe_src
              ):
                stream_url = iframe_src
                break

          # 3. Regex dans le code JS
          if not stream_url:
            found_urls = re.findall(
                r'https?://[^\s\'"]+\.(?:mp3|aac|m3u8|pls)[^\s\'"]*',
                p_res.text,
            )
            if found_urls:
              stream_url = found_urls[0]

          if stream_url:
            if not stream_url.startswith("http"):
              stream_url = BASE_URL + stream_url
            streams[name_cleaned] = stream_url
            print(f"   -> Flux récupéré : {name_cleaned} => {stream_url}")

        except Exception:
          pass

  except Exception as e:
    print(f"Erreur lors de la récupération des flux radios : {e}")

  return streams


def update_m3u_playlist():
  # 1. Récupérer les flux radios à jour
  fresh_streams = fetch_live_radio_streams()

  # 2. Récupérer le contenu actuel du fichier m3u (soit localement, soit sur GitHub)
  print("\n [2/3] Lecture du fichier M3U original...")
  if os.path.exists(OUTPUT_FILENAME):
    with open(OUTPUT_FILENAME, "r", encoding="utf-8") as f:
      content = f.read()
  else:
    res = requests.get(M3U_URL, headers=HEADERS)
    res.raise_for_status()
    content = res.text

  lines = content.splitlines()
  new_lines = []

  i = 0
  radios_updated = 0

  print("\n [3/3] Mise à jour des radios et conservation des chaînes TV...")
  while i < len(lines):
    line = lines[i]

    # Détection des entrées #EXTINF
    if line.startswith("#EXTINF"):
      is_radio = False
      matched_name = None

      # Vérification si c'est une radio
      for radio_name in fresh_streams:
        # Correspondance par nom exact ou par mots-clés
        if (
            radio_name.lower() in line.lower()
            or "radio" in line.lower()
            or "group-title=\"radios\"" in line.lower()
            or "group-title=\"radio\"" in line.lower()
        ):
          if radio_name.lower() in line.lower() or radio_est_concernee(line):
            is_radio = True
            matched_name = radio_name
            break

      if is_radio and matched_name:
        # On garde la ligne #EXTINF originale
        new_lines.append(line)

        # On remplace l'URL qui suit immédiatement par le nouveau flux frais
        if i + 1 < len(lines) and not lines[i + 1].startswith("#"):
          new_lines.append(fresh_streams[matched_name])
          i += 2  # Avancer de 2 lignes (EXTINF + URL)
          radios_updated += 1
          continue

    # Pour toutes les autres lignes (Chaînes Télévision, Headers, Commentaires...)
    new_lines.append(line)
    i += 1

  # Écriture du fichier final
  with open(OUTPUT_FILENAME, "w", encoding="utf-8") as f:
    f.write("\n".join(new_lines) + "\n")

  print(
      f"\n MISA À JOUR REUSSIE ! {radios_updated} radio(s) mise(s) à jour."
      " Toutes les chaînes télévisées sont restées strictement inchangées.\n"
  )


if __name__ == "__main__":
  update_m3u_playlist()
