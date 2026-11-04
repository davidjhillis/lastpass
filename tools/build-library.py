#!/usr/bin/env python3
"""Build templates.html (page-type index) and components.html (component library).

Every component example is cut from the page that uses it, so the library
always shows what is actually built. Re-run after changing any template page:

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
    depth, pos = 0, i
    pat = re.compile(r"<(/?)%s\b[^>]*?(/?)>" % tag)
    for m in pat.finditer(src, i):
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
    ids = set(re.findall(r'\bid="([^"]+)"', block))
    for i in ids:
        block = re.sub(r'(\b(?:id|aria-controls|aria-labelledby|for)=")%s"' % re.escape(i), r'\g<1>%s-%s"' % (prefix, i), block)
        block = block.replace('href="#%s"' % i, 'href="#%s-%s"' % (prefix, i))
    return block


PAGES = {
    "hub": ("hub-business.html", "Mini hub · LastPass Business"),
    "saas": ("topic-saas-monitoring.html", "Product hub · SaaS and AI Monitoring"),
    "billing": ("topic-billing.html", "Topic overview · Billing"),
    "faq": ("faq.html", "FAQ page"),
    "contact": ("contact-us.html", "Contact Us"),
    "releases": ("release-notes.html", "Release notes"),
    "downloads": ("downloads.html", "Downloads"),
    "issues": ("known-issues.html", "Known issues"),
    "lifecycle": ("lifecycle.html", "Product lifecycle"),
}
SRC = {k: read(v[0]) for k, v in PAGES.items()}

# group, slug, name, cms block, purpose, fields, used on, (page, start, trim), stage class
C = [
    ("Navigation", "breadcrumb", "Breadcrumb", "AncestorNavigation",
     "Shows where the page sits. Generated from the site tree; the last item is the current page.",
     [("Items", "Generated from ancestors; no authoring")], ["hub", "saas", "billing", "faq", "contact", "releases", "downloads", "issues", "lifecycle"],
     ("billing", '<nav class="t-crumbs"', None), ""),
    ("Navigation", "hub-switcher", "Hub switcher", "HubNavigation",
     "Moves between Mini hubs. Lists every hub page; the current one is highlighted and scrolled into view on phones.",
     [("Hubs", "Generated from every page of type Mini hub"), ("Label", "Text, default “Help hubs”")], ["hub"],
     ("hub", '<nav class="t-hubs"', None), ""),
    ("Navigation", "quick-links", "Quick links", "QuickLinks",
     "A floating bar of up to six shortcuts that overlaps the hero. Becomes a 3-column grid on phones.",
     [("Links", "Up to 6: label, icon, link")], ["hub"],
     ("hub", '<nav class="t-quick"', None), "cl-stage--quick"),
    ("Navigation", "in-page-nav", "On this page", "SectionNavigation",
     "A sticky list of the page’s H2 sections that highlights the one in view. Becomes chips on narrow screens.",
     [("Items", "Generated from the page’s section headings")], ["billing", "faq"],
     ("billing", '<nav class="t-ov-nav"', None), "cl-stage--narrow"),

    ("Heroes", "hero-standard", "Hero, standard", "HeroBand",
     "A centered title band in the brand gradient. Use on utility pages such as the FAQ.",
     [("Eyebrow", "Text"), ("Title", "Text, becomes the H1"), ("Intro", "Text")], ["faq", "contact", "releases", "issues", "lifecycle"],
     ("faq", '<section class="t-hero', None), ""),
    ("Heroes", "hero-media", "Hero, media", "HeroBand (media)",
     "Copy and buttons on the left, an image or Vimeo video on the right.",
     [("Eyebrow, title, intro", "Text"), ("Buttons", "Up to 2"), ("Media", "Image, or Vimeo URL with a required title")], ["billing", "downloads"],
     ("billing", '<section class="t-hero', None), ""),
    ("Heroes", "hero-hub", "Hero, hub", "HeroBand (hub)",
     "Marketing weight for a hub: a big promise, search scoped to the hub, and a numbered start-here card.",
     [("Badge, title, intro", "Text"), ("Search scope", "Product facet sent to Coveo"), ("Start here", "Up to 4 links with a short description")], ["hub"],
     ("hub", '<section class="mk-hero"', None), ""),
    ("Heroes", "hero-product", "Hero, product", "HeroBand (product)",
     "Marketing weight for a product hub: badge, headline, two calls to action and a product visual.",
     [("Badge", "Plan + product"), ("Title, intro", "Text"), ("Buttons", "Primary and secondary"), ("Fine print", "Text with a link"), ("Visual", "Screenshot, image or Vimeo")], ["saas"],
     ("saas", '<section class="mk-hero"', None), ""),
    ("Heroes", "proof-strip", "Proof strip", "ProofPoints",
     "Four short claims directly under a product hero.",
     [("Points", "Up to 4: bold label + one line")], ["saas"],
     ("saas", '<section class="mk-points"', None), ""),

    ("Content", "category-cards", "Category cards", "CategoryCards",
     "Task-led cards, each with an icon, a summary and the first links of its guide.",
     [("Icon, title, summary", "Per card"), ("Links", "Hand-picked, or the first entries of a DITA map branch"), ("More link", "Text + link")], ["hub"],
     ("hub", '<div class="t-cats">', ('<article class="t-cat"', 3)), ""),
    ("Content", "article-cards", "Article cards", "PopularTopics",
     "Cards for individual articles: type, title, summary and a Learn more link.",
     [("Articles", "Picked by the editor; later ranked by Coveo usage")], ["hub"],
     ("hub", '<div class="t-cards"', ('<a class="t-card"', 3)), ""),
    ("Content", "link-list", "Link list", "LinkList",
     "A two-column list of article links under a section heading.",
     [("Links", "Hand-picked; optionally “add all from a map branch”")], ["billing"],
     ("billing", '<div data-note="LinkList, hand-picked · editors', None), "cl-stage--narrow"),
    ("Content", "file-links", "File links", "LinkList (files)",
     "Links to downloadable guides and templates, with a file-type badge.",
     [("Files", "Imported downloadables: title, type, label")], ["hub"],
     ("hub", '<div class="t-files"', None), ""),
    ("Content", "table", "Table", "Table",
     "A data table with a required caption, header row and header column. Scrolls inside its box on phones.",
     [("Caption", "Required"), ("Header row / column", "On or off"), ("Layout", "One table, or two side by side")], ["billing"],
     ("billing", '<div class="t-table"', None), "cl-stage--narrow"),
    ("Content", "capability-table", "Capability table", "CapabilityTable",
     "Capability, what it does, and the articles that show how. Stacks into cards on phones.",
     [("Rows", "Icon, capability, description, article links")], ["saas"],
     ("saas", '<div class="mk-caps"', ('<tr>\n            <th scope="row">', 3)), ""),
    ("Content", "notice", "Notice", "Notice",
     "An info, tip or warning callout inside content.",
     [("Type", "Info, tip, warning"), ("Text", "Rich text")], ["billing", "lifecycle"],
     ("billing", '<div class="t-notice', None), "cl-stage--narrow"),
    ("Content", "video", "Video", "Media",
     "A poster that swaps to the Vimeo player when clicked, so pages load fast.",
     [("Vimeo URL", "Required"), ("Title", "Required, used by screen readers"), ("Poster", "Image")], ["billing"],
     ("billing", '<button class="t-video"', None), "cl-stage--video"),
    ("Content", "feature-tray", "Feature tray", "FeatureTray",
     "Media on one side, copy and a link on the other. Alternate sides down the page.",
     [("Media", "Image, screenshot or Vimeo"), ("Kicker, title, text", "Text"), ("Ticks", "Up to 4"), ("Links", "Primary arrow link + optional second link"), ("Side", "Media left or right")], ["saas", "hub"],
     ("saas", '<div class="mk-trays">', ('<article class="mk-tray', 2)), ""),
    ("Content", "benefits", "Benefits band", "BenefitCards",
     "A dark band of four benefit cards with icons.",
     [("Kicker, heading", "Text"), ("Cards", "Up to 4: icon, title, text")], ["saas"],
     ("saas", '<section class="mk-sec mk-dark"', None), ""),
    ("Content", "steps", "Steps", "Steps",
     "Numbered setup steps, each linking to the full instructions.",
     [("Steps", "Up to 4: title, text, link")], ["saas"],
     ("saas", '<ol class="mk-steps"', None), ""),

    ("Records and reuse", "record-list", "Record list", "RecordList",
     "Structured records, here release notes, filtered by product and shown newest first.",
     [("Record type", "Release notes, known issues, lifecycle"), ("Filters", "Product, status"), ("Limit", "Number shown")], ["hub"],
     ("hub", '<ol class="t-records"', None), ""),
    ("Records and reuse", "faq", "FAQ group", "FAQGroup",
     "Expandable questions. Each FAQ item is written once and reused on any page, and can feed lastpass.com.",
     [("Heading", "Text"), ("Items", "Picked FAQ items: question, answer, products")], ["faq", "hub", "saas"],
     ("hub", '<div class="t-faq"', None), "cl-stage--narrow"),

    ("Records and reuse", "filter-panel", "Filter panel", "RecordFilters",
     "Search plus facet checkboxes with live counts. Facets come from the product registry.",
     [("Record type", "Which records to filter"), ("Facets", "Product, change type, status")], ["releases"],
     ("releases", '<aside class="rc-side"', None), "cl-stage--narrow"),
    ("Records and reuse", "release-entry", "Release entry", "ReleaseNote",
     "One release: date, product, version, platform chips and typed items, with a stable link.",
     [("Product, platforms", "From the product registry"), ("Version, date", "Text, date"), ("Items", "Type (New, Improved, Changed, Fixed, Security, Removed) + text")], ["releases"],
     ("releases", '<ol class="rn-list"', ('<li class="rn"', 2)), ""),
    ("Records and reuse", "platform-card", "Platform card", "DownloadLead",
     "Recommends the download for the visitor’s operating system, with a way to see the rest.",
     [("Lead download per OS", "Picked from the download records")], ["downloads"],
     ("downloads", '<div class="dl-hero-card"', None), "cl-stage--narrow"),
    ("Records and reuse", "download-cards", "Download cards", "DownloadList",
     "Downloads per operating system in tabs. Version and date are read from the newest release note.",
     [("Downloads", "Name, text, link, product and platform from the registry")], ["downloads"],
     ("downloads", '<div class="dl-grid"', ('<article class="dl-card"', 3)), ""),
    ("Records and reuse", "issue-card", "Known issue", "KnownIssue",
     "A confirmed issue: ID, status, product, affected versions, workaround and the release that fixes it.",
     [("ID, title, status", "Investigating, Workaround available, Fix scheduled, Resolved"), ("Product, platforms, versions", "From the registry"), ("Workaround", "Rich text"), ("Fixed in", "Link to a release note record")], ["issues"],
     ("issues", '<article class="ki"', None), ""),
    ("Records and reuse", "resolved-list", "Resolved list", "RecordList (fixes)",
     "Recent fixes, each linked to the release that shipped it.",
     [("Window", "e.g. last six months"), ("Source", "Fixed items in release notes")], ["issues"],
     ("issues", '<ul class="ki-fixed"', ('<li>', 4)), ""),
    ("Records and reuse", "lifecycle-tables", "Lifecycle tables", "LifecycleTable",
     "Status definitions beside the product table (the original T3 layout). Stacks on phones.",
     [("Definitions", "Status, meaning"), ("Products", "From the registry: version, last release, status")], ["lifecycle"],
     ("lifecycle", '<div class="lc-pair"', None), ""),
    ("Calls to action", "contact-options", "Contact options", "ContactOption",
     "Ways to get help, each with an audience rule. The preview switch shows each audience; in production the sign-in decides.",
     [("Channel", "Title, text, button"), ("Audience", "Signed out, Free, Premium or Families, Business admin")], ["contact"],
     ("contact", '<div class="ct-grid"', None), ""),
    ("Calls to action", "spotlight", "Spotlight", "Spotlight",
     "One scheduled promotion with a visual. Can be shown only to a chosen audience.",
     [("Badge, title, text", "Text"), ("Buttons", "Up to 2"), ("Visual", "Screenshot or image"), ("Schedule", "Start and end dates"), ("Audience", "Rule, e.g. Business admins without Max")], ["hub"],
     ("hub", '<div class="mk-spot"', None), ""),
    ("Calls to action", "contact-band", "Contact band", "ContactButton",
     "Ends a help page with a way to get help.",
     [("Title, text", "Text"), ("Buttons", "Up to 2"), ("Audience", "Signed-in users see their plan’s channels (phase 4)")], ["hub", "billing", "faq", "downloads"],
     ("hub", '<div class="t-help"', None), ""),
    ("Calls to action", "cta-band", "CTA band", "CTABand",
     "Ends a product hub with a strong next step.",
     [("Title, text", "Text"), ("Buttons", "Primary and secondary"), ("Audience", "e.g. Max admins see “Enable”, others see the trial")], ["saas"],
     ("saas", '<div class="mk-cta"', None), ""),
]


def example(page, start, trim):
    block = extract(SRC[page], start)
    if trim:
        block = keep_first(block, *trim)
    return block


def chrome(title, desc, main):
    src = SRC["billing"]
    a = src.index('<nav class="t-crumbs"')
    b = src.index("</main>") + len("</main>")
    out = src[:a] + main + src[b:]
    out = re.sub(r"<title>.*?</title>", "<title>%s</title>" % H.escape(title), out, count=1)
    out = re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % H.escape(desc), out, count=1)
    return out


def page_link(k):
    return '<a href="%s">%s</a>' % (PAGES[k][0], PAGES[k][1])


# ---------------------------------------------------------------- components
groups = []
for g, *_ in C:
    if g not in groups:
        groups.append(g)

nav = []
for g in groups:
    items = "".join('<li><a href="#%s">%s</a></li>' % (s, n) for gg, s, n, *_ in C if gg == g)
    nav.append('<p class="cl-nav-group">%s</p><ul>%s</ul>' % (g, items))

body = []
for g in groups:
    body.append('<h2 class="cl-group" id="group-%s">%s</h2>' % (re.sub(r"\W+", "-", g.lower()), g))
    for gg, slug, name, cms, purpose, fields, used, (page, start, trim), stage in C:
        if gg != g:
            continue
        rows = "".join("<tr><th scope=\"row\">%s</th><td>%s</td></tr>" % (H.escape(a), H.escape(b)) for a, b in fields)
        ex = scope_ids(example(page, start, trim), "ex-" + slug)
        body.append('''<section class="cl-item" id="%s" aria-labelledby="h-%s">
  <header class="cl-item-head">
    <h3 id="h-%s">%s</h3>
    <code>%s</code>
  </header>
  <p class="cl-purpose">%s</p>
  <div class="cl-meta">
    <div class="t-table cl-fields"><table><caption>Author fields</caption><tbody>%s</tbody></table></div>
    <p class="cl-used"><span>Used on</span>%s</p>
  </div>
  <div class="cl-stage %s"><p class="cl-stage-label" aria-hidden="true">Live example · from %s</p>
%s
  </div>
</section>''' % (slug, slug, slug, name, cms, purpose, rows, " ".join(page_link(k) for k in used), stage, PAGES[page][1], ex))

components_main = '''<nav class="t-crumbs" aria-label="Breadcrumb">
  <ol>
    <li><a href="index.html">Home</a></li>
    <li><a href="templates.html">Page templates</a></li>
    <li><span aria-current="page">Component library</span></li>
  </ol>
</nav>

<main id="main">
<section class="t-hero t-hero--center t-hero--compact">
  <div class="t-hero-bg" aria-hidden="true"></div>
  <div class="t-hero-scrim" aria-hidden="true"></div>
  <div class="t-hero-in">
    <p class="t-eyebrow">LastPass support portal · design system</p>
    <h1>Component library</h1>
    <p class="t-hero-sub">%d blocks that build the new page templates. Each example below is taken from the page that uses it.</p>
  </div>
</section>

<div class="t-wrap">
<div class="t-ov cl-layout">
  <nav class="t-ov-nav cl-nav" aria-label="Components">%s</nav>
  <div class="cl-body">%s</div>
</div>
</div>
</main>''' % (len(C), "".join(nav), "\n".join(body))

# ---------------------------------------------------------------- templates index
used_by = {k: [(s, n) for g, s, n, cms, p, f, used, src, st in C if k in used] for k in PAGES}

TEMPLATES = [
    ("hub", "Mini hub", "Request 1", "Marketing weight",
     "A homepage for one audience or product area: promise, scoped search, start-here steps, task cards, what’s new, a spotlight and help."),
    ("saas", "Topic overview, product", "Request 2", "Marketing weight",
     "A product hub that sells and teaches: product hero, capabilities, feature trays, benefits, setup steps and a closing call to action."),
    ("billing", "Topic overview, utility", "Request 2", "Help weight",
     "Breaks a support topic into sections of hand-picked articles, with a table, a notice and a video."),
    ("faq", "FAQ page", "Request 3", "Help weight",
     "Questions grouped by product, collapsed until opened, each with a link that opens it directly."),
    ("contact", "Contact Us", "Request 4", "Help weight",
     "Ways to get help matched to the visitor’s plan, with a preview switch for each audience."),
    ("releases", "Release notes", "Request 5", "Help weight",
     "All 351 releases from lastpass.com/upgrade.php as records, filterable by product, change type and text."),
    ("downloads", "Downloads", "Request 6", "Help weight",
     "The visitor’s platform first, then every download by operating system, versions read from the release notes."),
    ("issues", "Known issue tracker", "Request 7", "Help weight",
     "Active issues with workarounds, and recent real fixes linked to the releases that shipped them."),
    ("lifecycle", "Product lifecycle", "Request 8", "Help weight",
     "Status definitions beside every product, with statuses proposed from release history for LastPass to confirm."),
]
cards = []
for k, name, req, weight, desc in TEMPLATES:
    chips = "".join('<li><a href="components.html#%s">%s</a></li>' % (s, n) for s, n in used_by[k])
    cards.append('''<article class="tp-card">
  <a class="tp-thumb" href="%s" tabindex="-1" aria-hidden="true"><iframe src="%s" title="" loading="lazy" tabindex="-1" scrolling="no"></iframe></a>
  <div class="tp-copy">
    <p class="tp-tags"><span class="tp-tag">%s</span><span class="tp-tag tp-tag--%s">%s</span></p>
    <h3><a href="%s">%s</a></h3>
    <p>%s</p>
    <p class="tp-sub">Built from %d component%s</p>
    <ul class="tp-chips">%s</ul>
  </div>
</article>''' % (PAGES[k][0], PAGES[k][0], req, "mk" if weight.startswith("Marketing") else "help", weight, PAGES[k][0], name, desc, len(used_by[k]), "" if len(used_by[k]) == 1 else "s", chips))

PLANNED = []
planned = ""

BASE = [("index.html", "Home"), ("reader.html", "Article"), ("search.html", "Search results"), ("contact.html", "Contact")]
base = "".join('<li><a href="%s">%s</a></li>' % (h, n) for h, n in BASE)

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
    <p class="t-hero-sub">All eight page types LastPass asked for, built on the approved design. Hubs carry marketing weight; help pages stay quiet.</p>
    <div class="t-hero-actions" style="justify-content:center"><a class="t-btn t-btn--brand" href="components.html">Open the component library</a></div>
  </div>
</section>

<section class="t-section" aria-labelledby="h-built">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-built">Designed</h2><p>Open a page to see it at full size. Use <b>Show build notes</b> on any page to see where each block’s content comes from.</p></div></div>
    <div class="tp-grid">%s</div>
  </div>
</section>

%s
<section class="t-section" aria-labelledby="h-base">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-base">Approved baseline</h2><p>The pages LastPass already approved. Every template shares their header, footer and brand tokens.</p></div></div>
    <ul class="tp-base">%s</ul>
  </div>
</section>
</main>''' % ("\n".join(cards), planned, base)

with open(os.path.join(ROOT, "components.html"), "w", encoding="utf-8") as f:
    f.write(chrome("Component library — LastPass Support", "The blocks that build the LastPass support portal page templates, with live examples and author fields.", components_main))
with open(os.path.join(ROOT, "templates.html"), "w", encoding="utf-8") as f:
    f.write(chrome("Page templates — LastPass Support", "Index of the new LastPass support portal page templates and the components each one uses.", templates_main))
print("components:", len(C), "| templates:", len(TEMPLATES))
