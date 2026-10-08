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

TIMEOUT_DOWNLOAD = 30
TIMEOUT_TEST = 8


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
            timeout=TIMEOUT_DOWNLOAD
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
# NORMALISATION DES NOMS
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

    # Supprimer les indications entre crochets
    text = re.sub(
        r"\[[^\]]*\]",
        "",
        text
    )

    # Supprimer les indications entre parenthèses
    text = re.sub(
        r"\([^)]*\)",
        "",
        text
    )

    # Retirer les qualités vidéo
    text = re.sub(
        r"\b(4k|uhd|fhd|hd|sd|1080p|720p|576p|480p)\b",
        "",
        text,
        flags=re.I
    )

    # Retirer quelques indications fréquentes
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


#
