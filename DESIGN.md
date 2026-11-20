---
version: 1.0.0
name: jasonyzk 作品站
description: 极简留白、深色优先、iOS 26 连续曲率圆角的个人作品门户；玻璃质感仅用于控件层
colors:
  primary: "#4438ca"
  primary-focus: "#9d92ff"
  ink: "#17171a"
  canvas: "#fbfbf9"
  surface: "#ffffff"
  on-primary: "#ffffff"
  line: "#e4e3dd"
  ink-dark: "#e9e9ee"
  canvas-dark: "#0d0e12"
  surface-dark: "#16181e"
  line-dark: "#2a2d35"
typography:
  hero-display:
    fontFamily: "-apple-system, BlinkMacSystemFont, PingFang SC, HarmonyOS Sans SC, Microsoft YaHei, sans-serif"
    fontSize: clamp(50px, 8vw, 92px)
    fontWeight: 700
    lineHeight: 1.28
  h1:
    fontFamily: "{typography.hero-display.fontFamily}"
    fontSize: clamp(26px, 5.4vw, 40px)
    fontWeight: 700
  body:
    fontFamily: "{typography.hero-display.fontFamily}"
    fontSize: 15px
    fontWeight: 400
    lineHeight: 1.75
  caption:
    fontFamily: "{typography.hero-display.fontFamily}"
    fontSize: 13px
    fontWeight: 400
rounded:
  none: 0px
  inside: 12px
  box: 16px
  card: 22px
  pill: 9999px
spacing:
  xs: 6px
  sm: 10px
  md: 14px
  lg: 20px
  xl: 32px
  section: 60px
components:
  button-primary:
    backgroundColor: "{colors.primary}"
    textColor: "{colors.on-primary}"
    typography: "{typography.body}"
    rounded: "{rounded.box}"
    minHeight: 44px
    padding: 12px 24px
  card:
    backgroundColor: "{colors.surface}"
    borderColor: "{colors.line}"
    rounded: "{rounded.card}"
    padding: 24px
  chip:
    backgroundColor: "transparent"
    borderColor: "{colors.primary}"
    textColor: "{colors.primary}"
    rounded: "{rounded.pill}"
    padding: 6px 14px
---

# jasonyzk 作品站 · 设计规范

本文件是全站 UI 的规范真源。可执行实现位于 `assets/design.css`（形状/尺寸/排版归一化层）
与 `assets/theme.css`（语义色/主题变量）。新增页面或修改组件时，先读本文件，再写代码。

## 1. Visual Theme & Atmosphere

极简、留白充足、信息密度低。深色为默认观感（跟随系统），浅色与「奶龙入侵」为主题变体。
视觉重量靠字重与留白建立，不靠色块堆叠。玻璃材质**只出现在按钮等控件层**，永不铺满内容区。
圆角采用 iOS 26 连续曲率（支持 `corner-shape: squircle` 的浏览器自动升级，其余回退大圆角）。

## 2. Color Palette & Roles

颜色**一律走 `theme.css` 的语义变量**，禁止在页面内联写死十六进制：

| 语义变量 | 浅色 | 深色 | 用途 |
|---|---|---|---|
| `--bg` | `#fbfbf9` | `#0d0e12` | 页面画布 |
| `--surface` | `#ffffff` | `#16181e` | 卡片/控件表面 |
| `--tx` | `#17171a` | `#e9e9ee` | 主文字 |
| `--tx2` / `--tx3` | 灰阶 | 灰阶 | 次要/辅助文字 |
| `--line` | `#e4e3dd` | `#2a2d35` | 描边（统一 1px） |
| `--accent` | `#4438ca` | `#9d92ff` | 交互主色、焦点环 |

教学页（`/seo`）保留蓝/琥珀/绿/红的**语义高亮色**（`--blue-l`、`--amber-l` 等），
用于区分概念，属于信息传递而非装饰，不纳入「单一强调色」约束。

## 3. Typography Rules

- 字族统一：`-apple-system, BlinkMacSystemFont, "PingFang SC", "HarmonyOS Sans SC", "Microsoft YaHei", sans-serif`
- 正文 15px / 行高 1.75；辅助文字 13px
- 标题字重统一 700（不要再出现 600 / 800 混用）
- 首页 hero 是唯一的大字展示层（`clamp(50px,8vw,92px)`），内页 h1 用 `clamp(26px,5.4vw,40px)`
- 中文断行用 `overflow-wrap`，**不要**用 `word-break: break-word`（会拆碎英文单词）

## 4. Component Stylings

圆角四级，**同类元素必须同形状**：

| 层级 | 令牌 | 值 | 适用元素 |
|---|---|---|---|
| 内框 | `--r-in` | 12px | 图标容器、输入、小标签底、编号块 |
| 控件 | `--r-box` | 16px | 主按钮、列表项、结果项、选项、手机示意 |
| 卡片 | `--r-card` | 22px | 作品卡、展示区、游戏区、玩法卡、答案框 |
| 胶囊 | `--r-pill` | 999px | 时间胶囊、标签、状态 chip（**主按钮不用胶囊**） |

- 描边统一 `1px solid var(--line)`，禁止 1.5px / 2px 离散值
- 阴影统一单层 `var(--shadow)`，禁止饱和色扩散阴影
- 按钮最小高度 44px；次要链接视觉不变，用伪元素把点击区补到 44px
- 交互态：`transform: scale(0.97)` 按下反馈、`:focus-visible` 焦点环 2px、时长 180ms

## 5. Layout Principles

- 间距基于 6/10/14/20/32pt 节奏（见 YAML `spacing`）
- 卡片间距对齐：桌面 26px、窄屏 14px
- 页面左右边距：桌面 4vw 或 20px，手机 20px，全局一致
- 内容最大宽度按页型选择：作品网格 980px、游戏 640~760px、长文 1000px、下载页 480px

## 6. Depth & Elevation

只有两层：平面内容（无阴影）+ 抬升控件（hover 时 `var(--shadow)`）。
材质厚度只用于表达层级，导航/工具栏可用玻璃（`rgba(surface,.7)` + `blur(20px) saturate(180%)`），
触屏设备关闭实时模糊改为高不透明实色，避免滑动重绘闪烁。

## 7. Do's and Don'ts

| Do | Don't |
|---|---|
| 卡片统一 22px 圆角 | 同一页出现 12/14/16/18/22px 五种圆角 |
| 描边 1px 语义色 | 2px 彩色描边制造「另一套设计」 |
| 标题统一字重 700 | 600/700/800 混用 |
| 语义色用于教学高亮 | 给整页铺蓝色渐变光晕背景 |
| 次要链接伪元素补命中区 | 返回链接只有 34px 高 |
| 改动后升 `?v=` 版本号 | 改了 CSS 不升版本号导致读缓存 |

## 8. Responsive Behavior

- 断点收敛：`560 / 820 / 1024 / 1600 / 2200px`；小屏微调用 360px
- 横屏矮屏（max-height 480）单独压缩纵向间距
- 命中区 ≥ 44px；`prefers-reduced-motion` 关闭位移动画，`prefers-reduced-transparency` 关闭玻璃
- 320~2560px 全宽度无横向溢出

## 8.5 Icon System & Brand（图标与品牌）

全站图标为**圆润实心**一套语言，一处定义、全站复用：

- 精灵源：`assets/icons.svg`（`<symbol>` sprite），`viewBox="0 0 24 24"`
- 规范：主体 `currentColor` 实心填充；圆角端点（`stroke-linecap:round`）；
  线宽统一 3.2（必须描边的图标如放大镜）；单一焦点、24px 下可辨
- 用法：`<svg class="ico"><use href="/assets/icons.svg#i-xxx"></use></svg>`
  （子目录页同样用**绝对**路径 `/assets/...`；颜色由父级 `color` 控制，自动跟随主题）
- 已有符号：`i-pet / i-recorder / i-search / i-bolt / i-snake / i-download /
  i-doc / i-mail / i-user / i-about / i-close / i-sound-on / i-sound-off /
  i-theme / i-upload`
- 项目卡图标色走 `--ic-blue/purple/green/amber/rose`（theme.css 深浅各一套），
  由 design.css 的 `.ic-*` 赋给 `color`，图标 `fill:currentColor` 继承

**品牌标识**：`assets/brand.svg`（紫色圆角方糖 + 白色 J + 右上光点），
favicon 四件套 `assets/icons/favicon-{16,32,64,256}.png` + `favicon.ico`（多尺寸）。
所有页面 `<link rel="icon">` 用绝对路径 `/assets/brand.svg` 与 `/favicon.ico`。

自包含脚本（如 `about.js`）不引外部精灵，内嵌实心 path 保持零文件依赖。

## 9. Agent Prompt Guide

新增页面时，按以下顺序落地即可自动保持一致：

1. `<style>` 里只写**本页独有**的布局与语义色，不写通用圆角/字号/描边
2. 引入共享层，顺序固定：`motion.css` → `theme.css` → `glass.css` → `nailong.css` → `design.css`
3. 卡片用 `.card`，按钮用 `.btn`，标签用 `.tag`/`.pill`，颜色取语义变量
4. 组件只需 `border-radius: var(--r-card|box|in|pill)` 四选一
5. 图标用 `<svg class="ico"><use href="/assets/icons.svg#i-xxx">`，新增图标先往精灵加 `<symbol>`；
   favicon 沿用 `/assets/brand.svg`，不要另做新标识

提示词示例：
> 按 DESIGN.md 新增一个项目展示页，用 `.card` 卡片网格、`.btn` 主按钮、语义色变量，
> 不要自定义圆角和字号，最后引入 design.css。
