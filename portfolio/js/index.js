/**
 * index.js — Script de la page d'accueil
 * Pas de logique spécifique : les animations hero sont gérées en CSS pur (animation: fadeUp).
 * On importe juste initReveal pour les quick-cards si elles devaient utiliser .reveal.
 */
import { initReveal } from './main.js';

document.addEventListener('DOMContentLoaded', () => {
  initReveal();
});
