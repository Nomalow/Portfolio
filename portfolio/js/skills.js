/**
 * skills.js — Script de la page Compétences
 *
 * Responsabilités :
 *  1. Révélation au scroll (via main.js)
 *  2. Animation des barres de maîtrise des langages
 *     Les barres lisent leur largeur cible depuis l'attribut data-width.
 */
import { initReveal } from './main.js';

/**
 * Observe chaque barre de langue et l'anime dès qu'elle est visible.
 * La largeur cible est portée par data-width="85%" sur l'élément .lang-bar.
 */
function initLangBars() {
  const bars = document.querySelectorAll('.lang-bar');

  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const bar = entry.target;
      const targetWidth = bar.dataset.width ?? '0%';
      bar.style.setProperty('--target-width', targetWidth);
      bar.classList.add('animated');
      observer.unobserve(bar);
    });
  }, { threshold: 0.5 });

  bars.forEach((bar) => observer.observe(bar));
}

document.addEventListener('DOMContentLoaded', () => {
  initReveal(70);
  initLangBars();
});
