(() => {
  document.documentElement.classList.add('enhanced');

  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#primary-navigation');
  const header = document.querySelector('.site-header');
  const programMenu = document.querySelector('[data-program-menu]');
  const programSummary = programMenu?.querySelector('summary');
  const menuLabel = toggle?.querySelector('[data-menu-label]');
  const closeMenu = (restoreFocus = false) => {
    toggle?.setAttribute('aria-expanded', 'false');
    nav?.removeAttribute('data-open');
    programMenu?.removeAttribute('open');
    document.documentElement.classList.remove('menu-open');
    if (menuLabel) menuLabel.textContent = 'Menu';
    if (restoreFocus) toggle?.focus();
  };

  toggle?.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    if (open) {
      nav?.setAttribute('data-open', 'true');
      document.documentElement.classList.add('menu-open');
      if (menuLabel) menuLabel.textContent = 'Close';
      window.requestAnimationFrame(() => nav?.querySelector('summary, a')?.focus());
    } else closeMenu();
  });
  nav?.addEventListener('click', (event) => {
    if (event.target.closest('a')) closeMenu();
  });
  document.addEventListener('click', (event) => {
    if (nav?.hasAttribute('data-open') && !header?.contains(event.target)) closeMenu();
    if (programMenu?.hasAttribute('open') && !programMenu.contains(event.target)) programMenu.removeAttribute('open');
  });
  document.addEventListener('keydown', (event) => {
    if (event.key === 'Escape') {
      if (programMenu?.hasAttribute('open')) {
        programMenu.removeAttribute('open');
        programSummary?.focus();
      } else if (nav?.hasAttribute('data-open')) closeMenu(true);
      return;
    }
    if (event.key === 'Tab' && nav?.hasAttribute('data-open') && toggle) {
      const focusable = [toggle, ...[...nav.querySelectorAll('summary, a')].filter((element) => element.offsetParent !== null)];
      const first = focusable[0];
      const last = focusable[focusable.length - 1];
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault(); last.focus();
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault(); first.focus();
      }
    }
  });
  window.addEventListener('resize', () => {
    if (window.innerWidth >= 860 && nav?.hasAttribute('data-open')) closeMenu();
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

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  document.querySelectorAll('[data-evidence-explorer]').forEach((explorer) => {
    const panels = [...explorer.querySelectorAll('[data-evidence-panel]')];
    const scopeControls = [...explorer.querySelectorAll('[data-scope-control]')];
    const yearControls = [...explorer.querySelectorAll('[data-year-control]')];
    const status = explorer.querySelector('[data-explorer-status]');
    const archive = explorer.querySelector('.evidence-archive');
    const scopes = new Set(panels.map((panel) => panel.dataset.scope || 'all'));
    const years = new Set(panels.map((panel) => panel.dataset.year));

    const readState = () => {
      const params = new URLSearchParams(window.location.search);
      const requestedScope = params.get('scope') || 'all';
      const requestedYear = params.get('year') || yearControls[0]?.dataset.yearControl;
      return {
        scope: scopes.has(requestedScope) ? requestedScope : 'all',
        year: years.has(requestedYear) ? requestedYear : yearControls[0]?.dataset.yearControl,
      };
    };

    const render = ({ scope, year }, announce = false) => {
      let selected;
      for (const panel of panels) {
        const matches = (panel.dataset.scope || 'all') === scope && panel.dataset.year === year;
        panel.hidden = !matches;
        if (matches) selected = panel;
      }
      for (const control of scopeControls) {
        if (control.dataset.scopeControl === scope) control.setAttribute('aria-current', 'true');
        else control.removeAttribute('aria-current');
      }
      for (const control of yearControls) {
        if (control.dataset.yearControl === year) control.setAttribute('aria-current', 'true');
        else control.removeAttribute('aria-current');
        const url = new URL(control.href);
        if (scopeControls.length) url.searchParams.set('scope', scope);
        control.href = `${url.pathname}${url.search}${url.hash}`;
      }
      if (status) {
        const scopeName = scopeControls.find((control) => control.dataset.scopeControl === scope)?.textContent.trim();
        status.textContent = announce ? (scopeName ? `Showing ${scopeName}, ${year}.` : `Showing ${year}.`) : '';
      }
      if (announce && selected && !reducedMotion) {
        selected.animate([{ transform: 'translate3d(0,8px,0)' }, { transform: 'none' }], { duration: 220, easing: 'cubic-bezier(.16,1,.3,1)' });
      }
    };

    const select = (next, push = true) => {
      const current = readState();
      const state = { scope: next.scope || current.scope, year: next.year || current.year };
      if (push) {
        const url = new URL(window.location.href);
        if (scopeControls.length) url.searchParams.set('scope', state.scope);
        url.searchParams.set('year', state.year);
        url.hash = 'evidence';
        window.history.pushState({}, '', url);
      }
      render(state, push);
    };

    scopeControls.forEach((control) => control.addEventListener('click', (event) => {
      event.preventDefault(); select({ scope: control.dataset.scopeControl });
    }));
    yearControls.forEach((control) => control.addEventListener('click', (event) => {
      event.preventDefault(); select({ year: control.dataset.yearControl });
    }));
    window.addEventListener('popstate', () => render(readState(), true));
    archive?.removeAttribute('open');
    render(readState());
  });

  if (reducedMotion) return;

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
