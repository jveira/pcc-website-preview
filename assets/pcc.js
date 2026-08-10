(() => {
  if (window.location.hash) {
    document.documentElement.style.scrollBehavior = 'auto';
    window.requestAnimationFrame(() => {
      let target;
      try { target = document.getElementById(decodeURIComponent(window.location.hash.slice(1))); } catch {}
      target?.scrollIntoView();
      window.requestAnimationFrame(() => document.documentElement.style.removeProperty('scroll-behavior'));
    });
  }
  document.documentElement.classList.add('enhanced');

  const programSlugs = new Set(['alpha-fc', 'caminos-nativos', 'mas-que-vencedores']);
  const programSlugFromPath = (pathname) => {
    const match = pathname.match(/^\/programs\/([^/]+)\/?$/);
    return match && programSlugs.has(match[1]) ? match[1] : '';
  };
  const currentProgramSlug = programSlugFromPath(window.location.pathname);
  if (currentProgramSlug) document.documentElement.dataset.programTransition = currentProgramSlug;
  const prepareProgramTransition = (targetUrl) => {
    const target = new URL(targetUrl, window.location.href);
    const targetSlug = target.origin === window.location.origin ? programSlugFromPath(target.pathname) : '';
    const isProgramOrigin = window.location.pathname === '/' || window.location.pathname === '/programs/';
    if (isProgramOrigin && targetSlug) document.documentElement.dataset.programTransition = targetSlug;
    else delete document.documentElement.dataset.programTransition;
  };
  document.addEventListener('click', (event) => {
    const link = event.target.closest('a[href]');
    if (link) prepareProgramTransition(link.href);
  }, { capture: true });
  window.addEventListener('pageswap', (event) => {
    const targetUrl = event.activation?.entry?.url;
    if (targetUrl) prepareProgramTransition(targetUrl);
  });

  const toggle = document.querySelector('.menu-toggle');
  const nav = document.querySelector('#primary-navigation');
  const header = document.querySelector('.site-header');
  const programMenu = document.querySelector('[data-program-menu]');
  const programSummary = programMenu?.querySelector('summary');
  const menuLabel = toggle?.querySelector('[data-menu-label]');
  let menuScrollY = 0;
  const lockPage = () => {
    menuScrollY = window.scrollY;
    document.body.style.position = 'fixed';
    document.body.style.top = `-${menuScrollY}px`;
    document.body.style.left = '0';
    document.body.style.right = '0';
    document.body.style.width = '100%';
  };
  const unlockPage = () => {
    document.body.style.removeProperty('position');
    document.body.style.removeProperty('top');
    document.body.style.removeProperty('left');
    document.body.style.removeProperty('right');
    document.body.style.removeProperty('width');
    const scrollBehavior = document.documentElement.style.scrollBehavior;
    document.documentElement.style.scrollBehavior = 'auto';
    window.requestAnimationFrame(() => {
      window.scrollTo(0, menuScrollY);
      window.requestAnimationFrame(() => {
        document.documentElement.style.scrollBehavior = scrollBehavior;
      });
    });
  };
  const closeMenu = (restoreFocus = false) => {
    const wasOpen = nav?.hasAttribute('data-open');
    toggle?.setAttribute('aria-expanded', 'false');
    nav?.removeAttribute('data-open');
    programMenu?.removeAttribute('open');
    document.documentElement.classList.remove('menu-open');
    if (wasOpen) unlockPage();
    if (menuLabel) menuLabel.textContent = 'Menu';
    if (restoreFocus) toggle?.focus();
  };

  toggle?.addEventListener('click', () => {
    const open = toggle.getAttribute('aria-expanded') !== 'true';
    toggle.setAttribute('aria-expanded', String(open));
    if (open) {
      lockPage();
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

  const mobileDock = document.querySelector('[data-mobile-dock]');
  const footer = document.querySelector('.site-footer');
  if (mobileDock && footer && 'IntersectionObserver' in window) {
    const dockObserver = new IntersectionObserver(([entry]) => {
      mobileDock.classList.toggle('is-near-footer', entry.isIntersecting);
    }, { rootMargin: '0px 0px 68px 0px', threshold: 0 });
    dockObserver.observe(footer);
  }
  const dockOcclusion = document.querySelector('[data-dock-occlusion]');
  if (mobileDock && dockOcclusion && 'IntersectionObserver' in window) {
    const actionObserver = new IntersectionObserver(([entry]) => {
      mobileDock.classList.toggle('is-over-local-actions', entry.isIntersecting);
    }, { rootMargin: '0px 0px 68px 0px', threshold: 0 });
    actionObserver.observe(dockOcclusion);
  }

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
        const url = new URL(control.href, window.location.href);
        url.searchParams.set('year', year);
        control.href = `${url.pathname}${url.search}${url.hash}`;
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

  document.querySelectorAll('[data-local-navigation]').forEach((strip) => {
    const links = [...strip.querySelectorAll('a[href^="#"]')];
    if (!links.length) return;
    let activeLink;
    let contextFrame = 0;
    const setCurrent = (next) => {
      if (!next || next === activeLink) return;
      activeLink = next;
      links.forEach((link) => {
        if (link === next) link.setAttribute('aria-current', 'location');
        else link.removeAttribute('aria-current');
      });
      if (window.innerWidth < 860) {
        const label = strip.querySelector('.context-label');
        const left = next === label ? 0 : Math.max(0, next.offsetLeft - (label?.offsetWidth || 0) - 12);
        strip.scrollTo({ left, behavior: reducedMotion ? 'auto' : 'smooth' });
      }
    };
    const syncContext = () => {
      const threshold = window.innerWidth < 860 ? 116 : 24;
      let next = links[0];
      for (const link of links) {
        const target = document.querySelector(link.hash);
        if (target && target.getBoundingClientRect().top <= threshold) next = link;
      }
      const hashLink = links.find((link) => link.hash === window.location.hash);
      const hashTarget = hashLink && document.querySelector(hashLink.hash);
      if (hashTarget && hashTarget.getBoundingClientRect().top <= threshold + 24) next = hashLink;
      setCurrent(next);
    };
    const requestContextSync = () => {
      if (contextFrame) return;
      contextFrame = window.requestAnimationFrame(() => {
        syncContext();
        contextFrame = 0;
      });
    };
    window.addEventListener('hashchange', requestContextSync);
    window.addEventListener('scroll', requestContextSync, { passive: true });
    window.addEventListener('resize', requestContextSync);
    syncContext();
    window.requestAnimationFrame(syncContext);
  });

  const compactContent = window.matchMedia('(max-width: 699px)');
  const criteriaDisclosure = document.querySelector('.criteria-disclosure');
  const syncCompactContent = () => {
    const values = document.querySelectorAll('.value-item');
    if (compactContent.matches) {
      values.forEach((item) => item.removeAttribute('open'));
      if (criteriaDisclosure && window.location.hash !== '#partner-criteria') criteriaDisclosure.removeAttribute('open');
      return;
    }
    values.forEach((item) => item.setAttribute('open', ''));
    criteriaDisclosure?.setAttribute('open', '');
  };
  syncCompactContent();
  compactContent.addEventListener('change', syncCompactContent);
  window.addEventListener('hashchange', () => {
    if (window.location.hash === '#partner-criteria') criteriaDisclosure?.setAttribute('open', '');
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
