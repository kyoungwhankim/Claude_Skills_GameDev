"""Collecting reference docs into <ws>/Docs: web pages as Markdown, YouTube subtitles."""
import os
import re
import shutil
import subprocess
import sys
import urllib.request


def _slug(url):
    s = re.sub(r"^https?://", "", url).strip("/")
    return re.sub(r"[^\w.-]+", "_", s)[:120] or "page"


def fetch(cfg, urls):
    try:
        import html2text
    except ImportError:
        raise SystemExit("html2text 가 필요합니다: python -m pip install html2text")
    out = os.path.join(cfg["ws"], "Docs")
    os.makedirs(out, exist_ok=True)
    for url in urls:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 uetk"})
        raw = urllib.request.urlopen(req, timeout=60).read().decode("utf-8", errors="replace")
        m = re.search(r"<main.*?</main>", raw, re.S) or re.search(r"<article.*?</article>", raw, re.S)
        h = html2text.HTML2Text()
        h.body_width = 0
        md = f"<!-- source: {url} -->\n\n" + h.handle(m.group(0) if m else raw)
        path = os.path.join(out, _slug(url) + ".md")
        open(path, "w", encoding="utf-8").write(md)
        print(f"[docs] {url} -> {path} ({len(md)} chars)")


def youtube(cfg, ids, lang="en"):
    out = os.path.join(cfg["ws"], "Docs", "youtube")
    os.makedirs(out, exist_ok=True)
    args = [sys.executable, "-m", "yt_dlp", "-q", "--skip-download", "--write-auto-subs", "--write-subs",
            "--sub-langs", lang, "--sub-format", "vtt", "-o", os.path.join(out, "%(id)s_%(title)s.%(ext)s")]
    deno = shutil.which("deno") or os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\WinGet\Links\deno.exe")
    if os.path.exists(deno):
        args += ["--js-runtimes", f"deno:{deno}"]
    for vid in ids:
        url = vid if vid.startswith("http") else f"https://youtu.be/{vid}"
        subprocess.call(args + [url])
    print(f"[docs] 자막 → {out} (자막이 없는 영상은 파일이 생기지 않습니다)")
