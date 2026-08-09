(() => {
  document.documentElement.classList.add('enhanced');

  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#primary-navigation');
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
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      closeMenu();
      toggle?.focus();
    }
  });

  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return;

  const reveals = [...document.querySelectorAll('.reveal')];
  if (!reveals.length || !('IntersectionObserver' in window)) return;

  document.documentElement.classList.add('motion-ready');
  const observer = new IntersectionObserver((entries) => {
    for (const entry of entries) {
      if (!entry.isIntersecting) continue;
      entry.target.classList.add('is-visible');
      observer.unobserve(entry.target);
    }
  }, { rootMargin: '0px 0px -8% 0px', threshold: 0.08 });

  for (const element of reveals) observer.observe(element);
})();
