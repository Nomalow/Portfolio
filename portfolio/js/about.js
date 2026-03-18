/**
 * about.js — Script de la page À propos
 * Gère uniquement l'animation de révélation au scroll.
 */
import { initReveal } from './main.js';

document.addEventListener('DOMContentLoaded', () => {
  initReveal(70);
});
