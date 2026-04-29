"""
fetch_rootme.py — Récupère les stats Root Me d'Arthur (Nomalow)
via l'API officielle Root Me et génère portfolio/data/rootme.json.

Stratégie :
 1. Récupérer l'id de l'auteur via /auteurs?nom=Nomalow
 2. Récupérer le détail via /auteurs/{id} qui contient :
      - nom, score, position
      - challenges : liste des challenges validés (avec url_challenge)
 3. Déduire le domaine de chaque challenge depuis son URL
    (ex: /Challenges/Web-Serveur/HTML → "Web - Serveur")
 4. Compter les validés par domaine

Ainsi : 1 seule requête utile, 0 problème de rate limit (HTTP 429).

Doc : https://api.www.root-me.org/
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests

# ─── CONFIG ────────────────────────────────────────────────────────────────────
USERNAME    = "Nomalow"
API_BASE    = "https://api.www.root-me.org"
OUTPUT_FILE = Path("data/rootme.json")
TIMEOUT     = 20

API_KEY = os.environ.get("ROOTME_API_KEY")
if not API_KEY:
    print("❌ ROOTME_API_KEY non défini.", file=sys.stderr)
    sys.exit(1)

COOKIES = {"api_key": API_KEY}
HEADERS = {
    "User-Agent": "Nomalow-Portfolio/1.0",
    "Accept": "application/json",
}

# Slugs d'URL → nom d'affichage du domaine
URL_TO_DOMAIN = {
    "App-Script":     "App - Script",
    "App-Systeme":    "App - Système",
    "App-Système":    "App - Système",
    "Cracking":       "Cracking",
    "Cryptanalyse":   "Cryptanalyse",
    "Forensic":       "Forensic",
    "Programmation":  "Programmation",
    "Realiste":       "Réaliste",
    "Réaliste":       "Réaliste",
    "Reseau":         "Réseau",
    "Réseau":         "Réseau",
    "Steganographie": "Stéganographie",
    "Stéganographie": "Stéganographie",
    "Web-Client":     "Web - Client",
    "Web-Serveur":    "Web - Serveur",
}

DOMAINS_DISPLAY = [
    "App - Script", "App - Système", "Cracking", "Cryptanalyse",
    "Forensic",     "Programmation",  "Réaliste", "Réseau",
    "Stéganographie", "Web - Client",  "Web - Serveur",
]

# Totaux connus (constants côté Root Me, mis à jour quand de nouveaux challenges sortent)
# On les met en dur ici plutôt que de spammer l'API et se prendre des HTTP 429.
# Tu peux les ajuster manuellement si Root Me ajoute des challenges.
DOMAIN_TOTALS = {
    "App - Script":   85,
    "App - Système":  88,
    "Cracking":       58,
    "Cryptanalyse":   75,
    "Forensic":       30,
    "Programmation":  31,
    "Réaliste":       12,
    "Réseau":         48,
    "Stéganographie": 22,
    "Web - Client":   36,
    "Web - Serveur":  87,
}


# ─── HTTP ──────────────────────────────────────────────────────────────────────
def api_get(path: str, **params):
    url = f"{API_BASE}{path}"
    try:
        r = requests.get(url, cookies=COOKIES, headers=HEADERS,
                         params=params, timeout=TIMEOUT)
        print(f"   GET {url} → HTTP {r.status_code}")
        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"⚠️  Erreur GET {path} : {e}", file=sys.stderr)
        return None


# ─── RECHERCHE DE L'ID UTILISATEUR ─────────────────────────────────────────────
def find_user_id(username: str):
    print(f"🔍 Recherche de '{username}'…")
    data = api_get("/auteurs", nom=username)
    if not data:
        return None
    pages = data if isinstance(data, list) else [data]
    for page in pages:
        if not isinstance(page, dict):
            continue
        for _, entry in page.items():
            if isinstance(entry, dict) and \
               str(entry.get("nom", "")).lower() == username.lower():
                uid = int(entry["id_auteur"])
                print(f"   ✓ Trouvé : id_auteur = {uid}")
                return uid
    return None


# ─── DOMAINES DEPUIS LES URLS ──────────────────────────────────────────────────
def domain_from_url(url: str):
    """
    Extrait le domaine d'une URL de challenge.
    Ex: https://www.root-me.org/fr/Challenges/Web-Serveur/HTML → "Web - Serveur"
    """
    if not url:
        return None
    try:
        path = unquote(urlparse(url).path)
        m = re.search(r"/Challenges/([^/]+)", path)
        if not m:
            return None
        return URL_TO_DOMAIN.get(m.group(1))
    except Exception:
        return None


# ─── CONSTRUCTION DU PAYLOAD ───────────────────────────────────────────────────
def build_payload(user: dict) -> dict:
    challenges = user.get("challenges") or []
    print(f"📋 Clés du profil : {list(user.keys())}")
    print(f"   {len(challenges)} challenges validés au total")

    # Comptage par domaine
    solved = {d: 0 for d in DOMAINS_DISPLAY}
    unmatched = 0
    for ch in challenges:
        url = ch.get("url_challenge", "")
        domain = domain_from_url(url)
        if domain and domain in solved:
            solved[domain] += 1
        else:
            unmatched += 1
            if unmatched <= 3:  # debug : affiche les 3 premiers non reconnus
                print(f"   ? Domaine non reconnu : {url}")

    if unmatched:
        print(f"   ⚠️  {unmatched} challenges sans domaine identifié")

    # Construction des domaines avec %
    domains_payload = []
    for d in DOMAINS_DISPLAY:
        solved_count = solved[d]
        total = DOMAIN_TOTALS.get(d, 0)
        pct = round(solved_count / total * 100, 1) if total else 0
        domains_payload.append({
            "name":    d,
            "solved":  solved_count,
            "total":   total,
            "percent": pct,
        })
        print(f"   • {d}: {solved_count}/{total} ({pct}%)")

    # Conversion des champs numériques
    def _to_int(v):
        if v is None: return None
        try: return int(v)
        except (ValueError, TypeError): return None

    return {
        "username":    user.get("nom") or USERNAME,
        "profile_url": f"https://www.root-me.org/{USERNAME}?lang=fr",
        "points":      _to_int(user.get("score")),
        "rank":        _to_int(user.get("position")),
        "challenges":  len(challenges),
        "domains":     domains_payload,
        "updated_at":  datetime.now(timezone.utc).isoformat(),
    }


# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main() -> int:
    uid = find_user_id(USERNAME)
    if not uid:
        print("❌ Utilisateur introuvable.", file=sys.stderr)
        return 1

    print(f"📥 Récupération du profil id={uid}…")
    user = api_get(f"/auteurs/{uid}")
    if not user:
        print("❌ Profil indisponible.", file=sys.stderr)
        return 1

    payload = build_payload(user)

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
