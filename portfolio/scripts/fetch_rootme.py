"""
fetch_rootme.py — Scrape les stats Root Me d'Arthur (Nomalow)
et génère data/rootme.json utilisé par la page certs.html.

Lancé automatiquement par .github/workflows/update-rootme.yml toutes les 6h.
"""

import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests
from bs4 import BeautifulSoup

# ─── CONFIG ────────────────────────────────────────────────────────────────────
USERNAME    = "Nomalow"
PROFILE_URL = f"https://www.root-me.org/{USERNAME}?lang=fr"
OUTPUT_FILE = Path("data/rootme.json")

# User-Agent qui passe l'anti-bot Anubis (qui bloque les UA "scraper" évidents)
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/120.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "fr-FR,fr;q=0.9,en;q=0.8",
}

# Domaines officiels Root Me (l'ordre est gardé pour l'affichage)
DOMAINS = [
    "App - Script", "App - Système", "Cracking", "Cryptanalyse",
    "Forensic",     "Programmation",  "Réaliste", "Réseau",
    "Stéganographie", "Web - Client",  "Web - Serveur",
]


# ─── SCRAPING ──────────────────────────────────────────────────────────────────
def fetch_profile() -> str:
    """Récupère le HTML de la page profil. Lève une exception si KO."""
    r = requests.get(PROFILE_URL, headers=HEADERS, timeout=20)
    r.raise_for_status()
    return r.text


def parse(html: str) -> dict:
    """
    Extrait :
      - points totaux
      - rang / classement
      - challenges validés
      - répartition par domaine (validés / total → %)
    """
    soup = BeautifulSoup(html, "html.parser")
    text = soup.get_text(" ", strip=True)

    data = {
        "username":   USERNAME,
        "profile_url": PROFILE_URL,
        "points":     None,
        "rank":       None,
        "challenges": None,
        "domains":    [],
        "updated_at": datetime.now(timezone.utc).isoformat(),
    }

    # Points : « 1 234 points » ou « 1234 points »
    m = re.search(r"(\d[\d\s]*)\s*points?", text, re.IGNORECASE)
    if m:
        data["points"] = int(re.sub(r"\s", "", m.group(1)))

    # Rang : « Place : 12 345 » (Root Me FR) ou « Position : 12345 »
    m = re.search(r"(?:Place|Position|Rang)\s*:?\s*(\d[\d\s]*)", text, re.IGNORECASE)
    if m:
        data["rank"] = int(re.sub(r"\s", "", m.group(1)))

    # Challenges validés
    m = re.search(r"(\d+)\s*challenges?\s*(?:valid[ée]s?|r[ée]ussis)", text, re.IGNORECASE)
    if m:
        data["challenges"] = int(m.group(1))

    # Domaines : « App - Script ... 12 / 80 »
    # On accepte un peu de bruit entre le nom et le ratio.
    for name in DOMAINS:
        pat = re.escape(name) + r".{0,200}?(\d+)\s*/\s*(\d+)"
        m = re.search(pat, text, re.IGNORECASE | re.DOTALL)
        if m:
            solved, total = int(m.group(1)), int(m.group(2))
            pct = round(solved / total * 100, 1) if total else 0
            data["domains"].append({
                "name":    name,
                "solved":  solved,
                "total":   total,
                "percent": pct,
            })
        else:
            # On garde l'entrée même si non trouvée, à 0 % — l'affichage reste cohérent
            data["domains"].append({
                "name": name, "solved": 0, "total": 0, "percent": 0,
            })

    return data


# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main() -> int:
    try:
        html = fetch_profile()
    except Exception as e:
        print(f"❌ Échec du fetch Root Me : {e}", file=sys.stderr)
        # On NE remplace PAS le fichier existant en cas d'échec : on garde l'ancien
        return 0  # exit 0 pour ne pas faire échouer le workflow

    data = parse(html)
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(data, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(f"✅ {OUTPUT_FILE} mis à jour : {data['points']} pts, "
          f"{data['challenges']} challenges, rang {data['rank']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
