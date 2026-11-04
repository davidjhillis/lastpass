#!/usr/bin/env python3
"""Build templates.html (page-type index) and components.html (page-building essentials).

The library follows the CMS model: content units are the trays an editor adds,
reorders and removes in Page Builder; components are the pieces that go inside
a unit's layout. Every example is cut from the page that uses it, so the
library always shows what is actually built. Re-run after changing any page:

    python3 tools/build-library.py
"""
import html as H
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def read(name):
    with open(os.path.join(ROOT, name), encoding="utf-8") as f:
        return f.read()


def extract(src, start):
    """Return the element that begins at the first match of `start`, tags balanced."""
    i = src.index(start)
    tag = re.match(r"<([a-z0-9-]+)", src[i:]).group(1)
    depth = 0
    for m in re.compile(r"<(/?)%s\b[^>]*?(/?)>" % tag).finditer(src, i):
        if m.group(1):
            depth -= 1
        elif not m.group(2):
            depth += 1
        if depth == 0:
            return src[i:m.end()]
    raise ValueError("unbalanced: " + start)


def keep_first(block, child_start, n):
    """Keep only the first n children that begin with child_start; keep the closing markup."""
    kids, pos = [], block.index(child_start)
    head = block[:pos]
    while True:
        j = block.find(child_start, pos)
        if j < 0:
            break
        k = extract(block[j:], child_start)
        kids.append(k)
        pos = j + len(k)
    return head + "\n".join(kids[:n]) + block[pos:]


def scope_ids(block, prefix):
    """Prefix ids and the attributes that point at them, so examples never collide."""
    for i in set(re.findall(r'\bid="([^"]+)"', block)):
        block = re.sub(r'(\b(?:id|aria-controls|aria-labelledby|for)=")%s"' % re.escape(i), r'\g<1>%s-%s"' % (prefix, i), block)
        block = block.replace('href="#%s"' % i, 'href="#%s-%s"' % (prefix, i))
    return block


PAGES = {
    "hub": ("hub-business.html", "Mini hub"),
    "saas": ("topic-saas-monitoring.html", "Topic overview, product"),
    "billing": ("topic-billing.html", "Topic overview, utility"),
    "faq": ("faq.html", "FAQ page"),
    "contact": ("contact-us.html", "Contact Us"),
    "releases": ("release-notes.html", "Release notes"),
    "downloads": ("downloads.html", "Downloads"),
    "issues": ("known-issues.html", "Known issue tracker"),
    "lifecycle": ("lifecycle.html", "Product lifecycle"),
}
SRC = {k: read(v[0]) for k, v in PAGES.items()}

# ---------------------------------------------------------------- content units
# slug, name, purpose, options, components inside, merges, variants (label, page, start, trim, stage class)
UNITS = [
    ("hero", "Hero", "Opens every page: the title, an intro, and optionally search, buttons and a media slot.",
     [("Layout", "Centered, or split with a media slot"), ("Weight", "Standard or marketing (dark, larger type)"),
      ("Search", "Off, all of support, or scoped to a product"), ("Media slot", "Image, screenshot, Vimeo, start-here list or platform download"),
      ("Extras", "Badge, up to 2 buttons, quick links bar, proof points")],
     ["Button", "Media", "Link list"], "4 hero variants, quick links, proof strip, start-here card, platform card",
     [("Standard", "faq", '<section class="t-hero', None, ""),
      ("Split, with media", "billing", '<section class="t-hero', None, ""),
      ("Marketing, with a screenshot", "saas", '<section class="mk-hero"', None, ""),
      ("Marketing, with search and a start-here list", "hub", '<section class="mk-hero"', None, "")]),
    ("feature", "Feature", "Media on one side and a message on the other, or a full-width banner that asks for one action.",
     [("Media side", "Left or right, or none for a banner"), ("Media", "Screenshot, photo or Vimeo, in a fixed frame"),
      ("Frame", "4:3 (default), 1:1 or 16:9, with a focus point for the crop"),
      ("Content", "Badge or kicker, heading, text, up to 4 ticks, up to 2 buttons or links"),
      ("Targeting", "Optional schedule and audience rule")],
     ["Media", "Button"], "feature tray, spotlight, CTA band, help banner",
     [("Media left, on white (try the options)", "saas", '<section class="u" data-bg="white" aria-labelledby="h-products"', None, "cl-stage--unit"),
      ("Media right, on cloud", "saas", '<section class="u" data-bg="cloud"', None, "cl-stage--unit"),
      ("Media right, on dark", "hub", '<section class="u" data-bg="dark"', None, "cl-stage--unit"),
      ("Banner, dark", "saas", '<div class="mk-cta"', None, ""),
      ("Banner, light", "hub", '<div class="t-help"', None, "")]),
    ("cards", "Cards", "A grid of cards. The card variant sets what each card shows; the source sets where they come from.",
     [("Card variant", "Category, article, icon, step, file, download, contact option"), ("Columns", "2, 3 or 4"),
      ("Background", "White, wash, dark"), ("Source", "Hand-picked, a DITA map branch, or records")],
     ["Card", "Button", "Link list", "Record"], "category, article, file, benefit, step, download and contact-option cards",
     [("Category, with links from the map", "hub", '<div class="t-cats">', ('<article class="t-cat"', 3), ""),
      ("Article", "hub", '<div class="t-cards"', ('<a class="t-card"', 3), ""),
      ("Icon, on dark", "saas", '<section class="mk-sec mk-dark"', None, ""),
      ("Steps", "saas", '<ol class="mk-steps"', None, "")]),
    ("faq", "FAQ", "Questions that expand. Items come from the shared FAQ library, so one answer can appear on many pages.",
     [("Items", "Picked from the FAQ library"), ("Heading", "Optional"), ("Open", "All closed, or first open")],
     ["FAQ item"], "FAQ group",
     [("Group", "hub", '<div class="t-faq"', None, "cl-stage--narrow")]),
    ("content", "Content", "Rich text for the body of a page, with link lists, tables, notices and video placed inside it.",
     [("Body", "Rich text, H2 and H3 only"), ("Inside", "Link list, table, notice, media"), ("Navigation", "Adds an “On this page” list from its H2s")],
     ["Link list", "Table", "Notice", "Media"], "link list, table, capability table, notice, video",
     [("Link list", "billing", '<ul class="t-links">', None, "cl-stage--narrow"),
      ("Table", "billing", '<div class="t-table"', None, "cl-stage--narrow"),
      ("Table, rich rows", "saas", '<div class="mk-caps"', ('<tr>\n            <th scope="row">', 3), "")]),
    ("records", "Record list", "Structured records from the product registry: release notes, known issues, downloads, lifecycle.",
     [("Record type", "Release note, known issue, download, product"), ("Display", "List, cards or table"),
      ("Filters", "Search and facets, optional"), ("Limit", "Newest n, or all with “Show more”")],
     ["Record", "Table", "Button"], "record list, filter panel, release entry, issue card, resolved list, lifecycle tables",
     [("List with filters", "releases", '<div class="rc-layout">', ('<li class="rn"', 2), ""),
      ("Compact list", "issues", '<ul class="ki-fixed"', ('<li>', 4), ""),
      ("Table", "lifecycle", '<div class="lc-pair"', None, "")]),
]

# ---------------------------------------------------------------- components (specimens are tiny, hand-made)
COMPONENTS = [
    ("Button", "Primary, secondary and arrow link. One primary per unit.", ["Hero", "Feature", "Cards", "Record list"],
     '<p style="display:flex;flex-wrap:wrap;gap:10px;margin:0"><a class="t-btn t-btn--brand" href="#">Primary</a><a class="t-btn t-btn--line" href="#">Secondary</a></p>'),
    ("Media", "Image, product screenshot or Vimeo video. Alt text or a title is required.", ["Hero", "Feature", "Cards"],
     '<img class="mk-shot" src="img/shot-saas-protect-categories.png" alt="SaaS Protect categories in the Admin Console" width="1935" height="926" loading="lazy">'),
    ("Card", "Title, text and a link, with an optional icon, kicker or image.", ["Cards"],
     '<a class="t-card" href="#" style="max-width:20rem"><p class="t-kicker">Article</p><h3>Access the Admin Console</h3><p>Sign in to manage users, policies and reporting.</p><span class="cta-link">Learn more</span></a>'),
    ("Link list", "Article links in one or two columns. Hand-picked, or filled from a map branch.", ["Content", "Hero", "Cards"],
     '<ul class="t-links" style="grid-template-columns:1fr"><li><a href="#">Update payment method</a></li><li><a href="#">Cancel LastPass Families</a></li></ul>'),
    ("Table", "Caption required; header row and column; scrolls inside its box on phones.", ["Content", "Record list"],
     '<div class="t-table"><table style="min-width:0"><caption>Example</caption><thead><tr><th scope="col">Task</th><th scope="col">Where</th></tr></thead><tbody><tr><th scope="row">Change seats</th><td><a href="#">Purchase licenses</a></td></tr></tbody></table></div>'),
    ("Notice", "Note, tip or notice. The same component as the notes imported from DITA, so articles and templates match.", ["Content"],
     '<div class="t-notice" style="margin:0"><img src="img/tip_icon.svg" alt="" width="20" height="20"><div><strong class="t-notice-label">Tip:</strong><p>One short message, styled exactly like a DITA note in an article.</p></div></div>'),
    ("FAQ item", "A question and answer, written once and reused on any page.", ["FAQ"],
     '<div class="t-faq"><div class="t-faq-item" id="spec-faq"><h3><button class="t-faq-q" type="button" aria-expanded="false" aria-controls="spec-faq-a">Is a password manager and VPN combination worth it?<span class="t-faq-chev" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg></span></button></h3><div class="t-faq-a" id="spec-faq-a" hidden><p>LastPass VPN uses the LastPass login you already have.</p></div></div></div>'),
    ("Record", "One release note, known issue, download or product, keyed to the product registry.", ["Record list", "Cards"],
     '<p style="margin:0;display:flex;flex-wrap:wrap;gap:8px;align-items:center"><span class="t-tag t-tag--new">New</span><span class="t-tag t-tag--improved">Improved</span><span class="t-tag t-tag--fixed">Fixed</span><span class="lc-status lc-active">Active</span><span class="ki-status">Workaround available</span></p>'),
]

AUTOMATIC = [("Header and footer", "From Site Control, on every page"), ("Breadcrumb", "From the page’s place in the site tree"),
             ("Hub switcher", "Lists every hub page"), ("On this page", "Built from a Content unit’s H2s"), ("Build notes", "Review aid; not in production")]

PAGE_UNITS = {
    "hub": ["hero", "cards", "records", "feature", "faq"], "saas": ["hero", "content", "feature", "cards", "faq"],
    "billing": ["hero", "content", "feature"], "faq": ["hero", "faq", "feature"], "contact": ["hero", "cards"],
    "releases": ["hero", "records"], "downloads": ["hero", "cards", "feature"], "issues": ["hero", "records"],
    "lifecycle": ["hero", "content", "records"],
}
UNAME = {u[0]: u[1] for u in UNITS}


def chrome(title, desc, main):
    src = SRC["billing"]
    a = src.index('<nav class="t-crumbs"')
    b = src.index("</main>") + len("</main>")
    out = src[:a] + main + src[b:]
    out = re.sub(r"<title>.*?</title>", "<title>%s</title>" % H.escape(title), out, count=1)
    return re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % H.escape(desc), out, count=1)


def slugify(s):
    return re.sub(r"\W+", "-", s.lower()).strip("-")


# ---------------------------------------------------------------- components.html
nav = "".join('<li><a href="#%s">%s</a></li>' % (u[0], u[1]) for u in UNITS) + '<li class="ul-nav-sep"><a href="#components">Components</a></li><li><a href="#automatic">Automatic</a></li>'
units_html = []
for slug, name, purpose, options, inside, merges, variants in UNITS:
    opts = "".join('<div><dt>%s</dt><dd>%s</dd></div>' % (H.escape(a), H.escape(b)) for a, b in options)
    vs = []
    if slug == "feature":
        vs.append('''<div class="ul-try" data-try="#ex-feature-0" role="group" aria-label="Try the Feature options">
  <span>Try the options</span>
  <div><b>Media</b><button type="button" data-set="media" data-val="left" aria-pressed="true">Left</button><button type="button" data-set="media" data-val="right" aria-pressed="false">Right</button></div>
  <div><b>Background</b><button type="button" data-set="bg" data-val="white" aria-pressed="true">White</button><button type="button" data-set="bg" data-val="wash" aria-pressed="false">Wash</button><button type="button" data-set="bg" data-val="cloud" aria-pressed="false">Cloud</button><button type="button" data-set="bg" data-val="dark" aria-pressed="false">Dark</button></div>
  <div><b>Frame</b><button type="button" data-set="ratio" data-val="4/3" aria-pressed="true">4:3</button><button type="button" data-set="ratio" data-val="1/1" aria-pressed="false">1:1</button><button type="button" data-set="ratio" data-val="16/9" aria-pressed="false">16:9</button></div>
</div>''')
    for n, (label, page, start, trim, stage) in enumerate(variants):
        block = extract(SRC[page], start)
        if trim:
            block = keep_first(block, *trim)
        vs.append('<figure class="ul-variant" id="ex-%s-%d"><figcaption>' % (slug, n) + '<b>%s</b><span>from <a href="%s">%s</a></span></figcaption><div class="cl-stage %s">%s</div></figure>' % (
            label, PAGES[page][0], PAGES[page][1], stage, scope_ids(block, "ex-%s-%d" % (slug, n))))
    units_html.append('''<section class="ul-unit" id="%s" aria-labelledby="h-%s">
  <div class="ul-head">
    <div>
      <p class="ul-kind">Content unit</p>
      <h2 id="h-%s">%s</h2>
      <p class="ul-purpose">%s</p>
      <p class="ul-merges"><b>Replaces</b> %s</p>
    </div>
    <dl class="ul-opts">%s
      <div><dt>Components</dt><dd><ul class="tp-chips">%s</ul></dd></div>
      <div><dt>Used on</dt><dd>%s</dd></div>
    </dl>
  </div>
  %s
</section>''' % (slug, slug, slug, name, purpose, merges, opts,
                 "".join('<li><a href="#c-%s">%s</a></li>' % (slugify(c), c) for c in inside),
                 ", ".join('<a href="%s">%s</a>' % (PAGES[k][0], PAGES[k][1]) for k, us in PAGE_UNITS.items() if slug in us), "\n  ".join(vs)))

comp_html = "".join('''<article class="ul-comp" id="c-%s">
  <h3>%s</h3><p>%s</p>
  <p class="ul-in">In %s</p>
  <div class="ul-spec">%s</div>
</article>''' % (slugify(n), n, d, ", ".join('<a href="#%s">%s</a>' % (u[0], u[1]) for u in UNITS if u[1] in used), spec) for n, d, used, spec in COMPONENTS)
auto_html = "".join('<li><b>%s</b><span>%s</span></li>' % (a, b) for a, b in AUTOMATIC)

components_main = '''<nav class="t-crumbs" aria-label="Breadcrumb">
  <ol>
    <li><a href="index.html">Home</a></li>
    <li><a href="templates.html">Page templates</a></li>
    <li><span aria-current="page">Page-building essentials</span></li>
  </ol>
</nav>

<main id="main">
<section class="t-hero t-hero--center t-hero--compact">
  <div class="t-hero-bg" aria-hidden="true"></div>
  <div class="t-hero-scrim" aria-hidden="true"></div>
  <div class="t-hero-in">
    <p class="t-eyebrow">LastPass support portal · design system</p>
    <h1>Page-building essentials</h1>
    <p class="t-hero-sub">%d content units that editors stack in Page Builder, and %d components that go inside them. Every page template is built from these.</p>
  </div>
</section>

<nav class="ul-nav" aria-label="Units and components"><div class="t-wrap"><ul>%s</ul></div></nav>

<div class="t-wrap ul-body">
  <div class="ul-model">
    <div><b>Content unit</b><span>A tray an editor adds, reorders or removes in Page Builder. Every unit has a <b>Background</b> option (white, wash, cloud, dark) and an optional heading; its other options pick the variant.</span></div>
    <div><b>Component</b><span>A piece placed inside a unit’s layout, such as a button, card or table.</span></div>
    <div><b>Automatic</b><span>Navigation the site builds itself. Editors never place it.</span></div>
  </div>
%s
<section class="ul-unit" id="components" aria-labelledby="h-components">
  <div class="ul-head"><div><p class="ul-kind">Inside the units</p><h2 id="h-components">Components</h2><p class="ul-purpose">The pieces editors place in a unit’s layout.</p></div></div>
  <div class="ul-comps">%s</div>
</section>
<section class="ul-unit" id="automatic" aria-labelledby="h-automatic">
  <div class="ul-head"><div><p class="ul-kind">Not authored</p><h2 id="h-automatic">Automatic</h2><p class="ul-purpose">Built by the site from the page tree and settings.</p></div></div>
  <ul class="ul-auto">%s</ul>
</section>
</div>
</main>''' % (len(UNITS), len(COMPONENTS), nav, "\n".join(units_html), comp_html, auto_html)

# ---------------------------------------------------------------- templates.html
TEMPLATES = [
    ("hub", "Request 1", "Marketing weight", "A homepage for one audience or product area: promise, scoped search, start-here steps, task cards, what’s new, a spotlight and help."),
    ("saas", "Request 2", "Marketing weight", "A product hub that sells and teaches: product hero, capabilities, features, benefits, setup steps and a closing call to action."),
    ("billing", "Request 2", "Help weight", "Breaks a support topic into sections of hand-picked articles, with a table, a notice and a video."),
    ("faq", "Request 3", "Help weight", "Questions grouped by product, collapsed until opened, each with a link that opens it directly."),
    ("contact", "Request 4", "Help weight", "Ways to get help matched to the visitor’s plan, with a preview switch for each audience."),
    ("releases", "Request 5", "Help weight", "All 351 releases from lastpass.com/upgrade.php as records, filterable by product, change type and text."),
    ("downloads", "Request 6", "Help weight", "The visitor’s platform first, then every download by operating system, versions read from the release notes."),
    ("issues", "Request 7", "Help weight", "Active issues with workarounds, and recent real fixes linked to the releases that shipped them."),
    ("lifecycle", "Request 8", "Help weight", "Status definitions beside every product, with statuses proposed from release history for LastPass to confirm."),
]
KIND = {"hub": "flex", "saas": "flex", "billing": "flex", "faq": "flex", "contact": "flex", "lifecycle": "flex",
        "releases": "record", "downloads": "record", "issues": "record"}
GAPS = [
    ("Record detail pages", "A page for one known issue (so support can link KI-0001) and one release-notes page per product with its own feed. Not designed yet."),
    ("Group by, on Cards", "Downloads groups cards into operating-system tabs. Today that is custom; it should be a Cards option so any grid can be grouped."),
    ("Audience rules", "Contact Us and the hub spotlight assume rules read from the SAML sign-in. The claims LastPass sends, and where editors set rules, are still open."),
    ("Video in a Feature", "The media frame takes Vimeo, but no tray shows one yet. It needs a poster, a play state and captions in the 4:3 frame."),
    ("Search for records", "Release notes, issues and downloads should be Coveo facets on the search page. The search template still shows articles only."),
]
cards = []
for k, req, weight, desc in TEMPLATES:
    us = PAGE_UNITS[k]
    cards.append('''<article class="tp-card">
  <a class="tp-thumb" href="%s" tabindex="-1" aria-hidden="true"><iframe src="%s" title="" loading="lazy" tabindex="-1" scrolling="no"></iframe></a>
  <div class="tp-copy">
    <p class="tp-tags"><span class="tp-tag">%s</span><span class="tp-tag tp-tag--%s">%s</span></p>
    <h3><a href="%s">%s</a></h3>
    <p>%s</p>
    <p class="tp-sub">%s · %d content unit%s</p>
    <ul class="tp-chips">%s</ul>
  </div>
</article>''' % (PAGES[k][0], PAGES[k][0], req, "mk" if weight.startswith("Marketing") else "help", weight, PAGES[k][0], PAGES[k][1], desc,
                 "Flex page" if KIND[k] == "flex" else "Record page type", len(us), "" if len(us) == 1 else "s", "".join('<li><a href="components.html#%s">%s</a></li>' % (u, UNAME[u]) for u in us)))

BASE = [("index.html", "Home"), ("reader.html", "Article"), ("search.html", "Search results"), ("contact.html", "Contact")]
templates_main = '''<nav class="t-crumbs" aria-label="Breadcrumb">
  <ol>
    <li><a href="index.html">Home</a></li>
    <li><span aria-current="page">Page templates</span></li>
  </ol>
</nav>

<main id="main">
<section class="t-hero t-hero--center t-hero--compact">
  <div class="t-hero-bg" aria-hidden="true"></div>
  <div class="t-hero-scrim" aria-hidden="true"></div>
  <div class="t-hero-in">
    <p class="t-eyebrow">LastPass support portal · design system</p>
    <h1>Page templates</h1>
    <p class="t-hero-sub">All eight page types LastPass asked for: six flex pages built only from the same %d content units, and three record page types.</p>
    <div class="t-hero-actions" style="justify-content:center"><a class="t-btn t-btn--brand" href="components.html">See the page-building essentials</a></div>
  </div>
</section>

<section class="t-section" aria-labelledby="h-flex">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-flex">Flex pages</h2><p>One page type. Editors stack content units in Page Builder, in any order, with any background. These six are starting layouts, not separate templates.</p></div></div>
    <div class="tp-grid">%s</div>
  </div>
</section>

<section class="t-section t-section--wash" aria-labelledby="h-record">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-record">Record page types</h2><p>Fixed layouts bound to one record type. They need their own page type for URLs, feeds and behavior that stacking units can’t give: filters and per-release links, platform detection and version lookups, issue status and subscriptions.</p></div></div>
    <div class="tp-grid">%s</div>
  </div>
</section>

<section class="t-section" aria-labelledby="h-gaps">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-gaps">Gaps</h2><p>What the templates still need before the build.</p></div></div>
    <ul class="tp-plans">%s</ul>
  </div>
</section>

<section class="t-section t-section--wash" aria-labelledby="h-base">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-base">Approved baseline</h2><p>The pages LastPass already approved. Every template shares their header, footer and brand tokens.</p></div></div>
    <ul class="tp-base">%s</ul>
  </div>
</section>
</main>''' % (len(UNITS), "\n".join(c for c, (k, *_r) in zip(cards, TEMPLATES) if KIND[k] == "flex"),
           "\n".join(c for c, (k, *_r) in zip(cards, TEMPLATES) if KIND[k] == "record"),
           "".join('<li class="tp-plan"><h3>%s</h3><p>%s</p></li>' % g for g in GAPS),
           "".join('<li><a href="%s">%s</a></li>' % (h, n) for h, n in BASE))

with open(os.path.join(ROOT, "components.html"), "w", encoding="utf-8") as f:
    f.write(chrome("Page-building essentials — LastPass Support", "The content units and components that build every LastPass support portal page template.", components_main))
with open(os.path.join(ROOT, "templates.html"), "w", encoding="utf-8") as f:
    f.write(chrome("Page templates — LastPass Support", "Index of the LastPass support portal page templates and the content units each one uses.", templates_main))
print("units:", len(UNITS), "| components:", len(COMPONENTS), "| templates:", len(TEMPLATES))
