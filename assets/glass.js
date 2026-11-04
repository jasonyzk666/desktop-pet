/* 液态玻璃（Apple HIG · 仅按钮）
   - 材质只给功能层：卡片 / 标题 / 手机壳等内容层不再叠玻璃
   - 指针跟随高光：仅鼠标设备参与（手指滑动时 pointermove 每帧触发，
     白跑 closest() + getBoundingClientRect 只会加重滚动负担）
   - 尊重系统「减少动效」设置 */
(function(){
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- 1. 给按钮加玻璃 ---------- */
  var SEL = [
    '.btn', '.link-btn', '.contact a', '.contact button'
  ].join(',');

  var nodes = [].slice.call(document.querySelectorAll(SEL));
  nodes.forEach(function(el){
    if(el.closest('.g-stage')) return;
    var cs = getComputedStyle(el);
    if(cs.display === 'inline') return;                    // 行内元素不加，避免变成方块
    if(cs.position === 'fixed') return;                    // 固定层不加
    el.classList.add('gx');
    if(cs.position === 'static') el.classList.add('gx-pos');   // ::before 定位兜底
    if(cs.borderTopLeftRadius === '0px') el.classList.add('gx-r');
  });

  /* ---------- 2. 指针跟随高光（仅鼠标） ---------- */
  if(reduce) return;
  var cur = null, pending = false, px = 0, py = 0;
  document.addEventListener('pointermove', function(e){
    if(e.pointerType && e.pointerType !== 'mouse') return;
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
