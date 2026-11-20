/* assets/about.js — 顶栏「账号 / 关于」按钮 + 关于弹窗 + 一次性开发者绑定彩蛋
 *
 * 彩蛋流程（口令只存在于服务器 dropbox.py，本文件及任何网页都看不到）：
 *   弹窗打开时 1.6s 内连按 5 次 J → 出现口令框 → 输入后打开服务器的
 *   /#dev=<口令>（fragment 不经过网络）→ 服务器校验口令并签发「一次性兑换券」
 *   → 在该页登录/注册的那个账号成为唯一开发者账号 → 全局永久锁，只此一次。
 * 未登录 = 游客模式：可浏览，不能传文件；登录后才能上传。
 */
(function(){
  'use strict';
  /* ============ 配置：部署服务器后把这里改成 http://<公网IP>:8787 ============ */
  var FILE_DROP = 'http://REPLACE-WITH-YOUR-SERVER-IP:8787';
  var READY = FILE_DROP.indexOf('REPLACE-WITH') === -1;
  /* ======================================================================== */

  if(document.querySelector('.atbtn')) return;   // 防重复注入
  var reduce = false;
  try{ reduce = matchMedia('(prefers-reduced-motion: reduce)').matches; }catch(e){}

  /* ---------- 样式（自包含，不新增 css 文件） ---------- */
  var css = [
    '.atbtn{position:relative;display:inline-flex;align-items:center;justify-content:center;',
    'width:34px;height:34px;flex:none;border-radius:50%;border:1px solid var(--line,#dce1ea);',
    'background:color-mix(in srgb,var(--surface,#fff) 82%,transparent);color:var(--tx2,#5b6577);',
    'cursor:pointer;padding:0;',
    'transition:color .18s ease,border-color .18s ease,transform .16s cubic-bezier(.2,.8,.3,1)}',
    '.atbtn:hover{border-color:var(--accent,#2f6bff);color:var(--accent,#2f6bff);transform:translateY(-1px)}',
    '.atbtn:active{transform:scale(.93)}',
    '.atbtn:focus-visible{outline:2px solid var(--accent,#2f6bff);outline-offset:3px}',
    /* 命中区只向上下补足 44px，不横向扩张，避免顶栏按钮密集时互相误触 */
    '.atbtn::after{content:"";position:absolute;left:0;top:50%;width:100%;height:44px;',
    'transform:translateY(-50%);border-radius:12px}',
    '.atbtn svg{width:16px;height:16px;stroke:currentColor;fill:none;stroke-width:1.8;',
    'stroke-linecap:round;stroke-linejoin:round}',
    '@media(max-width:560px){.atbtn{width:30px;height:30px}.atbtn svg{width:15px;height:15px}}',
    /* 遮罩 / 卡片 */
    '.amask{position:fixed;inset:0;z-index:9000;background:rgba(10,14,22,.44);',
    'display:flex;align-items:center;justify-content:center;padding:18px;',
    'opacity:0;visibility:hidden;transition:opacity .22s ease,visibility .22s ease}',
    '.amask.open{opacity:1;visibility:visible}',
    '.acard{width:min(430px,94vw);max-height:86vh;overflow:auto;background:var(--surface,#fff);',
    'color:var(--tx,#1a2233);border:1px solid var(--line,#dce1ea);border-radius:20px;padding:26px 26px 20px;',
    'box-shadow:0 18px 50px rgba(6,12,28,.28);transform:translateY(14px) scale(.97);',
    'transition:transform .22s cubic-bezier(.2,.8,.3,1)}',
    '.amask.open .acard{transform:none}',
    '.acard h2{font-size:19px;margin-bottom:4px}',
    '.acard h2 b{color:var(--accent,#2f6bff)}',
    '.acard .abio{color:var(--tx2,#5b6577);font-size:14px;line-height:1.7;margin:8px 0 16px}',
    '.acard .arow{display:flex;align-items:center;gap:9px;font-size:14px;margin:7px 0;color:var(--tx,#1a2233)}',
    '.acard .arow svg{width:15px;height:15px;stroke:var(--tx2,#5b6577);fill:none;stroke-width:1.8;flex:none;',
    'stroke-linecap:round;stroke-linejoin:round}',
    '.acard .arow a{color:inherit;text-decoration:none;border-bottom:1px solid transparent}',
    '.acard .arow a:hover{color:var(--accent,#2f6bff)}',
    '.acard .afile{margin:16px 0 6px;display:block;width:100%}',
    '.acard .afoot{color:var(--tx2,#5b6577);font-size:12px;text-align:center;margin-top:16px;line-height:1.6}',
    /* 口令视图 */
    '.adev{display:none;border-top:1px dashed var(--line,#dce1ea);margin-top:16px;padding-top:16px}',
    '.adev.on{display:block}',
    '.adev .dtip{font-size:12.5px;color:var(--tx2,#5b6577);margin-bottom:9px;line-height:1.6}',
    '.adev .drow{display:flex;gap:9px;flex-wrap:wrap}',
    '.adev input{flex:1;min-width:150px;border:1px solid var(--line,#dce1ea);border-radius:12px;',
    'padding:10px 13px;font-size:14px;background:var(--surface,#fff);color:var(--tx,#1a2233);outline:none}',
    '.adev input:focus{border-color:var(--accent,#2f6bff)}',
    '.abtnx,.dgo{border:0;border-radius:12px;padding:10px 20px;font-size:14px;cursor:pointer;color:#fff;',
    'background:linear-gradient(rgba(255,255,255,.18),rgba(255,255,255,0)),var(--accent,#2f6bff);',
    'box-shadow:inset 0 1px 0 rgba(255,255,255,.25),0 1px 3px rgba(0,0,0,.12);',
    'transition:transform .16s cubic-bezier(.2,.8,.3,1)}',
    '.abtnx:active,.dgo:active{transform:scale(.97)}',
    '.abtnx:focus-visible,.dgo:focus-visible{outline:2px solid var(--accent,#2f6bff);outline-offset:3px}',
    /* 轻提示 */
    '.atoast{position:fixed;left:50%;bottom:28px;z-index:9600;transform:translate(-50%,12px);',
    'background:#1f2937;color:#fff;font-size:13px;line-height:1.5;padding:11px 18px;border-radius:12px;',
    'box-shadow:0 8px 26px rgba(0,0,0,.28);opacity:0;pointer-events:none;max-width:88vw;text-align:center;',
    'transition:opacity .22s ease,transform .22s ease}',
    '.atoast.on{opacity:1;transform:translate(-50%,0)}',
    /* 首页 .pills 横排三胶囊 + 开关，再加两个按钮后窄屏会挤爆：
       ≤640px 收掉星期/日期，只留时间与三个圆形按钮 */
    '@media(max-width:640px){.pills #p-week,.pills #p-date{display:none}}',
    '@media(prefers-reduced-motion:reduce){.amask,.acard,.atbtn,.abtnx,.dgo,.atoast{transition:none!important}}'
  ].join('');
  var style = document.createElement('style');
  style.textContent = css;
  document.head.appendChild(style);

  /* ---------- 轻提示 ---------- */
  var toastEl = null, toastTimer = null;
  function toast(msg){
    if(!toastEl){
      toastEl = document.createElement('div');
      toastEl.className = 'atoast';
      toastEl.setAttribute('role', 'status');
      document.body.appendChild(toastEl);
    }
    toastEl.textContent = msg;
    requestAnimationFrame(function(){ toastEl.classList.add('on'); });
    clearTimeout(toastTimer);
    toastTimer = setTimeout(function(){ toastEl.classList.remove('on'); }, 2800);
  }
  function openStation(hash){
    if(!READY){ toast('文件服务尚未配置好，稍后再来吧'); return; }
    window.open(FILE_DROP + '/' + (hash || ''), '_blank', 'noopener');
  }

  /* ---------- 按钮：账号放时间胶囊旁，关于放主题开关旁 ---------- */
  function makeBtn(kind, label, svg){
    var b = document.createElement('button');
    b.type = 'button';
    b.className = 'atbtn';
    b.setAttribute('data-kind', kind);
    b.title = label;
    b.setAttribute('aria-label', label);
    if(kind === 'about') b.setAttribute('aria-haspopup', 'dialog');
    b.innerHTML = '<svg viewBox="0 0 24 24" aria-hidden="true">' + svg + '</svg>';
    if(kind === 'about') b.addEventListener('click', openModal);
    else b.addEventListener('click', function(){ openStation('#account'); });
    return b;
  }
  var ICON_ABOUT = '<circle cx="12" cy="12" r="9"/>' +
    '<path d="M12 11v5.2"/><circle cx="12" cy="7.6" r="1.1" fill="currentColor" stroke="none"/>';
  var ICON_ACCOUNT = '<circle cx="12" cy="8" r="3.4"/>' +
    '<path d="M4.8 20c.6-3.9 3.4-6 7.2-6s6.6 2.1 7.2 6"/>';

  /* 锚点用 .ttoggle 而不是 .tbar：theme.js 在首页把开关直接塞进 .pills
     （根本没有 .tbar），其余页面才建 .tbar（内嵌或悬浮）。以开关的父容器
     为准，三种顶栏结构全站通用。 */
  var tries = 0;
  (function place(){
    var t = document.querySelector('.ttoggle');
    if(t && t.parentNode && !document.querySelector('.atbtn')){
      var host = t.parentNode;               // 首页 = .pills；其余 = .tbar
      var acc = makeBtn('account', '账号 · 传文件（游客可直接看，登录后可传）', ICON_ACCOUNT);
      var abt = makeBtn('about', '关于本站', ICON_ABOUT);
      host.insertBefore(acc, t);              // 账号：时间组右侧、主题开关左侧
      host.insertBefore(abt, t.nextSibling);  // 关于：主题开关右侧
    }else if(++tries < 120 && !document.querySelector('.atbtn')){
      setTimeout(place, 50);   // theme.js 尚未建好开关，最长等约 6s
    }
  })();

  /* ---------- 弹窗 ---------- */
  var mask, card, devBox, devInput;
  function openModal(){
    if(mask){ show(); return; }
    mask = document.createElement('div');
    mask.className = 'amask';
    mask.setAttribute('role','dialog');
    mask.setAttribute('aria-modal','true');
    mask.setAttribute('aria-label','关于本站');
    mask.innerHTML =
      '<div class="acard">' +
        '<h2>关于 <b>jasonyzk.top</b></h2>' +
        '<p class="abio">Jason 的个人作品站：桌面宠物、安卓工具、网页小游戏，还有全站奶龙入侵主题。全部页面手写，无框架无广告。</p>' +
        '<div class="arow"><svg viewBox="0 0 24 24"><path d="M21 15a2 2 0 0 1-2 2H7l-4 4V5a2 2 0 0 1 2-2h14a2 2 0 0 1 2 2z"/></svg>QQ：3821888622</div>' +
        '<div class="arow"><svg viewBox="0 0 24 24"><path d="M4 6h16v12H4z"/><path d="M4 7l8 6 8-6"/></svg><a href="mailto:1583398311@163.com">1583398311@163.com</a></div>' +
        '<div class="arow"><svg viewBox="0 0 24 24"><path d="M12 3v10m0 0l-3.5-3.5M12 13l3.5-3.5"/><path d="M5 17v3h14v-3"/></svg>不登录也能看，登录后才能传文件</div>' +
        '<button type="button" class="abtnx afile" id="afileBtn">📦 给我传文件 / 登录账号</button>' +
        '<p class="afoot">© 2026 jasonyzk · 本站由 AI 协助搭建</p>' +
        '<div class="adev" id="adev">' +
          '<p class="dtip">验证后请在打开的页面登录或注册一个账号，该账号将成为<b>唯一的开发者账号</b>。此通道全局只开放一次，绑定后永久关闭。</p>' +
          '<div class="drow">' +
            '<input type="password" id="adevPwd" placeholder="访问口令" autocomplete="off">' +
            '<button type="button" class="dgo" id="adevGo">验证</button>' +
          '</div>' +
        '</div>' +
      '</div>';
    document.body.appendChild(mask);
    card = mask.querySelector('.acard');
    devBox = mask.querySelector('#adev');
    devInput = mask.querySelector('#adevPwd');
    mask.querySelector('#afileBtn').addEventListener('click', function(){ openStation('#account'); });
    mask.querySelector('#adevGo').addEventListener('click', goDev);
    devInput.addEventListener('keydown', function(e){ if(e.key === 'Enter') goDev(); });
    mask.addEventListener('click', function(e){ if(e.target === mask) close(); });
    /* 冻结背景：首页/游戏页把 wheel、touch、pointer、keydown 监听挂在 window 上，
       弹窗遮罩在冒泡阶段截断，避免弹窗打开时背景继续翻页 / 游戏误触发。 */
    ['wheel','touchmove','touchstart','pointerdown','pointermove','pointerup','keydown']
      .forEach(function(type){
        mask.addEventListener(type, function(e){
          e.stopPropagation();
          if((type === 'wheel' || type === 'touchmove') && card && !card.contains(e.target)){
            e.preventDefault();          // 卡片内部仍可正常滚动
          }
        }, {passive:false});
      });
    show();
  }
  function show(){
    if(!mask) return;
    document.addEventListener('keydown', onKey, true);
    requestAnimationFrame(function(){ mask.classList.add('open'); });
  }
  function close(){
    if(!mask) return;
    document.removeEventListener('keydown', onKey, true);
    mask.classList.remove('open');
    devBox.classList.remove('on');
    devInput.value = '';
    jcount = 0;
    setTimeout(function(){ if(mask && !mask.classList.contains('open')){ mask.remove(); mask = null; } }, reduce ? 0 : 260);
  }
  function goDev(){
    var v = devInput.value;
    if(!v) return;
    if(!READY){ toast('文件服务尚未配置好，暂时无法验证'); return; }
    /* 口令只经 fragment 传给服务器页面，fragment 不会出现在网络请求里；
       服务器校验后签发一次性兑换券，前端全程不知道口令是否正确。 */
    window.open(FILE_DROP + '/#dev=' + encodeURIComponent(v), '_blank', 'noopener');
    close();
  }

  /* ---------- 键盘：Esc 关闭；弹窗开着时连按 5 次 J 开口令框 ---------- */
  var jcount = 0, jlast = 0;
  function onKey(e){
    if(!mask || !mask.classList.contains('open')) return;
    if(e.key === 'Escape'){ e.stopPropagation(); close(); return; }
    if(e.target === devInput) return;       // 口令框里正常输入
    if(e.target && e.target.tagName === 'INPUT') return;
    var now = Date.now();
    if(e.key === 'j' || e.key === 'J'){
      if(now - jlast > 1600) jcount = 0;
      jlast = now;
      if(++jcount >= 5){
        jcount = 0;
        devBox.classList.add('on');
        setTimeout(function(){ devInput.focus(); }, 50);
      }
    } else {
      jcount = 0;
    }
  }
})();
