import re
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen


PLAYLIST = Path("ASUS-playlist_FR-AR.m3u")

TVRADIOZAP_URL = "https://tvradiozap.eu/get.php?username=f:1$ty:tv&password=public&type=m3u_plus"
IPTVORG_URL = "https://iptv-org.github.io/iptv/index.m3u"

TIMEOUT = 30


TVZ_HEADERS = {
    "User-Agent": "Mozilla/5.0",
    "Referer": "https://tvradiozap.eu/",
}


HEADERS = {
    "User-Agent": "Mozilla/5.0",
}


# ============================================================
# URLS PERSONNALISÉES
# ============================================================
#
# Ces chaînes ne doivent PAS être remplacées automatiquement
# par TVRadioZap ou IPTV-org.
#
# La clé doit correspondre au nom normalisé de la chaîne.
#
# "Voyages & Saveurs"
# devient :
# "voyagesandsaveurs"
#
# ============================================================

CUSTOM_URLS = {
    "voyagesandsaveurs": (
        "https://amg01821-amg01821c24-samsung-fr-5157.playouts.now.amagi.tv/"
        "playlist/amg01821-lovetvfast-voyagesandsaveurs-samsungfr/playlist.m3u8"
    ),
}


def download(url, headers):
    request = Request(url, headers=headers)

    with urlopen(request, timeout=TIMEOUT) as response:
        return response.read().decode(
            "utf-8",
            errors="replace"
        )


def normalize(text):
    if not text:
        return ""

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )

    text = text.lower()

    text = re.sub(
        r"\[[^\]]*\]",
        "",
        text
    )

    text = re.sub(
        r"\([^)]*\)",
        "",
        text
    )

    text = re.sub(
        r"\b(4k|uhd|fhd|hd|sd|1080p|720p|576p|480p)\b",
        "",
        text,
        flags=re.I
    )

    text = re.sub(
        r"\b(live|direct|fr|fra)\b",
        "",
        text,
        flags=re.I
    )

    text = text.replace(
        "&",
        "and"
    )

    return re.sub(
        r"[^a-z0-9]+",
        "",
        text
    )


def normalize_id(text):
    if not text:
        return ""

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )

    text = text.lower().strip()

    return re.sub(
        r"[-_.:]+",
        "",
        text
    )


def channel_name(extinf):
    if "," not in extinf:
        return ""

    return extinf.split(
        ",",
        1
    )[1].strip()


def get_tvg_id(extinf):
    match = re.search(
        r'tvg-id\s*=\s*"([^"]*)"',
        extinf,
        re.I
    )

    if match:
        return match.group(1).strip()

    return ""


def parse_m3u(text):
    channels = []

    current_info = None

    for raw in text.splitlines():

        line = raw.strip()

        if not line:
            continue

        if line.startswith("#EXTINF"):
            current_info = line
            continue

        if (
            current_info
            and line
            and not line.startswith("#")
        ):

            name = channel_name(
                current_info
            )

            if name:

                channels.append({
                    "info": current_info,
                    "name": name,
                    "url": line
                })

            current_info = None

    return channels


def make_indexes(channels):
    by_name = {}
    by_id = {}

    for item in channels:

        name_key = normalize(
            item["name"]
        )

        if name_key:

            if name_key not in by_name:
                by_name[name_key] = item

        ident = normalize_id(
            get_tvg_id(item["info"])
        )

        if ident:

            if ident not in by_id:
                by_id[ident] = item

    return by_name, by_id


# ============================================================
# RECHERCHE SÉCURISÉE
# ============================================================
#
# IMPORTANT :
#
# On ne fait PLUS de correspondance partielle.
#
# Avant :
#
#     tvg-id
#        ↓
#     correspondance partielle
#
# Cela pouvait envoyer une chaîne vers une autre.
#
# Maintenant :
#
#     URL personnalisée
#            ↓
#     nom exact
#            ↓
#     tvg-id + nom identique
#            ↓
#     aucune correspondance
#
# ============================================================

def find_match(info, name, by_name, by_id):

    key = normalize(name)

    # --------------------------------------------------------
    # 1. URL PERSONNALISÉE
    # --------------------------------------------------------

    if key in CUSTOM_URLS:

        return {
            "name": name,
            "url": CUSTOM_URLS[key],
            "custom": True
        }

    # --------------------------------------------------------
    # 2. NOM EXACT
    # --------------------------------------------------------

    if key and key in by_name:

        return by_name[key]

    # --------------------------------------------------------
    # 3. TVG-ID
    #
    # Le tvg-id n'est accepté que si le NOM correspond
    # exactement lui aussi.
    # --------------------------------------------------------

    ident = normalize_id(
        get_tvg_id(info)
    )

    if ident and ident in by_id:

        candidate = by_id[ident]

        candidate_name = normalize(
            candidate["name"]
        )

        if (
            key
            and candidate_name
            and key == candidate_name
        ):

            return candidate

        print(
            "  TVG-ID ignoré : nom différent"
        )

        print(
            "    Playlist :",
            name
        )

        print(
            "    Source   :",
            candidate["name"]
        )

    # --------------------------------------------------------
    # 4. AUCUNE CORRESPONDANCE
    # --------------------------------------------------------

    return None


def test_stream(url, tvradiozap=False):

    if not url.startswith(
        "http://"
    ) and not url.startswith(
        "https://"
    ):
        return False

    if tvradiozap:

        headers = TVZ_HEADERS.copy()

    else:

        headers = HEADERS.copy()

    headers["Range"] = "bytes=0-4095"

    try:

        request = Request(
            url,
            headers=headers
        )

        with urlopen(
            request,
            timeout=8
        ) as response:

            if (
                response.status < 200
                or response.status >= 400
            ):
                return False

            data = response.read(
                4096
            )

            if not data:
                return False

            sample = data[
                :1000
            ].lower()

            if b"<html" in sample:
                return False

            if b"<body" in sample:
                return False

            if b"<!doctype html" in sample:
                return False

            content_type = response.headers.get(
                "Content-Type",
                ""
            ).lower()

            if "mpegurl" in content_type:
                return True

            if ".m3u8" in url.lower():
                return True

            if "audio/" in content_type:
                return True

            if "aac" in content_type:
                return True

            if "mp3" in content_type:
                return True

            if "mpeg" in content_type:
                return True

            if len(data) >= 188:

                for pos in range(
                    min(188, len(data))
                ):

                    if data[pos] == 0x47:
                        return True

            return response.status in (
                200,
                206
            )

    except Exception:

        return False


def remove_vlc_lines(text):

    result = []

    removed = 0

    for line in text.splitlines():

        value = line.strip().lower()

        if value.startswith(
            "#extvlcopt:"
        ):

            removed += 1
            continue

        if value.startswith(
            "#vlcopt:"
        ):

            removed += 1
            continue

        result.append(line)

    return (
        "\n".join(result)
        + "\n",
        removed
    )


def read_playlist(text):

    header = []

    channels = []

    current_info = None

    for line in text.splitlines():

        stripped = line.strip()

        if stripped.startswith(
            "#EXTINF"
        ):

            current_info = line
            continue

        if (
            current_info
            and stripped
            and not stripped.startswith("#")
        ):

            channels.append({
                "info": current_info,
                "url": line
            })

            current_info = None
            continue

        if current_info is None:

            header.append(line)

    return (
        header,
        channels
    )


def build_channel(
    info,
    url,
    use_tvradiozap
):

    result = []

    result.append(info)

    if use_tvradiozap:

        result.append(
            "#EXTVLCOPT:http-referrer=https://tvradiozap.eu/"
        )

        result.append(
            "#EXTVLCOPT:http-user-agent=Mozilla/5.0"
        )

    result.append(url)

    return result


def update_playlist(
    original,
    tvz,
    iptv
):

    cleaned, removed = remove_vlc_lines(
        original
    )

    print(
        "Anciennes lignes EXT VLC supprimées :",
        removed
    )

    tvz_by_name, tvz_by_id = make_indexes(
        tvz
    )

    iptv_by_name, iptv_by_id = make_indexes(
        iptv
    )

    header, channels = read_playlist(
        cleaned
    )

    print(
        "Chaînes dans la playlist :",
        len(channels)
    )

    output = []

    output.extend(header)

    updated_custom = 0
    updated_tvz = 0
    updated_iptv = 0
    kept_old = 0

    tvz_bad = 0
    iptv_bad = 0

    for channel in channels:

        info = channel["info"]

        old_url = channel["url"]

        name = channel_name(
            info
        )

        name_key = normalize(
            name
        )

        print("")
        print(
            "Traitement :",
            name
        )

        # ====================================================
        # 1. URL PERSONNALISÉE
        # ====================================================

        if name_key in CUSTOM_URLS:

            custom_url = CUSTOM_URLS[
                name_key
            ]

            print(
                "  URL personnalisée : OUI"
            )

            # IMPORTANT :
            # On ne teste PAS l'URL Amagi.
            # Certains serveurs CDN refusent les requêtes
            # Python alors qu'ils fonctionnent parfaitement
            # dans un lecteur IPTV/VLC.

            output.extend(
                build_channel(
                    info,
                    custom_url,
                    False
                )
            )

            updated_custom += 1

            print(
                "  URL personnalisée conservée"
            )

            continue

        # ====================================================
        # 2. TVRADIOZAP
        # ====================================================

        match = find_match(
            info,
            name,
            tvz_by_name,
            tvz_by_id
        )

        if match:

            # Une correspondance personnalisée
            # aurait déjà été traitée ci-dessus.

            print(
                "  Correspondance TVRadioZap :",
                match["name"]
            )

            print(
                "  Test TVRadioZap..."
            )

            if test_stream(
                match["url"],
                True
            ):

                output.extend(
                    build_channel(
                        info,
                        match["url"],
                        True
                    )
                )

                updated_tvz += 1

                print(
                    "  TVRadioZap : OK"
                )

                continue

            tvz_bad += 1

            print(
                "  TVRadioZap : KO"
            )

        else:

            print(
                "  TVRadioZap : aucune correspondance sûre"
            )

        # ====================================================
        # 3. IPTV-ORG
        # ====================================================

        match = find_match(
            info,
            name,
            iptv_by_name,
            iptv_by_id
        )

        if match:

            print(
                "  Correspondance IPTV-org :",
                match["name"]
            )

            print(
                "  Test IPTV-org..."
            )

            if test_stream(
                match["url"],
                False
            ):

                output.extend(
                    build_channel(
                        info,
                        match["url"],
                        False
                    )
                )

                updated_iptv += 1

                print(
                    "  IPTV-org : OK"
                )

                continue

            iptv_bad += 1

            print(
                "  IPTV-org : KO"
            )

        else:

            print(
                "  IPTV-org : aucune correspondance sûre"
            )

        # ====================================================
        # 4. ANCIEN LIEN
        # ====================================================
        #
        # Si aucune correspondance certaine n'est trouvée,
        # on ne touche PAS à la chaîne.
        # ====================================================

        output.extend(
            build_channel(
                info,
                old_url,
                False
            )
        )

        kept_old += 1

        print(
            "  Ancien lien conservé"
        )

    result = (
        "\n".join(output)
        + "\n"
    )

    print("")
    print("=" * 60)
    print("RESULTAT")
    print("=" * 60)

    print(
        "URLs personnalisées :",
        updated_custom
    )

    print(
        "TVRadioZap mis à jour :",
        updated_tvz
    )

    print(
        "IPTV-org mis à jour   :",
        updated_iptv
    )

    print(
        "Ancien lien conservé  :",
        kept_old
    )

    print(
        "TVRadioZap KO         :",
        tvz_bad
    )

    print(
        "IPTV-org KO           :",
        iptv_bad
    )

    print(
        "EXTVLCOPT supprimées  :",
        removed
    )

    print("=" * 60)

    return result


def main():

    print("=" * 60)
    print("MISE A JOUR ASUS PLAYLIST")
    print("=" * 60)

    if not PLAYLIST.exists():

        raise SystemExit(
            "Fichier introuvable : "
            + str(PLAYLIST)
        )

    # ========================================================
    # TVRADIOZAP
    # ========================================================

    print("")
    print(
        "Téléchargement TVRadioZap..."
    )

    try:

        tvz_text = download(
            TVRADIOZAP_URL,
            TVZ_HEADERS
        )

        tvz = parse_m3u(
            tvz_text
        )

        print(
            "TVRadioZap :",
            len(tvz),
            "chaînes"
        )

    except Exception as exc:

        print(
            "TVRadioZap indisponible :",
            exc
        )

        tvz = []

    # ========================================================
    # IPTV-ORG
    # ========================================================

    print("")
    print(
        "Téléchargement IPTV-org..."
    )

    try:

        iptv_text = download(
            IPTVORG_URL,
            HEADERS
        )

        iptv = parse_m3u(
            iptv_text
        )

        print(
            "IPTV-org :",
            len(iptv),
            "chaînes"
        )

    except Exception as exc:

        print(
            "IPTV-org indisponible :",
            exc
        )

        iptv = []

    # ========================================================
    # PLAYLIST ACTUELLE
    # ========================================================

    original = PLAYLIST.read_text(
        encoding="utf-8",
        errors="replace"
    )

    # ========================================================
    # MISE À JOUR
    # ========================================================

    updated = update_playlist(
        original,
        tvz,
        iptv
    )

    # ========================================================
    # ÉCRITURE
    # ========================================================

    if updated != original:

        backup = Path(
            "ASUS-playlist_FR-AR.m3u.bak"
        )

        backup.write_text(
            original,
            encoding="utf-8"
        )

        PLAYLIST.write_text(
            updated,
            encoding="utf-8",
            newline="\n"
        )

        print("")
        print(
            "Playlist modifiée."
        )

        print(
            "Sauvegarde créée :",
            backup
        )

    else:

        print("")
        print(
            "Aucune modification nécessaire."
        )

    print("")
    print(
        "Terminé."
    )


if __name__ == "__main__":
    main()
