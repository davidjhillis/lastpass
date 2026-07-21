# LastPass Support Portal — Design Concept Templates

Brand-faithful, responsive HTML templates for the LastPass documentation & support
portal (DiscoverCX / Ingeniux concept). Static site — no build step required.

## Pages
- `index.html` — Home / landing
- `reader.html` — Article / reader (DITA content rail, TOC, video, choice tabs, feedback)
- `contact.html` — Contact
- `search.html` — Coveo-style search results

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
