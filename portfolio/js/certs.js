/**
 * certs.js — Script de la page Certifications
 *
 * Responsabilités :
 *  1. Révélation au scroll (via main.js)
 *  2. Animation des barres de progression "en cours"
 *     La largeur cible est portée par data-width sur chaque .progress-bar.
 */
import { initReveal } from './main.js';

/**
 * Observe chaque barre de progression et l'anime dès qu'elle entre dans le viewport.
 */
function initProgressBars() {
  const bars = document.querySelectorAll('.progress-bar');

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
  initReveal(80);
  initProgressBars();
});
