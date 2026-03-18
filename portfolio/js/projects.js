/**
 * projects.js — Page Projets
 *
 * Responsabilités :
 *  1. Révélation au scroll (via main.js)
 *  2. Filtrage des cartes par catégorie (data-cat)
 *  3. Ouverture de la modale PDF au clic sur une carte
 */

/* ── FILTRES ── */
function initFilters() {
  const buttons = document.querySelectorAll('.filter-btn');
  const cards   = document.querySelectorAll('.project-card');

  buttons.forEach((btn) => {
    btn.addEventListener('click', () => {
      buttons.forEach((b) => b.classList.remove('active'));
      btn.classList.add('active');

      const filter = btn.dataset.filter;
      cards.forEach((card) => {
        const match = filter === 'all' || card.dataset.cat === filter;
        card.classList.toggle('hidden', !match);
      });
    });
  });
}

/* ── MODALE PDF ── */
function initModal() {
  const overlay  = document.getElementById('modalOverlay');
  const iframe   = document.getElementById('modalIframe');
  const loading  = document.getElementById('modalLoading');
  const modalIco = document.getElementById('modalIco');
  const modalName= document.getElementById('modalName');
  const modalDl  = document.getElementById('modalDownload');
  const modalStack  = document.getElementById('modalStack');
  const modalStatus = document.getElementById('modalStatus');
  const closeBtn = document.getElementById('modalClose');

  // Ouvre la modale avec les infos du projet cliqué
  document.querySelectorAll('.project-card').forEach((card) => {
    card.addEventListener('click', () => {
      const pdf    = card.dataset.pdf;
      const name   = card.dataset.name;
      const ico    = card.dataset.ico;
      const stack  = card.dataset.stack ?? '';
      const status = card.dataset.status;

      // Rempli le header
      modalIco.textContent  = ico;
      modalName.textContent = name;
      modalDl.href          = pdf;

      // Rempli le footer — stack tags
      modalStack.innerHTML = stack
        .split(',')
        .map((s) => `<span class="stack-tag">${s.trim()}</span>`)
        .join('');

      // Status badge
      if (status === 'done') {
        modalStatus.textContent = '✓ Terminé';
        modalStatus.className   = 'modal-status status-done';
      } else {
        modalStatus.textContent = '⏳ En cours';
        modalStatus.className   = 'modal-status status-wip';
      }

      // Affiche le loader, cache l'iframe
      loading.style.display = 'flex';
      iframe.style.display  = 'none';
      iframe.src            = '';

      // Ouvre la modale
      overlay.classList.add('open');
      document.body.classList.add('modal-open');

      // Charge le PDF dans l'iframe
      // Petit délai pour que l'animation d'ouverture soit visible
      setTimeout(() => {
        iframe.src = pdf;
        iframe.onload = () => {
          loading.style.display = 'none';
          iframe.style.display  = 'block';
        };
      }, 150);
    });
  });

  // Ferme la modale — bouton ✕
  closeBtn.addEventListener('click', closeModal);

  // Ferme la modale — clic sur l'overlay (hors modal)
  overlay.addEventListener('click', (e) => {
    if (e.target === overlay) closeModal();
  });

  // Ferme la modale — touche Échap
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal();
  });

  function closeModal() {
    overlay.classList.remove('open');
    document.body.classList.remove('modal-open');
    // Vide l'iframe après la transition pour stopper le PDF
    setTimeout(() => { iframe.src = ''; }, 250);
  }
}

/* ── INIT ── */
document.addEventListener('DOMContentLoaded', () => {
  initReveal(80);
  initFilters();
  initModal();
});
