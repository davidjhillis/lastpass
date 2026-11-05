// Design feedback store: one Markdown file per note on a `feedback` branch.
//
//   GET   /api/feedback            -> { notes: [...] }       every note, oldest first
//   POST  /api/feedback            -> { note }               new note  {type, page, anchor, label, at, vw, author, text}
//   PATCH /api/feedback            -> { note }               status    {id, status, by}
//
// Environment (Vercel project settings):
//   GITHUB_TOKEN       fine-grained token, Contents: read and write, this repo only (required)
//   FEEDBACK_REPO      owner/name, default davidjhillis/lastpass
//   FEEDBACK_BRANCH    default "feedback"
//   FEEDBACK_PASSCODE  optional; reviewers enter it once
//
// The branch is created on the first note as an orphan holding only notes/, a README
// and a vercel.json that turns off deployments, so a note never triggers a site build.

const REPO = process.env.FEEDBACK_REPO || 'davidjhillis/lastpass';
const BRANCH = process.env.FEEDBACK_BRANCH || 'feedback';
const DIR = 'notes';
const STATUSES = ['open', 'edited', 'approved'];
const TYPES = ['design', 'notes', 'schema'];   // Design, Notes (build notes), Schema (spec)
const FIELDS = ['id', 'type', 'page', 'anchor', 'label', 'at', 'vw', 'author', 'status', 'created', 'updated', 'history'];

function fail(status, message) { const e = new Error(message); e.status = status; return e; }

async function gh(path, opts = {}) {
  const res = await fetch('https://api.github.com' + path, {
    method: opts.method || 'GET',
    headers: {
      Authorization: 'Bearer ' + process.env.GITHUB_TOKEN,
      Accept: 'application/vnd.github+json',
      'X-GitHub-Api-Version': '2022-11-28',
      'User-Agent': 'lastpass-design-feedback',
      ...(opts.body ? { 'Content-Type': 'application/json' } : {})
    },
    body: opts.body ? JSON.stringify(opts.body) : undefined
  });
  const data = res.status === 204 ? null : await res.json().catch(() => null);
  return { status: res.status, data };
}

// Front matter values are written as JSON, which is valid YAML, so no parser dependency
function toMd(n) {
  return '---\n' + FIELDS.filter(k => n[k] !== undefined).map(k => k + ': ' + JSON.stringify(n[k])).join('\n') +
    '\n---\n\n' + String(n.text || '').trim() + '\n';
}
function fromMd(s) {
  const m = /^---\n([\s\S]*?)\n---\n?([\s\S]*)$/.exec(s || '');
  if (!m) return null;
  const n = {};
  m[1].split('\n').forEach(line => {
    const i = line.indexOf(': ');
    if (i < 1) return;
    const k = line.slice(0, i), v = line.slice(i + 2);
    try { n[k] = JSON.parse(v); } catch (e) { n[k] = v; }
  });
  n.text = m[2].trim();
  return n;
}
const fileFor = id => DIR + '/' + String(id).padStart(4, '0') + '.md';
const now = () => new Date().toISOString();

function clean(s, max) {
  if (typeof s !== 'string') return '';
  return s.replace(/[\u0000-\u0008\u000b\u000c\u000e-\u001f]/g, '').trim().slice(0, max);
}

async function listNotes() {
  const [owner, name] = REPO.split('/');
  const query = 'query($owner:String!,$name:String!,$expr:String!){repository(owner:$owner,name:$name){object(expression:$expr){... on Tree{entries{name object{... on Blob{text}}}}}}}';
  const { status, data } = await gh('/graphql', { method: 'POST', body: { query, variables: { owner, name, expr: BRANCH + ':' + DIR } } });
  if (status !== 200 || !data || data.errors) throw fail(502, 'Could not read notes from GitHub');
  const tree = data.data && data.data.repository && data.data.repository.object;
  if (!tree || !tree.entries) return [];
  return tree.entries
    .filter(e => /\.md$/.test(e.name) && e.object && typeof e.object.text === 'string')
    .map(e => fromMd(e.object.text))
    .filter(Boolean)
    .sort((a, b) => a.id - b.id);
}

async function ensureBranch() {
  const ref = await gh(`/repos/${REPO}/git/ref/heads/${encodeURIComponent(BRANCH)}`);
  if (ref.status === 200) return;
  if (ref.status !== 404) throw fail(502, 'Could not reach the feedback branch');
  const tree = await gh(`/repos/${REPO}/git/trees`, { method: 'POST', body: { tree: [
    { path: 'README.md', mode: '100644', type: 'blob', content: '# Design feedback\n\nOne file per note in `notes/`, written by `/api/feedback` on the design preview. Statuses: open, edited (review again), approved (closed).\n' },
    { path: 'vercel.json', mode: '100644', type: 'blob', content: '{ "git": { "deploymentEnabled": false } }\n' }
  ] } });
  if (tree.status !== 201) throw fail(502, 'Could not start the feedback branch');
  const commit = await gh(`/repos/${REPO}/git/commits`, { method: 'POST', body: { message: 'Start design feedback', tree: tree.data.sha, parents: [] } });
  if (commit.status !== 201) throw fail(502, 'Could not start the feedback branch');
  const made = await gh(`/repos/${REPO}/git/refs`, { method: 'POST', body: { ref: 'refs/heads/' + BRANCH, sha: commit.data.sha } });
  if (made.status !== 201 && made.status !== 422) throw fail(502, 'Could not start the feedback branch');
}

async function createNote(b) {
  const page = clean(b.page, 80), anchor = clean(b.anchor, 600), label = clean(b.label, 120), author = clean(b.author, 80), text = clean(b.text, 4000);
  const type = TYPES.indexOf(b.type) >= 0 ? b.type : 'design';
  if (!/^[a-z0-9-]+\.html$/.test(page)) throw fail(400, 'Unknown page');
  if (!author) throw fail(400, 'Add your name');
  if (!text) throw fail(400, 'Write a note');
  const at = Array.isArray(b.at) ? b.at.slice(0, 2).map(v => Math.min(1, Math.max(0, Number(v) || 0))) : [0, 0];
  const vw = Math.round(Number(b.vw) || 0);
  await ensureBranch();
  const notes = await listNotes();
  let id = notes.reduce((m, n) => Math.max(m, n.id || 0), 0) + 1;
  const t = now();
  for (let tries = 0; tries < 5; tries++, id++) {
    const note = { id, type, page, anchor, label, at, vw, author, status: 'open', created: t, updated: t, history: [{ status: 'open', by: author, at: t }], text };
    const put = await gh(`/repos/${REPO}/contents/${fileFor(id)}`, { method: 'PUT', body: {
      message: `Feedback #${id} (${type}) on ${page} from ${author}`,
      content: Buffer.from(toMd(note)).toString('base64'),
      branch: BRANCH
    } });
    if (put.status === 201) return note;
    if (put.status !== 422) throw fail(502, 'Could not save the note');
    // 422: that number was just taken by another reviewer, try the next one
  }
  throw fail(409, 'Could not number the note, try again');
}

async function updateNote(b) {
  const id = parseInt(b.id, 10), status = clean(b.status, 20), by = clean(b.by, 80);
  if (!id) throw fail(400, 'Which note?');
  if (STATUSES.indexOf(status) < 0) throw fail(400, 'Unknown status');
  if (!by) throw fail(400, 'Add your name');
  for (let tries = 0; tries < 2; tries++) {
    const got = await gh(`/repos/${REPO}/contents/${fileFor(id)}?ref=${encodeURIComponent(BRANCH)}`);
    if (got.status === 404) throw fail(404, 'Note not found');
    if (got.status !== 200) throw fail(502, 'Could not read the note');
    const note = fromMd(Buffer.from(got.data.content, 'base64').toString('utf8'));
    if (!note) throw fail(500, 'Note file is damaged');
    if (note.status === status) return note;
    const t = now();
    note.status = status; note.updated = t;
    note.history = (note.history || []).concat([{ status, by, at: t }]);
    const label = { open: 'reopened', edited: 'marked edited', approved: 'approved' }[status];
    const put = await gh(`/repos/${REPO}/contents/${fileFor(id)}`, { method: 'PUT', body: {
      message: `Feedback #${id} ${label} by ${by}`,
      content: Buffer.from(toMd(note)).toString('base64'),
      sha: got.data.sha,
      branch: BRANCH
    } });
    if (put.status === 200) return note;
    if (put.status !== 409) throw fail(502, 'Could not save the change');
    // 409: someone changed it at the same moment, read it again and retry
  }
  throw fail(409, 'The note changed while saving, try again');
}

module.exports = async function handler(req, res) {
  res.setHeader('Cache-Control', 'no-store');
  if (!process.env.GITHUB_TOKEN) return res.status(503).json({ error: 'not-configured' });
  const pass = process.env.FEEDBACK_PASSCODE;
  if (pass && req.headers['x-feedback-key'] !== pass) return res.status(401).json({ error: 'passcode' });
  try {
    if (req.method === 'GET') return res.status(200).json({ notes: await listNotes() });
    let body = req.body || {};
    if (typeof body === 'string') { try { body = JSON.parse(body); } catch (e) { body = {}; } }
    if (req.method === 'POST') return res.status(201).json({ note: await createNote(body) });
    if (req.method === 'PATCH') return res.status(200).json({ note: await updateNote(body) });
    res.setHeader('Allow', 'GET, POST, PATCH');
    return res.status(405).json({ error: 'Method not allowed' });
  } catch (e) {
    return res.status(e.status || 500).json({ error: e.status ? e.message : 'Something went wrong' });
  }
};

module.exports.toMd = toMd;
module.exports.fromMd = fromMd;
