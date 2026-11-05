/* ===========================================================
   奶龙入侵 · 全站主题脚本
   - 左上角注入开关按钮，localStorage('jz-nailong') 持久化
   - 开启时：构建固定背景舞台，几百只奶龙静态/动态铺满视口
     （数量按视口面积分档；减少动效时数量减半且全静态）
   - 主题开启期间锁定深浅色开关（.ttoggle disabled）
   - 首页卡片 #nlCard 联动（点击卡片也能开关）
   =========================================================== */
(function(){
  var KEY = 'jz-nailong';
  var BASE = '/assets/nailong/';
  /* 29 张官方贴纸（3d-07 弃用未收录） */
  var IMG = [
    '2d-01.png','2d-02.png','2d-03.png','2d-04.png','2d-05.png','2d-06.png','2d-07.png',
    '2d-08.png','2d-09.png','2d-10.png','2d-11.png','2d-12.png','2d-13.png','2d-14.png',
    '3d-01.png','3d-02.png','3d-03.png','3d-04.png','3d-05.png','3d-06.png','3d-08.png',
    '3d-09.png','3d-10.png','3d-11.png','3d-12.png','3d-13.png','3d-14.png','3d-15.png','3d-16.png'
  ];

  var root = document.documentElement;

  /* 存储兜底：localStorage 不可用时退 sessionStorage / 内存 */
  var mem = null;
  var store = (function(){
    try{ localStorage.setItem('__n','1'); localStorage.removeItem('__n'); return localStorage; }catch(e){}
    try{ sessionStorage.setItem('__n','1'); sessionStorage.removeItem('__n'); return sessionStorage; }catch(e){}
    return null;
  })();
  function get(){ if(store){ try{ return store.getItem(KEY); }catch(e){} } return mem; }
  function set(v){ mem = v; if(store){ try{ store.setItem(KEY, v); }catch(e){} } }

  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;
  var coarse = window.matchMedia && window.matchMedia('(pointer: coarse)').matches;

  /* 确定性随机：每次刷新奶龙阵型一致，不闪烁换位 */
  function mulberry32(a){
    return function(){
      a |= 0; a = (a + 0x6D2B79F5) | 0;
      var t = Math.imul(a ^ (a >>> 15), 1 | a);
      t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t;
      return ((t ^ (t >>> 14)) >>> 0) / 4294967296;
    };
  }

  var stage = null;
  function buildStage(){
    if(stage){ if(stage.parentNode) stage.parentNode.removeChild(stage); stage = null; }
    if(!on) return;
    var w = window.innerWidth, h = window.innerHeight;
    /* 数量按视口面积分档：手机约 70，笔记本 160+，桌面 320 封顶 */
    var n = Math.round(Math.min(320, Math.max(70, w * h / 6500)));
    if(reduce) n = Math.round(n / 2);

    stage = document.createElement('div');
    stage.id = 'nl-stage';
    stage.setAttribute('aria-hidden', 'true');

    var R = mulberry32(20261105);
    var frag = document.createDocumentFragment();
    for(var i = 0; i < n; i++){
      var d = document.createElement('div');
      d.className = 'nl-item';
      var f = IMG[Math.floor(R() * IMG.length)];
      /* 尺寸偏小分布：大部分是远处的迷你奶龙，少数近景大只 */
      var s = Math.round(20 + R() * R() * 86);
      var x = R() * 100, y = R() * 100;
      /* 中心内容带（正文中往往是无背景的裸文字）：奶龙减淡缩小，保证可读性 */
      var central = x > 22 && x < 78 && y > 16 && y < 84;
      if(central){ s = Math.round(s * 0.72); }
      d.style.width = d.style.height = s + 'px';
      d.style.left = x.toFixed(2) + '%';
      d.style.top  = y.toFixed(2) + '%';
      var op = 0.25 + R() * 0.45;
      if(central) op *= 0.55;
      d.style.opacity = op.toFixed(2);
      d.style.backgroundImage = 'url(' + BASE + f + ')';
      var rot = (R() * 40 - 20).toFixed(1);
      if(!reduce && R() < 0.45){                 // 45% 动态：四种循环动作
        d.classList.add('nl-a' + (1 + Math.floor(R() * 4)));
        d.style.setProperty('--r', rot + 'deg');
        d.style.setProperty('--d', (3.5 + R() * 5).toFixed(2) + 's');
        d.style.animationDelay = (-R() * 8).toFixed(2) + 's';   // 负延迟：开局就各就各位
      }else{                                     // 其余静态：随机歪头
        d.style.transform = 'rotate(' + rot + 'deg)';
      }
      frag.appendChild(d);
    }

    /* 3 只大只守门员贴边站（右下 / 左下 / 右上），更醒目 */
    var corners = [
      { l: '84%', t: '82%' }, { l: '4%',  t: '76%' }, { l: '88%', t: '6%'  }
    ];
    for(var k = 0; k < corners.length; k++){
      var b = document.createElement('div');
      b.className = 'nl-item nl-big' + (reduce ? '' : ' nl-a1');
      var bf = IMG[Math.floor(R() * IMG.length)];
      var bs = Math.round(96 + R() * 64);
      b.style.width = b.style.height = bs + 'px';
      b.style.left = corners[k].l; b.style.top = corners[k].t;
      b.style.opacity = '.85';
      b.style.backgroundImage = 'url(' + BASE + bf + ')';
      b.style.setProperty('--r', (R() * 16 - 8).toFixed(1) + 'deg');
      b.style.setProperty('--d', (4.5 + R() * 3).toFixed(2) + 's');
      if(reduce) b.style.transform = 'rotate(0deg)';
      frag.appendChild(b);
    }

    stage.appendChild(frag);
    document.body.insertBefore(stage, document.body.firstChild);
  }

  /* ---------- 深浅色开关锁定 ---------- */
  function updateToggles(){
    var ts = document.querySelectorAll('.ttoggle');
    for(var i = 0; i < ts.length; i++){
      var b = ts[i];
      b.disabled = on;
      if(on){
        b.setAttribute('title', '奶龙入侵主题下不能切换深浅色');
        b.setAttribute('aria-label', '奶龙入侵主题下不能切换深浅色');
      }else{
        b.removeAttribute('title');
        b.setAttribute('aria-label', '切换深色 / 浅色模式');
      }
    }
  }

  /* ---------- toast ---------- */
  var toastEl = null, toastTimer = null;
  function toast(msg){
    if(!toastEl){
      toastEl = document.createElement('div');
      toastEl.id = 'nl-toast';
      toastEl.setAttribute('role', 'status');
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    toastEl.classList.add('show');
    if(toastTimer) clearTimeout(toastTimer);
    toastTimer = setTimeout(function(){ toastEl.classList.remove('show'); }, 2600);
  }

  /* ---------- 左上角开关按钮 ---------- */
  var btn = null;
  function makeBtn(){
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'nl-toggle';
    b.setAttribute('aria-label', '奶龙入侵主题开关');
    var img = document.createElement('img');
    img.src = BASE + '2d-07.png';
    img.alt = '';
    b.appendChild(img);
    b.addEventListener('click', function(){ toggle(); });
    return b;
  }
  /* 避让左上角已有的 fixed 元素（pet 页「返回主站」等）：被挡就往下挪 */
  function placeBtn(){
    btn.style.top = '';                           // 先回到 CSS 默认位置
    var br = btn.getBoundingClientRect();
    var bump = br.bottom, hit = false;
    var els = document.body.querySelectorAll('a,button,[role="button"]');
    for(var i = 0; i < els.length; i++){
      var el = els[i];
      if(el === btn || btn.contains(el)) continue;
      if(getComputedStyle(el).position !== 'fixed') continue;
      var r = el.getBoundingClientRect();
      if(r.width < 8 || r.height < 8) continue;
      if(r.left < br.right && r.right > br.left && r.top < br.bottom && r.bottom > br.top){
        hit = true;
        if(r.bottom > bump) bump = r.bottom;
      }
    }
    if(hit) btn.style.top = Math.round(bump + 10) + 'px';
  }

  /* ---------- 首页卡片联动 ---------- */
  var card = null;
  function bindCard(){
    card = document.getElementById('nlCard');
    if(!card) return;
    card.addEventListener('click', function(){
      toggle();
    });
    card.addEventListener('keydown', function(e){
      if(e.key === ' ' || e.key === 'Enter'){ e.preventDefault(); toggle(); }
    });
  }

  /* ---------- 应用 ---------- */
  var on = get() === '1';
  function apply(v, quiet){
    on = v;
    set(v ? '1' : '0');
    if(v) root.setAttribute('data-nailong', 'on');
    else root.removeAttribute('data-nailong');
    buildStage();
    updateToggles();
    syncUI();
    if(!quiet) toast(v
      ? '🦖 奶龙入侵主题已开启，左上角随时可关闭'
      : '奶龙已撤退，欢迎再来');
  }
  function toggle(){ apply(!on); }
  function syncUI(){
    if(btn) btn.setAttribute('aria-pressed', on ? 'true' : 'false');
    if(card) card.setAttribute('aria-pressed', on ? 'true' : 'false');
  }

  /* ---------- 启动 ---------- */
  btn = makeBtn();
  document.body.appendChild(btn);
  bindCard();
  /* 首帧定位后再避让一次（等布局/字体稳定） */
  placeBtn();
  setTimeout(placeBtn, 600);
  apply(on, true);

  /* 窗口尺寸变化：重建舞台（数量按新视口分档），轻防抖 */
  var lastW = window.innerWidth, rzTimer = null;
  window.addEventListener('resize', function(){
    if(!on) return;
    if(Math.abs(window.innerWidth - lastW) < 80) return;
    lastW = window.innerWidth;
    if(rzTimer) clearTimeout(rzTimer);
    rzTimer = setTimeout(function(){ buildStage(); placeBtn(); }, 350);
  });
})();
