import re
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError


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


def download(url, headers):
    request = Request(url, headers=headers)

    try:
        with urlopen(request, timeout=DOWNLOAD_TIMEOUT) as response:
            return response.read().decode(
                "utf-8",
                errors="replace"
            )

    except (HTTPError, URLError) as exc:
        raise RuntimeError(
            f"Erreur téléchargement {url}: {exc}"
        ) from exc


def normalize(text):
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )

    text = text.lower()

    text = re.sub(r"\[[^\]]*\]", "", text)
    text = re.sub(r"\([^)]*\)", "", text)

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

    text = text.replace("&", "and")

    return re.sub(r"[^a-z0-9]+", "", text)


def normalize_id(text):
    if not text:
        return ""

    text = unicodedata.normalize("NFKD", text)

    text = "".join(
        c for c in text
        if not unicodedata.combining(c)
    )

    text = text.lower().strip()

    return re.sub(r"[-_.:]+", "", text)


def channel_name(extinf):
    if "," not in extinf:
        return ""

    return extinf.split(",", 1)[1].strip()


def extract_tvg_id(extinf):
    match = re.search(
        r'tvg-id\s*=\s*"([^"]*)"',
        extinf,
        flags=re.I
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
            name = channel_name(current_info)

            if name:
                channels.append({
                    "info": current_info,
                    "name": name,
                    "url": line
                })

            current_info = None

    return channels


def build_indexes(channels):
    by_name = {}
    by_id = {}

    for item in channels:
        name_key = normalize(item["name"])

        if name_key:
            by_name.setdefault(
                name_key,
                item
            )

        ident = normalize_id(
            extract_tvg_id(item["info"])
        )

        if ident:
            by_id.setdefault(
                ident,
                item
            )

    return by_name, by_id


def find_match(info, name, by_name, by_id):
    ident = normalize_id(
        extract_tvg_id(info)
    )

    if ident and ident in by_id:
        return by_id[ident]

    key = normalize(name)

    if key and key in by_name:
        return by_name[key]

    if len(key) < 4:
        return None

    candidates = []

    for source_key, item in by_name.items():
        if key in source_key or source_key in key:
            candidates.append(item)

    if not candidates:
        return None

    candidates.sort(
        key=lambda item: abs(
            len(normalize(item["name"])) - len(key)
        )
    )

    return candidates[0]


def test_stream(url, tvradiozap=False):
    if not url.startswith(("http://", "https://")):
        return False

    headers = dict(
        TVZ_HEADERS if tvradiozap else GENERIC_HEADERS
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

            content_type = response.headers.get(
                "Content-Type",
                ""
            ).lower()

            sample = data[:1000].lower()

            if (
                b"<html" in sample
                or b"<body" in sample
                or b"<!doctype html" in sample
            ):
                return False

            if (
                ".m3u8" in url.lower()
                or "mpegurl" in content_type
            ):
                if (
                    b"#extm3u" in sample
                    or b"#ext-x-" in sample
                ):
                    return True

                return response.status in (200, 206)

            if (
                "audio/" in content_type
                or "aac" in content_type
                or "mp3" in content_type
                or "mpeg" in content_type
