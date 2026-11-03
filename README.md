# jasonyzk.cn 主站 · 使用与上线手册

## 当前线上地址

**https://jasonyzk-works.app.workbuddy.host/?sharecode=SMHZAR7MII**

已部署上线，下面所有子路径都能直接访问：

| 网址 | 内容 |
|---|---|
| 线上根路径 | 主站（图标索引） |
| `/pet/` | 桌面宠物（你之前做的那个介绍页，已原样保留） |
| `/pet/download.html` | 下载地址（百度 / 夸克 / 迅雷网盘） |
| `/recorder/` | 操作录制 |
| `/seo/` | 搜索引擎原理演示 |

> 分享出去的链接必须带 `?sharecode=SMHZAR7MII`，否则会提示「链接不完整」。

## 换成自己的域名

买好 `jasonyzk.cn`（或任何域名）后，在站点目录执行：

```bash
python switch-domain.py jasonyzk.cn
```

它会一次性替换 canonical / og:url / og:image / sitemap / CNAME 里的网址，然后重新部署即可。
页面之间的跳转用的是相对路径（`../`、`pet/`），**任何域名下都自动正确**，不需要改。

---

**站点结构：一个主站 + 每个项目一条短路径。**

绑定正式域名后，网址就是：

| 网址 | 内容 |
|---|---|
| `jasonyzk.cn` | 主站（图标索引） |
| `jasonyzk.cn/pet` | 桌面宠物（你之前做的那个介绍页，已原样保留） |
| `jasonyzk.cn/pet/download.html` | 桌面宠物下载地址（百度 / 夸克 / 迅雷网盘） |
| `jasonyzk.cn/recorder` | 操作录制 |
| `jasonyzk.cn/seo` | 搜索引擎原理演示 |

---

## 一、目录结构（扁平短路径）

```
jasonyzk-site/
├── index.html            主站首页
├── 404.html              找不到页面时显示
├── assets/icons/         主站用的图标
├── pet/                  ← 对应 jasonyzk.cn/pet
│   ├── index.html        你原来那个黑底介绍页（完整保留）
│   ├── download.html     网盘下载页
│   └── assets/           图标、待机/走动素材
├── recorder/             ← jasonyzk.cn/recorder
├── seo/                  ← jasonyzk.cn/seo
├── robots.txt / sitemap.xml
├── CNAME                 jasonyzk.cn
└── preview.bat           双击本地预览
```

文件夹叫什么名字，网址就是什么，**不要用多层嵌套**。

---

## 二、本地预览

双击 **`preview.bat`**，浏览器自动打开 `http://localhost:8000`。

停止：在黑色窗口按 `Ctrl+C`，或直接关掉。
没反应 = 没装 Python，去 python.org 装，安装时勾上 "Add Python to PATH"。

---

## 三、桌面宠物的下载怎么搞定的（重点）

exe 有 45 MB，**超过了 Cloudflare Pages 单文件 25 MB 的上限，不能塞进网站文件夹**。

但你之前已经把安装包传到了三个网盘，我把它们全部接了进来（`pet/download.html`）：

| 渠道 | 状态 |
|---|---|
| 百度网盘 | 已配置，提取码 `j0q3` |
| 夸克网盘 | 已配置 |
| 迅雷网盘 | 已配置，提取码 `y8yb` |
| GitHub Release | 兜底源（原页面里那个灰色死链，已改成指向 Release 页面） |

**网盘链接会过期**，建议每隔一段时间自己点一遍验证。
要换链接：打开 `pet/download.html`，改 `<a class="dl-item" href="...">` 里的网址就行。

---

## 四、买域名（jasonyzk.cn，预算 10~100 元/年）

`.cn` 和 `.com` 玩法不一样，注意区别：

| 域名 | 价格参考 | 说明 |
|---|---|---|
| **jasonyzk.cn** | 首年 19~29 元，续费约 30~40 元 | 国内认可度高、百度收录好，**必须实名认证** |
| jasonyzk.top | 约 25~30 元/年 | 便宜，同样要实名 |
| jasonyzk.com | 约 70~80 元/年 | 不用实名，但通常要信用卡，和 .cn 二选一即可 |

**买 `.cn` 的三个必知事实：**

1. **Cloudflare 不卖 `.cn`。** 去**腾讯云**或**阿里云**买，中文界面、微信/支付宝都能付。
2. **买完必须实名认证**（上传身份证），否则域名会被暂停解析（Serverhold）。在腾讯云/阿里云控制台里操作，一般 1~3 个工作日过审。
3. **实名 ≠ 备案。** 用 Cloudflare Pages（服务器在海外）**不需要 ICP 备案**，实名过了就能直接访问。只有将来换国内服务器才需要备案。

**通用避坑**：看**续费价**而不是首年价，很多域名首年 1 元、第二年收你 90 元。

---

## 五、上线（Cloudflare Pages，免费）

1. 把整个文件夹传到 GitHub 新仓库（比如 `jasonyzk-site`）。
2. 登录 [dash.cloudflare.com](https://dash.cloudflare.com) → **Workers & Pages** → **Create** → **Pages** → **Connect to Git**，选中仓库。
3. 构建配置：

   | 项 | 填什么 |
   |---|---|
   | Framework preset | `None` |
   | Build command | **留空** |
   | Build output directory | `/` |

4. 点 Save and Deploy，等一分钟。之后每次推代码，网站自动更新。
5. 绑域名：**Custom domains** → 填 `jasonyzk.cn` → Cloudflare 会提示加 DNS 记录。

   > 因为域名在腾讯云/阿里云，Cloudflare 会给你一个 `xxxx.pages.dev` 的地址，
   > 去腾讯云/阿里云的域名解析里加一条 **CNAME 记录**：主机记录 `@`，记录值 `xxxx.pages.dev`。
   > 等 HTTPS 证书签发（几分钟到几小时），就能用 `https://jasonyzk.cn` 访问了。

---

## 六、加一个新作品（3 步，复制粘贴）

**第 1 步**：复制 `recorder` 文件夹，改名成你要的路径，比如 `tools`。

**第 2 步**：用记事本打开 `tools/index.html`，改这些中文部分：
- `<title>` 项目名
- `<h1>` 项目名
- `<p class="sub">` 一句话简介
- `<p class="intro">` 详细介绍
- `<ul class="feat">` 里的功能条目

**第 3 步**：回主站 `index.html`，在 `<!-- ======== 01 软件项目 ======== -->` 下面照抄一个 `<a class="item">` 块：

```html
<a class="item" href="tools/">
  <span class="ico">
    <svg viewBox="0 0 24 24"><circle cx="12" cy="12" r="8"/></svg>
  </span>
  <span class="item-body">
    <span class="item-title">我的新作品</span>
    <span class="item-desc">一句话说清它是干嘛的</span>
  </span>
  <span class="item-side"><span class="pill">Web</span></span>
  <span class="arr">→</span>
</a>
```

最后把新地址加进 `sitemap.xml`。

> 每个子页面里的「← jasonyzk.cn」按钮已经处理过：本地预览走相对路径，上线后自动跳回主站。

---

## 七、出问题先看这里

| 现象 | 原因 / 解决办法 |
|---|---|
| 改了页面刷新没变化 | 浏览器缓存，按 `Ctrl + F5` |
| 图片裂了 | 文件名大小写不一致 |
| 上传后 404 | 文件名必须是 `index.html`，文件夹名要对应网址 |
| 域名访问不了 | .cn 要先完成**实名认证**；DNS 生效要几分钟到几小时 |
| 网页提示证书错误 | 证书还没签发完，等一会儿再试 |
| 网盘下载失效 | 编辑 `pet/download.html` 换链接 |
