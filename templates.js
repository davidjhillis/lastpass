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

  // Design-system shortcut beside the build-notes button
  var nt = document.querySelector('.t-notes-toggle');
  if(nt && !document.querySelector('.t-ds-link')){
    var here = location.pathname.split('/').pop();
    var ds = document.createElement('nav'); ds.className = 't-ds-link'; ds.setAttribute('aria-label', 'Design system');
    ds.innerHTML = '<a href="templates.html"' + (here === 'templates.html' ? ' aria-current="page"' : '') + '>All templates</a><a href="components.html"' + (here === 'components.html' ? ' aria-current="page"' : '') + '>Components</a>';
    nt.parentNode.insertBefore(ds, nt);
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
