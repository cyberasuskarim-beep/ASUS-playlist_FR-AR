import re
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


# ============================================================
# CONFIGURATION
# ============================================================

PLAYLIST = Path("ASUS-playlist_FR-AR.m3u")

TVRADIOZAP_URL = (
    "https://tvradiozap.eu/get.php"
    "?username=f:1$ty:tv"
    "&password=public"
    "&type=m3u_plus"
)

IPTVORG_URL = (
    "https://iptv-org.github.io/iptv/index.m3u"
)

DOWNLOAD_TIMEOUT = 30
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

def download_text(url, headers=None):

    if headers is None:
        headers = GENERIC_HEADERS

    request = Request(
        url,
        headers=headers
    )

    try:

        with urlopen(
            request,
            timeout=DOWNLOAD_TIMEOUT
        ) as response:

            data = response.read()

            print(
                f"HTTP {response.status} - "
                f"{len(data)} octets"
            )

            return data.decode(
                "utf-8",
                errors="replace"
            )

    except HTTPError as e:

        raise RuntimeError(
            f"Erreur HTTP {e.code}: {url}"
        ) from e

    except URLError as e:

        raise RuntimeError(
            f"Erreur réseau: {url} - {e}"
        ) from e


# ============================================================
# NORMALISATION
# ============================================================

def normalize(text):

    if not text:
        return ""

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        c
        for c in text
        if not unicodedata.combining(c)
    )

    text = text.lower()

    # Supprimer [France], [HD], etc.
    text = re.sub(
        r"\[[^\]]*\]",
        "",
        text
    )

    # Supprimer (1080p), (HD), etc.
    text = re.sub(
        r"\([^)]*\)",
        "",
        text
    )

    # Qualités vidéo
    text = re.sub(
        r"\b("
        r"4k|uhd|fhd|hd|sd|"
        r"1080p|720p|576p|480p"
        r")\b",
        "",
        text,
        flags=re.I
    )

    # Indications fréquentes
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

    text = re.sub(
        r"[^a-z0-9]+",
        "",
        text
    )

    return text


def normalize_id(text):

    if not text:
        return ""

    text = unicodedata.normalize(
        "NFKD",
        text
    )

    text = "".join(
        c
        for c in text
        if not unicodedata.combining(c)
    )

    text = text.lower().strip()

    text = re.sub(
        r"[-_.:]+",
        "",
        text
    )

    return text


# ============================================================
# M3U
# ============================================================

def channel_name(extinf):

    if "," not in extinf:
        return ""

    return extinf.split(
        ",",
        1
    )[1].strip()


def extract_tvg_id(extinf):

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

    for raw_line in text.splitlines():

        line = raw_line.strip()

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
                    "name": name,
                    "info": current_info,
                    "url": line
                })

            current_info = None

    return channels


# ============================================================
# INDEX SOURCES
# ============================================================

def build_indexes(channels):

    by_name = {}
    by_id = {}

    for item in channels:

        name_key = normalize(
            item["name"]
        )

        if name_key:

            by_name.setdefault(
                name_key,
                item
            )

        tvg_id = extract_tvg_id(
            item["info"]
        )

        id_key = normalize_id(
            tvg_id
        )

        if id_key:

            by_id.setdefault(
                id_key,
                item
            )

    return by_name, by_id


# ============================================================
# RECHERCHE CORRESPONDANCE
# ============================================================

def find_match(
    my_info,
    my_name,
    source_by_name,
    source_by_id
):

    # --------------------------------------------------------
    # 1. TVG-ID
    # --------------------------------------------------------

    my_tvg_id = extract_tvg_id(
        my_info
    )

    if my_tvg_id:

        key = normalize_id(
            my_tvg_id
        )

        if key in source_by_id:

            return (
                source_by_id[key],
                "tvg-id"
            )

    # --------------------------------------------------------
    # 2. Nom exact
    # --------------------------------------------------------

    name_key = normalize(
        my_name
    )

    if name_key in source_by_name:

        return (
            source_by_name[name_key],
            "nom exact"
        )

    # --------------------------------------------------------
    # 3. Nom partiel
    # --------------------------------------------------------

    if len(name_key) < 4:
        return None, None

    candidates = []

    for source_key, item in source_by_name.items():

        if len(source_key) < 4:
            continue

        if (
            name_key in source_key
            or source_key in name_key
        ):

            candidates.append(
                item
            )

    if not candidates:
        return None, None

    candidates.sort(
        key=lambda item: abs(
            len(
                normalize(
                    item["name"]
                )
            )
            - len(name_key)
        )
    )

    return (
        candidates[0],
        "nom partiel"
    )


# ============================================================
# TEST DU FLUX
# ============================================================

def test_stream(
    url,
    source="generic"
):

    if not url:
        return False, "URL vide"

    if not url.startswith(
        ("http://", "https://")
    ):
        return False, "URL non HTTP"

    if source == "tvradiozap":

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

            content_type = (
                response.headers.get(
                    "Content-Type",
                    ""
                )
                .lower()
            )

            data = response.read(
                4096
            )

            if status < 200 or status >= 400:

                return (
                    False,
                    f"HTTP {status}"
                )

            if not data:

                return (
                    False,
                    "réponse vide"
                )

            sample = data[:1000].lower()

            # ------------------------------------------------
            # Page HTML
            # ------------------------------------------------

            if (
                b"<html" in sample
                or b"<body" in sample
                or b"<!doctype html" in sample
            ):

                return (
                    False,
                    "réponse HTML"
                )

            # ------------------------------------------------
            # HLS
            # ------------------------------------------------

            if (
                ".m3u8" in url.lower()
                or "mpegurl" in content_type
                or "vnd.apple.mpegurl" in content_type
            ):

                if (
                    b"#extm3u" in sample
                    or b"#ext-x-" in sample
                ):

                    return (
                        True,
                        "HLS valide"
                    )

                if status in (200, 206):

                    return (
                        True,
                        f"HLS HTTP {status}"
                    )

                return (
                    False,
                    "HLS invalide"
                )

            # ------------------------------------------------
            # MPEG-TS
            # ------------------------------------------------

            if len(data) >= 188:

                for pos in range(
                    min(188, len(data))
                ):

                    if data[pos] == 0x47:

                        return (
                            True,
                            "MPEG-TS valide"
                        )

            # ------------------------------------------------
            # Audio
            # ------------------------------------------------

            if (
                "audio/" in content_type
                or "mpeg" in content_type
                or "aac" in content_type
                or "mp3" in content_type
                or "ogg" in content_type
            ):

                return (
                    True,
                    f"audio HTTP {status}"
                )

            # ------------------------------------------------
            # HTTP valide
            # ------------------------------------------------

            if status in (200, 206):

                return (
                    True,
                    f"HTTP {status}"
                )

            return (
                False,
                f"HTTP {status}"
            )

    except HTTPError as e:

        return (
            False,
            f
