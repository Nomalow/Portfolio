"""
fetch_rootme.py — Récupère les stats Root Me d'Arthur (Nomalow).

Format réel découvert grâce au diagnostic :
  /auteurs/{id} → dict avec :
    - score, position : strings/ints
    - validations : liste d'objets {id_challenge, titre, id_rubrique, date}
    - challenges, solutions : listes vides chez nous

Le domaine se déduit de id_rubrique (pas de l'URL).
"""

import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path

import requests

# ─── CONFIG ────────────────────────────────────────────────────────────────────
USERNAME    = "Nomalow"
USER_ID     = 1006965  # connu, on évite une requête inutile
API_BASE    = "https://api.www.root-me.org"
OUTPUT_FILE = Path("data/rootme.json")
TIMEOUT     = 20

API_KEY = os.environ.get("ROOTME_API_KEY")
if not API_KEY:
    print("❌ ROOTME_API_KEY non défini.", file=sys.stderr)
    sys.exit(1)

COOKIES = {"api_key": API_KEY}
HEADERS = {"User-Agent": "Nomalow-Portfolio/1.0", "Accept": "application/json"}

# ─── MAPPING id_rubrique → domaine ─────────────────────────────────────────────
# Source : structure officielle des rubriques Root Me
RUBRIQUE_TO_DOMAIN = {
    "16": "Web - Client",
    "17": "Cracking",
    "18": "Programmation",
    "19": "Stéganographie",
    "20": "Cryptanalyse",
    "22": "Réseau",
    "67": "Réaliste",
    "68": "Web - Serveur",
    "69": "App - Système",
    "70": "App - Script",
    "182": "Forensic",
}

DOMAINS_DISPLAY = [
    "App - Script", "App - Système", "Cracking", "Cryptanalyse",
    "Forensic",     "Programmation",  "Réaliste", "Réseau",
    "Stéganographie", "Web - Client",  "Web - Serveur",
]

# Totaux par domaine — ajustables manuellement
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
def api_get(path: str):
    url = f"{API_BASE}{path}"
    r = requests.get(url, cookies=COOKIES, headers=HEADERS, timeout=TIMEOUT)
    print(f"   GET {url} → HTTP {r.status_code}")
    r.raise_for_status()
    return r.json()


# ─── BUILD ─────────────────────────────────────────────────────────────────────
def build_payload(user: dict) -> dict:
    validations = user.get("validations") or []
    print(f"📋 {len(validations)} challenges validés trouvés")

    # Comptage par id_rubrique → domaine
    solved = {d: 0 for d in DOMAINS_DISPLAY}
    unknown_rubriques = {}

    for v in validations:
        id_rub = str(v.get("id_rubrique", ""))
        domain = RUBRIQUE_TO_DOMAIN.get(id_rub)
        if domain and domain in solved:
            solved[domain] += 1
        else:
            unknown_rubriques[id_rub] = unknown_rubriques.get(id_rub, 0) + 1

    if unknown_rubriques:
        print(f"   ⚠️  Rubriques inconnues : {unknown_rubriques}")

    # Construction du payload
    domains_payload = []
    for d in DOMAINS_DISPLAY:
        s = solved[d]
        t = DOMAIN_TOTALS.get(d, 0)
        pct = round(s / t * 100, 1) if t else 0
        domains_payload.append({
            "name": d, "solved": s, "total": t, "percent": pct,
        })
        print(f"   • {d}: {s}/{t} ({pct}%)")

    def _to_int(v):
        if v is None: return None
        try: return int(v)
        except (ValueError, TypeError): return None

    return {
        "username":    user.get("nom") or USERNAME,
        "profile_url": f"https://www.root-me.org/{USERNAME}?lang=fr",
        "points":      _to_int(user.get("score")),
        "rank":        _to_int(user.get("position")),
        "challenges":  len(validations),
        "domains":     domains_payload,
        "updated_at":  datetime.now(timezone.utc).isoformat(),
    }


# ─── MAIN ──────────────────────────────────────────────────────────────────────
def main() -> int:
    print(f"📥 Récupération du profil id={USER_ID}…")
    user = api_get(f"/auteurs/{USER_ID}")
    if not user or not isinstance(user, dict):
        print("❌ Profil invalide.", file=sys.stderr)
        return 1

    payload = build_payload(user)

    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_FILE.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    print(f"\n✅ {OUTPUT_FILE} mis à jour : "
          f"{payload['points']} pts, "
          f"{payload['challenges']} challenges, "
          f"rang {payload['rank']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
