"""
fetch_rootme.py — Récupère les stats Root Me d'Arthur (Nomalow) 100% en live.

Tout est récupéré dynamiquement depuis l'API Root Me :
 1. Profil utilisateur (score, rang, challenges validés)
 2. Totaux par domaine via /challenges?id_rubrique=XX (avec pagination)

Pour éviter le rate limit (HTTP 429), on attend 3s entre chaque requête.
Le workflow prend ~40s mais tout est 100% à jour.
"""

import json
import os
import sys
import time
from collections import defaultdict
from datetime import datetime, timezone
from pathlib import Path

import requests

USERNAME    = "Nomalow"
USER_ID     = 1006965
API_BASE    = "https://api.www.root-me.org"
OUTPUT_FILE = Path("data/rootme.json")
TIMEOUT     = 20
RATE_DELAY  = 3.0   # secondes entre chaque requête

API_KEY = os.environ.get("ROOTME_API_KEY")
if not API_KEY:
    print("❌ ROOTME_API_KEY non défini.", file=sys.stderr)
    sys.exit(1)

COOKIES = {"api_key": API_KEY}
HEADERS = {"User-Agent": "Nomalow-Portfolio/1.0", "Accept": "application/json"}

# Mapping id_rubrique → domaine (vérifié via les vraies données API + profil Root Me)
RUBRIQUE_TO_DOMAIN = {
    "16":  "Web - Client",
    "17":  "Cracking",
    "18":  "Programmation",
    "19":  "Stéganographie",
    "20":  "Cryptanalyse",
    "22":  "Réseau",
    "67":  "Réaliste",
    "68":  "Web - Serveur",
    "69":  "App - Système",
    "70":  "App - Script",
    "182": "Réseau",
    # Forensic : id à découvrir si tu en fais un jour (les logs te le diront)
}

# Mapping inverse : domaine → liste des id_rubrique à interroger pour avoir le total
DOMAIN_TO_RUBRIQUES = defaultdict(list)
for rid, dom in RUBRIQUE_TO_DOMAIN.items():
    DOMAIN_TO_RUBRIQUES[dom].append(rid)

DOMAINS_DISPLAY = [
    "App - Script", "App - Système", "Cracking", "Cryptanalyse",
    "Forensic",     "Programmation",  "Réaliste", "Réseau",
    "Stéganographie", "Web - Client",  "Web - Serveur",
]


# ─── HTTP avec rate limiting ───────────────────────────────────────────────────
_last_call = 0.0

def api_get(path: str, **params):
    """GET sur l'API avec un délai mini entre 2 appels pour éviter le 429."""
    global _last_call
    elapsed = time.time() - _last_call
    if elapsed < RATE_DELAY:
        time.sleep(RATE_DELAY - elapsed)

    url = f"{API_BASE}{path}"
    try:
        r = requests.get(url, cookies=COOKIES, headers=HEADERS,
                         params=params, timeout=TIMEOUT)
        _last_call = time.time()
        print(f"   GET {url}{(' ?' + str(params)) if params else ''} → HTTP {r.status_code}")

        # Si malgré tout on prend un 429, on attend plus longtemps et on retry une fois
        if r.status_code == 429:
            print("   ⏳ Rate limit, on attend 10s et on retente…")
            time.sleep(10)
            r = requests.get(url, cookies=COOKIES, headers=HEADERS,
                             params=params, timeout=TIMEOUT)
            _last_call = time.time()
            print(f"   GET (retry) → HTTP {r.status_code}")

        r.raise_for_status()
        return r.json()
    except Exception as e:
        print(f"   ⚠️ Erreur : {e}", file=sys.stderr)
        return None


# ─── COMPTAGE DES CHALLENGES PAR RUBRIQUE ──────────────────────────────────────
def count_challenges_in_rubrique(id_rubrique: str) -> int:
    """
    Compte le nombre total de challenges dans une rubrique.
    Parcourt les pages tant que l'API renvoie des résultats.
    """
    total = 0
    offset = 0
    PAGE_SIZE = 50

    while True:
        data = api_get("/challenges",
                       id_rubrique=id_rubrique,
                       debut_challenges=offset)
        if not data or not isinstance(data, list) or not data:
            break

        # Format : [ { "0": {...}, "1": {...}, ... } ]
        page = data[0] if isinstance(data[0], dict) else {}
        # On compte les clés numériques
        chunk_size = sum(1 for k in page if str(k).isdigit())
        total += chunk_size

        if chunk_size < PAGE_SIZE:
            break
        offset += PAGE_SIZE
        if offset > 1000:  # garde-fou
            break

    return total


def fetch_all_totals() -> dict:
    """Récupère le total de challenges pour chaque domaine."""
    totals = {d: 0 for d in DOMAINS_DISPLAY}

    print("\n📊 Comptage des challenges par domaine (via API)…")
    for domain in DOMAINS_DISPLAY:
        rubriques = DOMAIN_TO_RUBRIQUES.get(domain, [])
        if not rubriques:
            print(f"   • {domain} : pas de rubrique connue → total = 0")
            continue

        domain_total = 0
        for rid in rubriques:
            count = count_challenges_in_rubrique(rid)
            domain_total += count
        totals[domain] = domain_total
        print(f"   • {domain} : {domain_total} challenges au total")

    return totals


# ─── BUILD PAYLOAD ─────────────────────────────────────────────────────────────
def build_payload(user: dict, totals: dict) -> dict:
    validations = user.get("validations") or []
    print(f"\n📋 {len(validations)} challenges validés au total")

    # Comptage par domaine
    solved = {d: 0 for d in DOMAINS_DISPLAY}
    for v in validations:
        id_rub = str(v.get("id_rubrique", ""))
        domain = RUBRIQUE_TO_DOMAIN.get(id_rub)
        if domain in solved:
            solved[domain] += 1
        else:
            print(f"   ⚠️ Rubrique non mappée : id_rubrique={id_rub} (titre: {v.get('titre', '?')})")

    # Construction des domaines
    domains_payload = []
    print("\n🎯 Résultat final :")
    for d in DOMAINS_DISPLAY:
        s = solved[d]
        t = totals.get(d, 0)
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

    totals = fetch_all_totals()

    payload = build_payload(user, totals)

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
