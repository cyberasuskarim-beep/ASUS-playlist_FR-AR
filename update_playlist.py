import re
import unicodedata
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError

# ============================================================

# CONFIGURATION

# ============================================================

PLAYLIST = Path("ASUS-playlist_FR-AR.m3u")

# ------------------------------------------------------------

# SOURCE PRIORITAIRE : TVRadioZap

# ------------------------------------------------------------

TVRADIOZAP_URL = (
"https://tvradiozap.eu/live/x/vlc/d/tvzeu.m3u"
)

# ------------------------------------------------------------

# SOURCE SECONDAIRE : IPTV-org

# ------------------------------------------------------------

IPTVORG_URL = (
"https://iptv-org.github.io/iptv/index.m3u"
)

# Temps maximum pour télécharger les playlists sources

DOWNLOAD_TIMEOUT = 60

# Temps maximum pour tester un flux

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

```
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

except (HTTPError, URLError) as exc:

    raise RuntimeError(
        f"Erreur téléchargement : {url}\n{exc}"
    ) from exc
```

# ============================================================

# NORMALISATION DES NOMS

# ============================================================

def normalize(text):

```
if not text:
    return ""

# Suppression des accents
text = unicodedata.normalize(
    "NFKD",
    text
)

text = "".join(
    c for c in text
    if not unicodedata.combining(c)
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

# Supprimer les qualités vidéo
text = re.sub(
    r"\b("
    r"4k|uhd|fhd|hd|sd|"
    r"1080p|720p|576p|480p"
    r")\b",
    "",
    text,
    flags=re.I
)

# Supprimer quelques termes génériques
text = re.sub(
    r"\b("
    r"live|direct|fr|fra"
    r")\b",
    "",
    text,
    flags=re.I
)

text = text.replace(
    "&",
    "and"
)

# Garder uniquement lettres et chiffres
return re.sub(
    r"[^a-z0-9]+",
    "",
    text
)
```

# ============================================================

# NORMALISATION TVG-ID

# ============================================================

def normalize_id(text):

```
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
```

# ============================================================

# NOM DE LA CHAINE

# ============================================================

def channel_name(extinf):

```
if "," not in extinf:
    return ""

return extinf.split(
    ",",
    1
)[1].strip()
```

# ============================================================

# EXTRAIRE TVG-ID

# ============================================================

def extract_tvg_id(extinf):

```
match = re.search(
    r'tvg-id\s*=\s*"([^"]*)"',
    extinf,
    flags=re.I
)

if match:
    return match.group(1).strip()

return ""
```

# ============================================================

# ANALYSER UNE PLAYLIST M3U

# ============================================================

def parse_m3u(text):

```
channels = []

current_info = None

for raw_line in text.splitlines():

    line = raw_line.strip()

    if not line:
        continue

    # ----------------------------------------------------
    # EXTINF
    # ----------------------------------------------------

    if line.startswith("#EXTINF"):

        current_info = line
        continue

    # ----------------------------------------------------
    # URL
    # ----------------------------------------------------

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
```

# ============================================================

# CONSTRUIRE LES INDEX

# ============================================================

def build_indexes(channels):

```
by_name = {}
by_id = {}

for item in channels:

    # ----------------------------------------------------
    # Index par nom
    # ----------------------------------------------------

    name_key = normalize(
        item["name"]
    )

    if name_key:

        by_name.setdefault(
            name_key,
            item
        )

    # ----------------------------------------------------
    # Index par tvg-id
    # ----------------------------------------------------

    ident = normalize_id(
        extract_tvg_id(
            item["info"]
        )
    )

    if ident:

        by_id.setdefault(
            ident,
            item
        )

return by_name, by_id
```

# ============================================================

# RECHERCHER UNE CHAINE

# ============================================================

def find_match(
info,
name,
by_name,
by_id
):

```
# --------------------------------------------------------
# 1. RECHERCHE PAR TVG-ID
# --------------------------------------------------------

ident = normalize_id(
    extract_tvg_id(info)
)

if ident:

    if ident in by_id:

        return by_id[ident]

# --------------------------------------------------------
# 2. RECHERCHE EXACTE PAR NOM
# --------------------------------------------------------

key = normalize(name)

if key:

    if key in by_name:

        return by_name[key]

# --------------------------------------------------------
# 3. RECHERCHE PARTIELLE
# --------------------------------------------------------

if len(key) < 4:
    return None

candidates = []

for source_key, item in by_name.items():

    if (
        key in source_key
        or source_key in key
    ):

        candidates.append(
            (
                abs(
                    len(source_key)
                    - len(key)
                ),
                item
            )
        )

if not candidates:
    return None

candidates.sort(
    key=lambda x: x[0]
)

return candidates[0][1]
```

# ============================================================

# TESTER UN FLUX

# ============================================================

def test_stream(
url,
tvradiozap=False
):

```
if not url.startswith(
    (
        "http://",
        "https://"
    )
):

    return False

# --------------------------------------------------------
# Headers
# --------------------------------------------------------

if tvradiozap:

    headers = dict(
        TVZ_HEADERS
    )

else:

    headers = dict(
        GENERIC_HEADERS
    )

# Demander les premiers octets
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

        # ------------------------------------------------
        # Vérification HTTP
        # ------------------------------------------------

        if status < 200:
            return False

        if status >= 400:
            return False

        # ------------------------------------------------
        # Lire un petit morceau
        # ------------------------------------------------

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

        sample = data[
            :2000
        ].lower()

        # ------------------------------------------------
        # Refuser les pages HTML
        # ------------------------------------------------

        if (
            b"<html" in sample
            or b"<body" in sample
            or b"<!doctype html" in sample
        ):

            return False

        # ------------------------------------------------
        # M3U8 / HLS
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

            # Certains serveurs HLS
            # ne renvoient pas correctement
            # le Content-Type.
            return status in (
                200,
                206
            )

        # ------------------------------------------------
        # Flux audio
        # ------------------------------------------------

        if (
            "audio/" in content_type
            or "aac" in content_type
            or "mp3" in content_type
            or "mpeg" in content_type
        ):

            return True

        # ------------------------------------------------
        # Flux vidéo
        # ------------------------------------------------

        if (
            "video/" in content_type
            or "mpeg" in content_type
            or "octet-stream" in content_type
        ):

            return True

        # ------------------------------------------------
        # Cas général
        # ------------------------------------------------

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
```

# ============================================================

# MISE A JOUR

# ============================================================

def update_playlist():

```
# --------------------------------------------------------
# Vérifier la playlist locale
# --------------------------------------------------------

if not PLAYLIST.exists():

    raise RuntimeError(
        f"Playlist introuvable : {PLAYLIST}"
    )

print()
print(
    "================================================"
)
print(
    " ASUS PLAYLIST - MISE A JOUR"
)
print(
    "================================================"
)
print()

# ========================================================
# 1. TELECHARGER TVRADIOZAP
# ========================================================

print(
    "[1/2] Téléchargement TVRadioZap..."
)

try:

    tvz_text = download(
        TVRADIOZAP_URL,
        TVZ_HEADERS
    )

    tvz_channels = parse_m3u(
        tvz_text
    )

    tvz_by_name, tvz_by_id = (
        build_indexes(
            tvz_channels
        )
    )

    print(
        f"      {len(tvz_channels)} chaînes trouvées."
    )

except Exception as exc:

    print(
        "      ERREUR TVRadioZap :"
    )

    print(
        f"      {exc}"
    )

    tvz_by_name = {}
    tvz_by_id = {}

print()

# ========================================================
# 2. TELECHARGER IPTV-ORG
# ========================================================

print(
    "[2/2] Téléchargement IPTV-org..."
)

try:

    iptvorg_text = download(
        IPTVORG_URL,
        GENERIC_HEADERS
    )

    iptvorg_channels = parse_m3u(
        iptvorg_text
    )

    iptvorg_by_name, iptvorg_by_id = (
        build_indexes(
            iptvorg_channels
        )
    )

    print(
        f"      {len(iptvorg_channels)} chaînes trouvées."
    )

except Exception as exc:

    print(
        "      ERREUR IPTV-org :"
    )

    print(
        f"      {exc}"
    )

    iptvorg_by_name = {}
    iptvorg_by_id = {}

print()
print(
    "Analyse de ta playlist..."
)
print()

# ========================================================
# LIRE LA PLAYLIST ORIGINALE
# ========================================================

original_lines = PLAYLIST.read_text(
    encoding="utf-8"
).splitlines()

output_lines = []

current_info = None

# Compteurs
total = 0
tvz_found = 0
tvz_working = 0
iptvorg_found = 0
iptvorg_working = 0
old_kept = 0
no_match = 0

# ========================================================
# TRAITEMENT LIGNE PAR LIGNE
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

        output_lines.append(
            line
        )

        continue

    # ----------------------------------------------------
    # URL après EXTINF
    # ----------------------------------------------------

    if (
        current_info
        and stripped
        and not stripped.startswith("#")
    ):

        name = channel_name(
            current_info
        )

        if not name:

            output_lines.append(
                line
            )

            current_info = None

            continue

        total += 1

        old_url = stripped

        # =================================================
        # PRIORITE 1 : TVRADIOZAP
        # =================================================

        tvz_match = find_match(
            current_info,
            name,
            tvz_by_name,
            tvz_by_id
        )

        if tvz_match:

            tvz_found += 1

            candidate_url = (
                tvz_match["url"]
            )

            print(
                f"[TVZ] Test : {name}"
            )

            if test_stream(
                candidate_url,
                tvradiozap=True
            ):

                output_lines.append(
                    candidate_url
                )

                tvz_working += 1

                print(
                    f"      OK -> {candidate_url}"
                )

                current_info = None

                continue

            else:

                print(
                    "      Flux TVZ non valide."
                )

        # =================================================
        # PRIORITE 2 : IPTV-ORG
        # =================================================

        iptv_match = find_match(
            current_info,
            name,
            iptvorg_by_name,
            iptvorg_by_id
        )

        if iptv_match:

            iptvorg_found += 1

            candidate_url = (
                iptv_match["url"]
            )

            print(
                f"[IPTV-ORG] Test : {name}"
            )

            if test_stream(
                candidate_url,
                tvradiozap=False
            ):

                output_lines.append(
                    candidate_url
                )

                iptvorg_working += 1

                print(
                    f"      OK -> {candidate_url}"
                )

                current_info = None

                continue

            else:

                print(
                    "      Flux IPTV-org non valide."
                )

        # =================================================
        # PRIORITE 3 : ANCIENNE URL
        # =================================================

        output_lines.append(
            old_url
        )

        if (
            tvz_match is None
            and iptv_match is None
        ):

            no_match += 1

            print(
                f"[AUCUNE SOURCE] {name}"
            )

        else:

            old_kept += 1

            print(
                f"[ANCIEN LIEN] {name}"
            )

        current_info = None

        continue

    # ----------------------------------------------------
    # Autres lignes
    # ----------------------------------------------------

    output_lines.append(
        line
    )

# ========================================================
# SAUVEGARDER
# ========================================================

PLAYLIST.write_text(
    "\n".join(
        output_lines
    ) + "\n",
    encoding="utf-8"
)

# ========================================================
# RAPPORT FINAL
# ========================================================

print()
print(
    "================================================"
)
print(
    " MISE A JOUR TERMINEE"
)
print(
    "================================================"
)
print()

print(
    f"Chaînes analysées       : {total}"
)

print(
    f"TVRadioZap trouvées     : {tvz_found}"
)

print(
    f"TVRadioZap fonctionnelles: {tvz_working}"
)

print(
    f"IPTV-org trouvées       : {iptvorg_found}"
)

print(
    f"IPTV-org fonctionnelles : {iptvorg_working}"
)

print(
    f"Anciennes URLs gardées  : {old_kept}"
)

print(
    f"Aucune correspondance   : {no_match}"
)

print()
print(
    f"Playlist mise à jour : {PLAYLIST}"
)

print()
print(
    "================================================"
)
```

# ============================================================

# PROGRAMME PRINCIPAL

# ============================================================

if **name** == "**main**":

```
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
```
