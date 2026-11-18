import os
import subprocess
from datetime import datetime, timezone, timedelta

# On ne garde que la playlist principale dans le tableau
PLAYLISTS = [
    ("Playlist Principale (FR / AR)", "ASUS-playlist_FR-AR.m3u")
]

README_FILE = "README.md"

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

def get_recent_changes():
    """Extrait les noms des chaînes modifiées via git diff si disponible."""
    try:
        result = subprocess.run(
            ["git", "diff", "-U1", "*.m3u"],
            capture_output=True,
            text=True,
            encoding="utf-8"
        )
        if not result.stdout:
            return []
        
        changed_channels = []
        lines = result.stdout.splitlines()
        for line in lines:
            if line.startswith("-#EXTINF:") or line.startswith("+#EXTINF:"):
                parts = line.split(",")
                if len(parts) > 1:
                    channel_name = parts[-1].strip()
                    if channel_name not in changed_channels:
                        changed_channels.append(channel_name)
        return changed_channels[:15]
    except Exception:
        return []

def generate_readme():
    # Heure locale d'Algérie (UTC+1)
    tz_dz = timezone(timedelta(hours=1))
    now = datetime.now(tz_dz).strftime("%d/%m/%Y à %H:%M")

    changes = get_recent_changes()

    lines = [
        "# 📺 ASUS Playlist FR-AR (IPTV)",
        "",
        "Dépôt personnel de playlists IPTV maintenu et actualisé automatiquement.",
        "",
        f"🕒 **Dernière vérification automatique :** `{now} (UTC+1)`",
        "",
        "## 📋 État des listes",
        "",
        # Tableau épuré sans la colonne Accès
        "| Playlist | Fichier | Chaînes actives |",
        "| :--- | :--- | :---: |"
    ]

    for label, filename in PLAYLISTS:
        count = count_channels(filename)
        if count is not None:
            lines.append(f"| {label} | `{filename}` | **{count}** |")

    # Encadré des modifications récentes
    lines.extend([
        "",
        "## 🔄 Dernières chaînes actualisées",
        ""
    ])

    if changes:
        lines.append("> [!NOTE]")
        lines.append("> Les flux des chaînes suivantes ont été mis à jour lors de la dernière synchronisation :")
        lines.append(">")
        for ch in changes:
            lines.append(f"> - 🟢 `{ch}`")
    else:
        lines.append("> [!TIP]")
        lines.append("> Aucun changement de flux détecté lors de cette dernière vérification (toutes les URLs étaient déjà à jour).")

    lines.extend([
        "",
        "---",
        "*Les flux sont mis à jour toutes les 6 heures via GitHub Actions sans altérer l'ordre ni les groupes personnalisés.*"
    ])

    with open(README_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Succès : {README_FILE} mis à jour avec le design épuré le {now}.")

if __name__ == "__main__":
    generate_readme()
