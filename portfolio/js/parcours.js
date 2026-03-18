/**
 * parcours.js — Script de la page Parcours
 * Gère uniquement la révélation au scroll des éléments de la timeline.
 * Chaque .timeline-item reçoit un délai fixe pour simuler un effet cascade.
 */
import { initReveal } from './main.js';

document.addEventListener('DOMContentLoaded', () => {
  initReveal(100);
});
