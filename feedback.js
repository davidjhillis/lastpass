/* Design feedback: pinned notes on the review pages, and the all-notes table.
   Notes are saved by /api/feedback (one Markdown file per note on the `feedback` branch).
   Without that service (local preview, or before setup) notes stay in this browser. */
(function(){
  'use strict';
  if(window.self !== window.top) return;

  var PAGE = location.pathname.split('/').pop() || 'index.html';
  var STATUS = {
    open:     {label: 'Open', action: 'Reopen'},
    edited:   {label: 'Edited – review again', action: 'Mark edited'},
    approved: {label: 'Approved – closed', action: 'Approve'}
  };
  var TYPES = {design: 'Design', notes: 'Notes', schema: 'Schema'};
  var TYPE_HINT = {design: 'How it looks or reads', notes: 'The build notes', schema: 'CMS fields and spec'};
  // Notes on the CMS schema pop-up (its tabs are #sct-N / #scp-N)
  function inPopup(n){ return /^#sc[pt]-\d|sc-dialog/.test(String(n.anchor || '')); }
  function typeOf(n){ return TYPES[n.type] ? n.type : 'design'; }
  // What each status can move to, in button order
  var NEXT = {open: ['edited'], edited: ['approved', 'open'], approved: ['open']};
  var AVATAR = ['#3a213a', '#2f5bb0', '#255a33', '#7a3e0b', '#050606', '#5e4270', '#0f6b5c'];

  function store(k, v){ try { if(v === undefined) return localStorage.getItem(k); if(v === null) localStorage.removeItem(k); else localStorage.setItem(k, v); } catch(e){ return null; } }
  function esc(s){ return String(s == null ? '' : s).replace(/[&<>"']/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]; }); }
  function initials(name){ var w = String(name || '').trim().split(/\s+/).filter(Boolean); if(!w.length) return '?'; return ((w[0][0] || '') + (w.length > 1 ? w[w.length - 1][0] : '')).toUpperCase(); }
  function colorFor(name){ var h = 0; String(name).split('').forEach(function(c){ h = (h * 31 + c.charCodeAt(0)) >>> 0; }); return AVATAR[h % AVATAR.length]; }
  function avatar(name){ return '<span class="fb-av" style="background:' + colorFor(name) + '" title="' + esc(name) + '" aria-hidden="true">' + esc(initials(name)) + '</span>'; }
  function ago(iso){
    var s = (Date.now() - new Date(iso).getTime()) / 1000;
    if(!(s >= 0)) return '';
    if(s < 60) return 'just now'; if(s < 3600) return Math.floor(s / 60) + 'm ago'; if(s < 86400) return Math.floor(s / 3600) + 'h ago';
    if(s < 604800) return Math.floor(s / 86400) + 'd ago';
    return new Date(iso).toLocaleDateString(undefined, {month: 'short', day: 'numeric'});
  }
  function pageNames(){
    var m = {}; document.querySelectorAll('.rv-nav a').forEach(function(a){ m[a.getAttribute('href')] = a.textContent.trim(); }); return m;
  }

  /* ------------------------------------------------------------ storage */
  var mode = 'remote';           // remote | local | locked
  var LOCAL = 'fb-local-notes';
  function localNotes(){ try { return JSON.parse(store(LOCAL) || '[]'); } catch(e){ return []; } }
  function saveLocal(list){ store(LOCAL, JSON.stringify(list)); }
  function api(method, body){
    var h = {'Content-Type': 'application/json'}, p = store('fb-pass'); if(p) h['X-Feedback-Key'] = p;
    return fetch('/api/feedback', {method: method, headers: h, body: body ? JSON.stringify(body) : undefined, cache: 'no-store'})
      .then(function(r){ return r.json().catch(function(){ return {}; }).then(function(d){ d = d || {}; d._status = r.status; return d; }); });
  }
  function load(){
    return api('GET').then(function(d){
      if(d._status === 200 && Array.isArray(d.notes)){ mode = 'remote'; return d.notes; }
      if(d._status === 401){ mode = 'locked'; return []; }
      mode = 'local'; return localNotes();
    }, function(){ mode = 'local'; return localNotes(); });
  }
  function create(n){
    if(mode === 'local'){
      var list = localNotes(), t = new Date().toISOString();
      var note = Object.assign({id: list.reduce(function(m, x){ return Math.max(m, x.id); }, 0) + 1, status: 'open', created: t, updated: t, history: [{status: 'open', by: n.author, at: t}]}, n);
      list.push(note); saveLocal(list); return Promise.resolve(note);
    }
    return api('POST', n).then(function(d){ if(d._status === 201) return d.note; throw new Error(d.error || 'Could not save the note'); });
  }
  function update(id, status, by){
    if(mode === 'local'){
      var list = localNotes(), n = list.filter(function(x){ return x.id === id; })[0], t = new Date().toISOString();
      if(!n) return Promise.reject(new Error('Note not found'));
      n.status = status; n.updated = t; n.history = (n.history || []).concat([{status: status, by: by, at: t}]);
      saveLocal(list); return Promise.resolve(n);
    }
    return api('PATCH', {id: id, status: status, by: by}).then(function(d){ if(d._status === 200) return d.note; throw new Error(d.error || 'Could not save the change'); });
  }

  /* ------------------------------------------------------------ shared bits */
  var notes = [];
  function me(){ return store('fb-name') || ''; }
  function modeNote(){
    if(mode === 'local') return '<p class="fb-mode">Notes are saved in this browser only. Shared feedback isn’t connected yet.</p>';
    return '';
  }
  function nameForm(label){
    return '<form class="fb-name-form"><label for="fb-name-' + label + '">Your name</label><div class="fb-row"><input id="fb-name-' + label + '" name="name" required maxlength="80" autocomplete="name" value="' + esc(me()) + '"><button type="submit" class="fb-btn">Save</button></div></form>';
  }
  function passForm(){
    return '<form class="fb-pass-form"><label for="fb-pass">Review passcode</label><div class="fb-row"><input id="fb-pass" name="pass" type="password" required autocomplete="off"><button type="submit" class="fb-btn fb-btn--primary">Open</button></div></form>';
  }
  function wireIdentity(root, onDone){
    var nf = root.querySelector('.fb-name-form');
    if(nf) nf.addEventListener('submit', function(e){ e.preventDefault(); var v = nf.name.value.trim(); if(!v) return; store('fb-name', v); onDone(); });
    var pf = root.querySelector('.fb-pass-form');
    if(pf) pf.addEventListener('submit', function(e){ e.preventDefault(); store('fb-pass', pf.pass.value); location.reload(); });
    var ch = root.querySelector('.fb-change');
    if(ch) ch.addEventListener('click', function(){ store('fb-name', null); onDone(true); });
  }
  function whoami(){
    return '<p class="fb-me">' + avatar(me()) + '<span>' + esc(me()) + '</span><button type="button" class="fb-change">Change</button></p>';
  }

  /* ============================================================ board (feedback.html) */
  var board = document.getElementById('fb-board');
  if(board){
    var filt = {status: 'all', page: '', who: '', type: ''};
    function rowsFor(){ return notes.filter(function(n){ return (filt.status === 'all' || n.status === filt.status) && (!filt.type || typeOf(n) === filt.type) && (!filt.page || n.page === filt.page) && (!filt.who || n.author === filt.who); }); }
    function csv(){
      var cols = ['id', 'type', 'page', 'status', 'author', 'created', 'updated', 'text', 'link'];
      var base = location.href.replace(/[^/]*$/, '');
      var lines = [cols.join(',')].concat(notes.map(function(n){
        return cols.map(function(c){ var v = c === 'link' ? base + n.page + '#fb-' + n.id : c === 'type' ? TYPES[typeOf(n)] : n[c]; return '"' + String(v == null ? '' : v).replace(/"/g, '""') + '"'; }).join(',');
      }));
      var a = document.createElement('a'); a.href = URL.createObjectURL(new Blob([lines.join('\n')], {type: 'text/csv'})); a.download = 'design-feedback.csv';
      document.body.appendChild(a); a.click(); a.remove();
    }
    function renderBoard(){
      var names = pageNames();
      if(mode === 'locked'){ board.innerHTML = passForm(); wireIdentity(board, renderBoard); return; }
      var count = function(s){ return notes.filter(function(n){ return s === 'all' || n.status === s; }).length; };
      var pages = notes.map(function(n){ return n.page; }).filter(function(v, i, a){ return a.indexOf(v) === i; }).sort();
      var people = notes.map(function(n){ return n.author; }).filter(function(v, i, a){ return a.indexOf(v) === i; }).sort();
      var rows = rowsFor();
      board.innerHTML = modeNote() +
        '<div class="fb-board-id">' + (me() ? whoami() : nameForm('board')) + '</div>' +
        '<div class="fb-bar">' +
          '<div class="fb-seg" role="group" aria-label="Status">' + ['all', 'open', 'edited', 'approved'].map(function(s){
            return '<button type="button" data-s="' + s + '" aria-pressed="' + (filt.status === s) + '">' + (s === 'all' ? 'All' : STATUS[s].label.split(' –')[0]) + ' <b>' + count(s) + '</b></button>'; }).join('') + '</div>' +
          '<label class="fb-sel"><span class="sr-only">Type</span><select data-f="type"><option value="">All types</option>' + Object.keys(TYPES).map(function(t){ return '<option value="' + t + '"' + (filt.type === t ? ' selected' : '') + '>' + TYPES[t] + '</option>'; }).join('') + '</select></label>' +
          '<label class="fb-sel"><span class="sr-only">Page</span><select data-f="page"><option value="">All pages</option>' + pages.map(function(p){ return '<option value="' + esc(p) + '"' + (filt.page === p ? ' selected' : '') + '>' + esc(names[p] || p) + '</option>'; }).join('') + '</select></label>' +
          '<label class="fb-sel"><span class="sr-only">Reviewer</span><select data-f="who"><option value="">All reviewers</option>' + people.map(function(p){ return '<option' + (filt.who === p ? ' selected' : '') + '>' + esc(p) + '</option>'; }).join('') + '</select></label>' +
          '<button type="button" class="fb-btn fb-csv"' + (notes.length ? '' : ' disabled') + '>Download CSV</button>' +
        '</div>' +
        (rows.length ? '<div class="fb-table-wrap"><table class="fb-table"><thead><tr><th scope="col">#</th><th scope="col">Type</th><th scope="col">Page</th><th scope="col">Note</th><th scope="col">Reviewer</th><th scope="col">Updated</th><th scope="col">Status</th></tr></thead><tbody>' +
          rows.map(function(n){
            return '<tr data-status="' + n.status + '"><td><a class="fb-num" href="' + esc(n.page) + '#fb-' + n.id + '">' + n.id + '</a></td>' +
              '<td><span class="fb-type" data-type="' + typeOf(n) + '">' + TYPES[typeOf(n)] + '</span></td>' +
              '<td><a href="' + esc(n.page) + '#fb-' + n.id + '">' + esc(names[n.page] || n.page) + '</a></td>' +
              '<td class="fb-td-text">' + esc(n.text) + '</td>' +
              '<td><span class="fb-who-cell">' + avatar(n.author) + esc(n.author) + '</span></td>' +
              '<td><time datetime="' + esc(n.updated) + '" title="' + esc(new Date(n.updated).toLocaleString()) + '">' + ago(n.updated) + '</time></td>' +
              '<td><label class="sr-only" for="fb-st-' + n.id + '">Status of note ' + n.id + '</label><select id="fb-st-' + n.id + '" class="fb-status-sel" data-id="' + n.id + '">' +
                ['open', 'edited', 'approved'].map(function(s){ return '<option value="' + s + '"' + (n.status === s ? ' selected' : '') + '>' + STATUS[s].label + '</option>'; }).join('') + '</select></td></tr>';
          }).join('') + '</tbody></table></div>'
          : '<p class="fb-empty">' + (notes.length ? 'No notes match these filters.' : 'No notes yet. Open any page and choose Feedback to add one.') + '</p>');
      wireIdentity(board, renderBoard);
      board.querySelectorAll('.fb-seg button').forEach(function(b){ b.addEventListener('click', function(){ filt.status = b.getAttribute('data-s'); renderBoard(); }); });
      board.querySelectorAll('select[data-f]').forEach(function(s){ s.addEventListener('change', function(){ filt[s.getAttribute('data-f')] = s.value; renderBoard(); }); });
      var c = board.querySelector('.fb-csv'); if(c) c.addEventListener('click', csv);
      board.querySelectorAll('.fb-status-sel').forEach(function(s){
        s.addEventListener('change', function(){
          var id = +s.getAttribute('data-id'), n = notes.filter(function(x){ return x.id === id; })[0];
          if(!me()){ s.value = n.status; var inp = board.querySelector('.fb-name-form input'); if(inp) inp.focus(); return; }
          s.disabled = true;
          update(id, s.value, me()).then(function(u){ Object.assign(n, u); renderBoard(); }, function(err){ alert(err.message); s.value = n.status; s.disabled = false; });
        });
      });
    }
    function start(){ load().then(function(list){ notes = list; renderBoard(); }); }
    start();
    return;
  }

  /* ============================================================ review pages */
  if(!document.querySelector('.t-notes-toggle')) return;   // only the design-review pages

  var open = false, picking = false, draft = null, filter = 'active', selected = null, pendingPick = false, preset = null;
  function mine(){ return notes.filter(function(n){ return n.page === PAGE; }); }
  function active(n){ return n.status !== 'approved'; }

  // Dock button
  var dock = document.querySelector('.t-dock');
  if(!dock){ dock = document.createElement('div'); dock.className = 't-dock'; document.body.appendChild(dock); var nt = document.querySelector('.t-notes-toggle'); if(nt && !nt.hidden) dock.appendChild(nt); }
  var btn = document.createElement('button'); btn.type = 'button'; btn.className = 't-dock-btn fb-dock-btn';
  btn.setAttribute('aria-controls', 'fb-panel'); btn.setAttribute('aria-expanded', 'false');
  btn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg><span>Feedback</span><span class="fb-badge" hidden></span>';
  dock.insertBefore(btn, dock.firstChild);

  // Panel
  var panel = document.createElement('aside'); panel.id = 'fb-panel'; panel.className = 'fb-panel'; panel.hidden = true;
  panel.setAttribute('aria-label', 'Design feedback');
  document.body.appendChild(panel);

  // Pins layer, pointer catcher, hint
  var pins = document.createElement('div'); pins.className = 'fb-pins'; document.body.appendChild(pins);
  var catcher = document.createElement('div'); catcher.className = 'fb-catcher'; catcher.hidden = true; document.body.appendChild(catcher);
  var hover = document.createElement('div'); hover.className = 'fb-hover'; hover.hidden = true; document.body.appendChild(hover);
  var hint = document.createElement('div'); hint.className = 'fb-hint'; hint.hidden = true; hint.setAttribute('role', 'status');
  hint.innerHTML = '<span>Click the spot you want to comment on</span><button type="button" class="fb-hint-x">Cancel</button>'; document.body.appendChild(hint);
  hint.querySelector('.fb-hint-x').addEventListener('click', function(){ setPicking(false); if(open) renderPanel(); });

  function snippet(el){ return String(el.textContent || '').replace(/\s+/g, ' ').trim().slice(0, 80); }
  // Find the element again: by its path, or, if the page has changed around it, by its text
  function find(n){
    var el = null; try { el = document.querySelector(n.anchor); } catch(e){}
    if(el && (!n.label || snippet(el) === n.label)) return el;
    if(n.label){
      var tag = String(n.anchor).split('>').pop().trim().split(':')[0];
      if(/^[a-z][a-z0-9]*$/.test(tag)){
        var hit = [].filter.call(document.querySelectorAll(tag), function(x){ return !ours(x) && snippet(x) === n.label; });
        if(hit.length === 1) return hit[0];
      }
    }
    return el;
  }
  function resolve(n){
    var el = find(n);
    if(!el) return {state: 'detached'};
    var r = el.getBoundingClientRect();
    if(!r.width || !r.height) return {state: 'hidden'};
    var at = n.at || [0, 0];
    return {state: 'ok', x: r.left + window.scrollX + at[0] * r.width, y: r.top + window.scrollY + at[1] * r.height};
  }

  function renderPins(){
    pins.textContent = '';
    if(!open && !location.hash.match(/^#fb-/)) { pins.hidden = true; return; }
    pins.hidden = false;
    mine().forEach(function(n){
      if(filter === 'active' && !active(n) && selected !== n.id) return;
      var p = resolve(n); if(p.state !== 'ok') return;
      var b = document.createElement('button'); b.type = 'button'; b.className = 'fb-pin'; b.setAttribute('data-status', n.status); b.setAttribute('data-id', n.id);
      if(selected === n.id) b.classList.add('is-on');
      b.style.left = p.x + 'px'; b.style.top = p.y + 'px'; b.textContent = n.id;
      b.setAttribute('aria-label', 'Note ' + n.id + ' from ' + n.author + ', ' + STATUS[n.status].label);
      b.addEventListener('click', function(){ select(n.id, false); });
      pins.appendChild(b);
    });
    if(draft && draft.pos){
      var d = document.createElement('span'); d.className = 'fb-pin fb-pin--draft'; d.setAttribute('aria-hidden', 'true'); d.textContent = '+';
      d.style.left = draft.pos.x + 'px'; d.style.top = draft.pos.y + 'px'; pins.appendChild(d);
    }
  }

  function badge(){
    var c = mine().filter(active).length, b = btn.querySelector('.fb-badge');
    b.hidden = !c; b.textContent = c; btn.setAttribute('aria-label', 'Feedback' + (c ? ', ' + c + ' open' : ''));
  }

  function card(n){
    var where = resolve(n).state, acts = NEXT[n.status].map(function(s){ return '<button type="button" class="fb-act" data-to="' + s + '">' + STATUS[s].action + '</button>'; }).join('');
    return '<li class="fb-card' + (selected === n.id ? ' is-on' : '') + '" data-id="' + n.id + '" data-status="' + n.status + '">' +
      '<div class="fb-card-top"><button type="button" class="fb-num" aria-label="Show note ' + n.id + ' on the page">' + n.id + '</button>' + avatar(n.author) +
        '<span class="fb-who">' + esc(n.author) + '</span><time datetime="' + esc(n.created) + '" title="' + esc(new Date(n.created).toLocaleString()) + '">' + ago(n.created) + '</time></div>' +
      '<p class="fb-text">' + esc(n.text) + '</p>' +
      '<div class="fb-card-foot"><span class="fb-type" data-type="' + typeOf(n) + '">' + TYPES[typeOf(n)] + '</span><span class="fb-pill">' + STATUS[n.status].label + '</span>' +
        (where === 'detached' && inPopup(n) && document.querySelector('.t-schema-btn') ? '<span class="fb-flag fb-flag--info" title="Click the number to open it">In CMS schema</span>' : where === 'detached' ? '<span class="fb-flag" title="The part of the page this note was on has changed">Detached</span>' : where === 'hidden' ? '<span class="fb-flag" title="On a tab or section that is closed">Not visible</span>' : '') +
        '<span class="fb-acts">' + acts + '<button type="button" class="fb-copy" aria-label="Copy link to note ' + n.id + '"><svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/><path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/></svg></button></span></div></li>';
  }

  function renderPanel(){
    var list = mine(), act = list.filter(active), shown = filter === 'active' ? act : list;
    var html = '<div class="fb-head"><h2>Feedback</h2><a href="feedback.html" class="fb-all">All notes</a>' +
      '<button type="button" class="fb-x" aria-label="Close feedback"><svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" aria-hidden="true"><path d="M18 6 6 18M6 6l12 12"/></svg></button></div>';
    html += '<div class="fb-body">' + modeNote();
    if(mode === 'locked'){ panel.innerHTML = html + passForm() + '</div>'; wireIdentity(panel, renderPanel); return; }
    html += me() ? whoami() : nameForm('panel');
    if(draft){
      html += '<form class="fb-draft"><fieldset class="fb-typepick"><legend>Feedback on</legend>' + Object.keys(TYPES).map(function(t){
          return '<label title="' + TYPE_HINT[t] + '"><input type="radio" name="type" value="' + t + '"' + (draft.type === t ? ' checked' : '') + '><span>' + TYPES[t] + '</span></label>'; }).join('') + '</fieldset>' +
        '<label for="fb-draft-text">Note</label><textarea id="fb-draft-text" name="text" rows="4" maxlength="4000" required placeholder="What should change here?"></textarea>' +
        '<div class="fb-row"><button type="submit" class="fb-btn fb-btn--primary">Post note</button><button type="button" class="fb-btn fb-cancel">Cancel</button></div><p class="fb-err" role="alert" hidden></p></form>';
    } else {
      html += '<button type="button" class="fb-btn fb-btn--primary fb-add" aria-pressed="' + picking + '">' + (picking ? 'Cancel' : '+ Add a note') + '</button>';
    }
    html += '<div class="fb-tabs" role="group" aria-label="Show"><button type="button" data-f="active" aria-pressed="' + (filter === 'active') + '">Open <b>' + act.length + '</b></button>' +
      '<button type="button" data-f="all" aria-pressed="' + (filter === 'all') + '">All <b>' + list.length + '</b></button></div>';
    html += shown.length ? '<ol class="fb-list">' + shown.map(card).join('') + '</ol>'
      : '<p class="fb-empty">' + (list.length ? 'Everything here is approved.' : 'No notes on this page yet.') + '</p>';
    panel.innerHTML = html + '</div>';

    panel.querySelector('.fb-x').addEventListener('click', function(){ setOpen(false); btn.focus(); });
    wireIdentity(panel, function(changed){ renderPanel(); if(!changed && pendingPick){ pendingPick = false; setPicking(true); } else { var i = panel.querySelector('.fb-name-form input'); if(i) i.focus(); } });
    var add = panel.querySelector('.fb-add'); if(add) add.addEventListener('click', function(){ setPicking(!picking); });
    panel.querySelectorAll('.fb-tabs button').forEach(function(b){ b.addEventListener('click', function(){ filter = b.getAttribute('data-f'); renderPanel(); renderPins(); }); });
    var f = panel.querySelector('.fb-draft');
    if(f){
      var ta = f.text; ta.focus();
      ta.addEventListener('keydown', function(e){ if(e.key === 'Enter' && (e.metaKey || e.ctrlKey)){ e.preventDefault(); f.requestSubmit ? f.requestSubmit() : f.dispatchEvent(new Event('submit')); } });
      f.querySelector('.fb-cancel').addEventListener('click', function(){ draft = null; renderPanel(); renderPins(); });
      f.querySelectorAll('input[name=type]').forEach(function(r){ r.addEventListener('change', function(){ draft.type = r.value; }); });
      f.addEventListener('submit', function(e){
        e.preventDefault(); var text = ta.value.trim(); if(!text) return;
        var sub = f.querySelector('[type=submit]'); sub.disabled = true; sub.textContent = 'Posting…';
        create({type: draft.type, page: PAGE, anchor: draft.anchor, label: draft.label, at: draft.at, vw: window.innerWidth, author: me(), text: text}).then(function(n){
          notes.push(n); draft = null; filter = 'active'; selected = n.id; badge(); renderPanel(); renderPins();
        }, function(err){ sub.disabled = false; sub.textContent = 'Post note'; var p = f.querySelector('.fb-err'); p.hidden = false; p.textContent = err.message; });
      });
    }
    panel.querySelectorAll('.fb-card').forEach(function(li){
      var id = +li.getAttribute('data-id'), n = notes.filter(function(x){ return x.id === id; })[0];
      li.querySelector('.fb-num').addEventListener('click', function(){ select(id, true); });
      li.addEventListener('mouseenter', function(){ var p = pins.querySelector('.fb-pin[data-id="' + id + '"]'); if(p) p.classList.add('is-hot'); });
      li.addEventListener('mouseleave', function(){ var p = pins.querySelector('.fb-pin[data-id="' + id + '"]'); if(p) p.classList.remove('is-hot'); });
      li.querySelectorAll('.fb-act').forEach(function(b){
        b.addEventListener('click', function(){
          if(!me()){ var i = panel.querySelector('.fb-name-form input'); if(i) i.focus(); return; }
          b.disabled = true;
          update(id, b.getAttribute('data-to'), me()).then(function(u){ Object.assign(n, u); badge(); renderPanel(); renderPins(); }, function(err){ b.disabled = false; alert(err.message); });
        });
      });
      li.querySelector('.fb-copy').addEventListener('click', function(){
        var url = location.href.split('#')[0] + '#fb-' + id, c = this;
        (navigator.clipboard ? navigator.clipboard.writeText(url) : Promise.reject()).then(function(){ c.classList.add('is-done'); setTimeout(function(){ c.classList.remove('is-done'); }, 1200); }, function(){ prompt('Link to this note', url); });
      });
    });
  }

  // Open whatever hides a note's element: a closed tab, a <details>, the schema pop-up
  function reveal(el){
    for(var x = el; x && x !== document.body; x = x.parentElement){
      if(x.getAttribute('role') === 'tabpanel' && x.hidden){ var tab = document.querySelector('[aria-controls="' + x.id + '"]'); if(tab) tab.click(); }
      if(x.tagName === 'DETAILS' && !x.open) x.open = true;
      if(x.tagName === 'DIALOG' && !x.open) dockDialog(x);
    }
  }
  function select(id, scroll){
    var n0 = notes.filter(function(x){ return x.id === id; })[0];
    if(n0){
      var el0 = find(n0);
      if(el0 && resolve(n0).state === 'hidden') reveal(el0);
      // A schema note whose pop-up hasn't been built yet: open it, then come back
      if(!el0 && inPopup(n0) && !document.getElementById('sc-dialog')){
        var sb = document.querySelector('.t-schema-btn');
        if(sb && !select.waiting){
          select.waiting = true; if(!open) setOpen(true); sb.click();
          var tries = 0, iv = setInterval(function(){ if(document.getElementById('sc-dialog') || ++tries > 30){ clearInterval(iv); select.waiting = false; if(document.getElementById('sc-dialog')) select(id, scroll); } }, 100);
          return;
        }
      }
    }
    selected = id; var n = n0;
    if(n && !active(n)) filter = 'all';
    if(!open) setOpen(true); else { renderPanel(); renderPins(); }
    var li = panel.querySelector('.fb-card[data-id="' + id + '"]'); if(li) li.scrollIntoView({block: 'nearest'});
    if(scroll && n){ var p = resolve(n); if(p.state === 'ok') window.scrollTo({top: Math.max(0, p.y - window.innerHeight / 3), behavior: 'smooth'}); }
    var pin = pins.querySelector('.fb-pin[data-id="' + id + '"]'); if(pin){ pin.classList.remove('is-pulse'); void pin.offsetWidth; pin.classList.add('is-pulse'); }
  }

  function setOpen(v){
    open = v; panel.hidden = !v; document.body.classList.toggle('fb-open', v); btn.setAttribute('aria-expanded', v ? 'true' : 'false');
    if(!v){ setPicking(false); draft = null; selected = null; }
    renderPanel(); renderPins();
    if(v){ var first = panel.querySelector('.fb-name-form input, .fb-add'); if(first && !selected) first.focus(); }
    window.dispatchEvent(new Event('resize'));   // lets the build-notes layer re-measure
  }

  /* ------------------------------------------------------------ pointer tool */
  function ours(el){ return !el || !!el.closest('.fb-panel, .t-dock, .fb-pins, .fb-hint, .t-note-layer, .rv-nav, .fb-catcher, .fb-hover'); }
  function under(x, y){ catcher.style.pointerEvents = 'none'; var el = document.elementFromPoint(x, y); catcher.style.pointerEvents = ''; return ours(el) ? null : el; }
  function cssPath(el){
    var parts = [];
    while(el && el.nodeType === 1 && el !== document.body){
      if(el.id && !/^fb-/.test(el.id)){ parts.unshift('#' + CSS.escape(el.id)); return parts.join(' > '); }
      var i = 1, s = el; while((s = s.previousElementSibling)) if(s.tagName === el.tagName) i++;
      parts.unshift(el.tagName.toLowerCase() + ':nth-of-type(' + i + ')'); el = el.parentElement;
    }
    parts.unshift('body'); return parts.join(' > ');
  }
  function setPicking(v){
    if(!v) document.body.classList.remove('fb-picking');
    if(v && !me()){ pendingPick = true; if(!open) setOpen(true); var i = panel.querySelector('.fb-name-form input'); if(i) i.focus(); return; }
    picking = v; catcher.hidden = !v; hint.hidden = !v; hover.hidden = true; document.body.classList.toggle('fb-picking', v);
    if(open) renderPanel();
  }
  catcher.addEventListener('mousemove', function(e){
    var el = under(e.clientX, e.clientY); if(!el){ hover.hidden = true; return; }
    var r = el.getBoundingClientRect(); hover.hidden = false;
    hover.style.cssText = 'left:' + r.left + 'px;top:' + r.top + 'px;width:' + r.width + 'px;height:' + r.height + 'px';
  });
  catcher.addEventListener('click', function(e){
    var el = under(e.clientX, e.clientY); if(!el) return;
    var r = el.getBoundingClientRect();
    draft = {type: preset || guessType(el), anchor: cssPath(el), label: snippet(el), at: [+((e.clientX - r.left) / r.width).toFixed(4), +((e.clientY - r.top) / r.height).toFixed(4)],
             pos: {x: e.clientX + window.scrollX, y: e.clientY + window.scrollY}};
    preset = null; setPicking(false); renderPanel(); renderPins();
  });
  function guessType(el){
    if(el.closest('.sc-dialog, [class^="sc-"], [class*=" sc-"]')) return 'schema';
    if(document.body.classList.contains('show-notes') && el.closest('[data-note]')) return 'notes';
    return 'design';
  }
  document.addEventListener('keydown', function(e){
    if(e.key !== 'Escape') return;
    if(picking){ setPicking(false); return; }
    if(draft){ draft = null; renderPanel(); renderPins(); return; }
    if(open && !document.querySelector('dialog[open]')){ setOpen(false); btn.focus(); }
  });

  btn.addEventListener('click', function(){ setOpen(!open); });

  // The schema pop-up is modal, which would block the notes column. While feedback is on,
  // it opens as a normal panel instead, so its fields can take pins.
  function dockDialog(d){
    if(d.open) d.close();
    d.classList.add('fb-docked'); d.show(); document.body.classList.add('fb-dialog');
    if(!d._fbWired){ d._fbWired = true; d.addEventListener('close', function(){ if(d.open) return; d.classList.remove('fb-docked'); document.body.classList.remove('fb-dialog'); relayout(); }); }
    relayout();
  }
  window.FB = {
    get open(){ return open; },
    dock: dockDialog,
    // "Add feedback" in the schema pop-up
    schema: function(d){ dockDialog(d); if(!open) setOpen(true); preset = 'schema'; setPicking(true); }
  };

  /* ------------------------------------------------------------ keep pins on their spots */
  var queued = false;
  function relayout(){ if(queued) return; queued = true; requestAnimationFrame(function(){ queued = false; renderPins(); }); }
  window.addEventListener('resize', relayout); window.addEventListener('load', relayout);
  document.addEventListener('click', function(e){ if(!ours(e.target)) setTimeout(relayout, 60); }, true);
  document.addEventListener('scroll', function(e){ if(e.target !== document && document.body.classList.contains('fb-dialog')) relayout(); }, true);
  window.addEventListener('scroll', function(){ if(document.body.classList.contains('fb-dialog')) relayout(); }, {passive: true});
  if(window.ResizeObserver) new ResizeObserver(relayout).observe(document.body);

  function fromHash(){ var m = /^#fb-(\d+)$/.exec(location.hash); if(m) select(+m[1], true); }
  window.addEventListener('hashchange', fromHash);

  function start(){ load().then(function(list){ notes = list; badge(); if(open) renderPanel(); renderPins(); fromHash(); }); }
  start();
})();
