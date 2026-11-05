/* ===========================================================
   全站统一主题：时间显示 + 深浅模式开关
   - 主题读取优先级：localStorage 手动选择 > 系统偏好
   - 切换时同步 <html data-theme> 与 data-glass（供液态玻璃取深色配方）
   - 首页沿用原有三胶囊，只在其中追加开关；其余页面注入完整组件
   =========================================================== */
(function(){
  var KEY = 'jz-theme';
  var root = document.documentElement;

  /* 存储兜底：localStorage 不可用时（隐私模式 / file://）退到 sessionStorage，
     再不行就用内存变量，保证本次浏览内切换一定生效 */
  var mem = null;
  var store = (function(){
    try{ localStorage.setItem('__t','1'); localStorage.removeItem('__t'); return localStorage; }catch(e){}
    try{ sessionStorage.setItem('__t','1'); sessionStorage.removeItem('__t'); return sessionStorage; }catch(e){}
    return null;
  })();
  function get(){
    if(store){ try{ return store.getItem(KEY); }catch(e){} }
    return mem;
  }
  function set(v){
    mem = v;
    if(store){ try{ store.setItem(KEY, v); }catch(e){} }
  }

  function sysDark(){
    return !!(window.matchMedia && window.matchMedia('(prefers-color-scheme: dark)').matches);
  }
  function read(){
    var v = get();
    if(v === 'dark' || v === 'light') return v;
    return sysDark() ? 'dark' : 'light';
  }
  function apply(t){
    root.setAttribute('data-theme', t);
    if(t === 'dark') root.setAttribute('data-glass','dark');
    else root.removeAttribute('data-glass');
    var m = document.querySelector('meta[name="theme-color"]');
    if(m) m.setAttribute('content', t === 'dark' ? '#0d0e12' : '#fbfbf9');
  }
  function current(){
    return root.getAttribute('data-theme') === 'dark' ? 'dark' : 'light';
  }

  apply(read());

  /* ---------- 开关按钮 ---------- */
  function makeToggle(){
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'ttoggle';
    b.title = '切换深色 / 浅色模式';
    b.setAttribute('aria-label','切换深色 / 浅色模式');
    b.innerHTML =
      '<svg class="i-sun" viewBox="0 0 24 24" aria-hidden="true">' +
      '<circle cx="12" cy="12" r="4.2"/>' +
      '<path d="M12 2v2.6M12 19.4V22M2 12h2.6M19.4 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M19.1 4.9l-1.8 1.8M6.7 17.3l-1.8 1.8"/>' +
      '</svg>' +
      '<svg class="i-moon" viewBox="0 0 24 24" aria-hidden="true">' +
      '<path d="M20.5 14.3A8.5 8.5 0 0 1 9.7 3.5a8.5 8.5 0 1 0 10.8 10.8z"/>' +
      '</svg>';
    /* 切换动作挂成函数，由 window 捕获阶段统一派发：
       这样即使页面上有别的脚本（如首页拖拽翻页）在 click 上做拦截，也拦不到主题开关 */
    b._flip = function(){
      var next = current() === 'dark' ? 'light' : 'dark';
      set(next);
      root.classList.add('theme-ready');   // 首屏不加，只有用户主动切换后才启用过渡
      apply(next);
      sync();
      return next;
    };
    return b;
  }

  /* ---------- 时间 ---------- */
  var WK = ['周日','周一','周二','周三','周四','周五','周六'];
  var elTime = null, elWeek = null, elDate = null, toggle = null;

  function pad(n){ return n < 10 ? '0' + n : '' + n; }
  function sync(){
    var d = new Date();
    if(elTime) elTime.textContent = pad(d.getHours()) + ':' + pad(d.getMinutes()) + ':' + pad(d.getSeconds());
    if(elWeek) elWeek.textContent = WK[d.getDay()];
    if(elDate) elDate.textContent = pad(d.getMonth() + 1) + '/' + pad(d.getDate());
    if(toggle) toggle.setAttribute('aria-pressed', current() === 'dark' ? 'true' : 'false');
  }

  /* ---------- 组装时间 + 开关组件 ---------- */
  function buildBar(inline){
    var bar = document.createElement('div');
    bar.className = 'tbar' + (inline ? ' tbar-inline' : '');
    bar.setAttribute('role','group');
    bar.setAttribute('aria-label','时间与主题');

    elTime = document.createElement('span');
    elTime.className = 'tpill t-sec';
    elWeek = document.createElement('span');
    elWeek.className = 'tpill t-week';
    elDate = document.createElement('span');
    elDate.className = 'tpill t-date';

    bar.appendChild(elTime);
    bar.appendChild(elWeek);
    bar.appendChild(elDate);
    toggle = makeToggle();
    bar.appendChild(toggle);
    return bar;
  }

  /* 首页：沿用原有三胶囊，只在末尾追加开关。
     必须用首页专属的 #p-time 判定 —— 操作录制页也有 .pills（技术标签），不能只看 .pills */
  var homeTime = document.getElementById('p-time');
  var homePills = homeTime ? homeTime.parentElement : null;
  var slot = document.querySelector('[data-theme-slot]');   // 页面自己的顶栏挂载点
  if(homePills){
    toggle = makeToggle();
    homePills.appendChild(toggle);
    /* 首页有自己的时钟脚本在刷新 #p-time，这里不接管，避免两套脚本写同一元素 */
  }else if(slot){
    /* 嵌入页面自己的顶栏（操作录制 / 搜索引擎原理页），不悬浮、不遮挡 */
    slot.appendChild(buildBar(true));
    document.body.classList.add('has-tbar');
  }else{
    /* 其余页面（宠物两页 / 404）：右上角无内容，安全悬浮 */
    document.body.appendChild(buildBar(false));
    document.body.classList.add('has-tbar');
  }

  /* window 捕获阶段派发点击：注册时机早于页面里任何动态添加的 click 拦截器，
     所以主题开关不会被“拖拽后吞掉下一次 click”之类的逻辑影响。
     另加 260ms 节流：手抖/连点时只会切一次，不会两次互相抵消看起来像没反应 */
  var last = 0;
  window.addEventListener('click', function(e){
    var t = e.target;
    if(!t || !t.closest) return;
    var b = t.closest('.ttoggle');
    /* disabled：奶龙入侵主题下深浅色锁定，按钮不可用 */
    if(!b || b.disabled || typeof b._flip !== 'function') return;
    var now = Date.now();
    if(now - last < 260) { e.stopPropagation(); return; }   // 连点：吃掉，避免来回抵消
    last = now;
    b._flip();
  }, true);

  /* 手滑补救：按下开关后手指/鼠标挪开一点，抬手时已不在按钮上，
     浏览器就不会派发 click。这里在 pointerup 时补一次（位移过大视为主动拖走，不切换） */
  var downOn = null;
  document.addEventListener('pointerdown', function(e){
    var t = (e.target && e.target.closest) ? e.target.closest('.ttoggle') : null;
    downOn = t ? { b:t, x:e.clientX, y:e.clientY } : null;
  }, true);
  document.addEventListener('pointerup', function(e){
    if(!downOn) return;
    var d = downOn; downOn = null;
    if(d.b.disabled) return;                          // 深浅色锁定中：不响应
    var inside = (e.target && e.target.closest) ? (e.target.closest('.ttoggle') === d.b) : false;
    if(inside) return;                                   // 浏览器会派发 click，交给上面的处理器
    var dx = e.clientX - d.x, dy = e.clientY - d.y;
    if(Math.sqrt(dx*dx + dy*dy) > 100) return;           // 明显拖走，不算点按钮
    var now = Date.now();
    if(now - last < 260) return;
    last = now;
    d.b._flip();
  }, true);

  sync();
  setInterval(sync, 1000);

  /* 未手动选择过时，跟随系统变化 */
  if(window.matchMedia){
    var mq = window.matchMedia('(prefers-color-scheme: dark)');
    var onChange = function(){
      var manual = get();
      if(manual === 'dark' || manual === 'light') return;   // 尊重手动选择
      apply(mq.matches ? 'dark' : 'light');
      sync();
    };
    if(mq.addEventListener) mq.addEventListener('change', onChange);
    else if(mq.addListener) mq.addListener(onChange);
  }

  window.__themeReady = true;
})();
