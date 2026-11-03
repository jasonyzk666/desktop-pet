/* 液态玻璃：铺背景光斑 + 给 UI 元素上玻璃质感 + 指针跟随高光 */
(function(){
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. 背景漂浮光斑 ---------- */
  var stage = document.createElement('div');
  stage.className = 'g-stage';
  stage.setAttribute('aria-hidden','true');
  stage.innerHTML = '<div class="g-blob g-b1"></div><div class="g-blob g-b2"></div><div class="g-blob g-b3"></div>';
  document.body.insertBefore(stage, document.body.firstChild);

  /* ---------- 2. 给 UI 元素加玻璃 ---------- */
  var SEL = [
    '.card','.pill','.status','.phone','.note','.dl-item','.feat-item','.shot',
    '.btn','.tag','.link-btn','.contact-item','.changelog-item','.tools-title',
    '.stack span','.contact a','.contact button','.row','.sechead','.back','.topbar',
    '.links a','.kicker','.hero'
  ].join(',');

  var nodes = [].slice.call(document.querySelectorAll(SEL));
  nodes.forEach(function(el){
    if(el.closest('.g-stage')) return;
    var cs = getComputedStyle(el);
    if(cs.display === 'inline') return;                    // 行内元素不加，避免变成方块
    if(cs.position === 'fixed') return;                    // 固定层（返回按钮/浮层）不加
    el.classList.add('gx');
    if(cs.position === 'static') el.classList.add('gx-pos');   // 安全兜底，不破坏 absolute 布局
    if(cs.borderTopLeftRadius === '0px') el.classList.add('gx-r');
  });

  /* ---------- 3. 指针跟随高光 ---------- */
  if(reduce) return;
  var cur = null, pending = false, px = 0, py = 0;
  document.addEventListener('pointermove', function(e){
    var hit = e.target && e.target.closest ? e.target.closest('.gx') : null;
    cur = hit; px = e.clientX; py = e.clientY;
    if(pending) return;
    pending = true;
    requestAnimationFrame(function(){
      pending = false;
      if(!cur) return;
      var r = cur.getBoundingClientRect();
      cur.style.setProperty('--gx', ((px - r.left) / r.width * 100).toFixed(1) + '%');
      cur.style.setProperty('--gy', ((py - r.top) / r.height * 100).toFixed(1) + '%');
    });
  }, {passive:true});
})();
