/**
 * certs.js — Script de la page Certifications
 *
 * Responsabilités :
 *  1. Reveal au scroll (via main.js)
 *  2. Récupérer les stats Root Me depuis data/rootme.json
 *     (mis à jour automatiquement toutes les 6h par GitHub Actions)
 *  3. Afficher les stats globales + barres de progression par domaine
 *     (uniquement les domaines où l'utilisateur a au moins 1 challenge validé)
 */
import { initReveal } from './main.js';

const ROOTME_DATA_URL = 'data/rootme.json';

/** Formate un nombre avec des espaces : 1234 → "1 234" */
const fmt = (n) =>
  n == null ? '—' : n.toLocaleString('fr-FR').replace(/\u202f/g, ' ');

/** Formate un timestamp ISO en date FR lisible */
function fmtDate(iso) {
  if (!iso) return '';
  const d = new Date(iso);
  return d.toLocaleString('fr-FR', {
    day: '2-digit', month: 'long', year: 'numeric',
    hour: '2-digit', minute: '2-digit',
  });
}

/** Récupère les stats Root Me depuis le JSON statique */
async function loadRootMe() {
  try {
    const res = await fetch(ROOTME_DATA_URL, { cache: 'no-cache' });
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch (err) {
    console.error('[certs] Impossible de charger rootme.json :', err);
    return null;
  }
}

/** Remplit les valeurs numériques globales */
function renderStats(data) {
  document.getElementById('rm-points').textContent     = fmt(data.points);
  document.getElementById('rm-rank').textContent       = data.rank ? `#${fmt(data.rank)}` : '—';
  document.getElementById('rm-challenges').textContent = fmt(data.challenges);

  const updatedEl = document.getElementById('rm-updated');
  if (data.updated_at) {
    updatedEl.textContent = `Dernière mise à jour : ${fmtDate(data.updated_at)}`;
  }
}

/** Construit la liste des domaines avec barres de progression */
function renderDomains(domains) {
  const list = document.getElementById('rm-domains');
  if (!domains?.length) {
    list.innerHTML = '<p class="domains-loading">Aucune donnée pour les domaines.</p>';
    return;
  }

  // On ne garde que les domaines où l'utilisateur a fait au moins 1 challenge
  const activeDomains = domains.filter((d) => d.solved > 0);

  if (activeDomains.length === 0) {
    list.innerHTML = '<p class="domains-loading">Aucun challenge validé pour le moment.</p>';
    return;
  }

  list.innerHTML = activeDomains.map((d) => `
    <div class="domain-item">
      <span class="domain-name">${d.name}</span>
      <div class="domain-bar-bg">
        <div class="domain-bar" data-width="${d.percent}%"></div>
      </div>
      <span class="domain-pct">
        <strong>${d.percent}%</strong>
        <span style="color: var(--muted); font-weight: 500;">
          (${d.solved}/${d.total})
        </span>
      </span>
    </div>
  `).join('');

  animateBars();
}

/** Anime les barres dès qu'elles entrent dans le viewport */
function animateBars() {
  const bars = document.querySelectorAll('.domain-bar');
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const bar = entry.target;
      bar.style.setProperty('--target-width', bar.dataset.width ?? '0%');
      bar.classList.add('animated');
      observer.unobserve(bar);
    });
  }, { threshold: 0.3 });

  bars.forEach((bar) => observer.observe(bar));
}

/** Cas d'erreur : affiche un message propre */
function renderError() {
  document.getElementById('rm-domains').innerHTML =
    '<p class="domains-loading">Impossible de charger les stats Root Me pour le moment. Réessaie plus tard.</p>';
}

// ─── Init ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  // 1. Animations de scroll (déjà présentes sur le reste du site)
  if (typeof initReveal === 'function') initReveal(80);

  // 2. Stats Root Me
  const data = await loadRootMe();
  if (!data || data.points == null) {
    renderError();
    return;
  }

  renderStats(data);
  renderDomains(data.domains);
});
