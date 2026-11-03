/* 全站交互动画：点击涟漪 + 滚动依次浮现 */
(function(){
  window.__motionReady = true;   // 告知内联兜底：本脚本已就绪，不必恢复可见
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. 点击涟漪（跟随点击位置，颜色取自被点元素） ---------- */
  if(!reduce){
    document.addEventListener('pointerdown', function(e){
      var t = e.target;
      if(!t || !t.closest) return;
      var hit = t.closest('a,button,[role="button"],label[onclick]');
      if(!hit) return;
      var d = document.createElement('span');
      d.className = 'ripple-dot';
      d.style.left = e.clientX + 'px';
      d.style.top  = e.clientY + 'px';
      d.style.color = window.getComputedStyle(hit).color;
      document.body.appendChild(d);
      setTimeout(function(){ if(d.parentNode) d.parentNode.removeChild(d); }, 520);
    }, {passive:true});
  }

  /* ---------- 2. 平滑锚点滚动（首页有自己的翻页动画，跳过） ---------- */
  if(!reduce && !document.querySelector('.hero')){
    document.documentElement.style.scrollBehavior = 'smooth';
  }

  /* ---------- 3. 滚动浮现 ---------- */
  var items = [].slice.call(document.querySelectorAll('[data-reveal]'));
  if(!items.length) return;

  function show(el, delay){
    if(el.classList.contains('m-in')) return;
    setTimeout(function(){ el.classList.add('m-in'); }, delay || 0);
  }

  if(reduce || !('IntersectionObserver' in window)){
    items.forEach(function(el){ el.classList.add('m-in'); });
    return;
  }

  // 同一父元素下的兄弟按顺序错开
  var seq = {};
  items.forEach(function(el){
    var p = el.parentElement;
    var k = p ? (p.tagName + '|' + (p.className || '')) : 'root';
    var i = seq[k] = (seq[k] || 0);
    var custom = parseInt(el.getAttribute('data-delay'), 10);
    el._delay = isNaN(custom) ? Math.min(i * 70, 350) : custom;
    seq[k] = i + 1;
  });

  var io = new IntersectionObserver(function(es){
    es.forEach(function(en){
      if(!en.isIntersecting) return;
      show(en.target, en.target._delay || 0);
      io.unobserve(en.target);
    });
  }, {threshold:.12, rootMargin:'0px 0px -6% 0px'});
  items.forEach(function(el){ io.observe(el); });

  // 兜底：滚动时再扫一遍，防止任何情况下元素一直不显示
  function sweep(){
    items.forEach(function(el){
      if(el.classList.contains('m-in')) return;
      var r = el.getBoundingClientRect();
      if(r.top < window.innerHeight * 0.94 && r.bottom > 0) show(el, el._delay || 0);
    });
  }
  window.addEventListener('scroll', sweep, {passive:true});
  window.addEventListener('resize', sweep);
  [300, 800, 1600, 3000].forEach(function(t){ setTimeout(sweep, t); });
})();
