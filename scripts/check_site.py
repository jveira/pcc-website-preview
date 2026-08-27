#!/usr/bin/env python3
"""Deterministic gates over the generated site. Exit 1 on any failure.

Gate classes:
  A. Structure  — internal links resolve, local images exist, one h1/main,
                  landmarks, skip link, sitemap coverage, no placeholders.
  B. Validity   — HTML5 structural validation via html-validate (.htmlvalidate.json).
                  This gate FAILS (never skips) if the validator cannot run.
  C. Claims     — no do-not-publish / unresolved claim pattern from
                  data/content/claims.json appears in output without an ownerDecision.
  D. Consent    — no story with consentStatus != 'cleared' is rendered anywhere
                  (title or video URL).
  E. Media      — every <img> has alt and an explicit loading policy; exactly one
                  eager high-priority LCP on Home, at most one on other image-led
                  routes, and only the shared wordmark may be eager/low-priority.
  F. Conversion — Home keeps a persistent mobile Donate action, four-section
                  structure, unique photography, and non-gating reveal motion.
  G. Product UX  — required navigation, selectors, client program, conversion
                  order, and source-voice safeguards are present.
"""
import glob
import html
import json
import os
import re
import subprocess
import sys

ROOT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..")
SITE = os.path.join(ROOT, "site")
PLACEHOLDERS = ["lorem", "TODO", "PLACEHOLDER", "{{", "}}", "sample content"]
NOINDEX_ROUTES = {"/thank-you/", "/es/thank-you/"}
DOCUMENT_ASSETS = {
    "pcc-2025-year-in-review.pdf": "9ea101929d948e62eff7569e851be6003f150788c2efbdd7f837f8a8d5c5e297",
    "pcc-2024-year-in-review.pdf": "83c1735569249ba00050679ac73062a606fa4e294ce9e6ee5fa0be8043becab7",
    "pcc-2023-year-in-review.pdf": "96269358eee832cbe1f9bb70b391229d0981727e81a7cccc22a19d8cf2741183",
    "pcc-2022-year-in-review.pdf": "189bff43980761493351661c908fb968bfadab6de7c5c1973fa8ff9b44e2c2aa",
    "pcc-our-beginnings.pdf": "7cec78161c538885fff5a930b3307bedd8889a78bf0c5c4e9275a57bb40a339f",
    "pcc-privacy-policy.pdf": "08e3873250ba861e37491c6eb10af016e90afcc360efcd570779d5486860e7e1",
}


def load_json(rel):
    with open(os.path.join(ROOT, rel)) as f:
        return json.load(f)


def gate_structure(pages, failures):
    import hashlib
    documents_dir = os.path.join(SITE, "assets", "documents")
    for filename, expected_sha in DOCUMENT_ASSETS.items():
        path = os.path.join(documents_dir, filename)
        if not os.path.isfile(path):
            failures.append(f"[structure] missing repository-owned document {filename}")
            continue
        with open(path, "rb") as handle:
            payload = handle.read()
        if not payload.startswith(b"%PDF-"):
            failures.append(f"[structure] document is not a PDF: {filename}")
        if hashlib.sha256(payload).hexdigest() != expected_sha:
            failures.append(f"[structure] approved document changed unexpectedly: {filename}")
    for page in pages:
        rel = os.path.relpath(page, SITE)
        t = open(page).read()
        if t.count("<h1") != 1:
            failures.append(f"[structure] {rel}: h1 count = {t.count('<h1')}")
        if t.count("<main") != 1 or "<header" not in t or "<footer" not in t:
            failures.append(f"[structure] {rel}: landmark problem")
        if 'class="skip-link"' not in t:
            failures.append(f"[structure] {rel}: missing skip link")
        if "powerfulchildrencolombia.org/wp-content/uploads/" in t:
            failures.append(f"[structure] {rel}: depends on the retired WordPress uploads origin")
        if not re.search(r'href="/assets/pcc\.css\?v=[0-9a-f]{12}"', t):
            failures.append(f"[structure] {rel}: stylesheet URL is not content-versioned")
        if not re.search(r'src="/assets/pcc\.js\?v=[0-9a-f]{12}"', t):
            failures.append(f"[structure] {rel}: script URL is not content-versioned")
        for ph in PLACEHOLDERS:
            if ph in t:
                failures.append(f"[structure] {rel}: placeholder string {ph!r}")
        for m in re.finditer(r'href="(/[^"#]*)"', t):
            href = m.group(1)
            if href.startswith("/assets/"):
                asset_path = href.split("?", 1)[0]
                if not os.path.isfile(os.path.join(SITE, asset_path.lstrip("/"))):
                    failures.append(f"[structure] {rel}: missing asset {href}")
            elif href in ("/404.html", "/"):
                continue
            elif not os.path.isfile(os.path.join(SITE, href.strip("/"), "index.html")):
                failures.append(f"[structure] {rel}: broken internal link {href}")
    sitemap = open(os.path.join(SITE, "sitemap.xml")).read()
    for page in pages:
        rel = os.path.relpath(page, SITE)
        if rel == "404.html":
            continue
        url_path = "/" if rel == "index.html" else "/" + os.path.dirname(rel) + "/"
        if url_path in NOINDEX_ROUTES:
            if '<meta name="robots" content="noindex,nofollow">' not in t:
                failures.append(f"[structure] {rel}: private follow-up route must be noindex,nofollow")
            if url_path in sitemap:
                failures.append(f"[structure] sitemap must exclude private follow-up route {url_path}")
        elif url_path not in sitemap:
            failures.append(f"[structure] sitemap missing {url_path}")


def gate_validity(failures):
    try:
        r = subprocess.run(
            ["npx", "--yes", "html-validate", "--formatter", "stylish", "site/**/*.html"],
            capture_output=True, text=True, cwd=ROOT, timeout=300)
    except (FileNotFoundError, subprocess.TimeoutExpired) as e:
        failures.append(f"[validity] html-validate could not run ({e}) — gate fails, never skips")
        return
    if r.returncode != 0:
        tail = "\n".join((r.stdout or r.stderr).strip().splitlines()[-25:])
        failures.append(f"[validity] html-validate reported errors:\n{tail}")


def gate_claims(pages, failures):
    claims = load_json("data/content/claims.json")["claims"]
    by_id = {c["id"]: c for c in claims}
    required_denials = {
        "stale-mailing-address": {"846 Oneonta Drive"},
        "stale-focus-age-range": {"ages 5 to 15"},
        "zelle-transfer-limit": {"$2,000 limit", "$2000 limit"},
    }
    for claim_id, patterns in required_denials.items():
        claim = by_id.get(claim_id)
        if not claim or claim.get("status") != "do-not-publish" or not patterns.issubset(set(claim.get("patterns", []))):
            failures.append(f"[claims] registry must retain explicit do-not-publish guard {claim_id!r}")
    for page in pages:
        rel = os.path.relpath(page, SITE)
        t = open(page).read()
        plain = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", html.unescape(t)))
        for c in claims:
            if c.get("ownerDecision") or c.get("status") == "preview-pending":
                continue
            for pat in c["patterns"]:
                if pat in t or pat in plain:
                    failures.append(f"[claims] {rel}: {c['status']} claim '{c['id']}' pattern {pat!r} in output")


def gate_public_punctuation(pages, failures):
    """Owner direction: public copy uses sentences, not typographic dash constructions."""
    for page in pages:
        rel = os.path.relpath(page, SITE)
        text = open(page).read()
        for mark, label in (("—", "em dash"), ("–", "en dash")):
            if mark in text:
                failures.append(f"[copy] {rel}: public HTML contains an {label}")


def gate_consent(pages, failures):
    stories = load_json("data/content/stories.json")["items"]
    withheld = [s for s in stories if s.get("consentStatus") != "cleared"]
    for page in pages:
        rel = os.path.relpath(page, SITE)
        t = open(page).read()
        for s in withheld:
            marks = [s["title"]] + ([s["videoUrl"]] if s.get("videoUrl") else [])
            for mark in marks:
                if mark in t:
                    failures.append(f"[consent] {rel}: withheld story '{s['slug']}' "
                                    f"(consentStatus={s.get('consentStatus')}) rendered: {mark!r}")


def gate_media(pages, failures):
    for page in pages:
        rel = os.path.relpath(page, SITE)
        t = open(page).read()
        eager_high = 0
        for m in re.finditer(r"<img([^>]*)>", t):
            attrs = m.group(1)
            src = re.search(r'src="([^"]+)"', attrs)
            if src and src.group(1).startswith("/assets/") and \
                    not os.path.isfile(os.path.join(SITE, src.group(1).lstrip("/"))):
                failures.append(f"[media] {rel}: missing image {src.group(1)}")
            if 'alt="' not in attrs:
                failures.append(f"[media] {rel}: img without alt")
            if 'loading="' not in attrs:
                failures.append(f"[media] {rel}: img without explicit loading policy")
            if 'loading="eager"' in attrs:
                if 'fetchpriority="high"' in attrs:
                    eager_high += 1
                elif 'fetchpriority="low"' in attrs:
                    if not src or not src.group(1).endswith("/pcc-logo-horizontal.png"):
                        failures.append(f"[media] {rel}: only the shared wordmark may be eager/low-priority")
                else:
                    failures.append(f"[media] {rel}: eager img without explicit high/low fetch priority")
        if rel == "index.html" and eager_high != 1:
            failures.append(f"[media] {rel}: home must have exactly 1 high-priority LCP image, found {eager_high}")
        if rel != "index.html" and eager_high > 1:
            failures.append(f"[media] {rel}: more than one high-priority LCP candidate ({eager_high})")

        for source in re.finditer(r'<source\b([^>]*)>', t):
            srcset = re.search(r'\bsrcset="([^"]+)"', source.group(1))
            if not srcset:
                media_src = re.search(r'\bsrc="([^"]+)"', source.group(1))
                if not media_src:
                    failures.append(f"[media] {rel}: source without src or srcset")
                elif media_src.group(1).startswith("/assets/") and not os.path.isfile(
                        os.path.join(SITE, media_src.group(1).lstrip("/"))):
                    failures.append(f"[media] {rel}: missing media source {media_src.group(1)}")
                continue
            for candidate in srcset.group(1).split(','):
                local_src = candidate.strip().split()[0]
                if local_src.startswith('/assets/img/') and not os.path.exists(os.path.join(SITE, local_src.lstrip('/'))):
                    failures.append(f"[media] {rel}: missing responsive image {local_src}")

    field_film_routes = {
        "programs/caminos-nativos/index.html": ("August 2026", "en"),
        "es/programs/caminos-nativos/index.html": ("agosto de 2026", "es"),
    }
    field_film_assets = {
        "/assets/video/caminos-cabrera-august-2026.mp4": 25_000_000,
        "/assets/video/caminos-cabrera-august-2026.en.vtt": 20_000,
        "/assets/video/caminos-cabrera-august-2026.es.vtt": 20_000,
        "/assets/img/caminos-cabrera-august-2026-poster.webp": 200_000,
    }
    for src, size_limit in field_film_assets.items():
        path = os.path.join(SITE, src.lstrip("/"))
        if not os.path.isfile(path):
            failures.append(f"[media] Cabrera field film asset is missing: {src}")
        elif os.path.getsize(path) > size_limit:
            failures.append(f"[media] Cabrera field film asset exceeds {size_limit} bytes: {src}")
    for rel, (date_label, default_language) in field_film_routes.items():
        page = open(os.path.join(SITE, rel)).read()
        section = re.search(r'<section class="program-field-film.*?</section>', page, re.S)
        if not section:
            failures.append(f"[media] {rel}: approved Cabrera field film is missing")
            continue
        film = section.group(0)
        if film.count("<video ") != 1 or " autoplay" in film:
            failures.append(f"[media] {rel}: field film must be one user-initiated video")
        for required in (' controls', ' playsinline', 'preload="none"', date_label,
                         'caminos-cabrera-august-2026-poster.webp'):
            if required not in film:
                failures.append(f"[media] {rel}: field film is missing {required!r}")
        for language in ("en", "es"):
            track = re.search(rf'<track[^>]+srclang="{language}"[^>]*>', film)
            if not track:
                failures.append(f"[media] {rel}: field film is missing {language} captions")
            elif (language == default_language) != (' default' in track.group(0)):
                failures.append(f"[media] {rel}: {language} caption default does not match locale")
    for page in pages:
        rel = os.path.relpath(page, SITE)
        if rel not in field_film_routes and "caminos-cabrera-august-2026.mp4" in open(page).read():
            failures.append(f"[media] {rel}: Cabrera field film escaped its approved program route")

    fill_contracts = {
        "index.html": (r'<div class="home-program-photo">\s*<div class="img-slot[^\"]*"([^>]*)>', 3),
        "programs/index.html": (r'<div class="program-card-media">\s*<div class="img-slot[^\"]*"([^>]*)>', 3),
        "stories/index.html": (r'<figure class="masthead-media[^\"]*">\s*<a[^>]*>\s*<div class="img-slot[^\"]*"([^>]*)>', 1),
    }
    for rel, (pattern, expected) in fill_contracts.items():
        page = open(os.path.join(SITE, rel)).read()
        slots = re.findall(pattern, page)
        if len(slots) != expected:
            failures.append(f"[media] {rel}: expected {expected} bounded fill media slots, found {len(slots)}")
    css = open(os.path.join(SITE, "assets", "pcc.css")).read()
    for selector in [".home-program-photo > .img-slot", ".program-card-media > .img-slot",
                     ".masthead-media > a > .img-slot"]:
        rule = re.search(rf'{re.escape(selector)}[^{{}}]*\{{([^}}]+)\}}', css, re.S)
        declarations = rule.group(1).replace(" ", "") if rule else ""
        if "position:absolute" not in declarations or "inset:0" not in declarations:
            failures.append(f"[media] missing fill geometry contract for {selector}")

    with open(os.path.join(ROOT, "data", "content", "programs.json")) as handle:
        program_items = json.load(handle)["items"]
    gallery_counts = {item["slug"]: len(item.get("gallery", [])) for item in program_items}
    if any(count < 4 for count in gallery_counts.values()):
        failures.append("[media] every program requires at least four distinct field photographs")
    program_routes = {
        f"{prefix}programs/{slug}/index.html": count
        for prefix in ("", "es/")
        for slug, count in gallery_counts.items()
    }
    gallery_assets = set()
    for rel, expected_slides in program_routes.items():
        page = open(os.path.join(SITE, rel)).read()
        if page.count('data-field-gallery') != 1:
            failures.append(f"[media] {rel}: requires exactly one editorial field gallery")
        if page.count('data-gallery-slide') != expected_slides:
            failures.append(f"[media] {rel}: expected {expected_slides} sourced gallery slides")
        for control in ('data-gallery-prev', 'data-gallery-next'):
            if control not in page:
                failures.append(f"[media] {rel}: field gallery is missing {control}")
        gallery_assets.update(re.findall(
            r'<figure class="field-gallery-slide"[^>]*>\s*<img[^>]+src="(/assets/img/[^"]+)"', page))
    for src in gallery_assets:
        path = os.path.join(SITE, src.lstrip("/"))
        if not os.path.isfile(path):
            failures.append(f"[media] field gallery asset is missing: {src}")
        elif os.path.getsize(path) > 200_000:
            failures.append(f"[media] field gallery asset exceeds 200KB: {src}")
    expected_unique_assets = sum(gallery_counts.values())
    if len(gallery_assets) != expected_unique_assets:
        failures.append(
            f"[media] expected {expected_unique_assets} distinct source-listed field-gallery assets, "
            f"found {len(gallery_assets)}"
        )

    programs_index = open(os.path.join(SITE, "programs", "index.html")).read()
    if programs_index.count("pcc-child-art.webp") != 1 or "Artwork made by children in PCC programs" not in programs_index:
        failures.append("[media] Programs requires the owner-supplied organization-wide children's artwork exactly once")
    art_path = os.path.join(SITE, "assets", "img", "pcc-child-art.webp")
    if not os.path.isfile(art_path) or os.path.getsize(art_path) > 200_000:
        failures.append("[media] children's artwork is missing or exceeds 200KB")

    selected_features = {
        "alpha-fc": "alpha-kathy-selected.webp",
        "caminos-nativos": "caminos-kathy-selected.webp",
    }
    for slug, asset in selected_features.items():
        for prefix in ("", "es/"):
            rel = f"{prefix}programs/{slug}/index.html"
            page = open(os.path.join(SITE, rel)).read()
            if page.count(asset) != 1 or "program-documentary--paired" not in page:
                failures.append(f"[media] {rel}: Kathy-selected {asset} must be a permanent paired editorial feature")
        feature_path = os.path.join(SITE, "assets", "img", asset)
        if not os.path.isfile(feature_path) or os.path.getsize(feature_path) > 200_000:
            failures.append(f"[media] Kathy-selected feature is missing or exceeds 200KB: {asset}")

    for page in pages:
        rel = os.path.relpath(page, SITE)
        if "alpha-community.jpg" in open(page).read():
            failures.append(f"[media] {rel}: superseded legacy Alpha visit photo is present in public HTML")
    chat_only_assets = ("00003269", "00003270", "00003271", "00003272", "00003274")
    for root, _, filenames in os.walk(SITE):
        for filename in filenames:
            if any(token in filename for token in chat_only_assets):
                failures.append(f"[media] chat-only August 13 asset entered the public build: {filename}")


def gate_home_conversion(failures):
    home = open(os.path.join(SITE, "index.html")).read()
    css = open(os.path.join(SITE, "assets", "pcc.css")).read()
    required_sections = ["home-hero", "home-proof", "home-programs", "home-support"]
    for name in required_sections:
        if len(re.findall(rf'<section\s+class="[^"]*\b{name}\b[^"]*"', home)) != 1:
            failures.append(f"[conversion] home requires exactly one {name} section")
    narrative_order = [
        "Pedalea con Conciencia.",
        "PCC backs the Colombian leaders already doing the work.",
        "Powerful Children Colombia today",
        'class="home-program-list"',
        "Together in 2025",
        "Thank you for being a vital part of our familia poderosa!",
    ]
    narrative_positions = [home.find(marker) for marker in narrative_order]
    if -1 in narrative_positions or narrative_positions != sorted(narrative_positions):
        failures.append("[conversion] Home must sequence human story, PCC role, more programs, organization-wide proof, then donor role")
    if "home-record-facts" in home:
        failures.append("[conversion] Home must not restore the compact facts list removed by Kathy's August 13 revision")
    if 'class="btn notice-cta"' not in home or 'href="/earthquake-relief/" data-dock-collision' not in home:
        failures.append("[conversion] Home earthquake appeal requires a distinct, dock-safe primary action")
    programs_index = open(os.path.join(SITE, "programs", "index.html")).read()
    for translation in ("A Dream That Builds Dreams", "Pedal with Conscience", "Beyond the Chessboard"):
        if f'<span class="program-card-translation">({translation})</span>' not in programs_index:
            failures.append(f"[conversion] English Programs index is missing the approved program-name translation: {translation}")
    home_programs = re.search(r'<section class="home-programs".*?</section>', home, re.S)
    if home_programs and "100 children" in home_programs.group(0):
        failures.append("[conversion] compact Home partner entries must not show the MQV child count")
    if 'class="mobile-action-dock"' not in home or 'class="mobile-dock-link mobile-dock-donate"' not in home:
        failures.append("[conversion] persistent mobile action dock or Donate action is missing")
    if 'mobile-dock-index' in home or 'class="nav-index"' in home:
        failures.append("[conversion] mobile navigation must not use ornamental route numbers")
    if 'data-dock-occlusion' not in home or 'is-over-local-actions' not in css:
        failures.append("[conversion] mobile dock must yield to the closing page actions")
    if home.count('href="/donate/"') < 5:
        failures.append("[conversion] home requires persistent, opening, closing, and footer Donate paths")
    if "pcc-social-preview.jpg" not in home or 'content="summary_large_image"' not in home:
        failures.append("[conversion] large-image social preview metadata is missing")
    social_previews = ["pcc-social-preview.jpg", "og-alpha-fc.jpg",
                       "og-caminos-nativos.jpg", "og-mas-que-vencedores.jpg",
                       "og-earthquake-relief.jpg", "og-earthquake-relief-es.jpg"]
    for filename in social_previews:
        social_preview = os.path.join(SITE, "assets", "img", filename)
        if not os.path.isfile(social_preview) or os.path.getsize(social_preview) > 300_000:
            failures.append(f"[conversion] social preview {filename} is missing or exceeds 300KB")
    image_sources = re.findall(r'<img[^>]+src="(/assets/img/[^"]+)"', home)
    duplicates = sorted({src for src in image_sources if image_sources.count(src) > 1})
    if duplicates:
        failures.append(f"[conversion] home repeats photography/assets: {', '.join(duplicates)}")
    eager_match = re.search(r'<img[^>]+src="(/assets/img/[^"]+)"[^>]+loading="eager"', home)
    for src in image_sources:
        size = os.path.getsize(os.path.join(SITE, src.lstrip("/")))
        limit = 300_000 if eager_match and src == eager_match.group(1) else 200_000
        if size > limit:
            failures.append(f"[conversion] {src} is {size} bytes (budget {limit})")
    js_size = os.path.getsize(os.path.join(SITE, "assets", "pcc.js"))
    if js_size > 50_000:
        failures.append(f"[conversion] pcc.js is {js_size} bytes (budget 50000)")
    if re.search(r"\.motion-ready\s+\.reveal\s*\{[^}]*opacity\s*:\s*0", css, re.S):
        failures.append("[conversion] reveal motion opacity-gates essential content")


def gate_product_ux(pages, failures):
    rendered = {os.path.relpath(page, SITE): open(page).read() for page in pages}
    all_html = "\n".join(rendered.values())
    if 'mobile-dock-index' in all_html or 'class="nav-index"' in all_html:
        failures.append("[product-ux] ornamental navigation indices returned")
    if 'class="mobile-action-dock"' in rendered.get("donate/index.html", ""):
        failures.append("[product-ux] Donate must not repeat the fixed Donate dock over its form")
    for rel in ("index.html", "es/index.html"):
        page = rendered.get(rel, "")
        if page.count('class="meta program-link" data-dock-collision') != 3:
            failures.append(f"[product-ux] {rel}: every Home program action must clear the mobile dock")
    for rel in ("programs/index.html", "es/programs/index.html"):
        page = rendered.get(rel, "")
        if page.count('class="program-card-link" data-dock-collision') != 3:
            failures.append(f"[product-ux] {rel}: every program-card action must clear the mobile dock")
    for rel in ("thank-you/index.html", "es/thank-you/index.html"):
        page = rendered.get(rel, "")
        if 'class="mobile-action-dock"' in page:
            failures.append(f"[product-ux] {rel}: post-donation page must not show another fixed Donate action")
    required = {
        "index.html": ["home-hero", "home-programs", "/programs/mas-que-vencedores/",
                       "Pedalea con Conciencia.",
                       "Supporting Colombian-led efforts that enable children to embrace their individual power and potential.",
                       "PCC helped co-design and fully fund Pedalea con Conciencia",
                       "PCC backs the Colombian leaders already doing the work.",
                       "caminos-field-6.webp",
                       "They knew their communities long before PCC arrived.",
                       "Paola Arenas Duarte founded Caminos Nativos in Santander in 2017.",
                       "Our Partner · Caminos Nativos", "335", "98%", "Together in 2025",
                       "Thank you for being a vital part of our familia poderosa!",
                       "Your employer may match your gift. Don&#x27;t forget to double check."],
        "programs/index.html": ["partner-criteria", "program-card-grid", "where-we-work", "Our partners",
                                "alpha-logo.png", "caminos-logo.jpg", "mqv-logo.png",
                                "<h1>Programs</h1>",
                                "Powerful Children Colombia partners with Colombian-led organizations",
                                "Current programs are led in Pereira, Cabrera, and Santa Marta.",
                                "On the court, kids build health, confidence, and connection.",
                                "Pedaling toward stronger minds, stronger families, stronger community.",
                                "Every move builds sharper minds and steadier hearts."],
        "programs/alpha-fc/index.html": ["Un Sueño Que Construye Sueños (A Dream that Builds Dreams)", "nearly 200 children"],
        "programs/caminos-nativos/index.html": ["Pedalea con Conciencia (Pedal with Conscience)",
                                                  "Program design, funding, monitoring, and evaluation",
                                                  "Current program reach", ">35<", "From the 2025 Year in Review",
                                                  "Earlier published result · 2022",
                                                  "Children at launch", ">21<",
                                                  "Two of Pedalea con Conciencia&#x27;s original riders are now competing at a higher level",
                                                  "Caminos Nativos also introduced mental health workshops for parents."],
        "programs/mas-que-vencedores/index.html": ["Más Que Vencedores", "Más allá del tablero (Beyond the Chessboard)", "mqv-hero.jpg"],
        "impact/index.html": ["data-evidence-explorer", "data-scope-control=\"caminos-nativos\"", "data-year-control",
                              "We've watched the children in these programs grow alongside PCC.",
                              "Younger siblings are joining.",
                              "Current program reach", "Close to 200",
                              "Two of Pedalea con Conciencia&#x27;s original riders"],
        "transparency/index.html": ["data-evidence-explorer", "data-year-control", "document-list",
                                    "<h1>Annual reports</h1>",
                                    "Your trust, partnership and belief in Powerful Children Colombia",
                                    "Growing Together, Growing Responsibly",
                                    "Reports by year", "How PCC reports", "Reports and policies",
                                    "Partner organizations report to us regularly", "$48,000", "$43,500",
                                    "$41,500", "$62,700", "$29,500", "$38,700", "$18,000", "$9,800",
                                    "$700", "$2,600", "$1,700", "$2,400", "98%", "94%", "91%", "80%",
                                    "Numbers are rounded for simplicity."],
        "stories/index.html": ["film-grid", "Stories &amp; Films",
                               "In their own words.",
                               "Read letters from the PCC team and watch films from the people leading the programs."],
        "about/index.html": ["team-directory", "person-bio", "values-grid",
                              "Our partners and collaborators", "Julio Jaramillo",
                              "Enzo Peto", "Alejandro Ochoa", "Javier Espinosa", "Jaime Veira", "Julicore"],
        "donate/index.html": ["id=\"donation-form\"", "donorbox-frame", "https://donorbox.org/widgets.js",
                              'campaign="powerful-children-colombia-donation-form"', 'type="donation_form"',
                              'enable-auto-scroll="true"', "methods-section",
                              "Thank you so much for considering a donation!",
                              "Thank you for investing in this work.",
                              "Donate using the secure Donorbox form above.",
                              "Make a check out to Powerful Children Colombia and mail it to 2490 Country View Glen, Escondido, CA 92026.",
                              "Send your donation to our Zelle account at accounting@powerfulchildrencolombia.org.",
                              "Other ways to donate", "Read the annual reports", "Share feedback"],
        "es/index.html": ["Acompañamos iniciativas lideradas por colombianos para que los niños",
                           "PCC ayudó a codiseñar y financiar por completo Pedalea con Conciencia",
                           "Ellos conocían sus comunidades mucho antes de que llegara PCC.",
                           "Nuestra aliada · Caminos Nativos", "335", "98 %",
                           "Tu empresa puede hacer un aporte equivalente al tuyo. No olvides confirmarlo."],
        "es/programs/index.html": ["<h1>Programas</h1>", "Nuestros aliados", "Dónde trabajamos",
                                    "Tres lugares. Tres programas con liderazgo local.",
                                    "En la cancha, los niños fortalecen su salud, su confianza y sus vínculos."],
        "es/programs/alpha-fc/index.html": ["Inició en 2023", "Niños acompañados actualmente",
                                             "Casi 200", "Permanencia de participantes", "Más del 80%",
                                             "Organización", "Líderes", "Comunidades", "Resultados anuales",
                                             "1 en YouTube"],
        "es/programs/caminos-nativos/index.html": ["Organización", "Líderes", "Comunidades",
                                                     "Resultados anuales", "Participantes actuales del programa",
                                                     ">35 niños<", "Del Resumen del año 2025",
                                                     "Resultado anterior publicado · 2022", "Niños al inicio",
                                                     ">21<", "2 en YouTube"],
        "es/programs/mas-que-vencedores/index.html": ["Organización", "Líderes", "Colegios"],
        "es/impact/index.html": ["aria-label=\"Alcance del impacto\"", "aria-label=\"Año del impacto\"",
                                  ">Toda PCC<", "Impacto por programa y año"],
        "es/transparency/index.html": ["<h1>Informes anuales</h1>",
                                        "aria-label=\"Año del informe\"",
                                        "Crecemos juntos, crecemos con responsabilidad",
                                        "$48,000", "$43,500", "$41,500", "$62,700",
                                        "$29,500", "$38,700", "$18,000", "$9,800",
                                        "$700", "$2,600", "$1,700", "$2,400",
                                        "98 %", "94 %", "91 %", "80 %",
                                        "Las cifras están redondeadas para facilitar su lectura.",
                                        "Las organizaciones aliadas nos informan periódicamente"],
        "es/donate/index.html": ["Otras formas de donar", "Dona a través del formulario seguro de Donorbox de arriba.",
                                  "2490 Country View Glen, Escondido, CA 92026",
                                  "accounting@powerfulchildrencolombia.org"],
        "es/about/index.html": ["Profesor de inglés", "Asesoría tecnológica", "Administrador web", "Diseño del logo"],
        "earthquake-relief/index.html": ["id=\"donation-form\"", "donorbox-frame", "https://donorbox.org/widgets.js",
                                           'campaign="colombia-earthquake-relief"', 'type="donation_form"',
                                           'enable-auto-scroll="true"', "Support earthquake relief",
                                           'href="#donation-form" data-relief-form-link', "Donate to earthquake relief",
                                           "We&#x27;re raising funds to:",
                                           "Our hearts are with the families, communities, and partners we work alongside there.",
                                           "#PowerfulJuntos", "Make a general donation"],
        "es/earthquake-relief/index.html": ["Estamos recaudando fondos para:",
                                              'campaign="colombia-earthquake-relief"',
                                              'href="#donation-form" data-relief-form-link', "Dona para esta emergencia",
                                              "#PowerfulJuntos"],
        "thank-you/index.html": ['<meta name="robots" content="noindex,nofollow">',
                                  "Thank you for investing in this work.",
                                  "If Donorbox sent you here after checkout",
                                  "Thank you for being a vital part of our", "familia poderosa",
                                  'href="/programs/"', 'href="/stories/"',
                                  'href="mailto:info@powerfulchildrencolombia.org"'],
        "es/thank-you/index.html": ['<meta name="robots" content="noindex,nofollow">',
                                     "Gracias por invertir en este trabajo.",
                                     "Si Donorbox te envió a esta página",
                                     "¡Gracias por ser parte vital de nuestra", "familia poderosa",
                                     'href="/es/programs/"', 'href="/es/stories/"',
                                     'href="mailto:info@powerfulchildrencolombia.org"'],
    }
    for rel, markers in required.items():
        page = rendered.get(rel, "")
        for marker in markers:
            if marker not in page:
                failures.append(f"[product-ux] {rel}: missing {marker!r}")
    for rel in ("transparency/index.html", "es/transparency/index.html"):
        page = rendered.get(rel, "")
        if "Children in Pedalea con Conciencia" in page or "Niños en Pedalea con Conciencia" in page:
            failures.append(f"[product-ux] {rel}: a Caminos-only launch figure is presented as organization-wide transparency data")
        if page.count('class="ledger-item"') != 40:
            failures.append(f"[product-ux] {rel}: expected five sourced metrics in each of four annual panels and their no-JS fallbacks")
        for stale in ("$29,000", ">$600<"):
            if stale in page:
                failures.append(f"[product-ux] {rel}: superseded Transparency value remains: {stale!r}")
    donate = rendered.get("donate/index.html", "")
    es_donate = rendered.get("es/donate/index.html", "")
    for rel, page in (("donate/index.html", donate), ("es/donate/index.html", es_donate)):
        if 'campaign="colombia-earthquake-relief"' in page:
            failures.append(f"[product-ux] {rel}: emergency Donorbox campaign replaced regular giving")
        if page.count("https://donorbox.org/widgets.js") != 1 or page.count("<dbox-widget ") != 1:
            failures.append(f"[product-ux] {rel}: expected one Donorbox widget loader and form")
    for rel in ("earthquake-relief/index.html", "es/earthquake-relief/index.html"):
        page = rendered.get(rel, "")
        if 'campaign="powerful-children-colombia-donation-form"' in page:
            failures.append(f"[product-ux] {rel}: regular Donorbox campaign replaced emergency giving")
        if page.count("https://donorbox.org/widgets.js") != 1 or page.count("<dbox-widget ") != 1:
            failures.append(f"[product-ux] {rel}: expected one Donorbox widget loader and form")
    programs_index = rendered.get("programs/index.html", "")
    for slug in ("alpha-fc", "caminos-nativos", "mas-que-vencedores"):
        if f'data-program-location="{slug}"' not in programs_index or f'data-map-pin="{slug}"' not in programs_index:
            failures.append(f"[product-ux] programs/index.html: map/list relationship missing for {slug}")
    if donate.find('id="donation-form"') > donate.find('class="methods-section'):
        failures.append("[product-ux] donation form must appear before alternative methods")
    if "&amp;amp;" in all_html:
        failures.append("[product-ux] double-escaped public copy found")
    for rel in ("thank-you/index.html", "es/thank-you/index.html"):
        page = rendered.get(rel, "")
        if re.search(r"(?:location\.search|URLSearchParams|donor_name|donor_email|amount|transaction)", page, re.I):
            failures.append(f"[product-ux] {rel}: post-donation page must not read or reflect donor data")
    synthetic_phrases = [
        "A dash means", "URL-backed",
        "full record", "six destinations above", "Choose what works",
        "No figure reported", "Not reported", "No reportado", "Not published",
        "Not included in this report", "Compare all years",
        "does not include a separate", "does not list a separate total",
        "does not list a total for PCC", "no incluye un total separado",
        "No presenta un total para PCC",
        "Photograph pending", "Choose a program and year", "Choose a year",
        ">Covers<", ">Scope<", ">Source<", "PDF →", "PDF ↗",
        "Three Colombian organizations. Three departments of Colombia.",
        "A running record from the communities", "Part of the record",
        "This letter is the", "community record", "Results and reports",
    ]
    for phrase in synthetic_phrases:
        if phrase in all_html:
            failures.append(f"[product-ux] synthetic public phrase found: {phrase!r}")
    tracked_edit_artifacts = [
        "335233", "Más Aallá", "Ttablero", "reportletter", "anualcarta",
        "Risalralda", "Magdalenda", "wWays",
    ]
    for artifact in tracked_edit_artifacts:
        if artifact in all_html:
            failures.append(f"[product-ux] client-document tracked-edit artifact found: {artifact!r}")
    css = open(os.path.join(SITE, "assets", "pcc.css")).read()
    if re.search(r"\.program-card-link\s*\{[^}]*position\s*:\s*absolute", css, re.S):
        failures.append("[product-ux] program-card actions must remain in flow so copy cannot collide with them")
    if re.search(r"\.program-link\s*\{[^}]*position\s*:\s*absolute", css, re.S):
        failures.append("[product-ux] Home program actions must remain in flow so copy cannot collide with them")
    if ".program-card:first-child" in css:
        failures.append("[product-ux] mobile program cards must share one coherent layout")
    if "fonts.googleapis.com" in all_html or "fonts.gstatic.com" in all_html:
        failures.append("[product-ux] typography must not depend on a third-party render path")
    for font in ("archivo-latin.woff2",):
        if not os.path.isfile(os.path.join(SITE, "assets", "fonts", font)):
            failures.append(f"[product-ux] missing self-hosted type asset: {font}")
    if '@font-face' not in css or '/assets/fonts/archivo-latin.woff2' not in css:
        failures.append("[product-ux] self-hosted typefaces are not wired into the visual system")
    if "Geist Mono" in css or "geist-mono" in css:
        failures.append("[product-ux] owner-rejected Geist Mono must not load or render")
    if not re.search(r"\.home-caption,\s*\.crumb-strip,.*?font-family:\s*var\(--font-sans\)", css, re.S):
        failures.append("[product-ux] photographic captions and place labels must use the human-facing sans role")
    # Contract amendments, owner-approved 2026-08-10: outcome-scoped rules.
    # 1. No elevation on content surfaces; structural glass may carry one
    #    restrained hairline edge for legibility.
    GLASS_EDGE_SELECTORS = (".site-header", ".mobile-dock-link", ".menu-toggle", ".mobile-action-dock")
    for sel, body in re.findall(r"([^{}@]+)\{([^{}]*)\}", css):
        for decl in re.findall(r"box-shadow:\s*([^;]+)", body):
            decl = decl.strip()
            if not any(g in sel for g in GLASS_EDGE_SELECTORS):
                failures.append(f"[product-ux] elevation on a content surface: {sel.strip()[:70]}")
            elif decl != "none" and not re.fullmatch(
                    r"inset\s+0\s+1px\s+0\s+rgba\([^)]*\)", decl):
                failures.append(f"[product-ux] glass edge must be a single restrained hairline: {decl[:70]}")
    # 2. Gradient fields exist only on the Home hero ambient surface.
    for sel, body in re.findall(r"([^{}@]+)\{([^{}]*)\}", css):
        if "linear-gradient(" in body and ".home-hero-panel" not in sel:
            failures.append(f"[product-ux] gradient outside the hero ambient field: {sel.strip()[:70]}")
    if not re.search(r"\.home-hero-panel\s*\{[^}]*linear-gradient\(", css, re.S):
        failures.append("[product-ux] the Home hero ambient field gradient is missing")
    site_js = open(os.path.join(SITE, "assets", "pcc.js")).read()
    if "preserveLanguageContext" not in site_js or "target.search = window.location.search" not in site_js or "target.hash = window.location.hash" not in site_js:
        failures.append("[product-ux] language switching must preserve selected state and the current section")
    dock_collision_contract = (
        ".field-gallery-controls button", ".person-bio > summary", ".document-list a",
        ".graph-actions a", ".film-card", ".evidence-archive > summary",
    )
    for selector in dock_collision_contract:
        if selector not in site_js:
            failures.append(f"[product-ux] mobile dock collision coverage is missing {selector!r}")
    for rel, page in rendered.items():
        internal_links = re.findall(r'<a\b(?=[^>]*\bhref="(?:/|#))[^>]*>.*?</a>', page, re.S)
        if any("↗" in link for link in internal_links):
            failures.append(f"[product-ux] {rel}: internal navigation uses the external-link arrow")
            break
    # 3. Cross-document transitions stay conditional on instant navigation:
    #    allowed only with pair-scoped skip guards and prerender rules present.
    if "@view-transition" in css or "view-transition-name" in css:
        if "skipTransition" not in site_js or "speculationrules" not in site_js:
            failures.append("[product-ux] cross-document transitions require instant-navigation guards (pair-scoped skip + prerender)")
    if "mobile-dock-link.is-navigating" not in css or "aria-busy" not in site_js:
        failures.append("[product-ux] mobile dock must acknowledge a tap before navigation completes")
    for slug in ("alpha-fc", "caminos-nativos", "mas-que-vencedores"):
        page = rendered.get(f"programs/{slug}/index.html", "")
        if 'data-local-navigation' not in page:
            failures.append(f"[product-ux] programs/{slug}: missing scroll-aware local navigation")
        local_nav = re.search(r'<nav[^>]*data-local-navigation[^>]*>.*?</nav>', page, re.S)
        if local_nav and 'href="/donate/"' in local_nav.group(0):
            failures.append(f"[product-ux] programs/{slug}: local navigation duplicates the persistent Donate action")
    for year in (2022, 2023, 2024, 2025):
        page = rendered.get(f"stories/{year}-year-in-review/index.html", "")
        if 'data-local-navigation' not in page or 'aria-label="Back to All stories"' not in page:
            failures.append(f"[product-ux] stories/{year}: local rail must retain a return to All stories")



ES_FORBIDDEN_TOKENS = [
    ">Menu<", ">Donate<", ">Stories<", ">Impact<", ">Transparency<", ">About<",
    ">Play film<", ">Not reported<", ">Read the letter<", ">All programs<",
    ">Children reached<", ">Funds raised<", ">How PCC helps<", ">Ways to donate<",
    ">Our team<", ">Our values<", "Skip to main content", ">Organization<",
    ">Leaders<", ">Communities<", ">Annual results<", ">Participant retention<",
    ">Children currently reached<", ">Children · 2022<", " on YouTube<",
    'data-label="Year"', 'data-label="Children reached"', 'data-label="Raised"',
    'data-label="Letter"', 'data-label="Report"', 'data-label="Program spend"',
    'data-label="Operating"', 'data-label="Children"', ">Beyond a gift<",
    'aria-label="Switch to English"', 'aria-label="Keep exploring"',
    'aria-label="Year in review letters"',
    'aria-label="Artwork made by children in PCC programs"',
    'aria-label="Map showing PCC programs in Cabrera, Pereira, and Santa Marta"',
    'aria-label="PCC in ', ">Volunteer<", "Recommend a Colombian-led nonprofit",
    "Share feedback", "Volunteer%20with%20PCC", "Recommend%20a%20Colombian-led%20nonprofit",
    "Feedback%20for%20PCC",
]


def gate_bilingual(pages, failures):
    claims = load_json("data/content/claims.json")["claims"]
    pending = [c for c in claims if c.get("status") == "preview-pending" and not c.get("ownerDecision")]
    if pending:
        print(f"note: {len(pending)} preview-pending claim(s) render on the preview and BLOCK production cutover: "
              + ", ".join(c["id"] for c in pending))
    for page in pages:
        rel = os.path.relpath(page, SITE)
        if rel == "404.html":
            continue
        t = open(page).read()
        is_es = rel.startswith("es/") or rel == "es/index.html"
        path = "/" if rel == "index.html" else "/" + os.path.dirname(rel) + "/"
        if is_es:
            if '<html lang="es">' not in t:
                failures.append(f"[bilingual] {rel}: missing lang=es")
            counterpart = path[3:] or "/"
            if f'class="lang-toggle" href="{counterpart}"' not in t:
                failures.append(f"[bilingual] {rel}: toggle does not point to {counterpart}")
            for tok in ES_FORBIDDEN_TOKENS:
                if tok in t:
                    failures.append(f"[bilingual] {rel}: untranslated interface string {tok!r}")
        else:
            if f'class="lang-toggle" href="/es{path}"' not in t:
                failures.append(f"[bilingual] {rel}: toggle does not point to /es{path}")
        if 'hreflang="en"' not in t or 'hreflang="es"' not in t or 'hreflang="x-default"' not in t:
            failures.append(f"[bilingual] {rel}: incomplete hreflang set")


def main():
    failures = []
    # The editor is a private noindex tool, not a public content route. It has
    # its own shell and should not be counted in public route, bilingual, or
    # sitemap gates.
    pages = [page for page in sorted(glob.glob(os.path.join(SITE, "**", "index.html"), recursive=True))
             if os.path.relpath(page, SITE).split(os.sep, 1)[0] != "admin"] + \
        [os.path.join(SITE, "404.html")]
    if len(pages) < 12:
        failures.append(f"[structure] expected >=12 pages, found {len(pages)}")
    gate_structure(pages, failures)
    gate_validity(failures)
    gate_claims(pages, failures)
    gate_public_punctuation(pages, failures)
    gate_consent(pages, failures)
    gate_media(pages, failures)
    gate_bilingual(pages, failures)
    gate_home_conversion(failures)
    gate_product_ux(pages, failures)
    if failures:
        print("\n".join(failures))
        print(f"FAIL: {len(failures)} problems")
        sys.exit(1)
    print(f"OK: {len(pages)} pages — structure, HTML validity, claim registry, "
          "consent states, media policy, conversion and product UX safeguards all clean")


if __name__ == "__main__":
    main()
