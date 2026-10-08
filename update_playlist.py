import re
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ============================================================
# CONFIGURATION
# ============================================================

PLAYLIST = Path("ASUS-playlist_FR-AR.m3u")

TVRADIOZAP_URL = "https://tvradiozap.eu/live/x/vlc/d/tvzeu.m3u"

IPTVORG_URL = "https://iptv-org.github.io/iptv/index.m3u"

DOWNLOAD_TIMEOUT = 60
STREAM_TIMEOUT = 8


# ============================================================
# HEADERS
# ============================================================

TVZ_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://tvradiozap.eu/",
    "Accept": "*/*",
}

GENERIC_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "*/*",
}


# ============================================================
# TELECHARGEMENT
# ============================================================

def download(url, headers):

    request = Request(
        url,
        headers=headers
    )

    try:

        with urlopen(
            request,
            timeout=DOWNLOAD_TIMEOUT
        ) as response:

            return response.read().decode(
                "utf-8",
                errors="replace"
            )

    except (
        HTTPError,
        URLError
    ) as exc:

        raise RuntimeError(
            f"Erreur téléchargement : {url}\n{exc}"
        ) from exc


# ============================================================
# NORMALISATION DU NOM
# ============================================================

def normalize_name(text):

    if not text:
        return ""

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    text = text.lower()

    # Supprimer les informations entre crochets
    text = re.sub(
        r"\[[^\]]*\]",
        "",
        text
    )

    # Supprimer les informations entre parenthèses
    text = re.sub(
        r"\([^)]*\)",
        "",
        text
    )

    # Supprimer uniquement les indications techniques
    text = re.sub(
        r"\b("
        r"4k|uhd|fhd|hd|sd|"
        r"1080p|720p|576p|480p"
        r")\b",
        "",
        text,
        flags=re.I
    )

    # Supprimer espaces et caractères spéciaux
    text = re.sub(
        r"[^a-z0-9]+",
        "",
        text
    )

    return text


# ============================================================
# NORMALISATION TVG-ID
# ============================================================

def normalize_tvg_id(text):

    if not text:
        return ""

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        char
        for char in text
        if not unicodedata.combining(char)
    )

    text = text.lower().strip()

    return re.sub(
        r"[^a-z0-9]+",
        "",
        text
    )


# ============================================================
# EXTRAIRE LE NOM DE LA CHAINE
# ============================================================

def get_channel_name(extinf):

    if "," not in extinf:
        return ""

    return extinf.split(
        ",",
        1
    )[1].strip()


# ============================================================
# EXTRAIRE TVG-ID
# ============================================================

def get_tvg_id(extinf):

    match = re.search(
        r'tvg-id\s*=\s*"([^"]*)"',
        extinf,
        flags=re.I
    )

    if match:
        return match.group(1).strip()

    return ""


# ============================================================
# EXTRAIRE TVG-NAME
# ============================================================

def get_tvg_name(extinf):

    match = re.search(
        r'tvg-name\s*=\s*"([^"]*)"',
        extinf,
        flags=re.I
    )

    if match:
        return match.group(1).strip()

    return ""


# ============================================================
# PARSER UNE PLAYLIST M3U SOURCE
# ============================================================

def parse_source_playlist(text):

    channels = []

    current_info = None

    for raw_line in text.splitlines():

        line = raw_line.strip()

        if not line:
            continue

        if line.startswith("#EXTINF"):

            current_info = line

            continue

        if (
            current_info is not None
            and line
            and not line.startswith("#")
        ):

            name = get_channel_name(
                current_info
            )

            tvg_id = get_tvg_id(
                current_info
            )

            tvg_name = get_tvg_name(
                current_info
            )

            if name:

                channels.append({
                    "info": current_info,
                    "name": name,
                    "tvg_name": tvg_name,
                    "tvg_id": tvg_id,
                    "url": line
                })

            current_info = None

    return channels


# ============================================================
# CONSTRUIRE INDEX PAR TVG-ID ET PAR NOM
# ============================================================

def build_indexes(channels):

    by_id = {}
    by_name = {}

    for channel in channels:

        # ----------------------------------------------------
        # TVG-ID
        # ----------------------------------------------------

        tvg_id = normalize_tvg_id(
            channel["tvg_id"]
        )

        if tvg_id:

            if tvg_id not in by_id:

                by_id[tvg_id] = channel

        # ----------------------------------------------------
        # NOM
        # ----------------------------------------------------

        name = normalize_name(
            channel["name"]
        )

        if name:

            if name not in by_name:

                by_name[name] = channel

    return by_id, by_name


# ============================================================
# RECHERCHE STRICTE
# ============================================================

def find_source_channel(
    extinf,
    source_by_id,
    source_by_name
):

    # --------------------------------------------------------
    # 1. TVG-ID
    # --------------------------------------------------------

    source_tvg_id = normalize_tvg_id(
        get_tvg_id(extinf)
    )

    if source_tvg_id:

        if source_tvg_id in source_by_id:

            return source_by_id[
                source_tvg_id
            ]

    # --------------------------------------------------------
    # 2. TVG-NAME
    # --------------------------------------------------------

    source_tvg_name = get_tvg_name(
        extinf
    )

    if source_tvg_name:

        key = normalize_name(
            source_tvg_name
        )

        if key in source_by_name:

            return source_by_name[key]

    # --------------------------------------------------------
    # 3. NOM AFFICHE
    # --------------------------------------------------------

    displayed_name = get_channel_name(
        extinf
    )

    key = normalize_name(
        displayed_name
    )

    if key:

        if key in source_by_name:

            return source_by_name[key]

    # --------------------------------------------------------
    # AUCUNE CORRESPONDANCE
    # --------------------------------------------------------

    return None


# ============================================================
# TESTER UN FLUX
# ============================================================

def test_stream(
    url,
    tvradiozap=False
):

    if not url.startswith(
        (
            "http://",
            "https://"
        )
    ):

        return False

    if tvradiozap:

        headers = dict(
            TVZ_HEADERS
        )

    else:

        headers = dict(
            GENERIC_HEADERS
        )

    headers["Range"] = "bytes=0-4095"

    request = Request(
        url,
        headers=headers
    )

    try:

        with urlopen(
            request,
            timeout=STREAM_TIMEOUT
        ) as response:

            status = response.status

            if status < 200 or status >= 400:

                return False

            data = response.read(
                4096
            )

            if not data:

                return False

            content_type = (
                response.headers.get(
                    "Content-Type",
                    ""
                )
                .lower()
            )

            sample = data[:2000].lower()

            # ------------------------------------------------
            # PAGE HTML = PAS UN FLUX
            # ------------------------------------------------

            if (
                b"<html" in sample
                or b"<body" in sample
                or b"<!doctype html" in sample
            ):

                return False

            # ------------------------------------------------
            # HLS
            # ------------------------------------------------

            if (
                ".m3u8" in url.lower()
                or "mpegurl" in content_type
                or "application/vnd.apple.mpegurl"
                in content_type
            ):

                if (
                    b"#extm3u" in sample
                    or b"#ext-x-" in sample
                ):

                    return True

                return status in (
                    200,
                    206
                )

            # ------------------------------------------------
            # AUDIO
            # ------------------------------------------------

            if (
                "audio/" in content_type
                or "aac" in content_type
                or "mp3" in content_type
            ):

                return True

            # ------------------------------------------------
            # VIDEO
            # ------------------------------------------------

            if (
                "video/" in content_type
                or "octet-stream" in content_type
            ):

                return True

            return status in (
                200,
                206
            )

    except (
        HTTPError,
        URLError,
        TimeoutError,
        OSError
    ):

        return False


# ============================================================
# MISE A JOUR
# ============================================================

def update_playlist():

    if not PLAYLIST.exists():

        raise RuntimeError(
            f"Playlist introuvable : {PLAYLIST}"
        )

    print()
    print("================================================")
    print(" ASUS PLAYLIST - MISE A JOUR")
    print("================================================")
    print()

    # ========================================================
    # SOURCE 1 : TVRADIOZAP
    # ========================================================

    print(
        "[1/2] Chargement de TVRadioZap..."
    )

    try:

        tvz_text = download(
            TVRADIOZAP_URL,
            TVZ_HEADERS
        )

        tvz_channels = parse_source_playlist(
            tvz_text
        )

        tvz_by_id, tvz_by_name = (
            build_indexes(
                tvz_channels
            )
        )

        print(
            f"      {len(tvz_channels)} chaînes chargées."
        )

    except Exception as exc:

        print(
            f"      ERREUR TVRadioZap : {exc}"
        )

        tvz_by_id = {}
        tvz_by_name = {}

    print()

    # ========================================================
    # SOURCE 2 : IPTV-ORG
    # ========================================================

    print(
        "[2/2] Chargement de IPTV-org..."
    )

    try:

        iptv_text = download(
            IPTVORG_URL,
            GENERIC_HEADERS
        )

        iptv_channels = parse_source_playlist(
            iptv_text
        )

        iptv_by_id, iptv_by_name = (
            build_indexes(
                iptv_channels
            )
        )

        print(
            f"      {len(iptv_channels)} chaînes chargées."
        )

    except Exception as exc:

        print(
            f"      ERREUR IPTV-org : {exc}"
        )

        iptv_by_id = {}
        iptv_by_name = {}

    print()
    print(
        "Mise à jour sans modification de l'ordre..."
    )
    print()

    # ========================================================
    # LIRE LA PLAYLIST UTILISATEUR
    # ========================================================

    original_lines = PLAYLIST.read_text(
        encoding="utf-8"
    ).splitlines()

    output_lines = []

    current_info = None

    total = 0
    tvz_ok = 0
    iptv_ok = 0
    old_kept = 0
    not_found = 0

    # ========================================================
    # TRAITEMENT
    # ========================================================

    for line in original_lines:

        stripped = line.strip()

        # ----------------------------------------------------
        # EXTINF
        # ----------------------------------------------------

        if stripped.startswith(
            "#EXTINF"
        ):

            current_info = stripped

            # IMPORTANT :
            # On conserve exactement la position.
            output_lines.append(line)

            continue

        # ----------------------------------------------------
        # Lignes spéciales
        # ----------------------------------------------------

        if (
            current_info is not None
            and stripped.startswith("#")
        ):

            # #EXTVLCOPT etc.
            # On conserve exactement la ligne
            # et exactement sa position.

            output_lines.append(line)

            continue

        # ----------------------------------------------------
        # URL
        # ----------------------------------------------------

        if (
            current_info is not None
            and stripped
        ):

            total += 1

            old_url = line

            channel_name = get_channel_name(
                current_info
            )

            # =================================================
            # TVRADIOZAP
            # =================================================

            tvz_match = find_source_channel(
                current_info,
                tvz_by_id,
                tvz_by_name
            )

            if tvz_match is not None:

                candidate_url = (
                    tvz_match["url"]
                )

                print(
                    f"[TVZ] {channel_name}"
                )

                if test_stream(
                    candidate_url,
                    tvradiozap=True
                ):

                    # SEULEMENT L'URL CHANGE
                    output_lines.append(
                        candidate_url
                    )

                    tvz_ok += 1

                    print(
                        "      -> TVRadioZap OK"
                    )

                    current_info = None

                    continue

                print(
                    "      -> TVRadioZap indisponible"
                )

            # =================================================
            # IPTV-ORG
            # =================================================

            iptv_match = find_source_channel(
                current_info,
                iptv_by_id,
                iptv_by_name
            )

            if iptv_match is not None:

                candidate_url = (
                    iptv_match["url"]
                )

                print(
                    f"[IPTV-ORG] {channel_name}"
                )

                if test_stream(
                    candidate_url
                ):

                    # SEULEMENT L'URL CHANGE
                    output_lines.append(
                        candidate_url
                    )

                    iptv_ok += 1

                    print(
                        "      -> IPTV-org OK"
                    )

                    current_info = None

                    continue

                print(
                    "      -> IPTV-org indisponible"
                )

            # =================================================
            # GARDER L'ANCIENNE URL
            # =================================================

            output_lines.append(
                old_url
            )

            if (
                tvz_match is None
                and iptv_match is None
            ):

                not_found += 1

                print(
                    f"[CONSERVEE] {channel_name}"
                )

            else:

                old_kept += 1

                print(
                    f"[ANCIENNE URL] {channel_name}"
                )

            current_info = None

            continue

        # ----------------------------------------------------
        # Toute autre ligne
        # ----------------------------------------------------

        output_lines.append(line)

    # ========================================================
    # SAUVEGARDE
    # ========================================================

    PLAYLIST.write_text(
        "\n".join(output_lines) + "\n",
        encoding="utf-8"
    )

    # ========================================================
    # RAPPORT
    # ========================================================

    print()
    print("================================================")
    print(" MISE A JOUR TERMINEE")
    print("================================================")
    print()
    print(
        f"Chaînes analysées       : {total}"
    )
    print(
        f"TVRadioZap utilisées    : {tvz_ok}"
    )
    print(
        f"IPTV-org utilisées      : {iptv_ok}"
    )
    print(
        f"Anciennes URLs gardées : {old_kept}"
    )
    print(
        f"Sans correspondance     : {not_found}"
    )
    print()
    print(
        "ORDRE DE LA PLAYLIST : CONSERVE"
    )
    print(
        "METADONNEES            : CONSERVEES"
    )
    print()
    print(
        f"Fichier : {PLAYLIST}"
    )
    print()
    print("================================================")


# ============================================================
# PROGRAMME PRINCIPAL
# ============================================================

if __name__ == "__main__":

    try:

        update_playlist()

    except KeyboardInterrupt:

        print()
        print(
            "Mise à jour interrompue."
        )

    except Exception as exc:

        print()
        print(
            "ERREUR FATALE :"
        )
        print(
            exc
        )
        print()

        raise
