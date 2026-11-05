// Gates the whole design-review site behind a shared access code at Vercel's edge
// (same approach as the BCSB concepts preview). Unauthenticated requests get a
// neutral access page: Ingeniux, not LastPass branding, so it can't read as a
// lookalike LastPass login. A correct code sets a 30-day cookie.
// The code lives in the BASIC_AUTH_PASSWORD environment variable.
export const config = { matcher: '/:path*' };

const COOKIE = 'review_access';
const AUTH_PATH = '/__access';
const MAX_AGE = 60 * 60 * 24 * 30;

async function token(secret) {
  const data = new TextEncoder().encode(`lastpass-design-review:${secret}`);
  const hash = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(hash)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

function readCookie(request, name) {
  const header = request.headers.get('cookie') || '';
  const match = header.split(/;\s*/).find((c) => c.startsWith(`${name}=`));
  return match ? decodeURIComponent(match.slice(name.length + 1)) : '';
}

function safeNext(value) {
  return typeof value === 'string' && value.startsWith('/') && !value.startsWith('//') && !value.startsWith(AUTH_PATH) ? value : '/';
}

function escapeHtml(value) {
  return value.replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' })[c]);
}

function accessPage(next, failed) {
  const html = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="robots" content="noindex, nofollow">
<title>Design review — private preview</title>
<style>
  :root { --ink: #16181d; --ink-soft: #545a66; --line: #c9ccd3; --wash: #f4f5f7; --accent: #1f4fd1; --accent-hover: #173da6; --error: #a12a1b; }
  * { box-sizing: border-box; }
  html, body { height: 100%; }
  body { margin: 0; font-family: system-ui, -apple-system, "Segoe UI", Roboto, Arial, sans-serif; background: #0f1218; color: var(--ink); display: grid; place-items: center; padding: 24px; line-height: 1.5; }
  main { width: 100%; max-width: 420px; }
  .card { background: #fff; border-radius: 16px; padding: 36px 32px 28px; box-shadow: 0 24px 60px -20px rgba(0,0,0,.6); }
  .mark { display: inline-flex; align-items: center; gap: 8px; font-size: 13px; font-weight: 700; color: var(--ink-soft); background: var(--wash); padding: 6px 12px; border-radius: 999px; }
  .mark svg { width: 14px; height: 14px; }
  h1 { margin: 18px 0 8px; font-size: 26px; line-height: 1.15; letter-spacing: -0.02em; font-weight: 750; }
  p.lede { margin: 0 0 24px; color: var(--ink-soft); font-size: 15px; }
  label { display: block; font-size: 14px; font-weight: 700; margin-bottom: 8px; }
  input { width: 100%; height: 50px; border-radius: 10px; border: 1.5px solid var(--line); background: var(--wash); padding: 0 14px; font: 600 16px/1 system-ui, sans-serif; color: var(--ink); }
  input:focus { outline: none; border-color: var(--accent); background: #fff; box-shadow: 0 0 0 4px rgba(31,79,209,.15); }
  input[aria-invalid="true"] { border-color: var(--error); }
  .error { display: flex; gap: 8px; align-items: center; margin: 10px 0 0; color: var(--error); font-size: 14px; font-weight: 600; }
  .error svg { flex: none; width: 16px; height: 16px; }
  button { margin-top: 18px; width: 100%; height: 50px; border: 0; border-radius: 10px; background: var(--accent); color: #fff; font: 700 16px/1 system-ui, sans-serif; cursor: pointer; }
  button:hover { background: var(--accent-hover); }
  button:focus-visible { outline: 3px solid #9db4f5; outline-offset: 3px; }
  .foot { margin: 20px 0 0; text-align: center; color: #aab0bd; font-size: 13px; }
  .foot a { color: #fff; text-underline-offset: 3px; }
  @media (max-width: 480px) { .card { padding: 28px 22px 24px; } h1 { font-size: 23px; } }
</style>
</head>
<body>
<main>
  <div class="card">
    <span class="mark"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="3" y="11" width="18" height="10" rx="2"/><path d="M7 11V7a5 5 0 0 1 10 0v4"/></svg>Private preview</span>
    <h1>Design review</h1>
    <p class="lede">These page designs are shared privately for review. Enter the access code you received to continue.</p>
    <form method="post" action="${AUTH_PATH}">
      <input type="hidden" name="next" value="${escapeHtml(next)}">
      <label for="code">Access code</label>
      <input id="code" name="code" type="password" autocomplete="off" autocapitalize="none" spellcheck="false" required autofocus${failed ? ' aria-invalid="true" aria-describedby="code-error"' : ''}>
      ${failed ? '<p class="error" id="code-error" role="alert"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.4" stroke-linecap="round" aria-hidden="true"><circle cx="12" cy="12" r="9"/><path d="M12 8v5M12 16.5v.01"/></svg>That code didn’t match. Please try again.</p>' : ''}
      <button type="submit">Continue</button>
    </form>
  </div>
  <p class="foot">Prepared by Ingeniux · <a href="mailto:dhillis@ingeniux.com">dhillis@ingeniux.com</a></p>
</main>
</body>
</html>`;
  return new Response(html, {
    status: 401,
    headers: { 'Content-Type': 'text/html; charset=utf-8', 'Cache-Control': 'no-store', 'X-Robots-Tag': 'noindex, nofollow' },
  });
}

export default async function middleware(request) {
  const secret = process.env.BASIC_AUTH_PASSWORD;
  if (!secret) return new Response('Preview is not configured.', { status: 503 });

  const url = new URL(request.url);
  const expected = await token(secret);

  if (url.pathname === AUTH_PATH && request.method === 'POST') {
    const form = await request.formData();
    const next = safeNext(form.get('next'));
    if (form.get('code') === secret) {
      return new Response(null, {
        status: 303,
        headers: {
          Location: next,
          'Set-Cookie': `${COOKIE}=${expected}; Path=/; Max-Age=${MAX_AGE}; HttpOnly; Secure; SameSite=Lax`,
          'Cache-Control': 'no-store',
        },
      });
    }
    return accessPage(next, true);
  }

  if (readCookie(request, COOKIE) === expected) return;
  // The feedback API answers scripts, not people: refuse plainly instead of sending the page
  if (url.pathname.startsWith('/api/')) return new Response(JSON.stringify({ error: 'locked' }), { status: 401, headers: { 'Content-Type': 'application/json', 'Cache-Control': 'no-store' } });
  return accessPage(safeNext(url.pathname + url.search), false);
}
