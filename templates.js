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
    ['templates.html', 'All templates'], ['components.html', 'Essentials'], null,
    ['hub-business.html', 'Mini hub'], ['topic-saas-monitoring.html', 'Topic: product'], ['topic-billing.html', 'Topic: utility'],
    ['faq.html', 'FAQ'], ['contact-us.html', 'Contact Us'], ['lifecycle.html', 'Lifecycle'], null,
    ['release-notes.html', 'Release notes'], ['downloads.html', 'Downloads'], ['known-issues.html', 'Known issues']
  ];
  if(document.querySelector('.t-notes-toggle') && !document.querySelector('.rv-nav')){
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
    function setGrid(){ document.body.classList.toggle('show-grid', g); grid.setAttribute('aria-pressed', g ? 'true' : 'false'); grid.textContent = g ? 'Hide grid' : 'Show grid'; }
    grid.addEventListener('click', function(){ g = !g; try { localStorage.setItem('t-grid', g ? '1' : '0'); } catch(e){} setGrid(); });
    setGrid();
  }

  // Build notes: shows what each block is and where its content comes from
  var t = document.querySelector('.t-notes-toggle');
  if(t){
    var on = false; try { on = localStorage.getItem('t-notes') === '1'; } catch(e){}
    function apply(){ document.body.classList.toggle('show-notes', on); t.setAttribute('aria-pressed', on ? 'true' : 'false'); t.querySelector('span').textContent = on ? 'Hide build notes' : 'Show build notes'; }
    t.addEventListener('click', function(){ on = !on; try { localStorage.setItem('t-notes', on ? '1' : '0'); } catch(e){} apply(); });
    apply();
  }
})();
