#!/usr/bin/env python3
"""Build the record templates from real LastPass data.

    python3 tools/build-records.py

Reads data/releases.json (parsed from lastpass.com/upgrade.php) and
data/products.json (the product registry), and writes release-notes.html,
downloads.html, known-issues.html, lifecycle.html and contact.html's template
sibling, contact-us.html. Run tools/build-library.py afterwards.
"""
import datetime as dt
import html as H
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TODAY = dt.date(2026, 11, 4)


def read(p):
    with open(os.path.join(ROOT, p), encoding="utf-8") as f:
        return f.read()


def write(p, s):
    with open(os.path.join(ROOT, p), "w", encoding="utf-8") as f:
        f.write(s)


REG = json.loads(read("data/products.json"))
PRODUCTS = REG["products"]
PNAME = {p["id"]: p["name"] for p in PRODUCTS}
RAW = json.loads(read("data/releases.json"))

BROWSERS = [("chrome", r"chrome(?!ium)|chromium edge"), ("edge", r"\bedge\b"), ("firefox", r"firefox"),
            ("safari", r"safari"), ("opera", r"opera"), ("ie", r"\bie\b")]
BROWSER_NAME = {"chrome": "Chrome", "edge": "Edge", "firefox": "Firefox", "safari": "Safari", "opera": "Opera", "ie": "Internet Explorer"}
TYPES = {"fixed": "Fixed", "fix": "Fixed", "resolved": "Fixed", "new": "New", "improved": "Improved",
         "changed": "Changed", "security": "Security", "removed": "Removed", "note": "Note"}


def product_of(label):
    l = label.lower()
    for p in PRODUCTS:
        if p["id"] != "extension" and re.search(p["match"], l):
            return p["id"]
    if re.search(PRODUCTS[0]["match"], l):
        return "extension"
    return "other"


def date_of(s):
    s = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s).replace(",", "")
    for f in ("%B %d %Y", "%b %d %Y"):
        try:
            return dt.datetime.strptime(s, f).date()
        except ValueError:
            pass
    return dt.datetime.strptime(s.replace("Sept", "Sep"), "%b %d %Y").date()


# ---------------------------------------------------------------- records
REL = []
seen = {}
for r in RAW:
    pid = product_of(r["p"])
    d = date_of(r["d"])
    plats = [k for k, rx in BROWSERS if re.search(rx, r["p"].lower())] if pid == "extension" else []
    items = []
    for t, txt in r["items"]:
        typ = TYPES.get(t.strip().lower(), "")
        if not t and re.match(r"(?i)(fixed|resolved)\b", txt):
            typ = "Fixed"
        if not typ and t:
            txt = t + ": " + txt
        items.append((typ, txt))
    anchor = "%s-%s" % (pid, d.isoformat())
    seen[anchor] = seen.get(anchor, 0) + 1
    if seen[anchor] > 1:
        anchor += "-%d" % seen[anchor]
    REL.append({"id": anchor, "pid": pid, "label": r["p"], "v": r["v"].lstrip("vV"), "date": d, "plats": plats, "items": items})
REL.sort(key=lambda x: x["date"], reverse=True)


def latest(pid, platform=None):
    for r in REL:
        if r["pid"] == pid and (platform is None or platform in r["plats"]):
            return r
    return None


def fmt(d):
    return d.strftime("%B %-d, %Y")


def tag(t):
    return '<span class="t-tag t-tag--%s">%s</span>' % (t.lower(), t) if t else ""


# ---------------------------------------------------------------- page chrome
SRC = read("topic-billing.html")


def page(title, desc, main):
    a = SRC.index('<nav class="t-crumbs"')
    b = SRC.index("</main>") + len("</main>")
    out = SRC[:a] + main + SRC[b:]
    out = re.sub(r"<title>.*?</title>", "<title>%s</title>" % H.escape(title), out, count=1)
    return re.sub(r'<meta name="description" content="[^"]*">', '<meta name="description" content="%s">' % H.escape(desc), out, count=1)


def crumbs(*items):
    li = ['<li><a href="index.html">Home</a></li>']
    for name, href in items[:-1]:
        li.append('<li><a href="%s">%s</a></li>' % (href, name))
    li.append('<li><span aria-current="page">%s</span></li>' % items[-1][0])
    return '<nav class="t-crumbs" aria-label="Breadcrumb">\n  <ol>\n    %s\n  </ol>\n</nav>\n' % "\n    ".join(li)


def hero(eyebrow, h1, sub, note, extra=""):
    return '''<section class="t-hero t-hero--center t-hero--compact" data-note="%s">
  <div class="t-hero-bg" aria-hidden="true"></div>
  <div class="t-hero-scrim" aria-hidden="true"></div>
  <div class="t-hero-in">
    <p class="t-eyebrow">%s</p>
    <h1>%s</h1>
    <p class="t-hero-sub">%s</p>%s
  </div>
</section>
''' % (note, eyebrow, h1, sub, extra)


ICON = {
    "search": '<path d="m21 21-4.3-4.3"/><circle cx="11" cy="11" r="8"/>',
    "rss": '<path d="M4 11a9 9 0 0 1 9 9"/><path d="M4 4a16 16 0 0 1 16 16"/><circle cx="5" cy="19" r="1"/>',
    "chat": '<path d="M7.9 20A9 9 0 1 0 4 16.1L2 22Z"/>',
    "users": '<path d="M16 21v-2a4 4 0 0 0-4-4H6a4 4 0 0 0-4 4v2"/><circle cx="9" cy="7" r="4"/><path d="M22 21v-2a4 4 0 0 0-3-3.87"/><path d="M16 3.13a4 4 0 0 1 0 7.75"/>',
    "pulse": '<path d="M22 12h-4l-3 9L9 3l-3 9H2"/>',
    "card": '<rect width="20" height="14" x="2" y="5" rx="2"/><path d="M2 10h20"/>',
    "case": '<path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"/><circle cx="12" cy="13" r="3"/>',
    "login": '<path d="M15 3h4a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2h-4"/><path d="m10 17 5-5-5-5"/><path d="M15 12H3"/>',
    "alert": '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
    "briefcase": '<rect width="20" height="14" x="2" y="7" rx="2"/><path d="M16 21V5a2 2 0 0 0-2-2h-4a2 2 0 0 0-2 2v16"/>',
}


def svg(name, size=18):
    return '<svg width="%d" height="%d" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">%s</svg>' % (size, size, ICON[name])


# ---------------------------------------------------------------- release notes
def rn_html(r):
    li = []
    for t, txt in r["items"]:
        li.append('<li%s>%s<span>%s</span></li>' % ("" if t else ' class="rn-plain"', tag(t), H.escape(txt)))
    chips = "".join('<span class="rc-chip">%s</span>' % BROWSER_NAME[p] for p in r["plats"])
    return '''<li class="rn" id="%s" data-p="%s" data-types="%s">
  <div class="rn-meta"><time datetime="%s">%s</time><a href="#%s">Link to this release</a></div>
  <div>
    <h3>%s <span class="rn-v">Version %s</span></h3>
    %s
    <ul>%s</ul>
  </div>
</li>''' % (r["id"], r["pid"], " ".join(sorted({t for t, _ in r["items"] if t})), r["date"].isoformat(), fmt(r["date"]),
            r["id"], PNAME.get(r["pid"], "Other"), H.escape(r["v"]), '<p class="rc-chipset">%s</p>' % chips if chips else "", "".join(li))


counts = {}
for r in REL:
    counts[r["pid"]] = counts.get(r["pid"], 0) + 1
pfilters = "".join('<label><input type="checkbox" name="p" value="%s"> %s<span class="rc-count">%d</span></label>' % (p["id"], p["name"], counts.get(p["id"], 0))
                   for p in PRODUCTS if counts.get(p["id"]))
tfilters = "".join('<label><input type="checkbox" name="t" value="%s"> %s %s</label>' % (t, tag(t), "") for t in ["New", "Improved", "Changed", "Fixed", "Security"])
FIRST = 12
DATA = [{"id": r["id"], "p": r["pid"], "d": r["date"].isoformat(), "v": r["v"], "pl": r["plats"], "i": r["items"]} for r in REL]

rn_main = crumbs(("Release notes", "")) + '<main id="main">\n' + hero(
    "Release notes", "What’s new in LastPass",
    "Every release, newest first. Filter by product or by what changed.",
    "Hero unit · standard") + '''
<div class="t-wrap">
<div class="rc-layout">
  <aside class="rc-side" aria-label="Filter releases" data-note="Record list unit · filters · product facets come from the product registry; counts are live">
    <div class="rc-search">%s<input type="search" id="rn-q" aria-label="Search release notes" placeholder="Search release notes"></div>
    <div><h2>Product</h2><div class="rc-filter" id="rn-products">%s</div></div>
    <div><h2>What changed</h2><div class="rc-filter" id="rn-types">%s</div></div>
    <p><a class="rc-feed" href="#">%s Subscribe to updates</a></p>
  </aside>
  <div>
    <div class="rc-bar"><p id="rn-count">Showing <b>%d</b> of <b>%d</b> releases</p><button class="t-btn t-btn--line" type="button" id="rn-clear" hidden>Clear filters</button></div>
    <ol class="rn-list" id="rn-list" data-note="Record list unit · release note records; each has a stable link">%s</ol>
    <div class="rc-more"><button class="t-btn t-btn--line" type="button" id="rn-more">Show more releases</button></div>
  </div>
</div>
</div>
</main>
<script>
(function(){
  var DATA = %s;
  var NAMES = %s, BROW = %s;
  var list = document.getElementById('rn-list'), more = document.getElementById('rn-more'), count = document.getElementById('rn-count');
  var q = document.getElementById('rn-q'), clear = document.getElementById('rn-clear'), shown = %d;
  function esc(s){ return s.replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
  function fmt(iso){ var d = new Date(iso + 'T00:00:00'); return d.toLocaleDateString('en-US', {month:'long', day:'numeric', year:'numeric'}); }
  function card(r){
    var items = r.i.map(function(x){ return '<li' + (x[0] ? '' : ' class="rn-plain"') + '>' + (x[0] ? '<span class="t-tag t-tag--' + x[0].toLowerCase() + '">' + x[0] + '</span>' : '') + '<span>' + esc(x[1]) + '</span></li>'; }).join('');
    var chips = r.pl.length ? '<p class="rc-chipset">' + r.pl.map(function(p){ return '<span class="rc-chip">' + BROW[p] + '</span>'; }).join('') + '</p>' : '';
    return '<li class="rn" id="' + r.id + '"><div class="rn-meta"><time datetime="' + r.d + '">' + fmt(r.d) + '</time><a href="#' + r.id + '">Link to this release</a></div><div><h3>' + (NAMES[r.p] || 'Other') + ' <span class="rn-v">Version ' + esc(r.v) + '</span></h3>' + chips + '<ul>' + items + '</ul></div></li>';
  }
  function picked(name){ return [].slice.call(document.querySelectorAll('input[name=' + name + ']:checked')).map(function(i){ return i.value; }); }
  function match(){
    var ps = picked('p'), ts = picked('t'), term = q.value.trim().toLowerCase();
    return DATA.filter(function(r){
      if(ps.length && ps.indexOf(r.p) < 0) return false;
      if(ts.length && !r.i.some(function(x){ return ts.indexOf(x[0]) >= 0; })) return false;
      if(term && (NAMES[r.p] + ' ' + r.v + ' ' + r.i.map(function(x){ return x[1]; }).join(' ')).toLowerCase().indexOf(term) < 0) return false;
      return true;
    });
  }
  function render(){
    var m = match();
    list.innerHTML = m.slice(0, shown).map(card).join('') || '<li class="rc-empty"><b>No releases match</b>Try fewer filters.</li>';
    count.innerHTML = 'Showing <b>' + Math.min(shown, m.length) + '</b> of <b>' + m.length + '</b> releases';
    more.hidden = shown >= m.length;
    clear.hidden = !(picked('p').length || picked('t').length || q.value);
  }
  document.querySelectorAll('.rc-filter input').forEach(function(i){ i.addEventListener('change', function(){ shown = %d; render(); }); });
  q.addEventListener('input', function(){ shown = %d; render(); });
  more.addEventListener('click', function(){ shown += 20; render(); });
  clear.addEventListener('click', function(){ document.querySelectorAll('.rc-filter input').forEach(function(i){ i.checked = false; }); q.value = ''; shown = %d; render(); });
  // #admin-console style links preset the product filter; release ids open that release
  var h = location.hash.slice(1);
  if(h){
    var box = document.querySelector('input[name=p][value="' + h + '"]');
    if(box){ box.checked = true; render(); }
    else { var idx = DATA.map(function(r){ return r.id; }).indexOf(h); if(idx >= shown){ shown = idx + 5; render(); var el = document.getElementById(h); if(el) el.scrollIntoView(); } }
  }
})();
</script>
''' % (svg("search"), pfilters, tfilters, svg("rss", 14), FIRST, len(REL), "\n".join(rn_html(r) for r in REL[:FIRST]),
       json.dumps(DATA, ensure_ascii=False, separators=(",", ":"), default=str), json.dumps(PNAME), json.dumps(BROWSER_NAME),
       FIRST, FIRST, FIRST, FIRST)
write("release-notes.html", page("Release notes — LastPass Support", "Every LastPass release, newest first, filterable by product and change type.", rn_main))

# ---------------------------------------------------------------- downloads
OS = [("windows", "Windows"), ("mac", "macOS"), ("linux", "Linux"), ("mobile", "Mobile")]
LEAD = {"windows": 2, "mac": 1, "linux": 0, "mobile": 0}


def dl_card(d):
    r = latest(d["product"], d.get("platform")) if d.get("product") else None
    ver = ""
    note = ""
    vt = lambda v: tuple(int(x) for x in re.findall(r"\d+", v))
    if r and d.get("site") and vt(d["site"]) > vt(r["v"]):
        ver = '<p class="dl-ver"><span>Version <b>%s</b></span><a href="release-notes.html#%s">Release notes</a></p>' % (H.escape(d["site"]), d["product"])
        note = ' data-note="Card · download. Release notes stop naming this browser after %s, so the store version is shown; the registry should record each platform"' % r["v"]
    elif r:
        ver = '<p class="dl-ver"><span>Version <b>%s</b></span><span>%s</span><a href="release-notes.html#%s">What’s new</a></p>' % (H.escape(r["v"]), fmt(r["date"]), r["id"])
        if d.get("site") and d["site"] != r["v"]:
            note = ' data-note="Card · download. Version from release notes. lastpass.com/downloads shows %s today; the registry keeps them in step"' % d["site"]
    return '<article class="dl-card"%s><h3>%s</h3><p>%s</p>%s<a class="t-btn t-btn--brand" href="%s">Download<span class="sr-only"> %s</span></a></article>' % (
        note, H.escape(d["name"]), H.escape(d["text"]), ver, H.escape(d["href"]), H.escape(d["name"]))


tabs = "".join('<button type="button" role="tab" id="tab-%s" aria-controls="pane-%s" aria-selected="%s"%s>%s</button>' % (k, k, "true" if i == 0 else "false", "" if i == 0 else ' tabindex="-1"', n) for i, (k, n) in enumerate(OS))
panes = "".join('<div class="dl-grid" role="tabpanel" id="pane-%s" aria-labelledby="tab-%s"%s>%s</div>' % (k, k, "" if i == 0 else " hidden", "".join(dl_card(d) for d in REG["downloads"][k])) for i, (k, n) in enumerate(OS))
LEADS = {k: REG["downloads"][k][LEAD[k]] for k, _ in OS}
lead_json = {k: {"name": d["name"], "text": d["text"], "href": d["href"]} for k, d in LEADS.items()}
w = LEADS["windows"]
dl_main = crumbs(("Downloads", "")) + '''<main id="main">
<section class="t-hero t-hero--media" data-note="Hero unit · media · the media slot holds the detected-platform card">
  <div class="t-hero-bg" aria-hidden="true"></div>
  <div class="t-hero-scrim" aria-hidden="true"></div>
  <div class="t-hero-in">
    <div>
      <p class="t-eyebrow">Downloads</p>
      <h1>Get LastPass on every device you use</h1>
      <p class="t-hero-sub">Apps, browser extensions and installers for Windows, macOS, Linux and mobile. Versions update from the release notes.</p>
    </div>
    <div class="dl-hero-card" id="dl-lead" data-note="Hero unit · media slot: platform download · picks the visitor’s operating system; links to all platforms below">
      <p class="dl-detect" id="dl-os">Recommended for Windows</p>
      <h2 id="dl-name">%s</h2>
      <p id="dl-text">%s</p>
      <p><a class="t-btn t-btn--brand" id="dl-href" href="%s">Download</a></p>
      <p class="dl-switch">Not your system? <button type="button" data-goto="all">See all platforms</button></p>
    </div>
  </div>
</section>
<section class="t-section" id="all" aria-labelledby="h-all">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-all">All downloads</h2><p>Each version and date comes from the newest release note for that product.</p></div></div>
    <div class="dl-tabs" role="tablist" aria-label="Operating system">%s</div>
    %s
  </div>
</section>
<section class="t-section t-section--tight" style="padding-bottom:72px">
  <div class="t-wrap">
    <div class="t-help"><div><h2>Something not installing?</h2><p>Check the known issues, or read the installation guides.</p></div>
    <div class="t-help-actions"><a class="t-btn t-btn--line" href="known-issues.html">Known issues</a><a class="t-btn t-btn--brand" href="reader.html">Installation guides</a></div></div>
  </div>
</section>
</main>
<script>
(function(){
  var LEAD = %s, NAMES = {windows:'Windows', mac:'macOS', linux:'Linux', mobile:'your phone'};
  var ua = navigator.userAgent, os = /iPhone|iPad|Android/i.test(ua) ? 'mobile' : /Mac/i.test(ua) ? 'mac' : /Linux|X11/i.test(ua) ? 'linux' : 'windows';
  function lead(k){ var d = LEAD[k]; document.getElementById('dl-os').textContent = 'Recommended for ' + NAMES[k]; document.getElementById('dl-name').textContent = d.name; document.getElementById('dl-text').textContent = d.text; document.getElementById('dl-href').href = d.href; }
  var tabs = [].slice.call(document.querySelectorAll('.dl-tabs [role=tab]'));
  function pick(t, focus){ tabs.forEach(function(x){ var on = x === t; x.setAttribute('aria-selected', on); x.tabIndex = on ? 0 : -1; document.getElementById(x.getAttribute('aria-controls')).hidden = !on; }); if(focus) t.focus(); }
  tabs.forEach(function(t, i){
    t.addEventListener('click', function(){ pick(t); });
    t.addEventListener('keydown', function(e){ var j = e.key === 'ArrowRight' ? i + 1 : e.key === 'ArrowLeft' ? i - 1 : null; if(j === null) return; e.preventDefault(); pick(tabs[(j + tabs.length) %% tabs.length], true); });
  });
  lead(os); pick(document.getElementById('tab-' + os));
  document.querySelector('[data-goto]').addEventListener('click', function(){ document.getElementById('all').scrollIntoView(); });
})();
</script>
''' % (H.escape(w["name"]), H.escape(w["text"]), H.escape(w["href"]), tabs, panes, json.dumps(lead_json))
write("downloads.html", page("Downloads — LastPass Support", "Download LastPass apps, browser extensions and installers for Windows, macOS, Linux and mobile.", dl_main))

# ---------------------------------------------------------------- known issues
SINCE = TODAY - dt.timedelta(days=183)
fixed = []
for r in REL:
    if r["date"] < SINCE:
        break
    for t, txt in r["items"]:
        if t == "Fixed":
            fixed.append((r, txt))
fixed_li = "".join('<li><span>%s</span><span class="ki-where">%s · <a href="release-notes.html#%s">%s %s</a></span></li>' % (
    H.escape(txt), r["date"].strftime("%b %-d, %Y"), r["id"], PNAME.get(r["pid"], "Other"), H.escape(r["v"])) for r, txt in fixed[:14])

ki_main = crumbs(("Known issues", "")) + '<main id="main">\n' + hero(
    "Known issues", "Known issues and fixes",
    "Problems we’ve confirmed, what to do in the meantime, and the release that fixes them.",
    "Hero unit · standard") + '''
<section class="t-section" aria-labelledby="h-active">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-active">Active issues</h2><p>Updated as soon as anything changes.</p></div><a class="rc-feed" href="#">%s Subscribe</a></div>
    <div class="rc-empty" data-note="Record list unit · empty state · real: LastPass has not published known issues">
      <b>No active known issues</b>If something isn’t working, check <a href="#">service status</a> or <a href="contact-us.html">contact support</a>.
    </div>
    <h3 style="margin:36px 0 12px;font-size:16px;color:var(--lp-text-muted);font-weight:700">How an active issue appears</h3>
    <article class="ki" data-note="Record list unit · issue · ID, status, products, affected versions, workaround, fixed-in release">
      <header>
        <span class="ki-sample">Layout example · not a real issue</span>
        <span class="ki-id">KI-0000</span>
        <span class="ki-status">Workaround available</span>
        <h3>Example: the extension icon doesn’t appear after a browser update</h3>
      </header>
      <dl>
        <div><dt>Product</dt><dd>Browser extension</dd></div>
        <div><dt>Platforms</dt><dd>Chrome, Edge</dd></div>
        <div><dt>Affected versions</dt><dd>Example version</dd></div>
        <div><dt>Last updated</dt><dd>Date and time</dd></div>
      </dl>
      <div class="ki-body">
        <p><b>What happens.</b> A short description of the symptom in the reader’s words.</p>
        <p><b>Workaround.</b> The steps to get working again until the fix ships, linking to an article where there is one.</p>
        <p><b>Fix.</b> When resolved, this links to the release that fixed it, and the issue moves to Recently resolved.</p>
      </div>
    </article>
  </div>
</section>
<section class="t-section t-section--wash" aria-labelledby="h-resolved">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-resolved">Recently resolved</h2><p>Fixes from the last six months, each linked to the release that shipped it.</p></div><a class="t-more" href="release-notes.html">All release notes</a></div>
    <ul class="ki-fixed" data-note="Record list unit · real “Fixed” items from release notes since %s">%s</ul>
  </div>
</section>
</main>
''' % (svg("rss", 14), SINCE.strftime("%b %-d, %Y"), fixed_li)
write("known-issues.html", page("Known issues — LastPass Support", "Known LastPass issues with workarounds, and recent fixes linked to their releases.", ki_main))

# ---------------------------------------------------------------- lifecycle
DEFS = [("Active", "lc-active", "Fully supported and getting new features and fixes."),
        ("Active, mature", "lc-mature", "Supported and getting fixes, with few new features planned."),
        ("End of life", "lc-eol", "An end date is announced. Fixes only until that date."),
        ("Retired", "lc-retired", "No longer available or supported. A replacement is named.")]
defs_rows = "".join('<tr><th scope="row"><span class="lc-status %s">%s</span></th><td>%s</td></tr>' % (c, n, d) for n, c, d in DEFS)


def proposed(d):
    age = (TODAY - d).days
    if age <= 365:
        return "Active", "lc-active"
    if age <= 3 * 365:
        return "Active, mature", "lc-mature"
    return "End of life", "lc-eol"


rows = []
for p in PRODUCTS:
    r = latest(p["id"])
    if not r:
        continue
    if p["id"] == "extension":
        for plat in ["chrome", "edge", "firefox", "safari", "opera", "ie"]:
            rr = latest("extension", plat)
            if rr:
                s, c = proposed(rr["date"])
                rows.append((p["family"], "Browser extension for " + BROWSER_NAME[plat], rr, s, c))
        continue
    s, c = proposed(r["date"])
    rows.append((p["family"], p["name"], r, s, c))
lc_rows = "".join('<tr><th scope="row">%s</th><td>%s</td><td class="num">%s</td><td class="num"><a href="release-notes.html#%s">%s</a></td><td><span class="lc-status %s">%s</span><span class="lc-proposed">Proposed</span></td></tr>' % (
    n, f, H.escape(r["v"]), r["id"], r["date"].strftime("%b %Y"), c, s) for f, n, r, s, c in rows)

lc_main = crumbs(("Product lifecycle", "")) + '<main id="main">\n' + hero(
    "Product lifecycle", "Product lifecycle",
    "Where each LastPass product stands, from active to retired, so you can plan ahead.",
    "Hero unit · standard") + '''
<section class="t-section" aria-labelledby="h-lc">
  <div class="t-wrap">
    <h2 id="h-lc" class="sr-only">Lifecycle status</h2>
    <div class="t-notice t-notice--info" style="margin:0 0 28px" data-note="Content unit · notice · remove once LastPass publishes real statuses">
      %s
      <p><b>Statuses are proposals.</b> LastPass hasn’t published lifecycle status before. Each status below is proposed from the product’s last release (within a year: Active; one to three years: Active, mature; older: End of life) for LastPass to confirm.</p>
    </div>
    <div class="lc-pair" data-note="Record list unit · table · definitions beside products; stacks on phones">
      <div class="t-table"><table style="min-width:0"><caption>Status definitions</caption><thead><tr><th scope="col">Status</th><th scope="col">Meaning</th></tr></thead><tbody>%s</tbody></table></div>
      <div class="t-table"><table><caption>Products</caption><thead><tr><th scope="col">Product</th><th scope="col">Family</th><th scope="col">Latest version</th><th scope="col">Last release</th><th scope="col">Status</th></tr></thead><tbody>%s</tbody></table></div>
    </div>
  </div>
</section>
</main>
''' % (svg("alert", 20), defs_rows, lc_rows)
write("lifecycle.html", page("Product lifecycle — LastPass Support", "The lifecycle status of each LastPass product, with definitions.", lc_main))

# ---------------------------------------------------------------- contact us
CARDS = [
    ("search", "Search the help center", "Most answers are a search away, in the same articles our support team uses.", "Search help", "search.html", "all", False),
    ("login", "Sign in for your support options", "Signed in, you’ll see the ways to reach us that come with your plan.", "Log in", "#", "out", True),
    ("case", "Open a support case", "Tell us what’s wrong and a support specialist will reply by email.", "Open a case", "#", "premium business", True),
    ("card", "Ask about billing", "Questions about a charge, a renewal or an invoice.", "Open a billing case", "#", "free premium business", False),
    ("briefcase", "Talk to your account team", "For licensing, renewals and rollout help for your company.", "Contact sales", "#", "business", False),
    ("users", "Ask the community", "Get answers from other LastPass users and our community team.", "Visit the community", "https://community.lastpass.com/", "all", False),
    ("pulse", "Check service status", "See whether LastPass services are running normally.", "Service status", "https://status.lastpass.com", "all", False),
    ("alert", "Known issues", "Confirmed problems with workarounds, and the releases that fixed them.", "See known issues", "known-issues.html", "all", False),
]
AUD = [("out", "Signed out"), ("free", "Free"), ("premium", "Premium or Families"), ("business", "Business admin")]
WHO = {"out": "You’re signed out.", "free": "Signed in with LastPass Free.", "premium": "Signed in with Premium or Families.", "business": "Signed in as a Business admin."}
cards = []
for ic, h, p, cta, href, aud, primary in CARDS:
    vis = aud == "all" or "out" in aud.split()
    label = "Everyone" if aud == "all" else ", ".join(n for k, n in AUD if k in aud.split())
    cards.append('<article class="ct-card%s" data-aud="%s"%s><span class="t-cat-icon">%s</span><p class="ct-aud">%s</p><h3>%s</h3><p>%s</p><a class="t-btn %s" href="%s">%s</a></article>' % (
        " ct-card--primary" if primary else "", aud, "" if vis else " hidden", svg(ic, 20), label, h, p, "t-btn--brand" if primary else "t-btn--line", href, cta))
switch = '''
    <div style="margin-top:28px" data-note="Design preview · design only; in production the audience comes from the SAML sign-in and its plan claims">
      <div class="ct-switch" role="group" aria-label="Preview the page as">%s</div>
      <p class="ct-who" id="ct-who" aria-live="polite">%s</p>
    </div>''' % ("".join('<button type="button" data-aud="%s" aria-pressed="%s">%s</button>' % (k, "true" if k == "out" else "false", n) for k, n in AUD), WHO["out"])
ct_main = crumbs(("Contact us", "")) + '<main id="main">\n' + hero(
    "Contact us", "How can we help?",
    "The options you see depend on your plan. Sign in to see everything available to you.",
    "Hero unit · standard, with a design-preview switch", switch) + '''
<section class="t-section" aria-labelledby="h-ways">
  <div class="t-wrap">
    <div class="t-head"><div><h2 id="h-ways">Ways to get help</h2><p>Which options appear for which plan is set in the CMS, not in code. The rules shown here are examples for LastPass to replace.</p></div></div>
    <div class="ct-grid" data-note="Cards unit · contact option · each has an audience rule (F3); signed-out visitors never see an empty page">%s</div>
  </div>
</section>
</main>
<script>
(function(){
  var WHO = %s;
  var btns = [].slice.call(document.querySelectorAll('.ct-switch button'));
  btns.forEach(function(b){ b.addEventListener('click', function(){
    var a = b.getAttribute('data-aud');
    btns.forEach(function(x){ x.setAttribute('aria-pressed', x === b); });
    document.querySelectorAll('.ct-card').forEach(function(c){ var r = c.getAttribute('data-aud').split(' '); c.hidden = !(r.indexOf('all') >= 0 || r.indexOf(a) >= 0); });
    document.getElementById('ct-who').textContent = WHO[a];
  }); });
})();
</script>
''' % ("".join(cards), json.dumps(WHO))
write("contact-us.html", page("Contact us — LastPass Support", "Ways to contact LastPass support, matched to your plan.", ct_main))

print("releases:", len(REL), "| fixed (6 mo):", len(fixed), "| lifecycle rows:", len(rows))
