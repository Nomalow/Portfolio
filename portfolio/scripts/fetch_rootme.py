"""
fetch_rootme.py — VERSION DIAGNOSTIC

Affiche la structure complète de la réponse API pour comprendre
pourquoi 'validations' apparaît dans les clés mais semble vide.
"""

import json
import os
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse, unquote

import requests

USERNAME    = "Nomalow"
API_BASE    = "https://api.www.root-me.org"
OUTPUT_FILE = Path("data/rootme.json")

API_KEY = os.environ.get("ROOTME_API_KEY")
if not API_KEY:
    print("❌ ROOTME_API_KEY non défini.", file=sys.stderr)
    sys.exit(1)

COOKIES = {"api_key": API_KEY}
HEADERS = {"User-Agent": "Nomalow-Portfolio/1.0", "Accept": "application/json"}

URL_TO_DOMAIN = {
    "App-Script": "App - Script", "App-Systeme": "App - Système",
    "App-Système": "App - Système", "Cracking": "Cracking",
    "Cryptanalyse": "Cryptanalyse", "Forensic": "Forensic",
    "Programmation": "Programmation", "Realiste": "Réaliste",
    "Réaliste": "Réaliste", "Reseau": "Réseau", "Réseau": "Réseau",
    "Steganographie": "Stéganographie", "Stéganographie": "Stéganographie",
    "Web-Client": "Web - Client", "Web-Serveur": "Web - Serveur",
}

DOMAINS_DISPLAY = list(dict.fromkeys(URL_TO_DOMAIN.values()))

DOMAIN_TOTALS = {
    "App - Script": 85, "App - Système": 88, "Cracking": 58,
    "Cryptanalyse": 75, "Forensic": 30, "Programmation": 31,
    "Réaliste": 12, "Réseau": 48, "Stéganographie": 22,
    "Web - Client": 36, "Web - Serveur": 87,
}


def api_get(path):
    r = requests.get(f"{API_BASE}{path}", cookies=COOKIES, headers=HEADERS, timeout=20)
    print(f"   GET {API_BASE}{path} → HTTP {r.status_code}")
    r.raise_for_status()
    return r.json()


def domain_from_url(url):
    if not url: return None
    try:
        m = re.search(r"/Challenges/([^/]+)", unquote(urlparse(url).path))
        return URL_TO_DOMAIN.get(m.group(1)) if m else None
    except Exception:
        return None


# ─── DIAGNOSTIC : affiche la réponse brute ────────────────────────────────────
print("=" * 60)
print("🔍 DIAGNOSTIC — Réponse complète de l'API")
print("=" * 60)

uid = 1006965  # on connaît déjà ton id
print(f"\n📥 GET /auteurs/{uid}")
user = api_get(f"/auteurs/{uid}")

print("\n📋 STRUCTURE DE LA RÉPONSE :")
print(f"   Type racine : {type(user).__name__}")

if isinstance(user, dict):
    for key, value in user.items():
        if isinstance(value, list):
            print(f"   • {key} : liste de {len(value)} éléments")
            if value:
                print(f"       premier élément (clés) : {list(value[0].keys()) if isinstance(value[0], dict) else type(value[0])}")
                print(f"       premier élément (contenu) : {json.dumps(value[0], ensure_ascii=False)[:300]}")
        elif isinstance(value, dict):
            print(f"   • {key} : dict avec {len(value)} clés")
            print(f"       clés : {list(value.keys())[:10]}")
            # Aperçu des premières valeurs
            first_keys = list(value.keys())[:2]
            for k in first_keys:
                v = value[k]
                preview = json.dumps(v, ensure_ascii=False)[:200] if not isinstance(v, str) else v[:200]
                print(f"       [{k}] : {preview}")
        else:
            print(f"   • {key} : {value!r}")

elif isinstance(user, list):
    print(f"   Liste de {len(user)} éléments")
    if user:
        print(f"   Premier élément : {type(user[0]).__name__}")
        print(f"   Contenu : {json.dumps(user[0], ensure_ascii=False)[:500]}")

print("\n" + "=" * 60)
print("📊 EXTRACTION DES DONNÉES")
print("=" * 60)

# On essaie de trouver les challenges où qu'ils soient
def find_validations(obj, depth=0, path=""):
    """Cherche récursivement une liste de challenges (URL contenant /Challenges/)."""
    if depth > 4:
        return None
    if isinstance(obj, list):
        # Une liste qui ressemble à des challenges ?
        for item in obj:
            if isinstance(item, dict):
                for v in item.values():
                    if isinstance(v, str) and "/Challenges/" in v:
                        return obj  # Trouvé !
        return None
    if isinstance(obj, dict):
        for k, v in obj.items():
            result = find_validations(v, depth + 1, f"{path}.{k}")
            if result is not None:
                print(f"   ✓ Challenges trouvés à : {path}.{k} ({len(result)} entrées)")
                return result
    return None

validations = find_validations(user) or []

print(f"\n   {len(validations)} challenges récupérés")
if validations:
    print(f"   Exemple : {json.dumps(validations[0], ensure_ascii=False)}")

# Comptage par domaine
solved = {d: 0 for d in DOMAINS_DISPLAY}
for ch in validations:
    if isinstance(ch, dict):
        for v in ch.values():
            if isinstance(v, str) and "/Challenges/" in v:
                d = domain_from_url(v)
                if d in solved:
                    solved[d] += 1
                break

# ─── Génération du JSON ───────────────────────────────────────────────────────
def _to_int(v):
    if v is None: return None
    try: return int(v)
    except (ValueError, TypeError): return None

domains_payload = []
for d in DOMAINS_DISPLAY:
    s = solved[d]
    t = DOMAIN_TOTALS.get(d, 0)
    pct = round(s / t * 100, 1) if t else 0
    domains_payload.append({"name": d, "solved": s, "total": t, "percent": pct})
    print(f"   • {d}: {s}/{t} ({pct}%)")

payload = {
    "username":    user.get("nom") if isinstance(user, dict) else USERNAME,
    "profile_url": f"https://www.root-me.org/{USERNAME}?lang=fr",
    "points":      _to_int(user.get("score")) if isinstance(user, dict) else None,
    "rank":        _to_int(user.get("position")) if isinstance(user, dict) else None,
    "challenges":  len(validations),
    "domains":     domains_payload,
    "updated_at":  datetime.now(timezone.utc).isoformat(),
}

OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
OUTPUT_FILE.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")

print(f"\n✅ {OUTPUT_FILE} : {payload['points']} pts, {payload['challenges']} challenges, rang {payload['rank']}")
