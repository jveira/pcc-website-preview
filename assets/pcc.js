(() => {
  document.documentElement.classList.add('enhanced');

  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#primary-navigation');
  const header = document.querySelector('.site-header');
  const closeMenu = () => {
    toggle?.setAttribute('aria-expanded', 'false');
    nav?.removeAttribute('data-open');
  };

  toggle?.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    if (open) nav.setAttribute('data-open', 'true');
    else nav.removeAttribute('data-open');
  });
  nav?.addEventListener('click', (event) => {
    if (event.target.closest('a')) closeMenu();
  });
  document.addEventListener('click', (event) => {
    if (nav?.hasAttribute('data-open') && !header?.contains(event.target)) closeMenu();
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeMenu();
      toggle?.focus();
    }
  });

  let headerFrame = 0;
  const syncHeader = () => {
    header?.classList.toggle('is-scrolled', window.scrollY > 12);
    headerFrame = 0;
  };
  const requestHeaderSync = () => {
    if (!headerFrame) headerFrame = window.requestAnimationFrame(syncHeader);
  };
  syncHeader();
  window.addEventListener('scroll', requestHeaderSync, { passive: true });

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const reveals = [...document.querySelectorAll('.reveal, .media-reveal')];
  if (!reveals.length || !('IntersectionObserver' in window)) return;

  for (const element of reveals) {
    const bounds = element.getBoundingClientRect();
    if (bounds.top < window.innerHeight * .92 && bounds.bottom > 0) element.classList.add('is-visible');
  }
  document.documentElement.classList.add('motion-ready');
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    }
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

  for (const element of reveals) {
    if (!element.classList.contains('is-visible')) observer.observe(element);
  }
})();
