import re
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urljoin


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

RADIO_ALGERIE_URL = (
    "https://radioalgerie.dz/player/fr/live-player"
)

DOWNLOAD_TIMEOUT = 30
STREAM_TIMEOUT = 8
STREAM_TEST_BYTES = 4096


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

RADIO_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 "
        "(KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Referer": "https://radioalgerie.dz/",
    "Accept": (
        "text/html,application/xhtml+xml,"
        "application/xml;q=0.9,*/*;q=0.8"
    ),
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

def download(url, headers=None, timeout=DOWNLOAD_TIMEOUT):

    if headers is None:
        headers = GENERIC_HEADERS

    request = Request(
        url,
        headers=headers
    )

    try:

        with urlopen(
            request,
            timeout=timeout
        ) as response:

            data = response.read()

            print(
                f"HTTP {response.status} - "
                f"{len(data)} octets"
            )

            return data

    except HTTPError as e:

        raise RuntimeError(
            f"Erreur HTTP {e.code} : {url}"
        ) from e

    except URLError as e:

        raise RuntimeError(
            f"Erreur réseau : {url}\n{e}"
        ) from e


def download_text(url, headers=None):

    data = download(
        url,
        headers
    )

    return data.decode(
        "utf-8",
        errors="replace"
    )


# ============================================================
# TEST D'UN FLUX
# ============================================================

def verify_stream(url, source="generic"):

    if not url:
        return False, "URL vide"

    if not url.startswith(
        ("http://", "https://")
    ):
        return False, "URL non HTTP"

    if source == "tvradiozap":
        headers = dict(TVZ_HEADERS)

    elif source == "radioalgerie":
        headers = dict(RADIO_HEADERS)

    else:
        headers = dict(GENERIC_HEADERS)

    headers["Range"] = (
        f"bytes=0-{STREAM_TEST_BYTES - 1}"
    )

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
                STREAM_TEST_BYTES
            )

            if status < 200 or status >= 400:
                return False, f"HTTP {status}"

            if not data:
                return False, "réponse vide"

            sample = data[:1000].lower()

            # ------------------------------------------------
            # Page HTML
            # ------------------------------------------------

            if (
                b"<html" in sample
                or b"<body" in sample
                or b"<!doctype html" in sample
            ):

                return False, "réponse HTML"

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

                    return True, f"OK HLS / HTTP {status}"

                if status in (200, 206):

                    return True, f"OK HLS / HTTP {status}"

                return False, "HLS invalide"

            # ------------------------------------------------
            # MPEG-TS
            # ------------------------------------------------

            if len(data) >= 188:

                for position in range(
                    min(188, len(data))
                ):

                    if data[position] == 0x47:

                        return (
                            True,
                            f"OK MPEG-TS / HTTP {status}"
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
                    f"OK audio / HTTP {status}"
                )

            # ------------------------------------------------
            # HTTP valide
            # ------------------------------------------------

            if status in (200, 206):

                return True, f"HTTP {status}"

            return False, f"HTTP {status}"

    except HTTPError as e:

        return False, f"HTTP {e.code}"

    except URLError as e:

        reason = getattr(
            e,
            "reason",
            "erreur réseau"
        )

        return False, f"erreur réseau: {reason}"

    except TimeoutError:

        return False, "timeout"

    except Exception as e:

        return False, type(e).__name__


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

    text = text.replace(
        "’",
        "'"
    )

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
        r"\b(fhd|uhd|hd|sd|4k|1080p|720p|576p|480p)\b",
        "",
        text,
        flags=re.I
    )

    text = re.sub(
        r"\b(live|direct|fr|fra|france)\b",
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
        r"^(fr|fra)[-_:.]",
        "",
        text
    )

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

    for line in text.splitlines():

        line = line.strip()

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
# INDEXATION
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
# RECHERCHE SOURCE
# ============================================================

def find_match(
    my_info,
    my_name,
    source_by_name,
    source_by_id
):

    # --------------------------------------------------------
    # TVG-ID
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
    # Nom exact
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
    # Nom partiel
    # --------------------------------------------------------

    candidates = []

    if name_key:

        for source_key, item in source_by_name.items():

            if len(name_key) < 4:
                continue

            if len(source_key) < 4:
                continue

            if (
                name_key in source_key
                or source_key in name_key
            ):

                candidates.append(
                    item
                )

    if len(candidates) == 1:

        return (
            candidates[0],
            "nom partiel"
        )

    if candidates:

        candidates.sort(
            key=lambda item:
            abs(
                len(
                    normalize(
                        item["name"]
                    )
                )
                -
                len(name_key)
            )
        )

        return (
            candidates[0],
            "nom partiel"
        )

    return None, None


# ============================================================
# RADIO ALGERIENNE
# ============================================================

def get_radio_algerie_pages():

    print()
    print(
        "Recherche des sources Radio Algérienne..."
    )

    try:

        html = download_text(
            RADIO_ALGERIE_URL,
            RADIO_HEADERS
        )

    except Exception as e:

        print(
            f"Radio Algérienne indisponible : {e}"
        )

        return []

    pattern = re.compile(
        r'href\s*=\s*["\']([^"\']+)["\']',
        re.I
    )

    links = pattern.findall(
        html
    )

    pages = []

    for link in links:

        if link.startswith("#"):
            continue

        absolute = urljoin(
            RADIO_ALGERIE_URL,
            link
        )

        if (
            "radioalgerie.dz" in absolute
            or "my.radioalgerie.dz" in absolute
        ):

            pages.append(
                absolute
            )

    return list(
        dict.fromkeys(pages)
    )


def extract_radio_streams(
    page_url,
    html
):

    candidates = []

    # --------------------------------------------------------
    # URLs dans la page
    # --------------------------------------------------------

    url_pattern = re.compile(
        r'https?://[^\s"\'<>]+',
        re.I
    )

    urls = url_pattern.findall(
        html
    )

    for url in urls:

        url = (
            url
            .replace("&amp;", "&")
            .rstrip("),;")
        )

        lower = url.lower()

        if "/podcast/" in lower:
            continue

        if (
            ".m3u8" in lower
            or ".mp3" in lower
            or ".aac" in lower
            or ".ogg" in lower
            or ".m3u" in lower
            or "stream" in lower
            or "live" in lower
        ):

            candidates.append(
                url
            )

    # --------------------------------------------------------
    # src / file / source
    # --------------------------------------------------------

    src_pattern = re.compile(
        r'(?:src|file|source)\s*=\s*["\']([^"\']+)["\']',
        re.I
    )

    for value in src_pattern.findall(
        html
    ):

        value = value.strip()

        if value.startswith(
            ("http://", "https://")
        ):

            if "/podcast/" not in value.lower():

                candidates.append(
                    value
                )

        else:

            absolute = urljoin(
                page_url,
                value
            )

            if "/podcast/" not in absolute.lower():

                candidates.append(
                    absolute
                )

    return list(
        dict.fromkeys(candidates)
    )


def build_radio_algerie_index():

    index = {}

    pages = get_radio_algerie_pages()

    print(
        f"Pages Radio Algérienne trouvées : "
        f"{len(pages)}"
    )

    for page_url in pages:

        try:

            html = download_text(
                page_url,
                RADIO_HEADERS
            )

        except Exception:

            continue

        streams = extract_radio_streams(
            page_url,
            html
        )

        if not streams:
            continue

        path = page_url.lower()

        name = ""

        if "chaine1" in path:
            name = "Chaine 1"

        elif "chaine2" in path:
            name = "Chaine 2"

        elif "chaine3" in path:
            name = "Chaine 3"

        elif "jilfm" in path:
            name = "Jil FM"

        elif "bahdja" in path:
            name = "Radio El Bahdja"

        elif "internationale" in path:
            name = "Radio Algérie Internationale"

        elif "culture" in path:
            name = "Radio Culture"

        elif "coran" in path:
            name = "Radio Coran"

        if not name:

            title_match = re.search(
                r"<title[^>]*>(.*?)</title>",
                html
