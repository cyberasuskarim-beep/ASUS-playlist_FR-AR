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

IPTVORG_URL = "https://iptv-org.github.io/iptv/index.m3u"

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
# TELECHARGER UNE SOURCE
# ============================================================

def download(url, headers):
    request = Request(url, headers=headers)

    try:
        with urlopen(
            request,
            timeout=DOWNLOAD_TIMEOUT
        ) as response:

            return response.read().decode(
                "utf-8",
                errors="replace"
            )

    except (HTTPError, URLError) as exc:
        raise RuntimeError(
            f"Impossible de télécharger {url}: {exc}"
        ) from exc


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


# ============================================================
# INFORMATIONS D'UNE CHAINE
# ============================================================

def channel_name(extinf):
    if "," not in extinf:
        return ""

    return extinf.split(
        ",",
        1
    )[1].strip()


def tvg_id(extinf):
    match = re.search(
        r'tvg-id\s*=\s*"([^"]*)"',
        extinf,
        flags=re.I
    )

    if match:
        return match.group(1).strip()

    return ""


# ============================================================
# PARSER UNE SOURCE M3U
# ============================================================

def parse_m3u(text):
    result = []
    current = None

    for raw in text.splitlines():

        line = raw.strip()

        if not line:
            continue

        if line.startswith("#EXTINF"):
            current = line
            continue

        if (
            current
            and line
            and not line.startswith("#")
        ):

            name = channel_name(current)

            if name:
                result.append({
                    "info": current,
                    "name": name,
                    "url": line
                })

            current = None

    return result


# ============================================================
# INDEXER UNE SOURCE
# ============================================================

def make_indexes(channels):

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

        ident = normalize_id(
            tvg_id(item["info"])
        )

        if ident:
            by_id.setdefault(
                ident,
                item
            )

    return by_name, by_id


# ============================================================
# TROUVER UNE CHAINE
# ============================================================

def find_match(
    info,
    name,
    by_name,
    by_id
):

    # --------------------------------------------------------
    # TVG-ID
    # --------------------------------------------------------

    ident = normalize_id(
        tvg_id(info)
    )

    if ident and ident in by_id:
        return by_id[ident]

    # --------------------------------------------------------
    # Nom exact
    # --------------------------------------------------------

    key = normalize(name)

    if key in by_name:
        return by_name[key]

    # --------------------------------------------------------
    # Nom partiel
    # --------------------------------------------------------

    if len(key) < 4:
        return None

    candidates = []

    for source_key, item in by_name.items():

        if (
            key in source_key
            or source_key in key
        ):
            candidates.append(item)

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: abs(
            len(normalize(item["name"]))
            - len(key)
        )
    )

    return candidates[0]


# ============================================================
# VERIFIER UN FLUX
# ============================================================

def test_stream(url, tvradiozap=False):

    if not url.startswith(
        ("http://", "https://")
    ):
        return False

    headers = dict(
        TVZ_HEADERS if tvradiozap
        else GENERIC_HEADERS
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

            if response.status < 200:
                return False

            if response.status >= 400:
                return False

            data = response.read(4096)

            if not data:
                return False

            content_type = (
                response.headers.get(
                    "Content-Type",
                    ""
                ).lower()
            )

            sample = data[:1000].lower()

            # Page HTML = pas un flux
            if (
                b"<html" in sample
                or b"<body" in sample
                or b"<!doctype html" in sample
            ):
                return False

            # HLS
            if (
                ".m3u8" in url.lower()
                or "mpegurl" in content_type
            ):
                if (
                    b"#extm3u" in sample
                    or b"#ext-x-" in sample
                ):
                    return True

                # Certains serveurs HLS répondent
                # correctement mais ne donnent pas
                # le contenu attendu avec Range.
                return response.status in (200, 206)

            # Audio
            if (
                "audio/" in content_type
                or "aac" in content_type
                or "mp3" in content_type
                or "mpeg" in content_type
                or "ogg" in content_type
            ):
                return True

            # MPEG-TS
            if len(data) >= 188:

                for pos in range(
                    min(188, len(data))
                ):
                    if data[pos] == 0x47:
                        return True

            return response.status in (200, 206)

    except Exception:
        return False


# ============================================================
# SUPPRIMER TOUTES LES EXT VLC
# ============================================================

def remove_vlc_options(text):

    output = []
    removed = 0

    for line in text.splitlines():

        value = line.strip().lower()

        if (
            value.startswith("#extvlcopt:")
            or value.startswith("#vlcopt:")
        ):
            removed += 1
            continue

        output.append(line)

    return (
        "\n".join(output) + "\n",
        removed
    )


# ============================================================
# LIRE LA PLAYLIST
# ============================================================

def parse_playlist(text):

    lines = text.splitlines()

    header = []
    channels = []

    current_info = None

    for line in lines:

        stripped = line.strip()

        if stripped.startswith("#EXTINF"):

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

    return header, channels


# ============================================================
# CONSTRUIRE UN BLOC DE CHAINE
# ============================================================

def build_channel(
    info,
    url,
    use_tvradiozap=False
):

    result = [info]

    # IMPORTANT :
    # maximum UNE seule paire EXT VLC.

    if use_tvradiozap:

        result.append(
            "#EXTVLCOPT:http-referrer="
            "https://tvradiozap.eu/"
        )

        result.append(
            "#EXTVLCOPT:http-user-agent="
            "Mozilla/5.0"
        )

    result.append(url)

    return result


# ============================================================
# MISE A JOUR
# ============================================================

def update_playlist(original, tvz, iptv):

    # --------------------------------------------------------
    # ETAPE 1
    # Supprimer absolument toutes les anciennes EXT VLC.
