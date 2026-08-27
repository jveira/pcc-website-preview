(() => {
  if (window.location.hash) {
    const alignHashTarget = (force = false) => {
      let target;
      try { target = document.getElementById(decodeURIComponent(window.location.hash.slice(1))); } catch {}
      if (!target) return;
      const targetTop = target.getBoundingClientRect().top;
      const targetOffset = Number.parseFloat(window.getComputedStyle(target).scrollMarginTop) || 0;
      if (force || targetTop < targetOffset - 2) target.scrollIntoView();
    };
    document.documentElement.style.scrollBehavior = 'auto';
    window.requestAnimationFrame(() => {
      alignHashTarget(true);
      window.requestAnimationFrame(() => document.documentElement.style.removeProperty('scroll-behavior'));
    });
    window.addEventListener('load', () => {
      document.documentElement.style.scrollBehavior = 'auto';
      window.requestAnimationFrame(() => {
        alignHashTarget();
        window.requestAnimationFrame(() => document.documentElement.style.removeProperty('scroll-behavior'));
      });
    }, { once: true });
  }
  document.documentElement.classList.add('enhanced');

  const preserveLanguageContext = (link) => {
    const target = new URL(link.getAttribute('href'), window.location.origin);
    target.search = window.location.search;
    target.hash = window.location.hash;
    link.setAttribute('href', `${target.pathname}${target.search}${target.hash}`);
  };
  document.querySelectorAll('.lang-toggle').forEach((link) => {
    preserveLanguageContext(link);
    link.addEventListener('click', () => preserveLanguageContext(link), { capture: true });
  });

  document.addEventListener('click', (event) => {
    const link = event.target.closest('a[href]');
    if (!link?.matches('.mobile-dock-link')) return;
    const target = new URL(link.href, window.location.href);
    if (target.origin !== window.location.origin) return;
    link.classList.add('is-navigating');
    link.setAttribute('aria-busy', 'true');
  }, { capture: true });
  window.addEventListener('pageshow', () => {
    document.querySelectorAll('.mobile-dock-link.is-navigating').forEach((link) => {
      link.classList.remove('is-navigating');
      link.removeAttribute('aria-busy');
    });
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
  const finishClose = (restoreFocus) => {
    toggle?.setAttribute('aria-expanded', 'false');
    nav?.removeAttribute('data-open');
    nav?.classList.remove('is-closing');
    programMenu?.removeAttribute('open');
    document.documentElement.classList.remove('menu-open');
    if (menuLabel) menuLabel.textContent = 'Menu';
    if (restoreFocus) toggle?.focus();
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

  const prefersReduce = window.matchMedia('(prefers-reduced-motion: reduce)');
  const heroFrame = document.querySelector('.home-hero-media .frame');
  const dockEl = document.querySelector('[data-mobile-dock]');
  let lastY = window.scrollY;
  let progressEl = null;
  if (document.querySelector('.letter-layout') && header) {
    progressEl = document.createElement('div');
    progressEl.className = 'read-progress';
    progressEl.setAttribute('aria-hidden', 'true');
    header.appendChild(progressEl);
  }
  let headerFrame = 0;
  const syncHeader = () => {
    const y = window.scrollY;
    header?.classList.toggle('is-scrolled', y > 12);
    if (heroFrame && !prefersReduce.matches) {
      const drift = Math.min(22, Math.max(0, y * 0.055));
      heroFrame.style.setProperty('--hero-drift', `${drift.toFixed(2)}px`);
    }
    if (progressEl) {
      const max = document.documentElement.scrollHeight - window.innerHeight;
      progressEl.style.transform = `scaleX(${max > 0 ? Math.min(1, y / max) : 0})`;
    }
    lastY = y;
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

  const dockOcclusions = [...document.querySelectorAll('[data-dock-occlusion]')];
  if (mobileDock && dockOcclusions.length && 'IntersectionObserver' in window) {
    const visibleOcclusions = new Set();
    const actionObserver = new IntersectionObserver((entries) => {
      for (const entry of entries) {
        if (entry.isIntersecting) visibleOcclusions.add(entry.target);
        else visibleOcclusions.delete(entry.target);
      }
      mobileDock.classList.toggle('is-over-local-actions', visibleOcclusions.size > 0);
    }, { rootMargin: '0px 0px 68px 0px', threshold: 0 });
    dockOcclusions.forEach((element) => actionObserver.observe(element));
  }

  const dockCollisionSelector = [
    '[data-dock-collision]',
    '.field-gallery-controls button',
    '.person-bio > summary',
    '.criteria-disclosure > summary',
    '.document-list a',
    '.graph-actions a',
    '.film-card',
    '.where-we-work-list a',
    '.home-section-head a',
    '.home-proof-links a',
    '.evidence-archive > summary'
  ].join(',');
  const dockCollisionTargets = [...document.querySelectorAll(dockCollisionSelector)];
  if (mobileDock && dockCollisionTargets.length) {
    let collisionFrame = 0;
    const syncDockCollisions = () => {
      const dockRect = mobileDock.getBoundingClientRect();
      const collides = dockCollisionTargets.some((element) => {
        const rect = element.getBoundingClientRect();
        return rect.bottom > dockRect.top - 8 && rect.top < dockRect.bottom + 8 &&
          rect.right > dockRect.left && rect.left < dockRect.right;
      });
      mobileDock.classList.toggle('is-colliding-action', collides);
      collisionFrame = 0;
    };
    const requestDockCollisionSync = () => {
      if (!collisionFrame) collisionFrame = window.requestAnimationFrame(syncDockCollisions);
    };
    syncDockCollisions();
    window.addEventListener('scroll', requestDockCollisionSync, { passive: true });
    window.addEventListener('resize', requestDockCollisionSync);
  }

  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  // Give meaningful editorial groups one shared entrance rhythm. This is added
  // progressively so the HTML remains complete with JavaScript or motion off.
  const sequenceSelector = [
    '.home-metrics',
    '.home-proof-links',
    '.partner-logo-grid',
    '.where-we-work-list',
    '.fact-grid',
    '.program-record',
    '.evidence-panel',
    '.document-list',
    '.values-grid',
    '.team-directory',
    '.methods-grid',
    '.continuation-links > div'
  ].join(',');
  document.querySelectorAll(sequenceSelector).forEach((group) => {
    group.classList.add('motion-sequence');
    [...group.children].forEach((item, index) => {
      item.style.setProperty('--motion-index', Math.min(index, 5));
    });
  });

  document.querySelectorAll('[data-field-gallery]').forEach((gallery) => {
    const track = gallery.querySelector('[data-gallery-track]');
    const slides = [...gallery.querySelectorAll('[data-gallery-slide]')];
    const current = gallery.querySelector('[data-gallery-current]');
    const previous = gallery.querySelector('[data-gallery-prev]');
    const next = gallery.querySelector('[data-gallery-next]');
    if (!track || slides.length < 2) return;
    let activeIndex = 0;
    let frame = 0;
    const setActive = (index) => {
      activeIndex = Math.max(0, Math.min(index, slides.length - 1));
      slides.forEach((slide, slideIndex) => {
        if (slideIndex === activeIndex) slide.setAttribute('aria-current', 'true');
        else slide.removeAttribute('aria-current');
      });
      if (current) current.textContent = String(activeIndex + 1);
      current?.closest('.field-gallery-status')?.style.setProperty('--gallery-progress', String((activeIndex + 1) / slides.length));
      if (previous) previous.disabled = activeIndex === 0;
      if (next) next.disabled = activeIndex === slides.length - 1;
    };
    const nearestSlide = () => {
      const left = track.scrollLeft;
      let nearest = 0;
      let distance = Infinity;
      slides.forEach((slide, index) => {
        const delta = Math.abs(slide.offsetLeft - track.offsetLeft - left);
        if (delta < distance) { distance = delta; nearest = index; }
      });
      setActive(nearest);
    };
    const go = (index) => {
      const destination = Math.max(0, Math.min(index, slides.length - 1));
      track.scrollTo({
        left: slides[destination].offsetLeft - track.offsetLeft,
        behavior: reducedMotion ? 'auto' : 'smooth'
      });
      setActive(destination);
    };
    previous?.addEventListener('click', () => go(activeIndex - 1));
    next?.addEventListener('click', () => go(activeIndex + 1));
    track.addEventListener('scroll', () => {
      window.cancelAnimationFrame(frame);
      frame = window.requestAnimationFrame(nearestSlide);
    }, { passive: true });
    setActive(0);
  });

  // Keep each program name and its place visibly connected. Both the editorial
  // list and map remain ordinary links when JavaScript or motion is unavailable.
  document.querySelectorAll('[data-program-map]').forEach((map) => {
    const section = map.closest('.where-we-work');
    if (!section) return;
    const locations = [...section.querySelectorAll('[data-program-location]')];
    const pins = [...section.querySelectorAll('[data-map-pin]')];
    const related = [...locations, ...pins];
    const setActive = (program) => {
      related.forEach((element) => element.classList.toggle('is-active', element.dataset.programLocation === program || element.dataset.mapPin === program));
    };
    const clearActive = () => related.forEach((element) => element.classList.remove('is-active'));
    related.forEach((element) => {
      const program = element.dataset.programLocation || element.dataset.mapPin;
      element.addEventListener('pointerenter', () => setActive(program));
      element.addEventListener('pointerleave', clearActive);
      element.addEventListener('focus', () => setActive(program));
      element.addEventListener('blur', clearActive);
    });
  });

  document.querySelectorAll('[data-evidence-explorer]').forEach((explorer) => {
    const panels = [...explorer.querySelectorAll('[data-evidence-panel]')];
    const scopeControls = [...explorer.querySelectorAll('[data-scope-control]')];
    const yearControls = [...explorer.querySelectorAll('[data-year-control]')];
    const status = explorer.querySelector('[data-explorer-status]');
    const archive = explorer.querySelector('.evidence-archive');
    const panelsWrap = explorer.querySelector('.evidence-panels');
    const isSpanish = document.documentElement.lang.toLowerCase().startsWith('es');
    const orderedYears = yearControls.map((control) => control.dataset.yearControl);
    // A scope/year is selectable only when its panel contains published evidence.
    const validPanels = panels.filter((panel) => panel.querySelector('.evidence-ledger'));
    const validYearsByScope = new Map();
    for (const panel of validPanels) {
      const scope = panel.dataset.scope || 'all';
      if (!validYearsByScope.has(scope)) validYearsByScope.set(scope, new Set());
      validYearsByScope.get(scope).add(panel.dataset.year);
    }
    const defaultScope = validYearsByScope.has('all')
      ? 'all'
      : scopeControls.find((control) => validYearsByScope.has(control.dataset.scopeControl))?.dataset.scopeControl || 'all';
    const firstValidYear = (scope) => {
      const validYears = validYearsByScope.get(scope) || new Set();
      return orderedYears.find((year) => validYears.has(year)) || [...validYears][0];
    };
    const normalizeState = ({ scope, year }) => {
      const normalizedScope = validYearsByScope.has(scope) ? scope : defaultScope;
      const validYears = validYearsByScope.get(normalizedScope) || new Set();
      return {
        scope: normalizedScope,
        year: validYears.has(year) ? year : firstValidYear(normalizedScope),
      };
    };

    // Do not advertise a program scope that has no published program evidence.
    for (const control of scopeControls) {
      control.hidden = !validYearsByScope.has(control.dataset.scopeControl);
    }
    const thumbs = [];
    for (const tabsNav of explorer.querySelectorAll('.scope-tabs, .year-tabs')) {
      const thumb = document.createElement('span');
      thumb.className = 'tab-thumb';
      thumb.setAttribute('aria-hidden', 'true');
      tabsNav.appendChild(thumb);
      tabsNav.classList.add('has-thumb');
      thumbs.push({ tabsNav, thumb });
    }
    const syncThumbs = () => {
      for (const { tabsNav, thumb } of thumbs) {
        const active = tabsNav.querySelector('a[aria-current]');
        if (!active) continue;
        thumb.style.width = `${active.offsetWidth}px`;
        thumb.style.transform = `translate3d(${active.offsetLeft}px,0,0)`;
      }
    };
    window.addEventListener('resize', syncThumbs);
    window.setTimeout(() => {
      syncThumbs();
      if (!reducedMotion) thumbs.forEach(({ thumb }) => thumb.classList.add('is-ready'));
    }, 0);

    const readState = () => {
      const params = new URLSearchParams(window.location.search);
      const requestedScope = params.get('scope') || 'all';
      const requestedYear = params.get('year') || yearControls[0]?.dataset.yearControl;
      return normalizeState({ scope: requestedScope, year: requestedYear });
    };

    const replaceInvalidUrlState = (state) => {
      const url = new URL(window.location.href);
      const hasState = url.searchParams.has('scope') || url.searchParams.has('year');
      if (!hasState) return;
      let changed = false;
      if (scopeControls.length) {
        if (url.searchParams.get('scope') !== state.scope) changed = true;
        url.searchParams.set('scope', state.scope);
      } else if (url.searchParams.has('scope')) {
        url.searchParams.delete('scope');
        changed = true;
      }
      if (url.searchParams.get('year') !== state.year) changed = true;
      url.searchParams.set('year', state.year);
      if (changed) window.history.replaceState({}, '', url);
    };

    const render = ({ scope, year }, announce = false) => {
      let selected;
      const liquid = announce && panelsWrap && !reducedMotion;
      const startHeight = liquid ? panelsWrap.offsetHeight : 0;
      for (const panel of panels) {
        const matches = (panel.dataset.scope || 'all') === scope && panel.dataset.year === year;
        panel.hidden = !matches;
        if (matches) selected = panel;
      }
      for (const control of scopeControls) {
        if (control.dataset.scopeControl === scope) control.setAttribute('aria-current', 'true');
        else control.removeAttribute('aria-current');
        const targetYear = (validYearsByScope.get(control.dataset.scopeControl) || new Set()).has(year)
          ? year
          : firstValidYear(control.dataset.scopeControl);
        const url = new URL(control.href, window.location.href);
        if (targetYear) url.searchParams.set('year', targetYear);
        control.href = `${url.pathname}${url.search}${url.hash}`;
      }
      const validYears = validYearsByScope.get(scope) || new Set();
      for (const control of yearControls) {
        control.hidden = !validYears.has(control.dataset.yearControl);
        if (control.dataset.yearControl === year) control.setAttribute('aria-current', 'true');
        else control.removeAttribute('aria-current');
        const url = new URL(control.href);
        if (scopeControls.length) url.searchParams.set('scope', scope);
        control.href = `${url.pathname}${url.search}${url.hash}`;
      }
      if (status) {
        const scopeName = scopeControls.find((control) => control.dataset.scopeControl === scope)?.textContent.trim();
        if (!announce) status.textContent = '';
        else if (isSpanish) status.textContent = scopeName ? `Mostrando ${scopeName}, ${year}.` : `Mostrando ${year}.`;
        else status.textContent = scopeName ? `Showing ${scopeName}, ${year}.` : `Showing ${year}.`;
      }
      if (liquid) {
        const endHeight = panelsWrap.offsetHeight;
        if (Math.abs(endHeight - startHeight) > 2) {
          panelsWrap.style.height = `${startHeight}px`;
          panelsWrap.classList.add('is-resizing');
          void panelsWrap.offsetHeight;
          panelsWrap.style.height = `${endHeight}px`;
          window.setTimeout(() => {
            panelsWrap.classList.remove('is-resizing');
            panelsWrap.style.height = '';
          }, 300);
        }
      }
      syncThumbs();
      if (announce && selected && !reducedMotion) {
        const parts = [
          selected.querySelector('header'),
          selected.querySelector('.evidence-ledger'),
          selected.querySelector('.evidence-note'),
          selected.querySelector('.evidence-source')
        ].filter(Boolean);
        parts.forEach((part, index) => part.animate(
          [{ transform: 'translate3d(0,12px,0)' }, { transform: 'none' }],
          { duration: 420, delay: index * 55, easing: 'cubic-bezier(.16,1,.3,1)' }));
      }
    };

    const select = (next, push = true) => {
      const current = readState();
      const state = normalizeState({ scope: next.scope || current.scope, year: next.year || current.year });
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
    window.addEventListener('popstate', () => {
      const state = readState();
      replaceInvalidUrlState(state);
      render(state, true);
    });
    archive?.removeAttribute('open');
    const initialState = readState();
    replaceInvalidUrlState(initialState);
    render(initialState);
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
      const threshold = window.innerWidth < 860 ? 116 : 130;
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


  // Continuity experiment (2026-08-10): image continuity for the programs pair only,
  // conditional on instant navigation. Everything else skips; reduced motion skips.
  const VT_DETAIL = /^(\/es)?\/(programs|stories)\/[\w-]+\/$/;
  const VT_PROGRAM_DETAIL = /^(\/es)?\/programs\/[\w-]+\/$/;
  const VT_PROGRAM_INDEX = /^(\/es)?\/programs\/$/;
  const vtAllowed = (fromPath, toPath) =>
    (VT_PROGRAM_INDEX.test(fromPath) && VT_PROGRAM_DETAIL.test(toPath)) ||
    (VT_PROGRAM_DETAIL.test(fromPath) && VT_PROGRAM_INDEX.test(toPath));
  window.addEventListener('pageswap', (event) => {
    if (!event.viewTransition) return;
    let to = null;
    try { to = event.activation?.entry ? new URL(event.activation.entry.url).pathname : null; } catch (e) {}
    if (!to || !vtAllowed(window.location.pathname, to) || reducedMotion) event.viewTransition.skipTransition();
  });
  window.addEventListener('pagereveal', (event) => {
    if (!event.viewTransition) return;
    let from = null;
    try { from = navigation?.activation?.from ? new URL(navigation.activation.from.url).pathname : null; } catch (e) {}
    if (!from || !vtAllowed(from, window.location.pathname) || reducedMotion) event.viewTransition.skipTransition();
  });
  if (/^(\/es)?\/(programs|stories)\/$/.test(window.location.pathname) &&
      HTMLScriptElement.supports && HTMLScriptElement.supports('speculationrules')) {
    const urls = [...new Set([...document.querySelectorAll('a[href]')]
      .map((a) => a.getAttribute('href'))
      .filter((h) => h && VT_DETAIL.test(h)))];
    if (urls.length) {
      const spec = document.createElement('script');
      spec.type = 'speculationrules';
      spec.textContent = JSON.stringify({ prerender: [{ urls, eagerness: 'moderate' }] });
      document.head.appendChild(spec);
    }
  }

  if (reducedMotion) return;

  const reveals = [...document.querySelectorAll('.reveal, .media-reveal, .motion-sequence')];
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
