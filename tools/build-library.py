#!/usr/bin/env python3
"""Build templates.html (page types) and components.html (page-building essentials).

The scope is deliberately small: one Flex page type that editors build from
five trays (content units) in Page Builder, plus three special page types for
pages trays can't build (Release notes, Downloads, Known issues). Components
are the pieces placed inside a tray. Every example is cut from the page that
uses it, so the library always shows what is built. Re-run after changing a page:

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


def slugify(s):
    return re.sub(r"\W+", "-", s.lower()).strip("-")


PAGES = {
    "hub": ("hub-business.html", "Mini hub"),
    "saas": ("topic-saas-monitoring.html", "Topic overview, product"),
    "billing": ("topic-billing.html", "Topic overview, utility"),
    "faq": ("faq.html", "FAQ page"),
    "contact": ("contact-us.html", "Contact Us"),
    "lifecycle": ("lifecycle.html", "Product lifecycle"),
    "releases": ("release-notes.html", "Release notes"),
    "downloads": ("downloads.html", "Downloads"),
    "issues": ("known-issues.html", "Known issues"),
}
SRC = {k: read(v[0]) for k, v in PAGES.items()}
import json
SCHEMA = json.loads(read("data/schema.json"))
TYPES = SCHEMA["types"]


def element_name(f):
    """The XDR element name tools/schema-gen.mjs writes for this field."""
    n, t = f["name"], f["type"]
    if t in ("component[]", "link[]", "pagelink[]"):
        return "xpowerlist_" + (n + "List" if n.endswith("s") else n + "s")
    return {"rich": "xhtml_", "image": "xpowerasset_", "asset": "xpowerasset_", "link": "xpowerlink_", "pagelink": "xpowerlink_",
            "component": "xpowercomponent_"}.get(t, "") + n if t not in ("categories", "trays") else n


def schema_groups(groups):
    """Editor-facing schema: fields in the groups the edit form shows, with plain types and options."""
    out = []
    for g in groups:
        items = []
        for f in g["fields"]:
            vals = ""
            if f.get("values"):
                vals = '<p class="sf-vals">%s</p>' % " · ".join(
                    ('<b>%s</b> <span>default</span>' % H.escape(v)) if v == f.get("default") else H.escape(v) for v in f["values"])
            elif f.get("default"):
                vals = '<p class="sf-vals"><span>Default</span> <b>%s</b></p>' % H.escape(f["default"])
            items.append('<li class="sf"><div class="sf-top"><b class="sf-label">%s</b>%s<span class="sf-type">%s</span></div>%s%s<dl class="sf-meta"><div><dt>Element</dt><dd><code>%s</code></dd></div><div><dt>CMS type</dt><dd>%s</dd></div></dl></li>' % (
                H.escape(f["label"]), '<span class="sf-req">Required</span>' if f["required"] else "", TYPES.get(f["type"], f["type"]),
                '<p class="sf-help">%s</p>' % H.escape(f["help"]) if f.get("help") else "", vals, element_name(f), SCHEMA["cms_types"][f["type"]]))
        n = len(g["fields"])
        out.append('<section class="sg"><h4 class="sg-h">%s <span>%d field%s</span></h4>%s<ul class="sg-fields">%s</ul></section>' % (
            H.escape(g["label"]), n, "" if n == 1 else "s", '<p class="sg-help">%s</p>' % H.escape(g["help"]) if g.get("help") else "", "".join(items)))
    return '<div class="sg-wrap">%s</div>' % "".join(out)


def schema_tree(name, friendly, kind, groups):
    """The schema as Schema Designer lists it: schema, then each group block and its elements, in order."""
    rows = []
    for g in groups:
        rows.append('<li class="st-group"><span class="st-ico" aria-hidden="true">▾</span><code>xpowergroupstart_%s</code><span class="st-lab">%s</span><span class="st-type">Group</span></li>' % (
            re.sub(r"[^A-Za-z0-9]", "", g["label"]), H.escape(g["label"])))
        for f in g["fields"]:
            rows.append('<li class="st-el"><span class="st-ico" aria-hidden="true">%s</span><code>%s</code><span class="st-lab">%s%s</span><span class="st-type">%s</span></li>' % (
                "◇" if f["type"] in ("categories", "trays") else "·", element_name(f), H.escape(f["label"]),
                ' <b class="st-req" title="Required">*</b>' if f["required"] else "", SCHEMA["cms_types"][f["type"]]))
        rows.append('<li class="st-end"><code>xpowergroupend_</code></li>')
    return ('<figure class="st"><figcaption><span class="st-kind">%s</span><b>%s</b><span>Friendly name “%s” · DSS</span></figcaption>'
            '<ol>%s</ol><p class="st-note">◇ not a schema element: tags are taxonomy on the item; trays are the Page Builder area. * required.</p></figure>') % (
        kind, name, H.escape(friendly), "".join(rows))


def schema_view(name, friendly, kind, groups, lede=""):
    return '%s%s<h4 class="sc-h">Field details</h4>%s' % (lede, schema_tree(name, friendly, kind, groups), schema_groups(groups))


def tray_groups(slug):
    return SCHEMA["trays"][slug]["groups"] + [g for g in SCHEMA["shared_tray_groups"] if slug not in g.get("skip", [])]


def tabs(slug, panels):
    """panels: [(label, html)]. Accessible tablist; the first panel is open."""
    btns = "".join('<button type="button" role="tab" id="tab-%s-%d" aria-controls="panel-%s-%d" aria-selected="%s"%s>%s</button>' % (
        slug, i, slug, i, "true" if i == 0 else "false", "" if i == 0 else ' tabindex="-1"', lab) for i, (lab, _) in enumerate(panels))
    pans = "".join('<div role="tabpanel" id="panel-%s-%d" aria-labelledby="tab-%s-%d" class="sc-panel"%s>%s</div>' % (
        slug, i, slug, i, "" if i == 0 else " hidden", html) for i, (_, html) in enumerate(panels))
    return '<div class="sc-tabs" data-tabs><div class="sc-tablist" role="tablist" aria-label="View">%s</div>%s</div>' % (btns, pans)

SHARED = [("Background", "White, wash, cloud or dark"),
          ("Audience", "Metadata tag: Everyone, Signed out, Free, Premium or Families, Business admin")]

# ---------------------------------------------------------------- flex trays
# slug, name, purpose, options, components inside, replaces, variants (label, page, start, trim, stage class)
TRAYS = [
    ("hero", "Hero", "Opens every page: the title, an intro, and optionally search, buttons and a media slot.",
     [("Layout", "Centered, or split with a media slot"), ("Weight", "Standard or marketing (dark, larger type)"),
      ("Search", "Off, all of support, or scoped to a product"), ("Media slot", "Image, screenshot or start-here list"),
      ("Extras", "Badge, up to 2 buttons, quick links bar, proof points")],
     [], "4 hero variants, quick links, proof strip, start-here card",
     [("Standard", "faq", '<section class="t-hero', None, ""),
      ("Split, with media", "billing", '<section class="t-hero', None, ""),
      ("Marketing, with a screenshot", "saas", '<section class="mk-hero"', None, ""),
      ("Marketing, with search and a start-here list", "hub", '<section class="mk-hero"', None, "")]),
    ("feature", "Feature", "Media on one side and a message on the other, or a full-width banner that asks for one action.",
     [("Media side", "Left or right, or none for a banner"), ("Media", "Screenshot or photo, in a fixed frame"),
      ("Frame", "4:3 (default), 1:1 or 16:9, with a focus point for the crop"),
      ("Content", "Badge or kicker, heading, text, up to 4 ticks, up to 2 buttons or links")],
     [], "feature tray, spotlight, CTA band, help banner",
     [("Media left, on white (try the options)", "saas", '<section class="u" data-bg="white" aria-labelledby="h-products"', None, "cl-stage--unit"),
      ("Media right, on cloud", "saas", '<section class="u" data-bg="cloud"', None, "cl-stage--unit"),
      ("Media right, on dark", "hub", '<section class="u" data-bg="dark"', None, "cl-stage--unit"),
      ("Banner, dark", "saas", '<div class="mk-cta"', None, ""),
      ("Banner, light", "hub", '<div class="t-help"', None, "")]),
    ("cards", "Cards", "A grid of cards. The card variant sets what each card shows; the source sets where they come from.",
     [("Card variant", "Category, article, icon, step, file, contact option"), ("Columns", "2, 3 or 4"),
      ("Source", "Hand-picked, or a DITA map branch")],
     ["Card"], "category, article, file, benefit, step and contact-option cards",
     [("Category, with links from the map", "hub", '<div class="t-cats">', ('<article class="t-cat"', 3), ""),
      ("Article", "hub", '<div class="t-cards"', ('<a class="t-card"', 3), ""),
      ("Icon, on dark", "saas", '<section class="mk-sec mk-dark"', None, ""),
      ("Steps", "saas", '<ol class="mk-steps"', None, "")]),
    ("faq", "FAQ", "Questions that expand. Items come from the shared FAQ library, so one answer can appear on many pages.",
     [("Items", "Picked from the FAQ library"), ("Heading", "Optional"), ("Open", "All closed, or first open")],
     ["FAQ item"], "FAQ group",
     [("Group", "hub", '<div class="t-faq"', None, "cl-stage--narrow")]),
    ("content", "Content", "Rich text for the body of a page, with link lists, tables, notices and short lists placed inside it.",
     [("Body", "Rich text, H2 and H3 only"), ("Inside", "Link list, table, notice, media"), ("Navigation", "Adds an “On this page” list from its H2s")],
     ["Table", "Notice"], "link list, tables, capability table, notice, recent-items list",
     [("Link list", "billing", '<ul class="t-links">', None, "cl-stage--narrow"),
      ("Table", "billing", '<div class="t-table"', None, "cl-stage--narrow"),
      ("Two tables, side by side", "lifecycle", '<div class="lc-pair"', None, ""),
      ("Table, rich rows", "saas", '<div class="mk-caps"', ('<tr>\n            <th scope="row">', 3), "")]),
]
TNAME = {t[0]: t[1] for t in TRAYS}

# ---------------------------------------------------------------- special page types
SPECIAL = [
    ("releases", "Release notes", "Every release as a record, newest first, with filters and a stable link per release.",
     "Needs per-release URLs, a feed and filtering across 351 records, migrated from lastpass.com/upgrade.php.",
     [("Records", "Release: product, version, date, platforms, typed items"), ("Behavior", "Search, product and change-type filters, Show more, links"),
      ("Source", "Migrated once, then authored in the CMS")],
     [("Filters and release list", "releases", '<div class="rc-layout">', ('<li class="rn"', 2), "")]),
    ("downloads", "Downloads", "The visitor’s platform first, then every download by operating system.",
     "Needs platform detection and versions read from the release records, so downloads never show a stale version.",
     [("Records", "Download: name, text, link, product, platform"), ("Behavior", "Platform detection, operating-system tabs"),
      ("Versions", "Read from the newest release record")],
     [("Platform card", "downloads", '<div class="dl-hero-card"', None, "cl-stage--narrow"),
      ("Download cards", "downloads", '<div class="dl-grid"', ('<article class="dl-card"', 3), "")]),
    ("issues", "Known issues", "Confirmed issues with workarounds, and recent fixes linked to their releases.",
     "Needs an issue workflow (status, workaround, fixed-in release) and an empty state when nothing is open.",
     [("Records", "Issue: ID, title, status, product, versions, workaround, fixed in"), ("Behavior", "Active and resolved views"),
      ("Workflow", "Investigating, Workaround available, Fix scheduled, Resolved")],
     [("Issue record", "issues", '<article class="ki"', None, ""),
      ("Recently resolved", "issues", '<ul class="ki-fixed"', ('<li>', 4), "")]),
]

# ---------------------------------------------------------------- components (specimens are tiny, hand-made)
COMPONENTS = [
    ("Card", "Title, text and a link, with an optional icon, kicker or image.", ["Cards"],
     '<a class="t-card" href="#" style="max-width:20rem"><p class="t-kicker">Article</p><h3>Access the Admin Console</h3><p>Sign in to manage users, policies and reporting.</p><span class="cta-link">Learn more</span></a>'),
    ("Table", "Caption required; header row and column; scrolls inside its box on phones.", ["Content"],
     '<div class="t-table"><table style="min-width:0"><caption>Example</caption><thead><tr><th scope="col">Task</th><th scope="col">Where</th></tr></thead><tbody><tr><th scope="row">Change seats</th><td><a href="#">Purchase licenses</a></td></tr></tbody></table></div>'),
    ("Notice", "Note, tip or notice. The same component as the notes imported from DITA, so articles and pages match.", ["Content"],
     '<div class="t-notice" style="margin:0"><img src="img/tip_icon.svg" alt="" width="20" height="20"><div><strong class="t-notice-label">Tip:</strong><p>One short message, styled exactly like a DITA note in an article.</p></div></div>'),
    ("FAQ item", "A question and answer, written once and reused on any page.", ["FAQ"],
     '<div class="t-faq"><div class="t-faq-item" id="spec-faq"><h3><button class="t-faq-q" type="button" aria-expanded="false" aria-controls="spec-faq-a">Is a password manager and VPN combination worth it?<span class="t-faq-chev" aria-hidden="true"><svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round"><path d="m6 9 6 6 6-6"/></svg></span></button></h3><div class="t-faq-a" id="spec-faq-a" hidden><p>LastPass VPN uses the LastPass login you already have.</p></div></div></div>'),
]

# ---------------------------------------------------------------- flex recipes: trays in page order
RECIPES = {k: [tuple(t) for t in v["trays"]] for k, v in
           ((kk, SCHEMA["pages"][PAGES[kk][0]]) for kk in ["hub", "saas", "billing", "faq", "contact", "lifecycle"])}
FLEX_DESC = {
    "hub": "A homepage for one audience or product area, at marketing weight.",
    "saas": "A product page that sells and teaches: features, benefits, setup steps.",
    "billing": "A support topic broken into sections of hand-picked articles.",
    "faq": "Questions grouped by product, collapsed until opened.",
    "contact": "Ways to get help; cards tagged by audience show per plan.",
    "lifecycle": "Status definitions beside products, maintained by hand at launch.",
}
REQ = {"hub": "Request 1", "saas": "Request 2", "billing": "Request 2", "faq": "Request 3", "contact": "Request 4",
       "lifecycle": "Request 8", "releases": "Request 5", "downloads": "Request 6", "issues": "Request 7"}

DEFERRED = [
    ("Claims to audience tags", "Trays carry an Audience tag now. Mapping LastPass’s SAML claims to Free, Premium or Families and Business admin waits on LastPass."),
    ("Record detail pages", "A page per known issue and a release-notes page per product with its own feed."),
    ("Live lists in flex trays", "The hub’s recent releases are hand-picked. A tray that reads release records live comes later."),
    ("Search facets for records", "Search stays articles-only at launch; release notes, issues and downloads become facets later."),
    ("Video in Feature", "Media is an image or screenshot first; Vimeo in the 4:3 frame comes later."),
    ("Product registry", "Start as one shared product list for the three special page types, not a full data model."),
]


def chrome(title, desc, main):
    src = SRC["billing"]
    a = src.index('<nav class="t-crumbs"')
    b = src.index("</main>") + len("</main>")
    out = src[:a] + main + src[b:]
    out = re.sub(r"<title>.*?</title>", "<title>%s</title>" % H.escape(title), out, count=1)
    return re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % H.escape(desc), out, count=1)


def variant_figs(slug, variants):
    figs = []
    for n, (label, page, start, trim, stage) in enumerate(variants):
        block = extract(SRC[page], start)
        if trim:
            block = keep_first(block, *trim)
        figs.append('<figure class="ul-variant" id="ex-%s-%d"><figcaption><b>%s</b><span>from <a href="%s">%s</a></span></figcaption><div class="cl-stage %s">%s</div></figure>' % (
            slug, n, label, PAGES[page][0], PAGES[page][1], stage, scope_ids(block, "ex-%s-%d" % (slug, n))))
    return figs


def dl(rows):
    return "".join('<div><dt>%s</dt><dd>%s</dd></div>' % (H.escape(a), H.escape(b)) for a, b in rows)


TRY = '''<div class="ul-try" data-try="#ex-feature-0" role="group" aria-label="Try the Feature options">
  <span>Try the options</span>
  <div><b>Media</b><button type="button" data-set="media" data-val="left" aria-pressed="true">Left</button><button type="button" data-set="media" data-val="right" aria-pressed="false">Right</button></div>
  <div><b>Background</b><button type="button" data-set="bg" data-val="white" aria-pressed="true">White</button><button type="button" data-set="bg" data-val="wash" aria-pressed="false">Wash</button><button type="button" data-set="bg" data-val="cloud" aria-pressed="false">Cloud</button><button type="button" data-set="bg" data-val="dark" aria-pressed="false">Dark</button></div>
  <div><b>Frame</b><button type="button" data-set="ratio" data-val="4/3" aria-pressed="true">4:3</button><button type="button" data-set="ratio" data-val="1/1" aria-pressed="false">1:1</button><button type="button" data-set="ratio" data-val="16/9" aria-pressed="false">16:9</button></div>
</div>'''

# ---------------------------------------------------------------- components.html
nav = ("".join('<li><a href="#%s">%s</a></li>' % (t[0], t[1]) for t in TRAYS)
       + '<li class="ul-nav-sep"><a href="#special">Special page types</a></li><li><a href="#components">Components</a></li>')

trays_html = []
for slug, name, purpose, options, inside, merges, variants in TRAYS:
    used = [k for k, r in RECIPES.items() if any(t == slug for t, _, _ in r)]
    figs = ([TRY] if slug == "feature" else []) + variant_figs(slug, variants)
    tr = SCHEMA["trays"][slug]
    figs = [tabs(slug, [("Examples", "\n".join(figs)),
                        ("CMS schema", schema_view(SCHEMA["schema_names"][slug], tr["friendlyName"], "Component schema", tray_groups(slug),
                                                  '<p class="sc-lede">Editors see these fields when they add the tray in Page Builder.</p>'))])]
    trays_html.append('''<section class="ul-unit" id="%s" aria-labelledby="h-%s">
  <div class="ul-head">
    <div>
      <p class="ul-kind">Flex tray</p>
      <h2 id="h-%s">%s</h2>
      <p class="ul-purpose">%s</p>
      <p class="ul-merges"><b>Replaces</b> %s</p>
      <p class="ul-scope"><b>Scope</b> %s</p>
    </div>
    <dl class="ul-opts">%s
      <div><dt>Components</dt><dd><ul class="tp-chips">%s</ul></dd></div>
      <div><dt>Used on</dt><dd>%s</dd></div>
    </dl>
  </div>
  %s
</section>''' % (slug, slug, slug, name, purpose, merges, SCHEMA["scope"][slug], dl(options),
                 "".join('<li><a href="#c-%s">%s</a></li>' % (slugify(c), c) for c in inside),
                 ", ".join('<a href="%s">%s</a>' % (PAGES[k][0], PAGES[k][1]) for k in used), "\n  ".join(figs)))

special_html = []
for slug, name, purpose, why, options, variants in SPECIAL:
    special_html.append('''<div class="ul-special" id="sp-%s">
  <div class="ul-head">
    <div>
      <p class="ul-kind">Special page type</p>
      <h3 class="ul-h3"><a href="%s">%s</a></h3>
      <p class="ul-purpose">%s</p>
      <p class="ul-merges"><b>Why not flex</b> %s</p>
    </div>
    <dl class="ul-opts">%s</dl>
  </div>
  %s
</div>''' % (slug, PAGES[slug][0], name, purpose, why, dl(options), tabs("sp-" + slug, [
        ("Examples", "\n  ".join(variant_figs("sp-" + slug, variants))),
        ("Page schema", schema_view(SCHEMA["schema_names"][slug], SCHEMA["page_types"][slug]["name"], "Page schema", SCHEMA["page_types"][slug]["groups"],
                                     '<p class="sc-lede">%s</p>' % H.escape(SCHEMA["page_types"][slug]["about"]))),
        ("%s record schema" % SCHEMA["page_types"][slug]["record"]["name"], schema_view(SCHEMA["schema_names"]["record:" + slug], SCHEMA["page_types"][slug]["record"]["name"], "Component schema", SCHEMA["page_types"][slug]["record"]["groups"],
                                     '<p class="sc-lede">Each record is its own item in the CMS; this page lists them.</p>'))])))

comp_html = "".join('''<article class="ul-comp" id="c-%s">
  <h3>%s</h3><p>%s</p>
  <p class="ul-in"><b>%s</b> · In %s</p>
  <div class="ul-spec">%s</div>
  <details class="sc-fields"><summary>Fields</summary>%s</details>
</article>''' % (slugify(n), n, d, SCHEMA["scope"][n], ", ".join('<a href="#%s">%s</a>' % (t[0], t[1]) for t in TRAYS if t[1] in used), spec,
                  schema_groups(SCHEMA["components"][n])) for n, d, used, spec in COMPONENTS)
shared_html = "".join('<li><b>%s</b><span>%s</span></li>' % (a, b) for a, b in SHARED)

components_main = '''<nav class="t-crumbs" aria-label="Breadcrumb">
  <ol>
    <li><a href="index.html">Home</a></li>
    <li><a href="templates.html">Page types</a></li>
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
    <p class="t-hero-sub">The net-new work: the Flex page type, built from %d trays, %d special page types, and %d new components. Header, footer, articles and search are already built and not covered here.</p>
  </div>
</section>

<nav class="ul-nav" aria-label="Trays and page types"><div class="t-wrap"><ul>%s</ul><button type="button" class="ul-grid" aria-pressed="false">Show grid</button></div></nav>

<div class="t-wrap ul-body">
  <div class="ul-model">
    <div><b>Flex tray</b><span>One of %d trays an editor stacks on a page of the Flex page type in Page Builder, in any order.</span></div>
    <div><b>Special page type</b><span>A fixed layout over records, for pages trays can’t build.</span></div>
    <div><b>New component</b><span>A new piece placed inside a tray: card, table, notice or FAQ item.</span></div>
  </div>
  <div class="ul-shared"><p>Every tray also has</p><ul>%s</ul></div>
  <details class="sc-fields sc-fields--page"><summary>Flex page type schema</summary><p class="sc-lede">%s</p>%s</details>
%s
<section class="ul-unit" id="special" aria-labelledby="h-special">
  <div class="ul-head"><div><p class="ul-kind">Not built from trays</p><h2 id="h-special">Special page types</h2><p class="ul-purpose">Three pages that need records and behavior a stack of trays can’t give. Each has a fixed layout and still uses the Hero tray and the shared components.</p></div></div>
  %s
</section>
<section class="ul-unit" id="components" aria-labelledby="h-components">
  <div class="ul-head"><div><p class="ul-kind">Inside the trays</p><h2 id="h-components">Components</h2><p class="ul-purpose">The new pieces editors place inside trays. Buttons, images and link lists reuse what the built site already has.</p></div></div>
  <div class="ul-comps">%s</div>
</section>
</div>
</main>''' % (len(TRAYS), len(SPECIAL), len(COMPONENTS), nav, len(TRAYS), shared_html, H.escape(SCHEMA["page_types"]["flex"]["about"]),
             schema_view("Flex", "Flex page type", "Page schema", SCHEMA["page_types"]["flex"]["groups"]), "\n".join(trays_html),
             "\n  ".join(special_html), comp_html)

# ---------------------------------------------------------------- templates.html
def thumb(k):
    return '<a class="tp-thumb" href="%s" tabindex="-1" aria-hidden="true"><iframe src="%s" title="" loading="lazy" tabindex="-1" scrolling="no"></iframe></a>' % (PAGES[k][0], PAGES[k][0])


flex_cards = []
for k, recipe in RECIPES.items():
    steps = "".join('<li data-bg="%s"><a href="components.html#%s">%s</a><span>%s</span></li>' % (bg, t, TNAME[t], H.escape(v)) for t, v, bg in recipe)
    flex_cards.append('''<article class="tp-card">
  %s
  <div class="tp-copy">
    <p class="tp-tags"><span class="tp-tag">%s</span><span class="tp-tag tp-tag--flex">Flex</span></p>
    <h3><a href="%s">%s</a></h3>
    <p>%s</p>
    <p class="tp-sub">Built from %d trays, top to bottom</p>
    <ol class="tp-recipe">%s</ol>
  </div>
</article>''' % (thumb(k), REQ[k], PAGES[k][0], PAGES[k][1], FLEX_DESC[k], len(recipe), steps))

special_cards = []
for slug, name, purpose, why, options, variants in SPECIAL:
    special_cards.append('''<article class="tp-card">
  %s
  <div class="tp-copy">
    <p class="tp-tags"><span class="tp-tag">%s</span><span class="tp-tag tp-tag--special">Special page type</span></p>
    <h3><a href="%s">%s</a></h3>
    <p>%s</p>
    <p class="tp-why"><b>Why not flex</b> %s</p>
    <p><a class="t-more" href="components.html#sp-%s">See its parts</a></p>
  </div>
</article>''' % (thumb(slug), REQ[slug], PAGES[slug][0], name, purpose, why, slug))

BASE = [("index.html", "Home"), ("reader.html", "Article"), ("search.html", "Search results"), ("contact.html", "Contact")]
templates_main = '''<nav class="t-crumbs" aria-label="Breadcrumb">
  <ol>
    <li><a href="index.html">Home</a></li>
    <li><span aria-current="page">Page types</span></li>
  </ol>
</nav>

<main id="main">
<section class="t-hero t-hero--center t-hero--compact">
  <div class="t-hero-bg" aria-hidden="true"></div>
  <div class="t-hero-scrim" aria-hidden="true"></div>
  <div class="t-hero-in">
    <p class="t-eyebrow">LastPass support portal · design system</p>
    <h1>Four page types cover all eight requests</h1>
    <p class="t-hero-sub">The Flex page type, built from %d trays, plus %d special page types for the pages trays can’t build.</p>
    <div class="t-hero-actions" style="justify-content:center"><a class="t-btn t-btn--brand" href="components.html">See the trays and components</a></div>
  </div>
</section>

<section class="t-section" aria-labelledby="h-flex">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-flex">Flex page type</h2><p>The Flex page type: any page built from trays. Editors stack trays in Page Builder; these six pages are example layouts, each shown as its stack of trays from top to bottom. Every tray also takes a background and an audience tag.</p></div></div>
    <div class="tp-grid">%s</div>
  </div>
</section>

<section class="t-section t-section--wash" aria-labelledby="h-special">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-special">Special page types</h2><p>Fixed layouts over records. They exist because these pages need URLs, data and behavior that a stack of trays can’t give.</p></div></div>
    <div class="tp-grid tp-grid--3">%s</div>
  </div>
</section>

<section class="t-section" aria-labelledby="h-deferred">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-deferred">Deferred to reduce scope</h2><p>Designed for, but not in the first build.</p></div></div>
    <ul class="tp-plans">%s</ul>
  </div>
</section>

<section class="t-section t-section--wash" aria-labelledby="h-base">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-base">Approved baseline</h2><p>The pages LastPass already approved. Every page type shares their header, footer and brand tokens.</p></div></div>
    <ul class="tp-base">%s</ul>
  </div>
</section>
</main>''' % (len(TRAYS), len(SPECIAL), "\n".join(flex_cards), "\n".join(special_cards),
             "".join('<li class="tp-plan"><h3>%s</h3><p>%s</p></li>' % g for g in DEFERRED),
             "".join('<li><a href="%s">%s</a></li>' % (h, n) for h, n in BASE))

with open(os.path.join(ROOT, "components.html"), "w", encoding="utf-8") as f:
    f.write(chrome("Page-building essentials — LastPass Support", "One Flex page type built from five trays, three special page types, and the components inside them.", components_main))
with open(os.path.join(ROOT, "templates.html"), "w", encoding="utf-8") as f:
    f.write(chrome("Page types — LastPass Support", "The LastPass support portal page types: the Flex page type built from trays, and three special page types.", templates_main))
print("trays:", len(TRAYS), "| special:", len(SPECIAL), "| components:", len(COMPONENTS), "| flex examples:", len(RECIPES))
