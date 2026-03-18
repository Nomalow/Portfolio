/**
 * main.js — Utilitaires partagés entre toutes les pages
 */

/**
 * Active l'animation de révélation au scroll sur tous les éléments .reveal
 * Applique un délai en cascade pour les éléments dans le même parent
 * @param {number} staggerMs - délai entre chaque enfant (ms)
 */
export function initReveal(staggerMs = 70) {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;

      const el = entry.target;
      const siblings = [
        ...(el.parentElement?.querySelectorAll('.reveal') ?? [])
      ];
      const delay = siblings.indexOf(el) * staggerMs;

      setTimeout(() => el.classList.add('visible'), delay);
      observer.unobserve(el);
    });
  }, { threshold: 0.1 });

  document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
}

/**
 * Met en surbrillance le lien nav correspondant à la page courante
 * en comparant le href avec window.location.pathname
 */
export function initActiveNav() {
  const current = window.location.pathname.split('/').pop() || 'index.html';
  document.querySelectorAll('nav a').forEach((link) => {
    const href = link.getAttribute('href');
    if (href === current) link.classList.add('active');
  });
}
