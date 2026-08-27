#!/usr/bin/env python3
"""PCC static site generator.

Renders site/ from data/content/*.json against the frozen design system.
Run: python3 scripts/build_site.py   Check: python3 scripts/check_site.py
"""
import os
import shutil
from site_components import (ROOT, load, esc, es, head, header, crumb, footer,
                             img_slot, dash, film_cards,
                             cleared_films, withheld_films)

SITE = os.path.join(ROOT, "site")
LOCALE = "en"
NOTICE = load("notice.json")


def _deep_merge(base, overlay):
    out = dict(base)
    for k, v in overlay.items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = _deep_merge(out[k], v)
        else:
            out[k] = v
    return out


def load_locale_data(locale):
    """Return the six content globals for a locale (es overlays merge over en)."""
    site_d = load("site.json")
    programs_d = [dict(p) for p in load("programs.json")["items"]]
    stories_d = [dict(s) for s in load("stories.json")["items"]]
    years_d = [dict(y) for y in load("years.json")["items"]]
    people_d = load("people.json")
    if locale == "es":
        es_site = load("es/site.json")
        site_d = _deep_merge(site_d, {k: v for k, v in es_site.items() if not k.startswith("$")})
        es_prog = load("es/programs.json")["items"]
        for p in programs_d:
            p.update(es_prog.get(p["slug"], {}))
        es_sto = load("es/stories.json")["items"]
        for s in stories_d:
            s.update(es_sto.get(s["slug"], {}))
        es_yr = load("es/years.json")["items"]
        for y in years_d:
            key = f"{y['year']}-{y.get('program', 'organization') if y['scope'] == 'program' else 'organization'}"
            y.update(es_yr.get(key, {}))
        es_people = load("es/people.json")
        people_d = {**people_d}
        for group in ("team", "collaborators", "partnerLeaders"):
            people_d[group] = [dict(m) for m in people_d[group]]
            for m in people_d[group]:
                m["role"] = es_people["roles"].get(m["role"], m["role"])
                if m.get("name") in es_people["bios"]:
                    m["bio"] = es_people["bios"][m["name"]]
    return site_d, programs_d, stories_d, years_d, people_d


site, programs, stories, years, people = load_locale_data("en")
meta = site["meta"]

letters = sorted([s for s in stories if s["type"] == "letter"], key=lambda s: -s["year"])
all_films = [s for s in stories if s["type"] == "film"]
films = cleared_films(all_films)  # consent guardrail: pending/withheld never render
org_years = sorted([y for y in years if y["scope"] == "organization"], key=lambda y: -y["year"])
latest = org_years[0]
PAGES = []
NOINDEX_PAGES = set()


def set_locale(locale):
    """Rebind the content globals for a locale. UI strings translate at write-time."""
    global LOCALE, site, programs, stories, years, people, meta
    global letters, all_films, films, org_years, latest
    LOCALE = locale
    site, programs, stories, years, people = load_locale_data(locale)
    meta = site["meta"]
    letters = sorted([s for s in stories if s["type"] == "letter"], key=lambda s: -s["year"])
    all_films = [s for s in stories if s["type"] == "film"]
    films = cleared_films(all_films)
    org_years = sorted([y for y in years if y["scope"] == "organization"], key=lambda y: -y["year"])
    latest = org_years[0]


import re as _re
_UI_ES = None


def _ui_map():
    global _UI_ES
    if _UI_ES is None:
        pairs = dict(load("es/ui.json")["strings"])
        expanded = {}
        for k, v in pairs.items():
            expanded[k] = v
            k2 = k.replace("'", "&#x27;").replace(" & ", " &amp; ")
            v2 = v.replace("'", "&#x27;").replace(" & ", " &amp; ")
            if k2 != k:
                expanded[k2] = v2
        _UI_ES = sorted(expanded.items(), key=lambda kv: -len(kv[0]))
    return _UI_ES


def localize_html(html, path):
    """es pass: prefix internal links, translate UI strings, swap lang, add toggle target."""
    html = _re.sub(r'(href|action)="/(?!es/)(?!assets/)', lambda m: f'{m.group(1)}="/es/', html)
    html = html.replace('<html lang="en">', '<html lang="es">')
    for en_s, es_s in _ui_map():
        html = html.replace(en_s, es_s)
    return html


def normalize_internal_link_arrows(html):
    """Use a forward arrow for same-site navigation; reserve the northeast arrow for external links."""
    pattern = r'<a\b(?=[^>]*\bhref="(?:/|#))[^>]*>.*?</a>'
    return _re.sub(pattern, lambda match: match.group(0).replace("↗", "→"), html, flags=_re.S)


def write(path, title, description, active, trail, body, indexable=True):
    context = crumb(meta, trail) if trail else ""
    out_path = path if LOCALE == "en" else ("/es" + path)
    head_path = out_path
    full = head(meta, title, description, head_path, noindex=not indexable) + header(meta, active) + context + \
        f'\n<main id="main">{body}\n</main>' + footer(meta, active)
    if LOCALE == "es":
        full = localize_html(full, path)
    # language toggle + hreflang pair (both locales)
    domain = meta["domain"].rstrip("/")
    en_url, es_url = domain + path, domain + "/es" + path
    alt_href = ("/es" + path) if LOCALE == "en" else path
    toggle_lang = "es" if LOCALE == "en" else "en"
    toggle_aria = "Cambiar a español" if LOCALE == "en" else "Cambiar a inglés"
    toggle_label = (
        '<span class="lang-option lang-option--en is-current"><span class="lang-flag" aria-hidden="true">🇺🇸</span> EN</span>'
        '<span class="lang-divider" aria-hidden="true">/</span>'
        '<span class="lang-option lang-option--es"><span class="lang-flag" aria-hidden="true">🇨🇴</span> ES</span>'
        if LOCALE == "en" else
        '<span class="lang-option lang-option--en"><span class="lang-flag" aria-hidden="true">🇺🇸</span> EN</span>'
        '<span class="lang-divider" aria-hidden="true">/</span>'
        '<span class="lang-option lang-option--es is-current"><span class="lang-flag" aria-hidden="true">🇨🇴</span> ES</span>'
    )
    toggle = (f'<a class="lang-toggle" href="{alt_href}" lang="{toggle_lang}" '
              f'aria-label="{toggle_aria}">{toggle_label}</a>')
    full = full.replace('<div class="mobile-header-actions">',
                        f'<div class="mobile-header-actions">{toggle}', 1)
    full = full.replace('<a class="nav-donate"',
                        f'{toggle}<a class="nav-donate"', 1)
    hreflang = (f'<link rel="alternate" hreflang="en" href="{en_url}">\n'
                f'<link rel="alternate" hreflang="es" href="{es_url}">\n'
                f'<link rel="alternate" hreflang="x-default" href="{en_url}">\n')
    full = full.replace("</head>", hreflang + "</head>", 1)
    full = normalize_internal_link_arrows(full)
    full = "\n".join(line.rstrip() for line in full.splitlines()) + "\n"
    out = os.path.join(SITE, out_path.strip("/"), "index.html") if out_path != "/" else os.path.join(SITE, "index.html")
    os.makedirs(os.path.dirname(out), exist_ok=True)
    with open(out, "w") as f:
        f.write(full)
    PAGES.append(out_path)
    if not indexable:
        NOINDEX_PAGES.add(out_path)


def upfirst(s):
    return s[:1].upper() + s[1:] if s else s


def children_label(p):
    label = p["childrenLabel"]
    return label if ("children" in label.lower() or "niño" in label.lower()) else f"{label} children"


def sentence_pair(text):
    parts = text.split(". ", 1)
    if len(parts) != 2:
        return f'<span class="sentence-visual" aria-hidden="true">{esc(text)}</span>'
    return (f'<span class="sentence-visual" aria-hidden="true">{esc(parts[0])}.</span>'
            f'<span class="sentence-visual" aria-hidden="true">{esc(parts[1])}</span>')


def prog_card(p, last=False):
    logo = {
        "alpha-fc": "alpha-logo.png",
        "caminos-nativos": "caminos-logo.jpg",
        "mas-que-vencedores": "mqv-logo.png",
    }[p["slug"]]
    local_name = (
        f'<span lang="es">{esc(p["localName"])}</span> '
        f'<span class="program-card-translation">({esc(p["localNameTranslation"])})</span>'
        if LOCALE == "en" else f'<span lang="es">{esc(p["localName"])}</span>'
    )
    return f"""
      <a class="program-card reveal media-reveal" href="/programs/{p['slug']}/">
        <div class="program-card-media">{img_slot(p['heroImage'], p['heroAlt'], ratio_class=f"vt-{p['slug']}")}</div>
        <div class="program-card-body">
          <img class="program-card-logo" src="/assets/img/{logo}" alt="" loading="lazy" fetchpriority="low">
          <span class="meta meta-dim program-card-meta"><span>{esc(p['place'])}</span><span>{esc(children_label(p))}</span></span>
          <span class="program-card-title">{esc(p['name'])}</span>
          <span class="program-card-local">{local_name}</span>
          <span class="summary program-card-summary">{esc(p['tagline'])}</span>
          <span class="program-card-link" data-dock-collision>Explore <span aria-hidden="true">↗</span></span>
        </div>
      </a>"""


def year_row_link(y):
    return (f'<a class="underlink" href="{esc(y["reportPdf"])}" '
            f'aria-label="Read PCC\'s {y["year"]} report PDF">Read <span aria-hidden="true">↗</span></a>') \
        if y.get("reportPdf") else f'<span>PCC did not share a report for {y["year"]}.</span>'


def context_strip(label, links, local=False, label_href=""):
    class_name = "context-strip context-strip--local" if local else "context-strip"
    data_attr = ' data-local-navigation' if local else ''
    label_markup = f'<span class="context-label">{esc(label)}</span>'
    if local and label_href:
        label_markup = (f'<a class="context-label" href="{esc(label_href)}" '
                        f'aria-label="Back to {esc(label)}">{esc(label)} '
                        f'<span aria-hidden="true">←</span></a>')
    elif local and links and links[0][1].startswith("#"):
        _, overview_href, overview_current = links[0]
        current_attr = ' aria-current="location"' if overview_current else ''
        label_markup = (f'<a class="context-label" href="{esc(overview_href)}"{current_attr} '
                        f'aria-label="Back to {esc(label)} overview">{esc(label)} '
                        f'<span aria-hidden="true">↑</span></a>')
        links = links[1:]
    items = []
    for text, href, current in links:
        current_attr = ' aria-current="location"' if current else ''
        items.append(f'<a href="{esc(href)}"{current_attr}>{esc(text)}</a>')
    return (f'<nav class="{class_name}" aria-label="{esc(label)}"{data_attr}>'
            f'{label_markup}<div>{"".join(items)}</div></nav>')


def continuation_links(label, links):
    items = "".join(
        f'<a href="{esc(href)}"><span>{esc(text)}</span><span aria-hidden="true">↗</span></a>'
        for text, href in links
    )
    return (f'<nav class="continuation-links" aria-label="{esc(label)}" data-dock-occlusion>'
            f'<p>{esc(label)}</p><div>{items}</div></nav>')


def field_gallery(program):
    """A manual, progressively enhanced photo sequence using approved PCC assets."""
    gallery = program.get("gallery", [])
    if not gallery:
        return ""
    slides = "".join(
        f'<figure class="field-gallery-slide" data-gallery-slide>'
        f'<img src="/assets/img/{esc(item["image"])}" alt="{esc(item["alt"])}" '
        f'loading="lazy" decoding="async" width="1600" height="1200">'
        f'</figure>' for item in gallery
    )
    return f"""
  <section class="field-gallery rule-section media-reveal" aria-labelledby="field-gallery-{esc(program['slug'])}" data-field-gallery>
    <header class="field-gallery-header">
      <div><p class="section-kicker">From the program</p><h2 id="field-gallery-{esc(program['slug'])}">In the community</h2></div>
      <div class="field-gallery-controls">
        <p class="field-gallery-status" aria-live="polite"><span data-gallery-current>1</span> / {len(gallery)}</p>
        <button type="button" data-gallery-prev aria-label="Previous photo">←</button>
        <button type="button" data-gallery-next aria-label="Next photo">→</button>
      </div>
    </header>
    <div class="field-gallery-track" data-gallery-track>{slides}</div>
  </section>"""


def evidence_archive(rows, wide=False):
    wide_class = " year-table--wide" if wide else ""
    if wide:
        headings = "<th scope=\"col\">Year</th><th scope=\"col\">Raised</th><th scope=\"col\">Program spend</th><th scope=\"col\">Operating</th><th scope=\"col\">Children</th><th scope=\"col\">Report</th>"
        caption = "Powerful Children Colombia annual figures by year"
    else:
        headings = "<th scope=\"col\">Year</th><th scope=\"col\">Children reached</th><th scope=\"col\">Raised</th><th scope=\"col\">Letter</th><th scope=\"col\">Report</th>"
        caption = "Powerful Children Colombia children reached and funds raised by year, with sources"
    return f"""
    <details class="evidence-archive" open>
      <summary><span>Earlier reports</span><span aria-hidden="true">+</span></summary>
      <div class="year-table-wrap">
        <table class="year-table{wide_class}"><caption>{caption}</caption>
          <thead><tr>{headings}</tr></thead><tbody>{rows}</tbody>
        </table>
      </div>
    </details>"""


def notice_band():
    if not NOTICE.get("enabled"):
        return ""
    n = NOTICE[LOCALE]
    return f"""
  <aside class="notice-band reveal" aria-label="{esc(n['label'])}">
    <p class="notice-label">{esc(n['label'])}</p>
    <p class="notice-body">{esc(n['body'])}</p>
    <a class="btn notice-cta" href="{esc(n['ctaHref'])}" data-dock-collision>{esc(n['cta'])}</a>
  </aside>"""


def home():
    y25 = org_years[0]
    alpha, caminos, mqv = programs
    body = f"""
  <section class="home-hero" aria-labelledby="mission">
    <div class="home-hero-media">
      <div class="frame">{img_slot(site['home']['heroImage'], site['home']['heroAlt'], eager=True)}</div>
      <p class="home-caption meta"><span>Cabrera, Santander</span><span lang="es">Pedalea con Conciencia</span></p>
    </div>
    <div class="home-hero-panel">
      <p class="home-mission">{esc(meta['mission'])}</p>
      <p class="meta home-kicker">Our Partner · Caminos Nativos</p>
      <h1 class="home-display" id="mission">{esc(site['home']['storyTitle'])}</h1>
      <div class="home-deck"><p>{esc(site['home']['storyIntro'])}</p><p>{esc(site['home']['storyBridge'])}</p></div>
      <p class="home-hero-cta">{sentence_pair(site['home']['heroClose'])}</p>
      <div class="home-actions" data-dock-occlusion>
        <a class="btn btn-donate" href="/donate/">Donate</a>
        <a class="action-link" href="/programs/{caminos['slug']}/">See the program <span aria-hidden="true">→</span></a>
      </div>
    </div>
  </section>
{notice_band()}
  <section class="home-proof" id="how-it-works" aria-labelledby="model-h">
    <div class="home-model reveal">
      <h2 id="model-h">{esc(site['home']['howItWorksTitle'])}</h2>
      <div class="home-model-detail">
        <p class="body-text">{es(site['home']['howItWorksBody'])}</p>
        <a class="text-link" href="/programs/#partner-criteria">How partners are chosen <span aria-hidden="true">→</span></a>
      </div>
    </div>
    <section class="home-record reveal" aria-labelledby="evidence-h">
      <p class="meta">Powerful Children Colombia today</p>
      <h2 class="visually-hidden" id="evidence-h">Powerful Children Colombia today</h2>
      <div class="home-metrics">
        <div class="home-metric"><p class="num">{site['home']['currentChildren']}</p><p class="lbl">Children currently served</p></div>
        <div class="home-metric"><p class="num">3</p><p class="lbl">Colombian-led partners</p></div>
      </div>
      <nav class="home-proof-links" aria-label="Explore PCC's work">
        <a href="/programs/"><span>Meet the partners</span><span aria-hidden="true">→</span></a>
        <a href="/transparency/"><span>Read the annual reports</span><span aria-hidden="true">→</span></a>
      </nav>
    </section>
  </section>
  <section class="home-programs" aria-labelledby="programs-h">
    <header class="home-section-head reveal">
      <div><p class="meta meta-dim">Cabrera · Pereira · Santa Marta</p><h2 id="programs-h">Meet our partners.</h2></div>
      <a class="text-link" href="/programs/">All program details <span aria-hidden="true">→</span></a>
    </header>
    <div class="home-program-list">
      <article class="home-program reveal media-reveal">
        <a href="/programs/{caminos['slug']}/">
          <div class="home-program-photo">{img_slot(caminos['featureImage'], caminos['featureAlt'])}</div>
          <div class="home-program-copy">
            <p class="meta meta-dim">{esc(caminos['place'])}</p>
            <h3>{esc(caminos['name'])}</h3>
            <p class="local" lang="es">{esc(caminos['localName'])}</p>
            <p class="program-fact">{esc(caminos['tagline'])}</p>
            <span class="meta program-link" data-dock-collision>Explore <span aria-hidden="true">→</span></span>
          </div>
        </a>
      </article>
      <article class="home-program reveal media-reveal">
        <a href="/programs/{alpha['slug']}/">
          <div class="home-program-photo">{img_slot(alpha['featureImage'], alpha['featureAlt'])}</div>
          <div class="home-program-copy">
            <p class="meta meta-dim">{esc(alpha['place'])}</p>
            <h3>{esc(alpha['name'])}</h3>
            <p class="local" lang="es">{esc(alpha['localName'])}</p>
            <p class="program-fact">{esc(alpha['tagline'])}</p>
            <span class="meta program-link" data-dock-collision>Explore <span aria-hidden="true">→</span></span>
          </div>
        </a>
      </article>
      <article class="home-program reveal media-reveal">
        <a href="/programs/{mqv['slug']}/">
          <div class="home-program-photo">{img_slot(mqv['featureImage'], mqv['featureAlt'])}</div>
          <div class="home-program-copy">
            <p class="meta meta-dim">{esc(mqv['place'])}</p>
            <h3>{esc(mqv['name'])}</h3>
            <p class="local" lang="es">{esc(mqv['localName'])}</p>
            <p class="program-fact">{esc(mqv['tagline'])}</p>
            <span class="meta program-link" data-dock-collision>Explore <span aria-hidden="true">→</span></span>
          </div>
        </a>
      </article>
    </div>
  </section>
  <section class="home-support" aria-labelledby="support">
    <div class="home-support-photo media-reveal">{img_slot('caminos-field-6.webp', 'Pedalea con Conciencia riders gathered with their bicycles on a road near Cabrera')}</div>
    <div class="home-support-copy reveal" data-dock-occlusion>
      <p class="meta">Together in {y25['year']}</p>
      <div class="home-metrics home-metrics--closing" role="group" aria-label="Powerful Children Colombia results in 2025">
        <div class="home-metric"><p class="num">{y25['children']}</p><p class="lbl">Children reached</p></div>
        <div class="home-metric"><p class="num">{y25['raised']}</p><p class="lbl">Funds raised</p></div>
        <div class="home-metric"><p class="num">{y25['programShare']}</p><p class="lbl">Spent directly on programs</p><p class="src">Fiscal year {y25['year']}<br>From the {y25['year']} End of Year Report</p></div>
      </div>
      <p class="home-story">{esc(site['home']['latestQuote'])}</p>
      <div class="home-support-conversion" data-dock-occlusion>
        <h2 class="sentence-pair" id="support"><span class="visually-hidden">{esc(site['home']['supportTitle'])}</span>{sentence_pair(site['home']['supportTitle'])}</h2>
        <div class="home-actions">
          <a class="btn btn-donate" href="/donate/">Donate</a>
          <a class="action-link" href="/stories/{letters[0]['slug']}/">Read the {y25['year']} letter <span aria-hidden="true">→</span></a>
        </div>
        <p class="home-match">{esc(site['home']['employerMatch'])}</p>
      </div>
    </div>
  </section>"""
    write("/", f"{meta['name']} | Colombian-led programs for children",
          "Powerful Children Colombia supports Colombian-led programs for children in Pereira, Cabrera, and Santa Marta.",
          "/", "", body)


def programs_index():
    crits = "".join(f'<li>{es(c)}</li>' for c in site["programsIndex"]["criteria"])
    body = f"""
  <section class="editorial-masthead editorial-masthead--programs rule-section">
    <div class="masthead-copy">
      <p class="eyebrow">Pereira · Cabrera · Santa Marta</p>
      <h1>{esc(site['programsIndex']['title'])}</h1>
      <p class="masthead-deck">{esc(site['programsIndex']['intro'])}</p>
    </div>
    <figure class="masthead-media media-reveal">
      {img_slot('alpha-hero.jpg', 'Alpha FC players and coaches together on a fútbol sala court in Pereira', eager=True)}
      <figcaption class="meta"><span>Pereira, Risaralda</span><span>Alpha FC</span></figcaption>
    </figure>
  </section>
  <section class="program-index rule-section" aria-labelledby="partner-identities-h">
    <header class="section-heading reveal"><div><p class="section-kicker">Colombian-led organizations</p><h2 id="partner-identities-h">Our partners</h2></div></header>
    <div class="program-card-grid">{''.join(prog_card(p, i == len(programs) - 1) for i, p in enumerate(programs))}</div>
  </section>
  <section class="program-artwork rule-section media-reveal" aria-label="Artwork made by children in PCC programs">
    <figure><img src="/assets/img/pcc-child-art.webp" alt="A child's drawing of the Colombian flag colors, mountains, clouds, flowers, and the Powerful Children Colombia logo" loading="lazy" decoding="async" width="1600" height="1205"></figure>
  </section>
  <section class="where-we-work rule-section reveal" aria-labelledby="where-we-work-h">
    <div class="where-we-work-copy">
      <p class="section-kicker">Where we work</p><h2 id="where-we-work-h">Three places. Three locally led programs.</h2>
      <div class="where-we-work-list">
        <a href="/programs/caminos-nativos/" data-program-location="caminos-nativos"><strong>Cabrera, Santander</strong><span>Caminos Nativos</span></a>
        <a href="/programs/alpha-fc/" data-program-location="alpha-fc"><strong>Pereira, Risaralda</strong><span>Alpha FC</span></a>
        <a href="/programs/mas-que-vencedores/" data-program-location="mas-que-vencedores"><strong>Santa Marta, Magdalena</strong><span>Más Que Vencedores</span></a>
      </div>
    </div>
    <figure class="colombia-map" aria-label="Map showing PCC programs in Cabrera, Pereira, and Santa Marta" data-program-map>
      <div class="colombia-map-plot">
        <img src="/assets/img/colombia-map.webp" alt="" loading="lazy" fetchpriority="low" width="500" height="673">
        <span class="map-pin map-pin--santa" data-map-pin="mas-que-vencedores"><i aria-hidden="true"></i><b>Santa Marta</b></span>
        <span class="map-pin map-pin--cabrera" data-map-pin="caminos-nativos"><i aria-hidden="true"></i><b>Cabrera</b></span>
        <span class="map-pin map-pin--pereira" data-map-pin="alpha-fc"><i aria-hidden="true"></i><b>Pereira</b></span>
      </div>
      <figcaption>Map outline by Axel pardo1, Wikimedia Commons, CC BY-SA 4.0</figcaption>
    </figure>
  </section>
  <section class="editorial-section editorial-section--prose rule-section reveal" aria-labelledby="crit-h" id="partner-criteria">
    <header class="section-label"><p class="section-kicker">Partnership</p><h2 id="crit-h">How partners are chosen</h2></header>
    <div class="editorial-prose">
      <details class="criteria-disclosure" open>
        <summary><span>Read the partnership criteria</span><span aria-hidden="true">+</span></summary>
        <div class="criteria-content">
          <p class="body-text">{esc(site['programsIndex']['criteriaIntro'])}</p>
          <ul class="body-text criteria-list">{crits}</ul>
          <p class="body-text criteria-outro">{esc(site['programsIndex']['criteriaOutro'])}</p>
          <p class="body-text criteria-contact">{esc(site['programsIndex']['criteriaContact'])}</p>
        </div>
      </details>
    </div>
  </section>"""
    write("/programs/", f"Programs | {meta['name']}",
          "Powerful Children Colombia partners with Colombian-led organizations in Pereira, Cabrera, and Santa Marta.", "/programs/",
          "", body)


def program_pages():
    for p in programs:
        pfilms = [f for f in films if f.get("program") == p["slug"]]
        pyears = [y for y in years if y.get("program") == p["slug"]]
        leaders = [pl for pl in people["partnerLeaders"] if pl["program"] == p["slug"]]
        org_name = {
            "alpha-fc": "Alpha FC",
            "caminos-nativos": "Fundación Caminos Nativos",
            "mas-que-vencedores": "Fundación Más Que Vencedores",
        }[p["slug"]]
        nl = "".join(f"<p>{es(t)}</p>" for t in p["narrativeLeft"])
        nr = "".join(f"<p>{es(t)}</p>" for t in p["narrativeRight"])
        leaders_html = "".join(f'<span>{esc(l["name"])}</span>' for l in leaders)
        communities_html = "".join(f'<span>{esc(c)}</span>' for c in p["communities"])
        target = p.get("pilotTarget")
        caminos_2025_result = ("Two of Pedalea con Conciencia's original riders are now competing at a higher level "
                                "and mentoring younger riders. Caminos Nativos also introduced mental health workshops for parents.")
        if p["slug"] == "alpha-fc":
            results = """
          <div class="ledger-item"><dt>Children currently reached</dt><dd>Close to 200</dd>
            <p>Across five communities. From PCC's Alpha FC program page.</p></div>
          <div class="ledger-item"><dt>Participant retention</dt><dd>More than 80%</dd>
            <p>From PCC's Alpha FC program page.</p></div>"""
        elif target:
            results = f"""
          <div class="ledger-item"><dt>Children currently reached</dt><dd>{esc(p['childrenLabel'])}</dd>
            <p>Across five public schools in Santa Marta. From Powerful Children Colombia, July 2026.</p></div>"""
        elif p["slug"] == "caminos-nativos":
            historic_results = "".join(f"""
          <div class="ledger-item"><dt>Children at launch</dt><dd>{dash(y['children'], 'Children at launch', y['year'])}</dd>
            <p>{esc(y['source'])}</p></div>""" for y in pyears)
            results = f"""
          <div class="program-results-history">
            <article class="program-result-current">
              <p class="section-kicker">Current program reach</p>
              <p class="program-result-count"><strong>{esc(p['childrenLabel'])}</strong></p>
              <div class="program-result-report">
                <p class="section-kicker">From the 2025 Year in Review</p>
                <p>{esc(caminos_2025_result)}</p>
              </div>
            </article>
            <div class="program-result-prior">
              <p class="section-kicker">Earlier published result · 2022</p>
              <dl class="evidence-ledger evidence-ledger--single">{historic_results}</dl>
            </div>
          </div>"""
        else:
            results = "".join(f"""
          <div class="ledger-item"><dt>Children · {esc(y['year'])}</dt><dd>{dash(y['children'], 'Children reached', y['year'])}</dd>
            <p>{esc(y['source'])}</p></div>""" for y in pyears)
        results_block = (results if p["slug"] == "caminos-nativos" else
                         f'<dl class="evidence-ledger">{results}</dl>' if results else
                         f'<div class="program-evidence-note"><p>PCC\'s annual reports share results for PCC as a whole. They do not list a separate yearly total for {esc(p["name"])}.</p></div>')
        program_context = [('Overview', '#overview', True), ('Story', '#story', False)]
        if pfilms:
            program_context.append(('Films', '#films', False))
        if p["slug"] != "mas-que-vencedores":
            program_context.append(('Impact', '#impact', False))
        films_html = f"""
  <section class="media-section rule-section" id="films" aria-labelledby="films-h">
    <header class="section-heading"><div><p class="section-kicker">From the program</p><h2 id="films-h">Films</h2></div><span>{len(pfilms)} on YouTube</span></header>
    <div class="film-grid film-grid--{len(pfilms)}">{film_cards(pfilms, border_last=False)}</div>
  </section>""" if pfilms else ""
        field_video = p.get("fieldVideo")
        field_video_html = ""
        if field_video:
            en_default = " default" if LOCALE == "en" else ""
            es_default = " default" if LOCALE == "es" else ""
            field_video_html = f"""
  <section class="program-field-film rule-section" aria-labelledby="field-film-h" data-dock-occlusion>
    <div class="program-field-film-copy reveal">
      <p class="section-kicker" lang="es">Pedalea con Conciencia</p>
      <h2 id="field-film-h">{esc(field_video['place'])}</h2>
      <p class="program-field-film-date">{esc(field_video['date'])}</p>
      <p class="program-field-film-details">{esc(field_video['duration'])}<br>{esc(field_video['audioLabel'])} · {esc(field_video['captionLabel'])}</p>
    </div>
    <div class="program-field-film-media media-reveal">
      <video controls playsinline preload="none" poster="/assets/img/{esc(field_video['poster'])}"
             aria-label="{esc(field_video['ariaLabel'])}" width="720" height="1280">
        <source src="/assets/video/{esc(field_video['source'])}" type="video/mp4">
        <track kind="captions" srclang="en" label="English" src="/assets/video/caminos-cabrera-august-2026.en.vtt"{en_default}>
        <track kind="captions" srclang="es" label="Español" src="/assets/video/caminos-cabrera-august-2026.es.vtt"{es_default}>
      </video>
    </div>
  </section>"""
        impact_section = "" if p["slug"] == "mas-que-vencedores" else f"""
  <section class="program-evidence rule-section" id="impact">
    <header class="section-heading reveal"><div><p class="section-kicker">From PCC's reports</p><h2>Annual results</h2></div>
      <a class="text-link" href="/impact/">See PCC's impact <span aria-hidden="true">↗</span></a></header>
    <div class="program-evidence-grid">{results_block}<nav class="document-list" aria-label="Reports and related pages">
      {''.join(f'<a href="/stories/{l["slug"]}/"><span>{esc(l["title"])}</span><span>Read the letter ↗</span></a>' for l in letters[:2])}
      <a href="/transparency/"><span>Annual reports</span><span>Read the reports ↗</span></a><a href="/donate/"><span>Support this work</span><span>Donate ↗</span></a>
    </nav></div>
  </section>"""
        body = f"""
  {context_strip(p['name'], program_context, local=True)}
  <section class="detail-masthead rule-section" id="overview">
    <div class="detail-masthead-copy reveal">
      <p class="eyebrow">{esc(p['place'])} · {esc(p['launchLabel'])}</p><h1>{esc(p['name'])}</h1>
      <p class="local-name" lang="es">{esc(p['localName'])}</p><p class="masthead-deck">{es(p['summary'])}</p>
      <div class="masthead-actions"><a class="btn btn-donate" href="/donate/">Support this work</a><a class="text-link" href="/programs/">All programs <span aria-hidden="true">↗</span></a></div>
    </div>
    <figure class="detail-masthead-media media-reveal">{img_slot(p['heroImage'], p['heroAlt'], ratio_class=f"vt-{p['slug']}", eager=True)}<figcaption class="meta"><span>{esc(p['place'])}</span><span>{esc(p['discipline'])}</span></figcaption></figure>
  </section>
  <dl class="fact-grid rule-section">
    <div><dt>Location</dt><dd>{esc(p['place'])}</dd></div><div><dt>Program</dt><dd>{esc(p['launchLabel'])}</dd></div>
    <div><dt>Children</dt><dd>{esc(p['childrenLabel'])}</dd></div><div><dt>Discipline</dt><dd>{esc(p['discipline'])}</dd></div>
  </dl>
  <section class="program-story rule-section" id="story">
    <article class="program-narrative reveal"><p class="section-kicker">About the program</p><h2>{esc(p['narrativeTitle'])}</h2><div class="two-col"><div>{nl}</div><div>{nr}</div></div></article>
    <aside class="program-record reveal" aria-label="Program details">
      <div><span>Organization</span><strong>{esc(org_name)}</strong></div><div><span>Leaders</span><strong>{leaders_html}</strong></div>
      <div><span>{'Schools' if p['slug'] == 'mas-que-vencedores' else 'Communities'}</span><strong>{communities_html}</strong></div><div><span>How PCC helps</span><strong>{esc(p['pccRole'])}</strong></div>
      <div><span>Funding</span><strong>{esc(p['funding'])}</strong></div>
    </aside>
  </section>
  <section class="program-documentary{' program-documentary--paired' if p.get('featureCompanionImage') else ''} media-reveal" aria-label="{esc(p['name'])} in the community">
    <div class="frame program-documentary-primary">{img_slot(p['featureImage'], p['featureAlt'])}</div>
    {f'''<div class="frame program-documentary-companion">{img_slot(p['featureCompanionImage'], p['featureCompanionAlt'])}</div>''' if p.get('featureCompanionImage') else ''}
    <p class="h2-caption meta meta-dim"><span>{esc(p['place'])}</span><span>{esc(p['name'])}</span></p>
  </section>{field_video_html}{field_gallery(p)}{films_html}{impact_section}"""
        desc = p["summary"] if len(p["summary"]) <= 168 else p["summary"][:165].rsplit(" ", 1)[0] + "…"
        write(f"/programs/{p['slug']}/", f"{p['name']} · {p['localName']} | {meta['name']}",
              desc, "/programs/", "", body)


def impact():
    caminos_2022 = next(y for y in years if y.get("program") == "caminos-nativos")
    # A scope belongs in this explorer only when PCC has published at least one
    # figure for it in the reporting period. MQV launched after these reports,
    # so it remains on the Programs page rather than appearing as an empty tab.
    scope_options = [("all", "All PCC"), ("alpha-fc", "Alpha FC"),
                     ("caminos-nativos", "Caminos Nativos")]
    panels = []
    scope_paths = {p["slug"]: f'/programs/{p["slug"]}/' for p in programs}
    for scope, label in scope_options:
        for y in org_years:
            children_label = "Children reached"
            if scope == "all":
                children, raised, source = y["children"], y["raised"], y["source"]
                note = ""
            elif scope == "caminos-nativos" and y["year"] == 2022:
                children, raised, source = caminos_2022["children"], "", caminos_2022["source"]
                note = ""
            elif scope == "alpha-fc" and y["year"] == 2025:
                children, raised, source = "Close to 200", "", "2025 Year in Review and current program pages"
                children_label = "Current program reach"
                note = ("Families from five communities came together for Alpha FC's family event for the second time. "
                        "Alpha FC also introduced a dedicated initiative for participants ages 15 to 17.")
            elif scope == "caminos-nativos" and y["year"] == 2025:
                children, raised, source = "35", "", "2025 Year in Review and current program pages"
                children_label = "Current program reach"
                note = ("Two of Pedalea con Conciencia's original riders are now competing at a higher level and mentoring younger riders. "
                        "Caminos Nativos also introduced mental health workshops for parents.")
            else:
                continue
            hidden = "" if scope == "all" and y["year"] == latest["year"] else " hidden"
            report = (f'<a class="text-link" href="{esc(y["reportPdf"])}">Read the {y["year"]} report <span aria-hidden="true">↗</span></a>'
                      if y.get("reportPdf") else "")
            program_link = (f'<a class="text-link" href="{scope_paths[scope]}">About {esc(label)} <span aria-hidden="true">↗</span></a>'
                            if scope in scope_paths else "")
            metrics = []
            if children:
                metrics.append(f'<div class="ledger-item"><dt>{esc(children_label)}</dt><dd>{esc(children)}</dd></div>')
            if raised:
                metrics.append(f'<div class="ledger-item"><dt>Funds raised</dt><dd>{esc(raised)}</dd></div>')
            if scope == "all" and y.get("programShare"):
                metrics.append(f'<div class="ledger-item"><dt>Spent directly on programs</dt><dd>{esc(y["programShare"])}</dd></div>')
            ledger = (f'<dl class="evidence-ledger{" evidence-ledger--single" if len(metrics) == 1 else ""}">'
                      f'{"".join(metrics)}</dl>') if metrics else ""
            note_markup = f'<p class="evidence-note">{esc(note)}</p>' if note else ""
            provenance = f"From PCC's {source}."
            panels.append(f"""
      <article class="evidence-panel" data-evidence-panel data-scope="{scope}" data-year="{y['year']}"{hidden}>
        <header><div><p class="eyebrow">{label} · Year in Review</p><h2>{y['year']}</h2></div><span class="evidence-period">January to December</span></header>
        {ledger}{note_markup}
        <div class="evidence-source evidence-source--simple"><p>{esc(provenance)}</p><div class="evidence-actions">{program_link}{report}</div></div>
      </article>""")
    scope_links = "".join(
        f'<a href="?scope={scope}&amp;year={latest["year"]}#evidence" data-scope-control="{scope}"'
        + (' aria-current="true"' if scope == "all" else '') + f'>{label}</a>'
        for scope, label in scope_options)
    year_links = "".join(
        f'<a href="?scope=all&amp;year={y["year"]}#evidence" data-year-control="{y["year"]}"'
        + (' aria-current="true"' if y["year"] == latest["year"] else '') + f'>{y["year"]}</a>'
        for y in org_years)
    fallback_panels = "".join(panels).replace(" hidden", "")
    body = f"""
  <section class="editorial-masthead editorial-masthead--impact rule-section">
    <div class="masthead-copy reveal"><p class="eyebrow">2022 to 2025</p><h1>We've watched the children in these programs grow alongside PCC.</h1>
      <p class="masthead-deck">Younger siblings are joining. Graduating participants are staying on as volunteers. Families are forming networks of support and care.</p></div>
    <figure class="masthead-media media-reveal">{img_slot('recap-2025.jpg', 'Children and local leaders during PCC program activities in 2025', eager=True)}<figcaption class="meta"><span>2025</span><span>{latest['children']} children reached</span></figcaption></figure>
  </section>
  <section class="evidence-explorer rule-section" id="evidence" data-evidence-explorer>
    <header class="explorer-heading reveal"><div><p class="section-kicker">Annual reports</p><h2>Impact by program and year</h2></div></header>
    <div class="explorer-controls reveal" data-dock-occlusion><nav class="scope-tabs" aria-label="Impact scope">{scope_links}</nav><nav class="year-tabs" aria-label="Impact year">{year_links}</nav></div>
    <p class="visually-hidden" aria-live="polite" data-explorer-status></p>
    <div class="evidence-panels">{''.join(panels)}</div>
    <noscript><div class="evidence-panels evidence-panels--fallback">{fallback_panels}</div></noscript>
  </section>
  <section class="editorial-section editorial-section--narrative rule-section">
    <header class="section-label"><p class="eyebrow">2025 Year in Review</p><h2>Of course, numbers tell only part of the story.</h2></header>
    <div class="editorial-prose reveal"><p class="body-text">{es(letters[0]['body'][3].split('. ', 1)[1])}</p></div>
  </section>
  {continuation_links('Meet the programs', [('Alpha FC', '/programs/alpha-fc/#impact'), ('Caminos Nativos', '/programs/caminos-nativos/#impact'), ('Más Que Vencedores', '/programs/mas-que-vencedores/#impact'), ('Annual reports', '/transparency/')])}"""
    write("/impact/", f"Impact | {meta['name']}",
          "Children reached and funds raised, from Powerful Children Colombia's annual reports.",
          "/impact/", "", body)


def transparency():
    panel_list = []
    for y in org_years:
        metric_values = [
            ("Funds raised", y.get("transparencyRaised", y["raised"])),
            ("Children reached", y.get("transparencyChildren", y["children"])),
            ("Spent on programs", y.get("programSpend")),
            ("Administration", y.get("operating")),
            ("Share spent on programs", y.get("programShare")),
        ]
        metrics = [f'<div class="ledger-item"><dt>{esc(label)}</dt><dd>{esc(value)}</dd></div>'
                   for label, value in metric_values if value]
        ledger_class = "evidence-ledger evidence-ledger--single" if len(metrics) == 1 else "evidence-ledger"
        panel_list.append(f"""
      <article class="evidence-panel" data-evidence-panel data-year="{y['year']}"{' ' if y['year'] == latest['year'] else ' hidden'}>
        <header><div><p class="eyebrow">Powerful Children Colombia · Year in Review</p><h2>{y['year']}</h2></div><span class="evidence-period">January to December</span></header>
        <dl class="{ledger_class}">{''.join(metrics)}</dl>
        <div class="evidence-source evidence-source--simple evidence-source--actions">
          <div class="evidence-actions"><a class="text-link" href="/programs/">Programs behind these results <span aria-hidden="true">↗</span></a>
          <a class="text-link" href="{esc(y['reportPdf'])}">Read the {y['year']} report <span aria-hidden="true">↗</span></a></div></div>
      </article>""")
    panels = "".join(panel_list)
    fallback_panels = panels.replace(" hidden", "")
    year_links = "".join(
        f'<a href="?year={y["year"]}#evidence" data-year-control="{y["year"]}"'
        + (' aria-current="true"' if y["year"] == latest["year"] else '') + f'>{y["year"]}</a>'
        for y in org_years)
    docs = "".join(
        f'<a href="{esc(y["reportPdf"])}" aria-label="Read {esc(y["reportLabel"])} PDF"><span>{esc(y["reportLabel"])}</span><span>Read ↗</span></a>'
        for y in org_years) + \
        f'<a href="{esc(meta["privacyPdf"])}" aria-label="Read Privacy Policy PDF"><span>Privacy Policy</span><span>Read ↗</span></a>'
    body = f"""
  <section class="editorial-masthead editorial-masthead--transparency rule-section">
    <div class="masthead-copy reveal"><p class="eyebrow">2022 to 2025</p><h1>Annual reports</h1>
      <p class="masthead-deck">Your trust, partnership and belief in Powerful Children Colombia is important to us.</p></div>
    <figure class="masthead-media media-reveal">{img_slot('recap-2025.jpg', 'Children and leaders taking part in PCC partner programs in 2025', eager=True)}<figcaption class="meta"><span>501(c)(3)</span><span>Reports · 2022 to 2025</span></figcaption></figure>
  </section>
  <section class="transparency-context rule-section reveal">
    <header><p class="section-kicker">Our growth</p><h2>Growing Together, Growing Responsibly</h2></header>
    <div class="transparency-context-copy">
      <p>In 2022, our first program reached 21 children in Cabrera, Santander. In 2026, we're serving 335 children across Colombia, a story of trust, partnership, and community leaders who never stop innovating for their kids.</p>
      <p>Growth means nothing without responsibility. That's why we track not just how much we raise, but how well we spend it. In our first year, 80 cents of every dollar went directly to programs on the ground. Today, that number is 98 cents: the result of years spent building smarter systems, deepening our partnerships, and holding ourselves accountable to you, our <span lang="es">familia poderosa</span>.</p>
      <p>You may also notice our cash reserves have grown alongside our fundraising. That's intentional. As a young nonprofit, we hold funds in reserve so we can commit to multi-year programs with confidence and invest quickly when the right new partner emerges, rather than overcommit and put an existing program at risk.</p>
      <p>These numbers are children learning to play and ride, families finding community, and leaders in Colombia turning belief into action. Thank you for holding us to a standard of transparency every step of the way!</p>
    </div>
  </section>
  <section class="evidence-explorer rule-section" id="evidence" data-evidence-explorer>
    <header class="explorer-heading reveal"><div><p class="section-kicker">From PCC</p><h2>Reports by year</h2></div></header>
    <p class="explorer-note reveal">Read PCC's reports from 2022 to 2025 below. Numbers are rounded for simplicity.</p>
    <div class="explorer-controls reveal" data-dock-occlusion><nav class="year-tabs" aria-label="Financial year">{year_links}</nav></div>
    <p class="visually-hidden" aria-live="polite" data-explorer-status></p><div class="evidence-panels">{panels}</div>
    <noscript><div class="evidence-panels evidence-panels--fallback">{fallback_panels}</div></noscript>
  </section>
  <section class="editorial-section editorial-section--prose rule-section reveal"><header class="section-label"><p class="section-kicker">Reporting</p><h2>How PCC reports</h2></header>
    <div class="editorial-prose"><p class="body-text">Partner organizations report to us regularly on progress toward program objectives and on every dollar spent, with receipts and rationale against the original forecast. We reconcile actuals against forecasts on an ongoing basis and release additional funds only once objectives are met and spending matches what was agreed. The annual reports provide a high-level summary of actual spend.</p></div>
  </section>
  <section class="document-section rule-section reveal"><header class="section-label"><p class="section-kicker">From PCC</p><h2>Reports and policies</h2></header><nav class="document-list" aria-label="PCC reports and policies">{docs}</nav></section>
  {continuation_links('Meet the programs', [('Alpha FC', '/programs/alpha-fc/'), ('Caminos Nativos', '/programs/caminos-nativos/'), ('Más Que Vencedores', '/programs/mas-que-vencedores/'), ('Impact', '/impact/')])}"""
    write("/transparency/", f"Transparency | {meta['name']}",
          "Read Powerful Children Colombia's annual reports from 2022 to 2025.",
          "/transparency/", "", body)


def stories_index():
    lead = letters[0]
    lead_film = films[0]
    lrows = "".join(
        f'<a href="/stories/{l["slug"]}/"><span><strong>{l["year"]}</strong>{esc(l["title"])}'
        + (f': {esc(l["theme"])}' if l["theme"] else '')
        + '</span><span>Read ↗</span></a>' for l in letters)
    body = f"""
  <section class="editorial-masthead editorial-masthead--stories rule-section">
    <div class="masthead-copy reveal"><p class="section-kicker">Stories &amp; films</p><h1>In their own words.</h1>
      <p class="masthead-deck">Read letters from the PCC team and watch films from the people leading the programs.</p>
      <a class="stories-lead-letter" href="/stories/{lead['slug']}/"><span class="eyebrow">Latest letter · {lead['year']}</span><strong>{esc(lead['title'])}</strong><span>{es(lead['summary'])}</span><b>Read the letter <span aria-hidden="true">↗</span></b></a>
    </div>
    <figure class="masthead-media media-reveal"><a href="{esc(lead_film['videoUrl'])}">{img_slot(lead_film['still'], lead_film['stillAlt'], eager=True)}</a>
      <figcaption class="meta"><span>{esc(lead_film['meta'])}</span><span>Watch film ↗</span></figcaption></figure>
  </section>
  <section class="media-section rule-section" aria-labelledby="films-index-h"><header class="section-heading reveal"><div><p class="section-kicker">From the programs</p><h2 id="films-index-h">Films</h2></div><span>{len(films) - 1} more films · YouTube</span></header>
    <div class="film-grid film-grid--stories film-grid--{len(films) - 1}">{film_cards(films[1:], border_last=False)}</div></section>
  <section class="document-section rule-section reveal"><header class="section-label"><p class="section-kicker">From the PCC team</p><h2>Letters</h2></header><nav class="document-list" aria-label="Year in review letters">{lrows}</nav></section>"""
    write("/stories/", f"Stories & Films | {meta['name']}",
          "Letters from the team and films made with Powerful Children Colombia programs.",
          "/stories/", "", body)


def story_pages():
    for l in letters:
        y = next((x for x in org_years if x["year"] == l["year"]), None)
        paras = []
        for p in l["body"]:
            if "|" in p:
                paras.append("<p>" + "<br>".join(es(x) for x in p.split("|")) + "</p>")
            else:
                paras.append(f"<p>{es(p)}</p>")
        facts = [("Year", l["year"])]
        if y:
            if y["children"]:
                facts.append(("Children", y["children"]))
            if y["raised"]:
                facts.append(("Raised", y["raised"]))
        fact_html = "".join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in facts)
        report_link = (f'<a class="text-link" href="{esc(y["reportPdf"])}">Read the full report <span aria-hidden="true">↗</span></a>'
                       if y and y.get("reportPdf") else "")
        graph_figs = []
        if y and y.get("children"):
            graph_figs.append(("Children reached", y["children"]))
        if y and y.get("raised"):
            graph_figs.append(("Funds raised", y["raised"]))
        figures_html = "".join(f'<div><dt>{esc(k)}</dt><dd>{esc(v)}</dd></div>' for k, v in graph_figs)
        body = f"""
  {context_strip('All stories', [('Overview', '#overview', True), ('Letter', '#letter', False), ('Impact', f'/impact/?year={l["year"]}#evidence', False), ('Support', '/donate/', False)], local=True, label_href='/stories/')}
  <section class="detail-masthead story-detail-masthead rule-section" id="overview">
    <div class="detail-masthead-copy reveal"><p class="eyebrow">Letter · {l['year']}</p><h1>{esc(l['title'])}</h1>
      {f'<p class="local-name">{esc(l["theme"])}</p>' if l['theme'] else ''}<p class="masthead-deck">{es(l['summary'])}</p>
      <div class="masthead-actions">{report_link}<a class="text-link" href="/transparency/?year={l['year']}#evidence">{l['year']} financial information <span aria-hidden="true">↗</span></a></div>
    </div>
    <figure class="detail-masthead-media media-reveal">{img_slot(l['heroImage'], l['heroAlt'] or ('Photography from ' + str(l['year'])), eager=True)}<figcaption class="meta"><span>Year in Review</span><span>{l['year']}</span></figcaption></figure>
  </section>
  <dl class="fact-grid rule-section story-facts">{fact_html}</dl>
  <section class="letter-layout rule-section" id="letter"><aside aria-label="About this letter"><p class="section-kicker">Selected passages</p><p>{l['year']} Year in Review</p>{report_link}</aside>
    <article class="letter-body reveal">{''.join(paras)}</article></section>
  <aside class="graph-context rule-section reveal" aria-label="PCC in {l['year']}">
    <p class="eyebrow">{l['year']} at a glance</p>
    <dl class="graph-figures">{figures_html}</dl>
    <div class="graph-actions"><a class="text-link" href="/impact/?scope=all&amp;year={l['year']}#evidence">Impact · {l['year']} <span aria-hidden="true">↗</span></a>
      <a class="text-link" href="/transparency/?year={l['year']}#evidence">Financial information · {l['year']} <span aria-hidden="true">↗</span></a>
      {report_link}</div>
  </aside>
  {continuation_links('Keep reading', [('All stories', '/stories/'), (f'Impact {l["year"]}', f'/impact/?year={l["year"]}#evidence'), ('Donate', '/donate/')])}"""
        write(f"/stories/{l['slug']}/", f"{l['title']} | {meta['name']}", l["summary"],
              "/stories/", "", body)


def about():
    vals = "".join(f"""<article class="value-item"><h3>{esc(v['name'])}</h3><p>{esc(v['body'])}</p></article>"""
                   for v in site["values"])
    team = "".join(f"""
      <article class="person">
        <div class="portrait img-slot has-img"><img src="/assets/img/{esc(t['portrait'])}" alt="Portrait of {esc(t['name'])}" loading="lazy"></div>
        <div class="person-heading"><h3>{esc(t['name'])}</h3><p>{esc(t['role'])}</p></div>
        <details class="person-bio"><summary><span>Biography</span><span aria-hidden="true">+</span></summary><p>{esc(t['bio'])}</p></details>
      </article>""" for t in people["team"])
    partner_rows = []
    for p in site["partners"]:
        tag, href, close = ("a", f' href="{esc(p["href"])}"', "a") if p["href"] else ("div", "", "div")
        place = f' · {esc(p["place"])}' if p["place"] else ""
        partner_rows.append(f'<{tag}{href}><span><strong>{esc(p["name"])}</strong><span class="partner-relationship">{esc(p["relationship"])}</span></span><span>{esc(p["type"])}{place}{" ↗" if p["href"] else ""}</span></{close}>')
    collaborator_roles_es = {
        "English Teacher": "Profesor de inglés",
        "Technology Advisory": "Asesoría tecnológica",
        "Ambassador": "Embajadora",
        "Webmaster": "Administrador web",
        "Digital Strategy": "Estrategia digital",
        "Logo design": "Diseño del logo",
    }
    collaborator_rows = "".join(
        f'<div><span><strong>{esc(c["name"])}</strong><span class="partner-relationship">'
        f'{esc(collaborator_roles_es.get(c["role"], c["role"]) if LOCALE == "es" else c["role"])}</span></span>'
        f'<span>{"Colaborador" if LOCALE == "es" else "Collaborator"}</span></div>'
        for c in people["collaborators"]
    )
    partners = "".join(partner_rows) + collaborator_rows
    body = f"""
  <section class="editorial-masthead editorial-masthead--about rule-section">
    <div class="masthead-copy reveal"><p class="eyebrow">About PCC</p><h1>{esc(meta['mission'])}</h1><p class="masthead-deck">{esc(site['focus'][0])}</p></div>
    <figure class="masthead-media media-reveal">{img_slot('team-community.jpg', 'PCC and Caminos Nativos leaders meeting with children in the community', eager=True)}<figcaption class="meta"><span>Colombian-led</span><span>Since 2022</span></figcaption></figure>
  </section>
  <section class="editorial-section editorial-section--prose rule-section">
    <header class="section-label"><p class="section-kicker">Why PCC exists</p><h2>Our focus and origins</h2></header>
    <div class="editorial-prose reveal"><div class="two-col">
      <div>{''.join(f'<p>{esc(t)}</p>' for t in site['origins'][:2])}</div>
      <div>{''.join(f'<p>{esc(t)}</p>' for t in site['origins'][2:])}</div>
    </div></div>
  </section>
  <section class="values-section rule-section reveal"><header class="section-heading"><div><p class="section-kicker">How PCC works</p><h2>Our values</h2></div></header><div class="values-grid">{vals}</div></section>
  <section class="team-section rule-section reveal"><header class="section-heading"><div><p class="section-kicker">People</p><h2>Our team</h2></div></header>
    <div class="team-directory">{team}</div></section>
  <section class="document-section rule-section reveal"><header class="section-label"><p class="section-kicker">Network</p><h2>Our partners and collaborators</h2></header><div class="document-list partner-list">{partners}</div></section>
  {continuation_links('Keep exploring', [('Programs', '/programs/'), ('Annual reports', '/transparency/'), ('Contact PCC', f'mailto:{meta["email"]}')])}"""
    write("/about/", f"About | {meta['name']}",
          "Who PCC is: focus, origins, values, the team, and the Colombian organizations it partners with.",
          "/about/", "", body)


def donate():
    methods = "".join(f"""
      <article class="method-item"><h3>{esc(m['name'])}</h3><p>{esc(m['detail'])}</p></article>"""
        for m in site["donate"]["methods"])
    body = f"""
  <section class="donate-hero rule-section">
    <div class="donate-copy reveal"><p class="section-kicker">Donate</p><h1>{esc(site['donate']['title'])}</h1>
      <p class="donate-intro">{esc(site['donate']['intro'])}</p>
      <div class="masthead-actions"><a class="btn btn-donate" href="{esc(meta['donorboxUrl'])}">Donate on Donorbox</a><a class="text-link" href="/transparency/">Read the annual reports <span aria-hidden="true">↗</span></a></div>
      <dl class="donate-trust"><div><dt>{latest['raised']}</dt><dd>Raised in {latest['year']}</dd></div><div><dt>{site['home']['currentChildren']}</dt><dd>Children currently served</dd></div><div><dt>501(c)(3)</dt><dd>EIN 87-3057220</dd></div></dl>
    </div>
    <div class="donate-form reveal" id="donation-form"><div class="donate-form-heading"><p class="section-kicker">Donation form</p><p>Processed securely by Donorbox</p></div>
      <script type="module" src="https://donorbox.org/widgets.js" async></script>
      <div class="donorbox-frame"><dbox-widget campaign="{esc(meta['donorboxCampaign'])}" type="donation_form" enable-auto-scroll="true"></dbox-widget></div>
      <p class="form-fallback">If the form does not load, <a class="underlink" href="{esc(meta['donorboxUrl'])}">donate directly on Donorbox</a>.</p>
    </div>
  </section>
  <section class="methods-section rule-section reveal"><header class="section-label"><p class="section-kicker">Donate</p><h2>Other ways to donate</h2></header><div class="methods-grid">{methods}</div>
    <p class="certification">{esc(site['donate']['certification'])}</p></section>
  <section class="document-section rule-section reveal"><header class="section-label"><p class="section-kicker">Beyond a gift</p><h2>Other ways to help</h2></header><nav class="document-list" aria-label="Other ways to support PCC">
    <a href="mailto:{esc(meta['email'])}?subject=Learn%20more%20about%20PCC"><span>Learn more about PCC</span><span>Write to us ↗</span></a>
    <a href="mailto:{esc(meta['email'])}?subject=Volunteer%20with%20PCC"><span>Volunteer</span><span>Write to us ↗</span></a>
    <a href="mailto:{esc(meta['email'])}?subject=Recommend%20a%20Colombian-led%20nonprofit"><span>Recommend a Colombian-led nonprofit</span><span>Write to us ↗</span></a>
    <a href="mailto:{esc(meta['email'])}?subject=Feedback%20for%20PCC"><span>Share feedback</span><span>Write to us ↗</span></a>
  </nav></section>"""
    write("/donate/", f"Donate | {meta['name']}",
          f"{site['donate']['title']} {site['donate']['certification']}", "/donate/",
          "", body)


def earthquake_relief():
    n = NOTICE[LOCALE]
    kicker = "Earthquake relief" if LOCALE == "en" else "Respuesta al terremoto"
    form_label = "Emergency donation form" if LOCALE == "en" else "Formulario para la emergencia"
    regular_label = "Make a general donation" if LOCALE == "en" else "Haz una donación general"
    relief_donate_label = "Donate to earthquake relief" if LOCALE == "en" else "Dona para esta emergencia"
    fallback = "If the form does not load, donate directly on Donorbox." if LOCALE == "en" else "Si el formulario no carga, dona directamente en Donorbox."
    purposes = "".join(f"<li>{esc(item)}</li>" for item in n["purposes"])
    body = f"""
  <section class="donate-hero earthquake-relief-hero rule-section">
    <div class="donate-copy reveal"><p class="section-kicker">{esc(kicker)}</p><h1>{esc(n['title'])}</h1>
      <p class="earthquake-intro">{esc(n['intro'])}</p>
      <p class="earthquake-purpose-lead">{esc(n['purposeLead'])}</p>
      <ul class="earthquake-purposes">{purposes}</ul>
      <p class="earthquake-outro">{esc(n['outro'])}</p>
      <div class="masthead-actions" data-dock-occlusion><a class="btn btn-donate" href="#donation-form" data-relief-form-link>{esc(relief_donate_label)}</a><a class="text-link" href="/donate/">{esc(regular_label)} <span aria-hidden="true">→</span></a></div>
    </div>
    <div class="donate-form reveal" id="donation-form"><div class="donate-form-heading"><p class="section-kicker">{esc(form_label)}</p><p>Processed securely by Donorbox</p></div>
      <script type="module" src="https://donorbox.org/widgets.js" async></script>
      <div class="donorbox-frame"><dbox-widget campaign="{esc(meta['earthquakeDonorboxCampaign'])}" type="donation_form" enable-auto-scroll="true"></dbox-widget></div>
      <p class="form-fallback"><a class="underlink" href="{esc(meta['earthquakeDonorboxUrl'])}">{esc(fallback)}</a></p>
    </div>
  </section>"""
    relief_title = "Colombia earthquake relief" if LOCALE == "en" else "Ayuda por el terremoto en Colombia"
    write("/earthquake-relief/", f"{relief_title} | {meta['name']}", n["intro"], "/donate/", "", body)


def thank_you():
    thanks = site["thankYou"]
    body = f"""
  <section class="thank-you-hero rule-section" data-dock-occlusion>
    <div class="thank-you-copy reveal">
      <p class="section-kicker">{esc(thanks['kicker'])}</p>
      <h1>{esc(thanks['title'])}</h1>
      <p class="thank-you-receipt">{esc(thanks['receipt'])}</p>
      <p class="thank-you-gratitude">{es(thanks['gratitude'])}</p>
      <nav class="thank-you-actions" aria-label="{esc(thanks['nextStepsLabel'])}">
        <a class="btn" href="/programs/">{esc(thanks['programsCta'])}</a>
        <a class="action-link" href="/stories/">{esc(thanks['storiesCta'])} <span aria-hidden="true">→</span></a>
      </nav>
      <p class="thank-you-contact">{esc(thanks['contactIntro'])} <a class="underlink" href="mailto:{esc(meta['email'])}">{esc(meta['email'])}</a>.</p>
    </div>
    <figure class="thank-you-media media-reveal">
      {img_slot('caminos-ride.jpg', thanks['imageAlt'], ratio_class='thank-you-image', eager=True)}
      <figcaption><span>{esc(thanks['imagePlace'])}</span><span lang="es">Pedalea con Conciencia</span></figcaption>
    </figure>
  </section>"""
    write("/thank-you/", f"{thanks['title']} | {meta['name']}",
          thanks["description"], "/thank-you/", "", body, indexable=False)


def notfound():
    body = """
  <section class="split rule-section">
    <div class="page-hero-text"><h1>Page not found</h1>
      <p class="intro">The page you were looking for does not exist.</p>
      <div style="margin-top:24px;"><a class="btn" href="/">Back to the start</a></div></div>
  </section>"""
    full = head(meta, f"Page not found | {meta['name']}", "This page does not exist on the Powerful Children Colombia site. The main destinations cover programs, impact, stories, transparency, and donations.", "/404.html", noindex=True) + \
        header(meta, "") + crumb(meta, "Not found") + f'\n<main id="main">{body}\n</main>' + footer(meta)
    full = normalize_internal_link_arrows(full)
    full = "\n".join(line.rstrip() for line in full.splitlines()) + "\n"
    with open(os.path.join(SITE, "404.html"), "w") as f:
        f.write(full)


def aux_files():
    urls = "".join(f"  <url><loc>{meta['domain'].rstrip('/')}{p}</loc></url>\n"
                   for p in sorted(PAGES) if p not in NOINDEX_PAGES)
    with open(os.path.join(SITE, "sitemap.xml"), "w") as f:
        f.write(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n{urls}</urlset>\n')
    with open(os.path.join(SITE, "robots.txt"), "w") as f:
        f.write(f"User-agent: *\nAllow: /\nDisallow: /admin/\nSitemap: {meta['domain'].rstrip('/')}/sitemap.xml\n")


def editor_files():
    """Copy the private editor UI and hosted API into the deploy payload.

    The UI is noindex and the API is key-gated. Content still lives in the
    repository JSON files; this step only makes the editing surface deployable.
    """
    for directory in ("admin", "api"):
        source = os.path.join(ROOT, directory)
        destination = os.path.join(SITE, directory)
        if os.path.isdir(source):
            shutil.copytree(source, destination, dirs_exist_ok=True)
    # Give the editor a picker backed by the same images that are actually
    # shipped. This is a filename index only; no private source data is added.
    image_dir = os.path.join(SITE, "assets", "img")
    media_manifest = {"items": sorted(
        name for name in os.listdir(image_dir)
        if os.path.isfile(os.path.join(image_dir, name))
        and name.lower().endswith((".jpg", ".jpeg", ".png", ".webp", ".avif", ".gif"))
    )} if os.path.isdir(image_dir) else {"items": []}
    with open(os.path.join(SITE, "admin", "media.json"), "w") as f:
        import json
        json.dump(media_manifest, f, ensure_ascii=False, indent=2)
        f.write("\n")


def build_locale(locale):
    set_locale(locale)
    home()
    programs_index()
    program_pages()
    impact()
    transparency()
    stories_index()
    story_pages()
    about()
    donate()
    earthquake_relief()
    thank_you()


def main():
    old_home = os.path.join(SITE, "home")
    if os.path.isdir(old_home):
        shutil.rmtree(old_home)  # route moved to site root
    es_dir = os.path.join(SITE, "es")
    if os.path.isdir(es_dir):
        shutil.rmtree(es_dir)  # regenerate the Spanish mirror cleanly
    build_locale("en")
    build_locale("es")
    set_locale("en")
    notfound()
    aux_files()
    editor_files()
    print(f"built {len(PAGES)} pages (en+es) + 404 + sitemap + robots")


if __name__ == "__main__":
    main()
