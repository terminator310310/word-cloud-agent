# AGENTS.md

Guidance for agents working in this repository. Kept short on purpose; verify anything you are unsure about against the code.

## What this repo is

A single-script daily job (`wordcloud_daily.py`, no package, no tests). It scrapes
"hot" lists from Baidu, Toutiao, Zhihu, and Bilibili, caches the results as JSONL,
and renders word cloud PNGs (one per board, plus a weekly one) into `out/`.

There is no README, no requirements file, and no test/lint/CI configuration —
the script itself is the only source of truth.

## Commands

- Run the daily job (from the repo root, because all paths are relative):
  ```bash
  python wordcloud_daily.py
  ```
- Dependencies are not declared anywhere (`jieba` and `wordcloud` are imported by
  the script). They are not installed in this environment; install them with:
  ```bash
  pip install jieba wordcloud
  ```
- There are no tests, linters, or build steps. Do not invent commands — the only
  supported workflow is running the script above.

## Directories

- `wordcloud_daily.py` — the entire program; it runs top to bottom on execution
  (there is no `main()` guard).
- `stopwords.txt` — read at startup and split on whitespace. **Currently empty.**
- `cache/` — append-only JSONL cache. The file name is the current month
  (`YYYY-MM`, e.g. `cache/2026-10.jsonl`); the script appends to it every run and
  never rewrites history. The readers later in the script rely on these files, so
  do not delete them without checking that code.
- `out/` — PNG files are written here (`out/<board>_<date>.png` and
  `out/本周全板块_<date>.png`). The directory is expected to exist.
- `fonts/` — WordCloud is configured with
  `font_path="C:\Windows\Fonts\simhei.ttf"` (the system font), not a file in this
  repository. The directory itself is empty and unused.
- `.opencode/` — OpenCode config. Contains only an empty custom skill
  (`skills/hot-wordcloud/SKILL.md`); nothing to invoke today.

## Script flow and quirks

- Five "boards" are defined in `BOARDS` (Baidu realtime/game, Toutiao, Zhihu,
  Bilibili). Each maps to a `(scraper-kind, url)` tuple; the dict's insertion
  order defines the order of the output files.
- Three scraper kinds are special-cased: Baidu embeds its data inside an HTML
  comment (`<!--s-data:{...}-->`) and parses it with a regex; Toutiao, Zhihu, and
  Bilibili use JSON APIs.
- A failing board does **not** abort the run — the exception is caught and the
  board is skipped (`跳过 <ExceptionType>`).
- After scraping, the script reads back only today's rows from the cache, draws
  one PNG per board, then draws a "this week" PNG covering the last 7 days across
  **all** cache files.
- Tokenization uses `jieba.lcut`; words shorter than two characters or purely
  numeric are dropped. `random_state=42` fixes the daily layout.
- All paths (`stopwords.txt`, `cache/`, `out/`, `fonts/`) resolve relative to the
  current working directory, so always run from the repo root.
