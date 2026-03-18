/**
 * projects.js — Page Projets
 * Autonome : ne dépend pas de main.js
 */

/* ── REVEAL AU SCROLL ── */
function initReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const el = entry.target;
      const siblings = [...(el.parentElement?.querySelectorAll('.reveal') ?? [])];
      const delay = siblings.indexOf(el) * 80;
      setTimeout(() => el.classList.add('visible'), delay);
      observer.unobserve(el);
    });
  }, { threshold: 0.1 });
  document.querySelectorAll('.reveal').forEach((el) => observer.observe(el));
}

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
  const overlay     = document.getElementById('modalOverlay');
  const iframe      = document.getElementById('modalIframe');
  const loading     = document.getElementById('modalLoading');
  const errorBox    = document.getElementById('modalError');
  const modalIco    = document.getElementById('modalIco');
  const modalName   = document.getElementById('modalName');
  const modalDl     = document.getElementById('modalDownload');
  const modalStack  = document.getElementById('modalStack');
  const modalStatus = document.getElementById('modalStatus');
  const closeBtn    = document.getElementById('modalClose');

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

      // Stack tags
      modalStack.innerHTML = stack.split(',')
        .map((s) => `<span class="stack-tag">${s.trim()}</span>`)
        .join('');

      // Status
      modalStatus.textContent = status === 'done' ? '✓ Terminé' : '⏳ En cours';
      modalStatus.className   = 'modal-status ' + (status === 'done' ? 'status-done' : 'status-wip');

      // Reset état
      loading.style.display  = 'flex';
      iframe.style.display   = 'none';
      errorBox.style.display = 'none';
      iframe.src             = '';

      // Ouvre la modale
      overlay.classList.add('open');
      document.body.classList.add('modal-open');

      // Vérifie que le PDF existe avant de le charger
      fetch(pdf, { method: 'HEAD' })
        .then((res) => {
          if (!res.ok) throw new Error('PDF introuvable');

          // PDF trouvé → charge dans l'iframe
          iframe.src = pdf;
          iframe.onload = () => {
            loading.style.display = 'none';
            iframe.style.display  = 'block';
          };
        })
        .catch(() => {
          // PDF manquant → affiche message d'erreur
          loading.style.display  = 'none';
          errorBox.style.display = 'flex';
        });
    });
  });

  closeBtn.addEventListener('click', closeModal);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });

  function closeModal() {
    overlay.classList.remove('open');
    document.body.classList.remove('modal-open');
    setTimeout(() => { iframe.src = ''; }, 250);
  }
}

document.addEventListener('DOMContentLoaded', () => {
  initReveal();
  initFilters();
  initModal();
});
