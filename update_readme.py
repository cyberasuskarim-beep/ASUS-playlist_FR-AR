import os
from datetime import datetime, timezone, timedelta

# Liste de vos fichiers M3U à analyser
PLAYLISTS = [
    ("Playlist Principale (FR / AR)", "ASUS-playlist_FR-AR.m3u"),
    ("Source IPTV-org", "iptv-org.m3u"),
    ("Source TVRadioZap", "tvradiozap.m3u")
]

README_FILE = "README.md"
REPO_RAW_BASE = "https://raw.githubusercontent.com/cyberasuskarim-beep/ASUS-playlist_FR-AR/refs/heads/main"

def count_channels(filepath):
    """Compte le nombre de balises #EXTINF dans un fichier M3U."""
    if not os.path.exists(filepath):
        return None
    count = 0
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip().startswith("#EXTINF:"):
                count += 1
    return count

def generate_readme():
    # Heure locale d'Algérie (UTC+1)
    tz_dz = timezone(timedelta(hours=1))
    now = datetime.now(tz_dz).strftime("%d/%m/%Y à %H:%M")

    lines = [
        "# 📺 ASUS Playlist FR-AR (IPTV)",
        "",
        "Dépôt personnel de playlists IPTV maintenu et actualisé automatiquement.",
        "",
        f"🕒 **Dernière vérification automatique :** `{now} (UTC+1)`",
        "",
        "## 📋 État des listes",
        "",
        "| Playlist | Fichier | Chaînes actives | Lien direct (Raw) |",
        "| :--- | :--- | :---: | :--- |"
    ]

    for label, filename in PLAYLISTS:
        count = count_channels(filename)
        if count is not None:
            raw_url = f"{REPO_RAW_BASE}/{filename}"
            lines.append(f"| {label} | `{filename}` | **{count}** | [Copier le lien]({raw_url}) |")

    lines.extend([
        "",
        "---",
        "*Les flux sont mis à jour toutes les 6 heures via GitHub Actions sans altérer l'ordre ni les groupes personnalisés.*"
    ])

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Succès : {README_FILE} mis à jour le {now}.")

if __name__ == "__main__":
    generate_readme()
