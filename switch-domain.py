# -*- coding: utf-8 -*-
"""
把站内所有「绝对网址」一次性换成你的正式域名。

用法（在 jasonyzk-site 目录下）：
    python switch-domain.py jasonyzk.cn

会替换：
  - <link rel="canonical">          SEO 规范链接
  - <meta property="og:url">        分享卡片链接
  - <meta property="og:image">      分享卡片配图
  - sitemap.xml                     站点地图里的全部 <loc>
  - CNAME                           绑定的域名

不会动任何页面内的相对跳转（如 ../ 、pet/），所以
/py 主站和各个子站之间的跳转在任何域名下都是对的，不用改。
"""
import io, os, re, sys

OLD_HOST = "jasonyzk-works.app.workbuddy.host"   # 当前临时域名
TARGETS = (".html", ".xml")                       # 处理的后缀

def main():
    if len(sys.argv) < 2:
        print("用法: python switch-domain.py <你的域名>")
        print("例如: python switch-domain.py jasonyzk.cn")
        return 1

    new = sys.argv[1].strip().rstrip("/")
    new = re.sub(r"^https?://", "", new)          # 允许带不带 https://
    if not re.match(r"^[A-Za-z0-9.-]+$", new):
        print("域名看起来不合法:", new)
        return 1

    changed = 0
    hits = 0
    for root, _, files in os.walk("."):
        if os.path.basename(root) in (".git", "node_modules"):
            continue
        for fn in files:
            if not fn.endswith(TARGETS) and fn != "CNAME":
                continue
            p = os.path.join(root, fn)
            s = io.open(p, encoding="utf-8").read()
            if OLD_HOST not in s:
                continue
            s2 = s.replace(OLD_HOST, new)
            hits += s.count(OLD_HOST)
            io.open(p, "w", encoding="utf-8").write(s2)
            changed += 1
            print("  已更新 %-28s (%d 处)" % (p.replace("\\", "/"), s.count(OLD_HOST)))

    # CNAME 文件单独写
    cname = os.path.join(".", "CNAME")
    existed = os.path.exists(cname)
    io.open(cname, "w", encoding="utf-8").write(new + "\n")
    print("  %-26s -> %s" % ("CNAME 已写入" if existed else "CNAME 已新建", new))

    print("\n完成：%d 个文件、%d 处网址 -> https://%s" % (changed, hits, new))
    print("提示：改完后需要重新部署一次才会生效。")
    return 0

if __name__ == "__main__":
    sys.exit(main())
