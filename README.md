# LastPass Support Portal — Design Concept Templates

Brand-faithful, responsive HTML templates for the LastPass documentation & support
portal (DiscoverCX / Ingeniux concept). Static site — no build step required.

## Pages
- `index.html` — Home / landing
- `reader.html` — Article / reader (DITA content rail, TOC, video, choice tabs, feedback)
- `contact.html` — Contact
- `search.html` — Coveo-style search results
- `hub-business.html` — Mini hub (template request 1): a topic homepage, here LastPass Business admin
- `topic-billing.html` — Topic overview (request 2): Billing, with map-fed link lists, a table and a video hero
- `topic-saas-monitoring.html` — Topic overview at marketing weight: SaaS and AI Monitoring, with a product hero, capability table, benefits band, setup steps and a closing call to action
- `faq.html` — FAQ page (request 3): reusable FAQ items with an accessible accordion

- `contact-us.html` — Contact Us (request 4): options matched to the visitor's plan, with an audience preview switch
- `release-notes.html` — Release notes (request 5): all 351 releases from lastpass.com/upgrade.php as filterable records
- `downloads.html` — Downloads (request 6): the visitor's platform first, versions read from the release notes
- `known-issues.html` — Known issue tracker (request 7): active issues and recent real fixes
- `lifecycle.html` — Product lifecycle (request 8): definitions beside products, statuses proposed from release history
- `templates.html` — the page types: one Flex page type (six example layouts, each shown as its stack of trays) and three special page types (Release notes, Downloads, Known issues), plus what is deferred
- `components.html` — page-building essentials: 5 flex trays (Hero, Feature, Cards, FAQ, Content) with options and live variants, the shared Background and Audience options, the special page types' parts, 7 components and what is automatic

The five record pages are generated from `data/releases.json` (parsed from lastpass.com/upgrade.php) and `data/products.json` (the product registry): run `python3 tools/build-records.py`, then `python3 tools/build-library.py`.

`templates.html` and `components.html` are generated: run `python3 tools/build-library.py` after changing a template page. Each example is cut from the page that uses it, so the library cannot drift from the pages.

The template pages share `templates.css` and `templates.js`. A **Show build notes** button on each marks every block and where its content comes from (authored, DITA map, release-note records, FAQ items).

## Assets
- `styles.css` — compiled stylesheet (linked, not inlined)
- `img/` — photography (optimized JPEG) and the LastPass wordmarks
- Icons are inline SVG; the language selector is wired up in a small inline script per page.

## Deploy to Vercel
1. Push this folder to a GitHub repo.
2. In Vercel: **Add New → Project → Import** the repo.
3. **Framework Preset: Other.** No build command, no install command; **Output Directory: `./` (root)**.
4. Deploy. `vercel.json` only sets long-cache headers for static assets.

Optional: set `"cleanUrls": true` in `vercel.json` for extensionless URLs
(`/reader` instead of `/reader.html`).

### Private review (recommended for client sharing)
These pages use the real LastPass brand, so Chrome Safe Browsing may flag a public
deployment as a lookalike site. For client review, protect the deployment
(Vercel: Project → Settings → Deployment Protection → Password/Vercel Auth).

## Notes
- Pages are indexable (no `noindex`). Add `noindex` only if you deploy publicly and
  don't want them crawled.
- The language selector lists placeholder locales (English, Deutsch, Español, Français,
  Italiano, Nederlands, Português). Swap for the confirmed six locales and wire each
  `href` to its per-locale path when the multilingual routing is defined.
