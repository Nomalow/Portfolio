/**
 * projects.js — Script de la page Projets
 *
 * Responsabilités :
 *  1. Révélation au scroll (via main.js)
 *  2. Filtrage des cartes projet par catégorie (data-cat)
 */
import { initReveal } from './main.js';

/**
 * Attache le comportement de filtrage aux boutons .filter-btn.
 * Chaque bouton possède un attribut data-filter (ex: "web", "ia", "all").
 * Les cartes projet possèdent un attribut data-cat correspondant.
 */
function initFilters() {
  const buttons = document.querySelectorAll('.filter-btn');
  const cards   = document.querySelectorAll('.project-card');

  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      // Mise à jour du bouton actif
      buttons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.dataset.filter;

      // Affiche ou masque les cartes selon la catégorie
      cards.forEach((card) => {
        const match = filter === 'all' || card.dataset.cat === filter;
        card.classList.toggle('hidden', !match);
      });
    });
  });
}

document.addEventListener('DOMContentLoaded', () => {
  initReveal(80);
  initFilters();
});
