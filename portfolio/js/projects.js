/**
 * projects.js — Page Projets
 * Autonome : contient initReveal, filtres et modale PDF.
 * Ne dépend pas de main.js.
 */

/* ── REVEAL AU SCROLL ── */
function initReveal() {
  const observer = new IntersectionObserver((entries) => {
    entries.forEach((entry) => {
      if (!entry.isIntersecting) return;
      const el       = entry.target;
      const siblings = [...(el.parentElement?.querySelectorAll('.reveal') ?? [])];
      setTimeout(() => el.classList.add('visible'), siblings.indexOf(el) * 80);
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
        card.classList.toggle('hidden', filter !== 'all' && card.dataset.cat !== filter);
      });
    });
  });
}

/* ── BLAGUES PORTFOLIO (rotation aléatoire) ── */
const PORTFOLIO_JOKES = [
  {
    ico: "👀",
    title: "Euh… vous êtes déjà dessus 😅",
    desc: "Le projet « Portfolio en ligne », c'est littéralement le site sur lequel vous êtes en train de cliquer. Inception level: 100."
  },
  {
    ico: "🪞",
    title: "Vous regardez le site… depuis le site",
    desc: "Pas besoin de PDF pour ce projet, il vous suffit de regarder autour de vous. Joli, n'est-ce pas ?"
  },
  {
    ico: "🤯",
    title: "Erreur 404 : votre cerveau a buggé",
    desc: "Ouvrir la doc d'un portfolio depuis ce même portfolio… vous venez de créer une boucle infinie."
  },
  {
    ico: "🎬",
    title: "Plot twist du siècle",
    desc: "Spoiler alert : le projet, c'est ce site. Vous êtes le héros de l'histoire. 🍿"
  }
];

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

      /* Rempli le header */
      modalIco.textContent  = ico;
      modalName.textContent = name;
      modalDl.href          = pdf;

      /* Stack tags */
      modalStack.innerHTML = stack.split(',')
        .map((s) => `<span class="stack-tag">${s.trim()}</span>`)
        .join('');

      /* Status badge */
      modalStatus.textContent = status === 'done' ? '✓ Terminé' : '⏳ En cours';
      modalStatus.className   = 'modal-status ' + (status === 'done' ? 'status-done' : 'status-wip');

      /* Reset état */
      loading.style.display  = 'flex';
      errorBox.style.display = 'none';
      iframe.style.display   = 'none';
      iframe.src             = '';

      /* Ouvre la modale */
      overlay.classList.add('open');
      document.body.classList.add('modal-open');

      /* ── CAS SPÉCIAL : carte "Portfolio en ligne" ── */
      if (card.dataset.easter === 'portfolio') {
        const joke = PORTFOLIO_JOKES[Math.floor(Math.random() * PORTFOLIO_JOKES.length)];

        /* Cache le download (pas de PDF à télécharger) */
        modalDl.style.display = 'none';

        /* Affiche le message de blague à la place */
        loading.style.display  = 'none';
        iframe.style.display   = 'none';
        errorBox.style.display = 'flex';
        errorBox.querySelector('.modal-error-ico').textContent       = joke.ico;
        errorBox.querySelector('.modal-error-title').textContent     = joke.title;
        errorBox.querySelector('.modal-error-desc').innerHTML        = joke.desc;
        return;
      }

      /* Réaffiche le bouton télécharger pour les autres projets */
      modalDl.style.display = '';

      /* Restaure le message d'erreur par défaut (au cas où il a été modifié) */
      errorBox.querySelector('.modal-error-ico').textContent   = '📂';
      errorBox.querySelector('.modal-error-title').textContent = 'PDF introuvable';
      errorBox.querySelector('.modal-error-desc').innerHTML    =
        'Ajoute le fichier dans le dossier <code>pdfs/</code> de ton repo GitHub.';

      /* Vérifie que le PDF existe avant de charger */
      fetch(pdf, { method: 'HEAD' })
        .then((res) => {
          if (!res.ok) throw new Error('PDF introuvable');
          iframe.src = pdf;
          iframe.onload = () => {
            loading.style.display = 'none';
            iframe.style.display  = 'block';
          };
        })
        .catch(() => {
          loading.style.display  = 'none';
          errorBox.style.display = 'flex';
        });
    });
  });

  function closeModal() {
    overlay.classList.remove('open');
    document.body.classList.remove('modal-open');
    setTimeout(() => { iframe.src = ''; }, 250);
  }

  closeBtn.addEventListener('click', closeModal);
  overlay.addEventListener('click', (e) => { if (e.target === overlay) closeModal(); });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') closeModal(); });
}

/* ── INIT ── */
document.addEventListener('DOMContentLoaded', () => {
  initReveal();
  initFilters();
  initModal();
});
