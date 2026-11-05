/* Template behaviors: FAQ accordion, expand all, copy question link, Vimeo
   poster swap, in-page nav highlight, build-notes toggle. No dependencies. */
(function(){
  // FAQ accordion — button in heading, aria-expanded drives the answer
  function setItem(btn, open){
    btn.setAttribute('aria-expanded', open ? 'true' : 'false');
    var panel = document.getElementById(btn.getAttribute('aria-controls'));
    if(panel) panel.hidden = !open;
  }
  document.querySelectorAll('.t-faq-q').forEach(function(btn){
    btn.addEventListener('click', function(){ setItem(btn, btn.getAttribute('aria-expanded') !== 'true'); });
  });
  document.querySelectorAll('[data-faq-all]').forEach(function(ctl){
    ctl.addEventListener('click', function(){
      var scope = document.querySelector(ctl.getAttribute('data-faq-all')) || document;
      var btns = [].slice.call(scope.querySelectorAll('.t-faq-q'));
      var open = btns.some(function(b){ return b.getAttribute('aria-expanded') !== 'true'; });
      btns.forEach(function(b){ setItem(b, open); });
      ctl.querySelector('span').textContent = open ? 'Collapse all' : 'Expand all';
    });
  });
  // Open the question named in the URL hash
  function openFromHash(){
    var id = location.hash.slice(1); if(!id) return;
    var item = document.getElementById(id);
    var btn = item && item.querySelector('.t-faq-q');
    if(btn){ setItem(btn, true); item.scrollIntoView({block:'start'}); btn.focus({preventScroll:true}); }
  }
  openFromHash(); addEventListener('hashchange', openFromHash);
  // Copy a link to one question
  document.querySelectorAll('[data-copy-anchor]').forEach(function(b){
    b.addEventListener('click', function(){
      var url = location.href.split('#')[0] + '#' + b.getAttribute('data-copy-anchor');
      var label = b.querySelector('span'); var was = label.textContent;
      function done(){ label.textContent = 'Link copied'; setTimeout(function(){ label.textContent = was; }, 1600); }
      if(navigator.clipboard) navigator.clipboard.writeText(url).then(done, function(){ location.hash = b.getAttribute('data-copy-anchor'); });
      else location.hash = b.getAttribute('data-copy-anchor');
    });
  });

  // Vimeo: poster button swaps to the player on click
  document.querySelectorAll('.t-video[data-vimeo]').forEach(function(btn){
    btn.addEventListener('click', function(){
      var f = document.createElement('iframe');
      f.src = 'https://player.vimeo.com/video/' + btn.getAttribute('data-vimeo') + '?autoplay=1&dnt=1';
      f.title = btn.getAttribute('data-title') || 'Video';
      f.allow = 'autoplay; fullscreen; picture-in-picture';
      f.setAttribute('allowfullscreen', '');
      f.style.cssText = 'width:100%;aspect-ratio:16/9;border:0;border-radius:16px;display:block';
      btn.replaceWith(f);
    });
  });

  // In-page nav: highlight the section in view
  var nav = document.querySelector('[data-section-nav]');
  if(nav && 'IntersectionObserver' in window){
    var links = {}; nav.querySelectorAll('a[href^="#"]').forEach(function(a){ links[a.getAttribute('href').slice(1)] = a; });
    var io = new IntersectionObserver(function(es){
      es.forEach(function(e){
        if(e.isIntersecting && links[e.target.id]){
          Object.keys(links).forEach(function(k){ links[k].classList.remove('is-active'); links[k].removeAttribute('aria-current'); });
          links[e.target.id].classList.add('is-active'); links[e.target.id].setAttribute('aria-current', 'true');
        }
      });
    }, { rootMargin: '-30% 0px -60% 0px' });
    Object.keys(links).forEach(function(id){ var s = document.getElementById(id); if(s) io.observe(s); });
  }

  // Hub switcher: start the scrolling row at the current hub
  var hubRow = document.querySelector('.t-hubs .t-wrap'), hubCur = document.querySelector('.t-hubs [aria-current]');
  if(hubRow && hubCur && hubRow.scrollWidth > hubRow.clientWidth){ hubRow.scrollLeft = hubCur.offsetLeft - hubRow.offsetLeft - 24; }

  // Template index: scale each live thumbnail to its card
  var thumbs = document.querySelectorAll('.tp-thumb');
  function fit(){ thumbs.forEach(function(t){ t.style.setProperty('--tp-scale', (t.clientWidth / 1440).toFixed(4)); }); }
  if(thumbs.length){ fit(); addEventListener('resize', fit); }

  // Review super nav: switch between the new page designs (not part of the site)
  var PAGES = [
    ['templates.html', 'Page types'], ['components.html', 'Essentials'], null,
    ['hub-business.html', 'Mini hub'], ['topic-saas-monitoring.html', 'Topic: product'], ['topic-billing.html', 'Topic: utility'],
    ['faq.html', 'FAQ'], ['contact-us.html', 'Contact Us'], ['lifecycle.html', 'Lifecycle'], null,
    ['release-notes.html', 'Release notes'], ['downloads.html', 'Downloads'], ['known-issues.html', 'Known issues']
  ];
  if(window.self === window.top && document.querySelector('.t-notes-toggle') && !document.querySelector('.rv-nav')){
    var here = location.pathname.split('/').pop() || 'index.html';
    var rv = document.createElement('nav'); rv.className = 'rv-nav'; rv.setAttribute('aria-label', 'Design review pages');
    rv.innerHTML = '<div class="rv-in"><span class="rv-label">Design review</span><ul>' + PAGES.map(function(p){
      return p ? '<li><a href="' + p[0] + '"' + (p[0] === here ? ' aria-current="page"' : '') + '>' + p[1] + '</a></li>' : '<li class="rv-sep" aria-hidden="true"></li>';
    }).join('') + '</ul></div>';
    document.body.insertBefore(rv, document.body.firstChild);
    var cur = rv.querySelector('[aria-current]'), list = rv.querySelector('ul');
    if(cur && list.scrollWidth > list.clientWidth){ list.scrollLeft = cur.offsetLeft - list.offsetLeft - 24; }
  }

  // Library: try a unit's options on its first example
  document.querySelectorAll('[data-try]').forEach(function(bar){
    var fig = document.querySelector(bar.getAttribute('data-try')); if(!fig) return;
    bar.querySelectorAll('button[data-set]').forEach(function(btn){
      btn.addEventListener('click', function(){
        var k = btn.getAttribute('data-set'), v = btn.getAttribute('data-val');
        if(k === 'media'){ var t = fig.querySelector('.mk-tray'); if(t) t.setAttribute('data-media', v); }
        if(k === 'bg'){ var u = fig.querySelector('.u'); if(u) u.setAttribute('data-bg', v); }
        if(k === 'ratio'){ var m = fig.querySelector('.mk-tray-media'); if(m) m.style.setProperty('--ratio', v); }
        bar.querySelectorAll('button[data-set="' + k + '"]').forEach(function(b){ b.setAttribute('aria-pressed', b === btn ? 'true' : 'false'); });
      });
    });
  });

  // Library: alignment grid behind examples, off by default
  var grid = document.querySelector('.ul-grid');
  if(grid){
    var g = false; try { g = localStorage.getItem('t-grid') === '1'; } catch(e){}
    grid.setAttribute('role', 'switch'); grid.removeAttribute('aria-pressed');
    grid.innerHTML = '<span>Grid</span><span class="t-switch" aria-hidden="true"></span>';
    function setGrid(){ document.body.classList.toggle('show-grid', g); grid.setAttribute('aria-checked', g ? 'true' : 'false'); }
    grid.addEventListener('click', function(){ g = !g; try { localStorage.setItem('t-grid', g ? '1' : '0'); } catch(e){} setGrid(); });
    setGrid();
  }

  // Tabs (library schema tabs and the schema panel): click, arrows, Home/End
  function wireTabs(root){
    var tabs = [].slice.call(root.querySelectorAll('[role=tab]'));
    function pick(t, focus){
      tabs.forEach(function(x){ var on = x === t; x.setAttribute('aria-selected', on ? 'true' : 'false'); x.tabIndex = on ? 0 : -1;
        var p = document.getElementById(x.getAttribute('aria-controls')); if(p) p.hidden = !on; });
      if(focus) t.focus();
    }
    tabs.forEach(function(t, i){
      t.addEventListener('click', function(){ pick(t); });
      t.addEventListener('keydown', function(e){
        var j = e.key === 'ArrowRight' ? i + 1 : e.key === 'ArrowLeft' ? i - 1 : e.key === 'Home' ? 0 : e.key === 'End' ? tabs.length - 1 : null;
        if(j === null) return; e.preventDefault(); pick(tabs[(j + tabs.length) % tabs.length], true);
      });
    });
  }
  document.querySelectorAll('[data-tabs]').forEach(wireTabs);

  // CMS schema panel: how this page is edited, from data/schema.json
  var notesBtn = document.querySelector('.t-notes-toggle');
  var page = location.pathname.split('/').pop() || 'index.html';
  // Pages only: the library and index show schemas inline
  if(notesBtn && window.self === window.top && !document.querySelector('.ul-body, .tp-grid')){
    var dock = document.createElement('div'); dock.className = 't-dock';
    notesBtn.parentNode.insertBefore(dock, notesBtn);
    var scBtn = document.createElement('button'); scBtn.type = 'button'; scBtn.className = 't-dock-btn t-schema-btn';
    scBtn.setAttribute('aria-haspopup', 'dialog');
    scBtn.innerHTML = '<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect width="18" height="18" x="3" y="3" rx="2"/><path d="M3 9h18"/><path d="M9 21V9"/></svg><span>CMS schema</span>';
    dock.appendChild(scBtn); dock.appendChild(notesBtn);
    var dlg = null;
    function esc(x){ return String(x).replace(/[&<>"]/g, function(c){ return {'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;'}[c]; }); }
    function elName(f){
      var n = f.name, t = f.type;
      if(t === 'component[]' || t === 'link[]' || t === 'pagelink[]') return 'xpowerlist_' + (/s$/.test(n) ? n + 'List' : n + 's');
      if(t === 'categories' || t === 'trays') return n;
      return ({rich: 'xhtml_', image: 'xpowerasset_', asset: 'xpowerasset_', link: 'xpowerlink_', pagelink: 'xpowerlink_', component: 'xpowercomponent_'}[t] || '') + n;
    }
    function groups(S, gs){
      return '<div class="sg-wrap">' + gs.map(function(g){
        var n = g.fields.length;
        return '<section class="sg' + (g.label ? '' : ' sg--flat') + '">' + (g.label ? '<h4 class="sg-h">' + esc(g.label) + ' <span>' + n + ' field' + (n === 1 ? '' : 's') + '</span></h4>' : '') +
          (g.help ? '<p class="sg-help">' + esc(g.help) + '</p>' : '') + '<ul class="sg-fields">' + g.fields.map(function(f){
            var vals = f.values ? '<p class="sf-vals">' + f.values.map(function(v){ return v === f['default'] ? '<b>' + esc(v) + '</b> <span>default</span>' : esc(v); }).join(' · ') + '</p>'
              : (f['default'] ? '<p class="sf-vals"><span>Default</span> <b>' + esc(f['default']) + '</b></p>' : '');
            return '<li class="sf"><div class="sf-top"><b class="sf-label">' + esc(f.label) + '</b>' + (f.required ? '<span class="sf-req">Required</span>' : '') +
              '<span class="sf-type">' + esc(S.types[f.type] || f.type) + '</span></div>' + (f.help ? '<p class="sf-help">' + esc(f.help) + '</p>' : '') + vals +
              '<dl class="sf-meta"><div><dt>Element</dt><dd><code>' + esc(elName(f)) + '</code></dd></div><div><dt>CMS type</dt><dd>' + esc(S.cms_types[f.type]) + '</dd></div></dl></li>';
          }).join('') + '</ul></section>';
      }).join('') + '</div>';
    }
    function tree(S, name, friendly, kind, gs){
      var rows = '';
      gs.forEach(function(g){
        var flat = !g.label;
        if(!flat) rows += '<li class="st-group"><span class="st-ico" aria-hidden="true">▾</span><code>xpowergroupstart_' + esc(g.label.replace(/[^A-Za-z0-9]/g, '')) + '</code><span class="st-lab">' + esc(g.label) + '</span><span class="st-type">Group</span></li>';
        g.fields.forEach(function(f){
          rows += '<li class="st-el' + (flat ? ' st-el--flat' : '') + '"><span class="st-ico" aria-hidden="true">' + (f.type === 'categories' || f.type === 'trays' ? '◇' : '·') + '</span><code>' + esc(elName(f)) + '</code><span class="st-lab">' + esc(f.label) +
            (f.required ? ' <b class="st-req" title="Required">*</b>' : '') + '</span><span class="st-type">' + esc(S.cms_types[f.type]) + '</span></li>';
        });
        if(!flat) rows += '<li class="st-end"><code>xpowergroupend_</code></li>';
      });
      return '<figure class="st"><figcaption><span class="st-kind">' + kind + '</span><b>' + esc(name) + '</b><span>Friendly name “' + esc(friendly) + '” · DSS</span></figcaption><ol>' + rows +
        '</ol><p class="st-note">◇ not a schema element: tags are taxonomy on the item; trays are the Page Builder area. * required.</p></figure>';
    }
    function view(S, name, friendly, kind, gs, lede){ return (lede || '') + tree(S, name, friendly, kind, gs) + '<h4 class="sc-h">Field details</h4>' + groups(S, gs); }
    function build(S){
      var P = S.pages[page]; if(!P) return null;
      var T = S.page_types[P.type], panels = [['Page', view(S, S.schema_names[P.type], T.name, 'Page schema', T.groups, '<p class="sc-lede">' + esc(T.about) + '</p>')]];
      if(P.trays){
        P.trays.forEach(function(t, i){
          var tr = S.trays[t[0]];
          panels.push([(i + 1) + '. ' + tr.name, view(S, S.schema_names[t[0]], tr.friendlyName, 'Component schema', tr.groups.concat(S.shared_tray_groups.map(function(g){ return {label: g.label, help: g.help, fields: g.fields.filter(function(f){ return !((g.heading_skip || []).indexOf(t[0]) >= 0 && /^Section/.test(f.name)); })}; })),
            '<p class="sc-lede">Tray ' + (i + 1) + ' of ' + P.trays.length + ': <b>' + esc(tr.name) + '</b>, ' + esc(t[1]) + ', on a ' + esc(t[2]) + ' background.</p>')]);
        });
      }
      if(T.record) panels.push([T.record.name + ' record', view(S, S.schema_names['record:' + P.type], T.record.name, 'Component schema', T.record.groups, '<p class="sc-lede">Each record is its own item in the CMS; this page lists them.</p>')]);
      var d = document.createElement('dialog'); d.className = 'sc-dialog'; d.setAttribute('aria-labelledby', 'sc-title');
      d.innerHTML = '<div class="sc-head"><div><p class="sc-kind">' + esc(T.name) + '</p><h2 id="sc-title">How this page is edited: ' + esc(P.label) + '</h2>' +
        (P.trays ? '<p class="sc-sub">' + P.trays.length + ' trays, top to bottom. Pick a tab to see the fields an editor fills in.</p>' : '<p class="sc-sub">A fixed layout: the page fields, then the records it lists.</p>') +
        '</div><button type="button" class="sc-close" aria-label="Close">&times;</button></div>' +
        '<div class="sc-tabs" data-tabs><div class="sc-tablist" role="tablist" aria-label="Schema">' +
        panels.map(function(p, i){ return '<button type="button" role="tab" id="sct-' + i + '" aria-controls="scp-' + i + '" aria-selected="' + (i ? 'false' : 'true') + '"' + (i ? ' tabindex="-1"' : '') + '>' + esc(p[0]) + '</button>'; }).join('') +
        '</div>' + panels.map(function(p, i){ return '<div role="tabpanel" id="scp-' + i + '" aria-labelledby="sct-' + i + '" class="sc-panel"' + (i ? ' hidden' : '') + '>' + p[1] + '</div>'; }).join('') + '</div>' +
        '<p class="sc-foot">Field types follow the lastpass_cms manifests, so <code>tools/schema-gen.mjs</code> can generate these as Schema Designer XDR.</p>';
      document.body.appendChild(d); wireTabs(d);
      d.querySelector('.sc-close').addEventListener('click', function(){ d.close(); });
      d.addEventListener('click', function(e){ if(e.target === d) d.close(); });
      d.addEventListener('close', function(){ scBtn.focus(); });
      return d;
    }
    scBtn.addEventListener('click', function(){
      if(dlg){ dlg.showModal(); return; }
      fetch('data/schema.json', {cache: 'no-cache'}).then(function(r){ return r.json(); }).then(function(S){
        dlg = build(S); if(dlg){ dlg.showModal(); var t = dlg.querySelector('[role=tab]'); if(t) t.focus(); }
      });
    });
  }

  // Build notes: shows what each block is and where its content comes from
  var t = document.querySelector('.t-notes-toggle');
  if(t){
    var on = false; try { on = localStorage.getItem('t-notes') === '1'; } catch(e){}
    t.setAttribute('role', 'switch'); t.removeAttribute('aria-pressed');
    t.innerHTML = '<span>Build notes</span><span class="t-switch" aria-hidden="true"></span>';
    function apply(){ document.body.classList.toggle('show-notes', on); t.setAttribute('aria-checked', on ? 'true' : 'false'); }
    t.addEventListener('click', function(){ on = !on; try { localStorage.setItem('t-notes', on ? '1' : '0'); } catch(e){} apply(); });
    apply();
  }
})();
