import re
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen

PLAYLIST = Path("ASUS-playlist_FR-AR.m3u")

TVRADIOZAP_URL = "https://tvradiozap.eu/live/x/vlc/s/tvrztv.m3u"

# Playlist publique générale IPTV-org
IPTVORG_URL = "https://iptv-org.github.io/iptv/index.m3u"

TIMEOUT = 30


def download(url):
    request = Request(
        url,
        headers={"User-Agent": "Mozilla/5.0"}
    )
    with urlopen(request, timeout=TIMEOUT) as response:
        return response.read().decode("utf-8", errors="replace")


def normalize(text):
    text = unicodedata.normalize("NFKD", text)
    text = "".join(c for c in text if not unicodedata.combining(c))
    text = text.lower()

    # Retirer les indications qui ne servent pas à identifier la chaîne
    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"\([^)]*\)", "", text)

    text = text.replace("&", "and")
    text = re.sub(r"[^a-z0-9]+", "", text)

    return text


def channel_name(extinf):
    if "," not in extinf:
        return ""

    return extinf.split(",", 1)[1].strip()


def parse_m3u(text):
    channels = {}

    lines = text.splitlines()
    current_info = None

    for line in lines:
        line = line.strip()

        if line.startswith("#EXTINF"):
            current_info = line

        elif current_info and line and not line.startswith("#"):
            name = channel_name(current_info)

            if name:
                key = normalize(name)

                if key and key not in channels:
                    channels[key] = {
                        "name": name,
                        "info": current_info,
                        "url": line
                    }

            current_info = None

    return channels


def extract_tvg_id(extinf):
    match = re.search(r'tvg-id="([^"]*)"', extinf, re.I)
    return match.group(1).strip() if match else ""


def build_indexes(channels):
    by_name = {}

    by_tvg_id = {}

    for key, item in channels.items():
        by_name[key] = item

        tvg_id = extract_tvg_id(item["info"])

        if tvg_id:
            by_tvg_id[tvg_id.lower()] = item

    return by_name, by_tvg_id


def find_match(my_info, my_name, source_by_name, source_by_id):
    # 1. Correspondance par tvg-id lorsqu'il existe
    my_tvg_id = extract_tvg_id(my_info)

    if my_tvg_id:
        item = source_by_id.get(my_tvg_id.lower())

        if item:
            return item

    # 2. Correspondance exacte sur le nom normalisé
    key = normalize(my_name)

    if key in source_by_name:
        return source_by_name[key]

    return None


def update_playlist(original, tvz, iptv):
    tvz_by_name, tvz_by_id = build_indexes(tvz)
    iptv_by_name, iptv_by_id = build_indexes(iptv)

    lines = original.splitlines()

    output = []
    current_info = None

    updated_tvz = 0
    updated_iptv = 0
    kept_old = 0

    for line in lines:
        stripped = line.strip()

        if stripped.startswith("#EXTINF"):
            current_info = line
            output.append(line)
            continue

        if current_info and stripped and not stripped.startswith("#"):
            old_url = line
            name = channel_name(current_info)

            # PRIORITÉ 1 : TVRadioZap
            match = find_match(
                current_info,
                name,
                tvz_by_name,
                tvz_by_id
            )

            if match:
                output.append(match["url"])
                updated_tvz += 1
                current_info = None
                continue

            # PRIORITÉ 2 : IPTV-org
            match = find_match(
                current_info,
                name,
                iptv_by_name,
                iptv_by_id
            )

            if match:
                output.append(match["url"])
                updated_iptv += 1
                current_info = None
                continue

            # Aucun nouveau flux trouvé :
            # on conserve celui de ta playlist.
            output.append(old_url)
            kept_old += 1

            current_info = None
            continue

        output.append(line)

    result = "\n".join(output) + "\n"

    print("======================================")
    print("Mise à jour ASUS playlist")
    print("======================================")
    print(f"TVRadioZap : {updated_tvz}")
    print(f"IPTV-org   : {updated_iptv}")
    print(f"Ancien lien conservé : {kept_old}")
    print("======================================")

    return result


def main():
    if not PLAYLIST.exists():
        raise SystemExit(f"Fichier introuvable : {PLAYLIST}")

    print("Téléchargement TVRadioZap...")
    tvz_text = download(TVRADIOZAP_URL)

    print("Téléchargement IPTV-org...")
    iptv_text = download(IPTVORG_URL)

    original = PLAYLIST.read_text(
        encoding="utf-8",
        errors="replace"
    )

    tvz = parse_m3u(tvz_text)
    iptv = parse_m3u(iptv_text)

    print(f"Chaînes TVRadioZap disponibles : {len(tvz)}")
    print(f"Chaînes IPTV-org disponibles : {len(iptv)}")

    updated = update_playlist(
        original,
        tvz,
        iptv
    )

    if updated != original:
        PLAYLIST.write_text(
            updated,
            encoding="utf-8",
            newline="\n"
        )

        print("Playlist modifiée.")
    else:
        print("Aucune modification nécessaire.")


if __name__ == "__main__":
    main()
