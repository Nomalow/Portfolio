/**
 * contact.js — Script de la page Contact
 *
 * Responsabilités :
 *  1. Révélation au scroll (via main.js)
 *  2. Gestion de la soumission du formulaire (feedback visuel)
 */
import { initReveal } from './main.js';

/**
 * Intercepte la soumission du formulaire pour afficher un feedback visuel.
 * En production, remplacer le corps de handleSubmit par un vrai appel fetch().
 */
function initContactForm() {
  const form      = document.querySelector('.contact-form');
  const submitBtn = document.querySelector('.form-submit');

  if (!form || !submitBtn) return;

  form.addEventListener('submit', handleSubmit);

  function handleSubmit(event) {
    event.preventDefault();

    const originalText = submitBtn.textContent;
    submitBtn.textContent = '✓ Message envoyé !';
    submitBtn.classList.add('success');
    submitBtn.disabled = true;

    setTimeout(() => {
      submitBtn.textContent = originalText;
      submitBtn.classList.remove('success');
      submitBtn.disabled = false;
      form.reset();
    }, 3000);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initReveal(100);
  initContactForm();
});
