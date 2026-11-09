# publish_to_github.py —— 方案B一键发布：更新词云 → 重建相册页 → 推送 GitHub
# 日常用法（就这一条命令）：
#     python publish_to_github.py
# 可选参数：
#     --no-run      不重新抓取，只用现有数据重建相册页并推送
#     --index-only  只重建 index.html，不提交不推送（预览用）
import datetime
import subprocess
import sys
import urllib.parse
from pathlib import Path

ROOT = Path(__file__).parent
PAGES_URL = "https://terminator310310.github.io/word-cloud-agent/"

INDEX_TMPL = """<!doctype html>
<html lang="zh">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>热榜词云 · 每日更新</title>
<style>
 body{font-family:"Microsoft YaHei",sans-serif;background:#f6f6f4;color:#111;margin:0}
 header{max-width:980px;margin:0 auto;padding:40px 20px 8px}
 h1{font-size:34px;margin:0 0 8px}
 .sub{color:#666;font-size:15px;line-height:1.8}
 .grid{max-width:980px;margin:24px auto 40px;padding:0 20px;display:grid;
       grid-template-columns:repeat(auto-fill,minmax(430px,1fr));gap:24px}
 figure{margin:0;background:#fff;border:1px solid #e4e4e0;border-radius:10px;overflow:hidden}
 img{width:100%;display:block}
 figcaption{padding:10px 14px;font-size:14px;color:#444;border-top:1px solid #eee}
 footer{max-width:980px;margin:0 auto 40px;padding:0 20px;color:#999;font-size:13px}
 a{color:#0b62d0}
</style>
</head>
<body>
<header>
 <h1>热榜词云 · 每日更新</h1>
 <div class="sub">每天自动抓取百度 / 头条 / 知乎 / B站公开热榜，聚合分词生成词云。<b>词越大 = 讨论越多。</b><br>本页随每日推送自动更新，更新于 {{NOW}}。</div>
</header>
<div class="grid">
{{CARDS}}
</div>
<footer>数据来源均为各平台公开榜单，仅做词频统计展示，不转载原文。｜
仓库：<a href="https://github.com/terminator310310/word-cloud-agent">word-cloud-agent</a></footer>
</body>
</html>
"""


def run_daily():
    print("1/3 抓取热榜并生成词云...")
    subprocess.run([sys.executable, str(ROOT / "wordcloud_daily.py")], check=True)


def build_index():
    print("2/3 重建相册页 index.html ...")
    pngs = sorted((ROOT / "out").glob("*.png"), key=lambda p: p.stem, reverse=True)[:14]
    cards = []
    for p in pngs:
        if "_" in p.stem:
            board, date = p.stem.rsplit("_", 1)
        else:
            board, date = p.stem, ""
        src = "out/" + urllib.parse.quote(p.name)
        cards.append(
            f'<figure><a href="{src}"><img src="{src}" loading="lazy"></a>'
            f"<figcaption>{board} · {date}</figcaption></figure>"
        )
    html = (INDEX_TMPL.replace("{{CARDS}}", "\n".join(cards))
                    .replace("{{NOW}}", datetime.date.today().isoformat()))
    (ROOT / "index.html").write_text(html, encoding="utf-8")
    print(f"   本页放入最近 {len(pngs)} 张图")


def push():
    print("3/3 提交并推送 GitHub...")

    def git(*args):
        r = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
        out = (r.stdout + r.stderr).lower()
        if r.returncode != 0 and "nothing to commit" in out:
            print("   仓库没有新变化，跳过提交")
            return
        if r.returncode != 0:
            print(r.stdout, r.stderr)
            r.check_returncode()

    git("add", "-A")
    git("add", "-f", "out/")          # out 被 .gitignore 忽略，用 -f 强制带上（图片才会上到 Pages）
    git("commit", "-m", f"更新词云与相册 {datetime.date.today().isoformat()}")
    git("push")
    print(f"完成 ✅ 相册页地址：{PAGES_URL}")


if __name__ == "__main__":
    if "--index-only" in sys.argv:
        build_index()
        sys.exit()
    if "--no-run" not in sys.argv:
        run_daily()
    build_index()
    push()
