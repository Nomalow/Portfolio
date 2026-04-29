"""
fetch_rootme.py — Récupère les stats Root Me d'Arthur (Nomalow).

Cette version groupe les challenges par id_rubrique et affiche les
titres associés, pour permettre de vérifier le mapping.
"""

import json
import os
import sys
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

USERNAME    = "Nomalow"
USER_ID     = 1006965
API_BASE    = "https://api.www.root-me.org"
OUTPUT_FILE = Path("data/rootme.json")
TIMEOUT     = 20

API_KEY = os.environ.get("ROOTME_API_KEY")
if not API_KEY:
    print("❌ ROOTME_API_KEY non défini.", file=sys.stderr)
    sys.exit(1)

COOKIES = {"api_key": API_KEY}
HEADERS = {"User-Agent": "Nomalow-Portfolio/1.0", "Accept": "application/json"}

# Mapping id_rubrique → domaine (à corriger si nécessaire)
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

DOMAIN_TOTALS = {
    "App - Script": 85, "App - Système": 88, "Cracking": 58,
    "Cryptanalyse": 75, "Forensic": 30, "Programmation": 31,
    "Réaliste": 12, "Réseau": 48, "Stéganographie": 22,
    "Web - Client": 36, "Web - Serveur": 87,
}


def api_get(path: str):
    url = f"{API_BASE}{path}"
    r = requests.get(url, cookies=COOKIES, headers=HEADERS, timeout=TIMEOUT)
    print(f"   GET {url} → HTTP {r.status_code}")
    r.raise_for_status()
    return r.json()


def build_payload(user: dict) -> dict:
    validations = user.get("validations") or []
    print(f"📋 {len(validations)} challenges validés au total\n")

    # Groupement par id_rubrique
    by_rubrique = defaultdict(list)
    for v in validations:
        id_rub = str(v.get("id_rubrique", "?"))
        title = v.get("titre", "(sans titre)")
        by_rubrique[id_rub].append(title)

    # Affichage du contenu de chaque id_rubrique
    print("📊 Challenges groupés par id_rubrique :")
    for id_rub in sorted(by_rubrique.keys(), key=lambda x: int(x) if x.isdigit() else 9999):
        domain = RUBRIQUE_TO_DOMAIN.get(id_rub, "❓ INCONNU")
        titles = by_rubrique[id_rub]
        print(f"\n   📁 id_rubrique={id_rub} → {domain} ({len(titles)} challenges)")
        for t in titles[:5]:
            print(f"      - {t}")
        if len(titles) > 5:
            print(f"      ... et {len(titles) - 5} autres")

    print("\n" + "=" * 50)

    # Comptage par domaine
    solved = {d: 0 for d in DOMAINS_DISPLAY}
    for id_rub, titles in by_rubrique.items():
        domain = RUBRIQUE_TO_DOMAIN.get(id_rub)
        if domain in solved:
            solved[domain] += len(titles)

    domains_payload = []
    print("\n🎯 Résultat final :")
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
