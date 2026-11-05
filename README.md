# LastPass Support Portal — Design Concept Templates

Brand-faithful, responsive HTML templates for the LastPass documentation & support
portal (DiscoverCX / Ingeniux concept). Static site — no build step required.

## Pages
- `reader.html` — Article / reader (DITA content rail, TOC, video, choice tabs, feedback)
- `contact.html` — Contact
- `search.html` — Coveo-style search results
- `hub-business.html` — Mini hub (template request 1): a topic homepage, here LastPass Business admin
- `topic-billing.html` — Topic overview (request 2): Billing, with map-fed link lists, a table and a video hero
- `topic-saas-monitoring.html` — Topic overview at marketing weight: SaaS and AI Monitoring, with a product hero, capability table, benefits band, setup steps and a closing call to action
- `faq.html` — FAQ page (request 3), its own page type: groups of questions picked from the FAQ library, a Topics index with counts, and Expand all

- `contact-us.html` — Contact Us (request 4): options matched to the visitor's plan, with an audience preview switch
- `release-notes.html` — Release notes (request 5): all 351 releases from lastpass.com/upgrade.php as filterable records
- `downloads.html` — Downloads (request 6): the visitor's platform first, versions read from the release notes
- `known-issues.html` — Known issue tracker (request 7): active issues and recent real fixes
- `lifecycle.html` — Product lifecycle (request 8): definitions beside products, statuses proposed from release history
- `index.html` (home) — the page types: one Flex page type (five example layouts, each shown as its stack of trays) and four special page types (FAQ, Release notes, Downloads, Known issues), plus how each part was kept simple
- `components.html` — page-building essentials: 5 flex trays (Hero, Feature, Cards, FAQ, Content) with options and live variants, the shared Background and Audience options, the special page types' parts, 7 components and what is automatic

The five record pages are generated from `data/releases.json` (parsed from lastpass.com/upgrade.php) and `data/products.json` (the product registry): run `python3 tools/build-records.py`, then `python3 tools/build-library.py`.

`index.html`, `components.html` and `feedback.html` are generated (`templates.html` only redirects to the home page): run `python3 tools/build-library.py` after changing a template page. Each example is cut from the page that uses it, so the library cannot drift from the pages.

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

## CMS schema (net-new work only)

`data/schema.json` holds the CMS fields for the new work only: the Flex page type, the FAQ, Release notes, Downloads and Known issues page types and their records (FAQ groups, releases, downloads, issues), the five trays, and four new components (Card, Table, Notice, FAQ item). The header, footer, articles, search and other pages the team already built are out of scope.

Fields are grouped the way the edit form shows them, with editor-facing labels and help, in the `lastpass_cms` manifest vocabulary (`text`, `rich`, `enum`, `link`, `component[]` and so on), so `tools/schema-gen.mjs` there can generate them as Schema Designer XDR. On every new page, **CMS schema** (bottom right) opens a panel with a tab for the page and one per tray; `components.html` shows the same schemas under each tray's **CMS schema** tab.

## Access code

The whole site sits behind a shared access code (`middleware.js`, the same edge gate as the BCSB preview). Visitors see a neutral Ingeniux access page; the right code sets a 30-day cookie. The code is the `BASIC_AUTH_PASSWORD` environment variable in Vercel (Production and Preview). Changing it signs everyone out. If the variable is missing the site answers "Preview is not configured", so set it before deploying.

## Design feedback

Reviewers pin numbered notes on any design page and track them to sign-off.

- **On a page:** the **Feedback** button (bottom right) opens a notes column on the right. A reviewer enters their name once (it shows as initials), chooses **+ Add a note**, clicks the spot, and writes the note. Pins show only while the column is open.
- **Types:** each note is **Design** (how it looks or reads), **Notes** (the build notes) or **Schema** (CMS fields and spec). The type is guessed from where the pin lands and can be changed before posting.
- **Schema feedback:** the CMS schema pop-up has **Add feedback**. While feedback is on, the pop-up opens beside the notes column instead of blocking the page, so its fields can take pins. Opening a schema note later reopens the pop-up on the right tab. The inline schemas on the Essentials page take pins directly.
- **All notes:** `feedback.html` lists every note with its type, page link, reviewer, date and status, with type, status, page and reviewer filters and a CSV download. Each link opens the page at that note (`page.html#fb-12`).
- **Statuses:** Open → Edited – review again (after the design changes) → Approved – closed. Anyone can reopen. Every change records who and when.
- **Where notes live:** one Markdown file per note in `notes/` on the `feedback` branch, written by `api/feedback.js`. That branch holds only the notes, a README and a `vercel.json` that turns off its deployments, so a note never triggers a build. The first note creates the branch.
- **Pins survive design changes:** each pin stores the element's path and a short piece of its text. If the path no longer matches, the text finds it again; if neither does, the note is marked Detached and stays in the list.
- **Without setup**, the tool still works but saves notes in that viewer's browser only, and says so.

### Setup (once)

1. **GitHub token:** GitHub → Settings → Developer settings → Fine-grained tokens → Generate. Repository access: only `davidjhillis/lastpass`. Permissions: **Contents: Read and write**. Copy the token.
2. **Vercel:** the `lastpass` project → Settings → Environment Variables → add `GITHUB_TOKEN` with that token, for Production and Preview.
   Optional: `FEEDBACK_PASSCODE` to ask reviewers for a passcode once.
3. **Redeploy** the branch you'll share so it picks up the variable.
