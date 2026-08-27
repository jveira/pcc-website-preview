"""Shared shell + components for the PCC static site generator.

Design source of truth: design/PCC Website System.dc.html (frozen tokens).
Content source of truth: data/content/*.json (platform-neutral collections).
"""
import html
import hashlib
import json
import os

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")


def asset_revision(name):
    with open(os.path.join(ROOT, "site", "assets", name), "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()[:12]


CSS_REVISION = asset_revision("pcc.css")
JS_REVISION = asset_revision("pcc.js")


def load(name):
    with open(os.path.join(ROOT, "data", "content", name)) as f:
        return json.load(f)


def esc(s):
    return html.escape(str(s), quote=True)


SPANISH_PHRASES = [
    "Un Sueño Que Construye Sueños", "Pedalea con Conciencia", "Pedalea Con Conciencia",
    "Juventud con Futuro", "familia poderosa", "Familia Poderosa",
    "El deporte es paz", "Fútbol sala", "fútbol sala",
    "Más Que Vencedores", "Más allá del tablero",
    "Lo que se escribe en el alma de un niño no se puede borrar",
]


def es(s):
    """Escape text, wrapping known Spanish phrases with lang=es for screen readers."""
    out = esc(s)
    for ph in SPANISH_PHRASES:
        out = out.replace(esc(ph), f'<span lang="es">{esc(ph)}</span>')
    return out


NAV = [
    ("Impact", "/impact/"),
    ("Stories", "/stories/"),
    ("Transparency", "/transparency/"),
    ("About", "/about/"),
]
PROGRAM_NAV = load("programs.json")["items"]


def head(meta, title, description, path, noindex=False):
    s = meta["social"]
    canonical = meta["domain"].rstrip("/") + path
    program_previews = {
        "/programs/alpha-fc/": ("og-alpha-fc.jpg", "Alpha FC participants in Pereira, with the Powerful Children Colombia logo"),
        "/programs/caminos-nativos/": ("og-caminos-nativos.jpg", "Caminos Nativos riders in Cabrera, with the Powerful Children Colombia logo"),
        "/programs/mas-que-vencedores/": ("og-mas-que-vencedores.jpg", "Más Que Vencedores chess participants in Santa Marta, with the Powerful Children Colombia logo"),
        "/earthquake-relief/": ("og-earthquake-relief.jpg", "Earthquake relief led locally in Colombia, from Powerful Children Colombia"),
        "/es/earthquake-relief/": ("og-earthquake-relief-es.jpg", "Ayuda por el terremoto liderada localmente en Colombia, de Powerful Children Colombia"),
    }
    og_filename, og_alt = program_previews.get(
        path,
        ("pcc-social-preview.jpg", "Children in a Powerful Children Colombia partner program, with the organization logo"),
    )
    og_image = meta["domain"].rstrip("/") + "/assets/img/" + og_filename
    robots = '<meta name="robots" content="noindex,nofollow">\n' if noindex else ""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
{robots}<title>{esc(title)}</title>
<meta name="description" content="{esc(description)}">
<link rel="canonical" href="{esc(canonical)}">
<meta property="og:type" content="website">
<meta property="og:site_name" content="{esc(meta['name'])}">
<meta property="og:title" content="{esc(title)}">
<meta property="og:description" content="{esc(description)}">
<meta property="og:url" content="{esc(canonical)}">
<meta property="og:image" content="{esc(og_image)}">
<meta property="og:image:width" content="1200">
<meta property="og:image:height" content="630">
<meta property="og:image:alt" content="{esc(og_alt)}">
<meta name="twitter:card" content="summary_large_image">
<meta name="twitter:title" content="{esc(title)}">
<meta name="twitter:description" content="{esc(description)}">
<meta name="twitter:image" content="{esc(og_image)}">
<link rel="icon" type="image/png" href="/assets/img/pcc-logo-square.png">
<link rel="preload" href="/assets/fonts/archivo-latin.woff2" as="font" type="font/woff2" crossorigin>
<link rel="stylesheet" href="/assets/pcc.css?v={CSS_REVISION}">
<script src="/assets/pcc.js?v={JS_REVISION}" defer></script>
<script type="application/ld+json">{{"@context":"https://schema.org","@type":"NGO","name":"{esc(meta['name'])}","url":"{esc(meta['domain'].rstrip('/'))}","logo":"{esc(meta['domain'].rstrip('/'))}/assets/img/pcc-logo-square.png","email":"{esc(meta['email'])}","foundingDate":"2022","nonprofitStatus":"Nonprofit501c3","areaServed":"Colombia","sameAs":["{esc(s['instagram'])}","{esc(s['linkedin'])}","{esc(s['facebook'])}"]}}</script>
</head>
<body>
<a class="skip-link" href="#main">Skip to main content</a>"""


def header(meta, active):
    donate_href = "#donation-form" if active == "/donate/" else "/donate/"
    links = []
    for label, href in NAV:
        current = ' aria-current="page"' if active == href else ""
        links.append(
            f'<a href="{href}"{current}><span class="nav-label">{label}</span>'
            f'<span class="nav-arrow" aria-hidden="true">↗</span></a>')
    program_links = ['<a href="/programs/"><span>All programs</span><span>Overview ↗</span></a>']
    for program in PROGRAM_NAV:
        program_links.append(
            f'<a href="/programs/{esc(program["slug"])}/"><span>{esc(program["name"])}</span>'
            f'<span>{esc(program["department"])} ↗</span></a>')
    program_current = " is-current" if active == "/programs/" else ""
    dock_program_current = ' aria-current="page"' if active == "/programs/" else ""
    dock_stories_current = ' aria-current="page"' if active == "/stories/" else ""
    dock_html = "" if active in ("/donate/", "/thank-you/") else f"""
<nav class="mobile-action-dock" aria-label="Mobile quick access" data-mobile-dock>
  <a class="mobile-dock-link" href="/programs/"{dock_program_current}><span>Programs</span></a>
  <a class="mobile-dock-link" href="/stories/"{dock_stories_current}><span>Stories</span></a>
  <a class="mobile-dock-link mobile-dock-donate" href="{donate_href}"><span>Donate</span><span class="mobile-dock-arrow" aria-hidden="true">↗</span></a>
</nav>"""
    return f"""
<header class="site-header">
  <div class="bar">
    <a class="wordmark" href="/" aria-label="{esc(meta['name'])}, Home"><img src="/assets/img/pcc-logo-horizontal.png" alt="" width="800" height="128" loading="eager" fetchpriority="low" decoding="async"></a>
    <div class="mobile-header-actions">
      <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="primary-navigation"><span data-menu-label>Menu</span><span aria-hidden="true">+</span></button>
    </div>
    <nav class="site-nav" id="primary-navigation" aria-label="Primary">
      <details class="nav-programs{program_current}" data-program-menu>
        <summary><span class="nav-label">Programs</span><span class="nav-arrow" aria-hidden="true">+</span></summary>
        <div class="programs-popover">{''.join(program_links)}</div>
      </details>
      {''.join(links)}
      <a class="nav-donate" href="{donate_href}"{' aria-current="page"' if active == '/donate/' else ''}><span class="nav-label">Donate</span><span class="nav-arrow" aria-hidden="true">↗</span></a>
      <a class="mobile-nav-contact" href="mailto:{esc(meta['email'])}"><span class="nav-label">Contact PCC</span><span class="nav-arrow" aria-hidden="true">↗</span></a>
    </nav>
  </div>
</header>
{dock_html}"""


def crumb(meta, trail):
    destinations = {
        "Home": "/", "Programs": "/programs/", "Impact": "/impact/",
        "Stories": "/stories/", "Transparency": "/transparency/", "About": "/about/",
        "Donate": "/donate/",
    }
    parts = [part.strip() for part in trail.split("/")]
    items = []
    for index, part in enumerate(parts):
        if index == len(parts) - 1:
            items.append(f'<li><span aria-current="page">{esc(part)}</span></li>')
        elif part in destinations:
            items.append(f'<li><a href="{destinations[part]}">{esc(part)}</a><span aria-hidden="true">/</span></li>')
        else:
            items.append(f'<li><span>{esc(part)}</span><span aria-hidden="true">/</span></li>')
    return f"""
<nav class="crumb-strip meta" aria-label="Breadcrumb">
  <ol>{''.join(items)}</ol>
  <span>{esc(meta['tagline'])}</span>
</nav>"""


def footer(meta, active=""):
    s = meta["social"]
    donate_href = "#donation-form" if active == "/donate/" else "/donate/"
    footer_links = [
        ("Programs", "/programs/"), ("Impact", "/impact/"),
        ("Stories", "/stories/"), ("Transparency", "/transparency/"),
        ("About", "/about/"), ("Donate", donate_href),
    ]
    def footer_link(label, href):
        current_path = "/donate/" if label == "Donate" else href
        current_attr = ' aria-current="page"' if active == current_path else ""
        return f'<a href="{href}"{current_attr}>{label}</a>'
    footer_menu = "".join(footer_link(label, href) for label, href in footer_links)
    return f"""
<footer class="site-footer">
  <div class="footer-bar reveal">
    <div class="footer-brand">
      <a class="footer-name" href="/">{esc(meta['name'])}</a>
      <a class="footer-email underlink" href="mailto:{esc(meta['email'])}">{esc(meta['email'])}</a>
    </div>
    <nav class="footer-menu meta" aria-label="Footer">
      {footer_menu}
    </nav>
    <nav class="footer-connect meta" aria-label="Follow and updates">
      <a href="mailto:{esc(meta['email'])}?subject=Sign%20me%20up%20for%20PCC%20updates">Email updates</a>
      <a href="{esc(s['instagram'])}">Instagram</a><a href="{esc(s['linkedin'])}">LinkedIn</a>
      <a href="{esc(s['facebook'])}">Facebook</a><a href="{esc(meta['privacyPdf'])}">Privacy</a>
    </nav>
  </div>
  <p class="legal-strip meta">
    <span>{esc(meta['name'])} · 501(c)(3)</span>
    <span>Pereira · Cabrera · Santa Marta</span>
    <span>©2026</span>
  </p>
</footer>
</body>
</html>"""


def img_slot(src, alt, ratio_class="", extra_style="", eager=False,
             mobile_src="", mobile_fallback_src="", mobile_small_src=""):
    """A photography slot backed by an approved local asset.

    Always a <div> (flow content) — callers must not wrap it in a <span>.
    eager=True marks the above-the-fold LCP image: loaded eagerly with high
    fetch priority. Everything else lazy-loads.
    """
    if not src:
        raise ValueError(f"Missing approved image source for: {alt}")
    if not ratio_class and not extra_style:
        extra_style = "position:absolute; inset:0;"
    style = f' style="{extra_style}"' if extra_style else ""
    loading = ('loading="eager" fetchpriority="high"' if eager
               else 'loading="lazy" fetchpriority="low"')
    decoding = "sync" if eager else "async"
    image = f'<img src="/assets/img/{esc(src)}" alt="{esc(alt)}" {loading} decoding="{decoding}">'
    if mobile_src:
        media_type = ' type="image/webp"' if mobile_src.endswith('.webp') else ''
        mobile_srcset = f'/assets/img/{esc(mobile_src)}'
        sizes = ''
        if mobile_small_src:
            mobile_srcset = (f'/assets/img/{esc(mobile_small_src)} 430w, '
                             f'/assets/img/{esc(mobile_src)} 780w')
            sizes = ' sizes="100vw"'
        fallback = (f'<source media="(max-width: 699px)" '
                    f'srcset="/assets/img/{esc(mobile_fallback_src)}">') if mobile_fallback_src else ''
        image = (f'<picture><source media="(max-width: 699px)"{media_type} '
                 f'srcset="{mobile_srcset}"{sizes}>{fallback}{image}</picture>')
    return (f'<div class="img-slot has-img {ratio_class}"{style}>'
            f'{image}</div>')


def rail_rows(pairs):
    return "".join(
        f'<div class="rail-row meta"><span class="meta-dim">{esc(k)}</span><span>{esc(v)}</span></div>'
        for k, v in pairs)


def dash(v, metric="figure", year="this year"):
    """Render a compact table value without treating an absent figure as zero."""
    if v:
        return esc(v)
    label = f"{metric} was not included in PCC's {year} report"
    return (f'<span class="empty"><span aria-hidden="true">Not reported</span>'
            f'<span class="visually-hidden">{esc(label)}</span></span>')


def film_cards(films, border_last=True):
    out = []
    for f in films:
        out.append(f"""
      <a class="film-card reveal media-reveal" href="{esc(f['videoUrl'])}">
        <div class="film-card-media img-slot has-img">
          <img src="/assets/img/{esc(f['still'])}" alt="{esc(f['stillAlt'])}" loading="lazy" fetchpriority="low" decoding="async"></div>
        <div class="card-body">
          <span class="film-card-meta">{esc(f['meta'])}</span>
          <span class="card-title">{esc(f['title'])}</span>
          <span class="film-card-play"><span>Play film</span><span aria-hidden="true">↗</span></span>
        </div>
      </a>""")
    return "".join(out)


def cleared_films(films):
    """Only films whose consent state is cleared may render (CMS guardrail)."""
    return [f for f in films if f.get("consentStatus") == "cleared"]


def withheld_films(films):
    return [f for f in films if f.get("consentStatus") != "cleared"]
