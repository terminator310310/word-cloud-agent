# wordcloud_daily.py
import json, re, datetime, urllib.request
import jieba
from wordcloud import WordCloud

BOARDS = {  # 板块名: (取法, 地址)
    "全网热搜": ("baidu", "https://top.baidu.com/board?tab=realtime"),
    "游戏": ("baidu", "https://top.baidu.com/board?tab=game"),
    "头条": (
        "toutiao",
        "https://www.toutiao.com/hot-event/hot-board/?origin=toutiao_pc",
    ),
    "知乎": ("zhihu", "https://api.zhihu.com/topstory/hot-lists/total?limit=50"),
    "B站热门": ("bili", "https://api.bilibili.com/x/web-interface/popular?ps=20"),
}
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    )
}


def get(url, is_json=False):
    req = urllib.request.Request(url, headers=HEADERS)
    raw = urllib.request.urlopen(req, timeout=20).read().decode("utf-8", "replace")
    return json.loads(raw) if is_json else raw


def titles_for(kind):
    if kind == "baidu":  # 数据在页内 <!--s-data:{...}--> 注释里
        raw = get(BOARDS[name][1])
        j = json.loads(re.search(r"<!--s-data:(.*?)-->", raw, re.S).group(1))
        return [c["word"] for c in j["data"]["cards"][0]["content"]]
    if kind == "toutiao":
        return [it["Title"] for it in get(BOARDS[name][1], True)["data"]]
    if kind == "zhihu":
        return [it["target"]["title"] for it in get(BOARDS[name][1], True)["data"]]
    if kind == "bili":
        return [it["title"] for it in get(BOARDS[name][1], True)["data"]["list"]]


today = datetime.date.today().isoformat()
stop = set(open("stopwords.txt", encoding="utf-8").read().split())
import os
cache_path = f"cache/{today[:7]}.jsonl"
seen = set()  # 去重：先记下缓存里已有的记录，重复跑不会写两遍
if os.path.exists(cache_path):
    for l in open(cache_path, encoding="utf-8"):
        r = json.loads(l)
        seen.add((r["date"], r["board"], r["title"]))
cache = open(cache_path, "a", encoding="utf-8")

for name, (kind, _) in BOARDS.items():  # 1) 抓当天所有板块，存进缓存
    try:
        for t in titles_for(kind):
            if (today, name, t) in seen:  # 已经记过的标题直接跳过
                continue
            seen.add((today, name, t))
            cache.write(
                json.dumps(
                    {"date": today, "board": name, "title": t}, ensure_ascii=False
                )
                + "\n"
            )
        print(f"{name}: ok")
    except Exception as e:  # 单板块失败不影响其他板块
        print(f"{name}: 跳过 {type(e).__name__}")
cache.close()


def draw(rows, out_png):  # 2) 聚合分词出图
    words = []
    for r in rows:
        words += [
            w
            for w in jieba.lcut(r["title"])
            if len(w) >= 2 and w not in stop and not w.isdigit()
        ]
    if len(words) < 20:
        print(f"{out_png} 词量太少，跳过")
        return
    wc = WordCloud(
        font_path="C:\\Windows\\Fonts\\simhei.ttf",
        width=1280,
        height=720,
        background_color="white",
        max_words=120,
        collocations=False,
        random_state=42,
    )  # 固定随机数=每天版式稳定
    wc.generate(" ".join(words))
    wc.to_file(out_png)
    print("出图:", out_png)


all_today = [
    json.loads(l)
    for l in open(f"cache/{today[:7]}.jsonl", encoding="utf-8")
    if json.loads(l)["date"] == today
]
for b in BOARDS:  # 3) 每个板块一张当日图
    draw([r for r in all_today if r["board"] == b], f"out/{b}_{today}.png")

import glob  # 周汇总：读所有缓存，取近 7 天

week = (datetime.date.today() - datetime.timedelta(days=6)).isoformat()
recent = [
    json.loads(l)
    for f in glob.glob("cache/*.jsonl")
    for l in open(f, encoding="utf-8")
    if json.loads(l)["date"] >= week
]
draw(recent, f"out/本周全板块_{today}.png")
print("完成")
