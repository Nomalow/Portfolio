"""
fetch_rootme.py — Récupère les stats Root Me d'Arthur (Nomalow)
via l'API officielle Root Me et génère portfolio/data/rootme.json.

L'API key est passée via la variable d'environnement ROOTME_API_KEY
(stockée dans les secrets GitHub Actions, jamais dans le code).

Documentation API : https://api.www.root-me.org/
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

# ─── CONFIG ────────────────────────────────────────────────────────────────────
USERNAME      = "Nomalow"
API_BASE      = "https://api.www.root-me.org"
OUTPUT_FILE   = Path("data/rootme.json")
TIMEOUT       = 20

API_KEY = os.environ.get("ROOTME_API_KEY")
if not API_KEY:
    print("❌ La variable d'env ROOTME_API_KEY n'est pas définie.", file=sys.stderr)
    sys.exit(1)

# L'API Root Me s'authentifie via un cookie nommé "api_key"
COOKIES = {"api_key": API_KEY}
HEADERS = {
    "User-Agent": "Nomalow-Portfolio/1.0 (+https://github.com/Nomalow/Portfolio)",
    "Accept": "application/json",
}


# ─── HELPERS ───────────────────────────────────────────────────────────────────
def api_get(path: str, **params):
    """GET sur l'API Root Me. Retourne le JSON ou None en cas d'échec."""
    url = f"{API_BASE}{path}"
    try:
        r = requests.get(url, cookies=COOKIES, headers=HEADERS,
                         params=params, timeout=TIMEOUT)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"⚠️  GET {path} : {e}", file=sys.stderr)
        return None


def find_user_id(username: str):
    """Cherche l'id de l'auteur correspondant au pseudo."""
    data = api_get("/auteurs", nom=username)
    if not data:
        return None
    # L'API renvoie une liste paginée. On prend la correspondance exacte.
    if isinstance(data, list) and data:
        page = data[0] if isinstance(data[0], dict) else {}
        for _, user in page.items():
            if isinstance(user, dict) and str(user.get("nom", "")).lower() == username.lower():
                return int(user["id_auteur"])
    return None


def fetch_user_details(user_id: int):
    """Récupère le détail d'un auteur (points, position, validations)."""
    return api_get(f"/auteurs/{user_id}")


# ─── PARSING ───────────────────────────────────────────────────────────────────
# Domaines officiels Root Me — on les liste pour garantir un ordre stable
DOMAINS = [
    "App - Script", "App - Système", "Cracking", "Cryptanalyse",
    "Forensic",     "Programmation",  "Réaliste", "Réseau",
    "Stéganographie", "Web - Client",  "Web - Serveur",
]


def fetch_total_per_domain():
    """
    Récupère le nombre TOTAL de challenges par domaine
    en interrogeant /challenges?rubrique=<domaine>.
    """
    totals = {}
    for domain in DOMAINS:
        count = 0
        page = 0
        while True:
            data = api_get("/challenges", rubrique=domain, debut_challenges=page * 50)
            if not data or not isinstance(data, list) or not data:
                break
            entries = data[0] if isinstance(data[0], dict) else {}
            chunk = sum(1 for k in entries if k.isdigit())
            count += chunk
            if chunk < 50:
                break
            page += 1
            if page > 20:  # garde-fou
                break
        totals[domain] = count
        print(f"  • {domain} : {count} challenges au total")
    return totals


def build_payload(user: dict, totals: dict) -> dict:
    """Assemble le JSON final consommé par certs.js."""
    solved_per_domain = {d: 0 for d in DOMAINS}
    validations = user.get("validations", []) or []

    for v in validations:
        rubrique = v.get("rubrique") or ""
        for d in DOMAINS:
            if rubrique.replace(" ", "").lower() == d.replace(" ", "").lower():
                solved_per_domain[d] += 1
                break

    domains_payload = []
    for d in DOMAINS:
        solved = solved_per_domain[d]
        total  = totals.get(d, 0)
        pct    = round(solved / total * 100, 1) if total else 0
        domains_payload.append({
            "name":    d,
            "solved":  solved,
            "total":   total,
            "percent": pct,
        })

    points = user.get("score") or user.get("points") or None
    if points is not None:
        points = int(points)

    rank = user.get("position") or user.get("place") or None
    if rank is not None:
        rank = int(rank)

    return {
        "username":    USERNAME,
        "profile_url": f"https://www.root-me.org/{USERNAME}?lang=fr",
        "points":      points,
        "rank":        rank,
        "challenges":  len(validations),
        "domains":     domains_payload,
        "updated_at":  datetime.now(timezone.utc).isoformat(),
    }


# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main() -> int:
    print(f"🔍 Recherche de l'utilisateur {USERNAME}…")
    user_id = find_user_id(USERNAME)
    if not user_id:
        print("❌ Utilisateur introuvable via l'API.", file=sys.stderr)
        return 1
    print(f"   → id_auteur = {user_id}")

    print("📥 Récupération du détail du profil…")
    user = fetch_user_details(user_id)
    if not user:
        print("❌ Détail utilisateur non récupérable.", file=sys.stderr)
        return 1

    print("📊 Comptage des challenges par domaine…")
    totals = fetch_total_per_domain()

    payload = build_payload(user, totals)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"✅ {OUTPUT_FILE} mis à jour : "
          f"{payload['points']} pts, "
          f"{payload['challenges']} challenges, "
          f"rang {payload['rank']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
