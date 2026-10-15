"""Builds a single self-contained HTML report from <ws>/Analysis/00_*.md and <ws>/Analysis/sections/*.md.

Left sidebar: chapter list + headings of the open chapter. Right: scrollable reading pane.
Mermaid is inlined from <toolkit>/vendor/mermaid.min.js so the file works offline.
"""
import glob
import html
import json
import os
import re

import markdown
from markdown.extensions.toc import slugify_unicode

MERMAID = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "vendor", "mermaid.min.js")
file_to_id = {}


def chapter_id(path):
    return "ch" + os.path.basename(path)[:2]




def fix_links(body):
    # Links between report files become in-page chapter links.
    def repl(m):
        target = m.group(1)
        name = os.path.basename(target.split("#")[0])
        if name in file_to_id:
            return f'href="#{file_to_id[name]}"'
        return m.group(0)

    return re.sub(r'href="([^"]+\.md(?:#[^"]*)?)"', repl, body)


def fix_mermaid_block(src):
    # Quote [labels] containing characters mermaid treats as syntax, and turn literal \n into line breaks.
    def quote(m):
        node, label = m.group(1), m.group(2)
        if label[:1] in "([/\\" or not re.search(r"[(){}=:;|<>#&]", label):
            return m.group(0)
        return f'{node}["{label.replace(chr(34), chr(39))}"]'

    src = src.replace("\\n", "<br/>")
    return re.sub(r'(\b[\w-]+)\[(?!")([^\]\n]*)\]', quote, src)


def convert(path):
    cid = chapter_id(path)
    text = open(path, encoding="utf-8").read()
    text = re.sub(r"```mermaid\n(.*?)```", lambda m: "```mermaid\n" + fix_mermaid_block(m.group(1)) + "```", text, flags=re.S)
    md = markdown.Markdown(
        extensions=["extra", "sane_lists", "toc"],
        extension_configs={"toc": {"slugify": lambda v, sep: f"{cid}-" + slugify_unicode(v, sep), "toc_depth": "2-3"}},
    )
    body = md.convert(text)
    body = re.sub(r'<pre><code class="language-mermaid">(.*?)</code></pre>', r'<pre class="mermaid">\1</pre>', body, flags=re.S)
    body = re.sub(r"<table>", '<div class="table-wrap"><table>', body)
    body = re.sub(r"</table>", "</table></div>", body)
    body = fix_links(body)
    m = re.search(r"^#\s+(.+)$", text, re.M)
    title = m.group(1).strip() if m else os.path.basename(path)
    return cid, title, body



def short_title(cid, title):
    t = re.sub(r"^\d+\.\s*", "", title)
    return t

def build(analysis_dir, out_path, title, subtitle=""):
    files = sorted(glob.glob(os.path.join(analysis_dir, "00_*.md"))) + sorted(glob.glob(os.path.join(analysis_dir, "sections", "*.md")))
    if not files:
        raise SystemExit(f"[report] {analysis_dir} 에 00_*.md 나 sections/*.md 가 없습니다.")
    file_to_id.clear()
    file_to_id.update({os.path.basename(p): chapter_id(p) for p in files})
    chapters = [convert(p) for p in files]



    nav_items = "\n".join(
        f'<li><a class="chapter-link" href="#{cid}" data-ch="{cid}"><span class="num">{cid[2:]}</span>'
        f'<span class="label">{html.escape(short_title(cid, title))}</span></a><ul class="subtoc" id="toc-{cid}"></ul></li>'
        for cid, title, _ in chapters
    )
    articles = "\n".join(f'<article class="chapter" id="{cid}" hidden>{body}</article>' for cid, _, body in chapters)
    mermaid_js = open(MERMAID, encoding="utf-8").read().replace("</script", "<\\/script")

    page = f"""<!doctype html>
    <html lang="ko">
    <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{html.escape(title)}</title>
    <style>
    :root {{
      --bg: #f7f7f5; --panel: #ffffff; --side: #f0efeb; --text: #1f2328; --muted: #5f6670;
      --border: #dedcd5; --accent: #c2410c; --accent-soft: #fdebe1; --code-bg: #f3f2ee;
      --row-alt: #fafaf8; --scroll-thumb: #b9b6ad; --scroll-track: #ecebe6;
      color-scheme: light;
    }}
    @media (prefers-color-scheme: dark) {{
      :root:not([data-theme="light"]) {{
        --bg: #17181b; --panel: #1d1f23; --side: #141518; --text: #e6e6e3; --muted: #9aa0a8;
        --border: #2f3238; --accent: #fb923c; --accent-soft: #3a2518; --code-bg: #24262b;
        --row-alt: #212328; --scroll-thumb: #4a4e56; --scroll-track: #1d1f23;
        color-scheme: dark;
      }}
    }}
    :root[data-theme="dark"] {{
      --bg: #17181b; --panel: #1d1f23; --side: #141518; --text: #e6e6e3; --muted: #9aa0a8;
      --border: #2f3238; --accent: #fb923c; --accent-soft: #3a2518; --code-bg: #24262b;
      --row-alt: #212328; --scroll-thumb: #4a4e56; --scroll-track: #1d1f23;
      color-scheme: dark;
    }}
    * {{ box-sizing: border-box; }}
    html, body {{ height: 100%; margin: 0; }}
    body {{
      background: var(--bg); color: var(--text); overflow: hidden;
      font: 15px/1.7 "Segoe UI", "Malgun Gothic", "Apple SD Gothic Neo", system-ui, sans-serif;
      display: grid; grid-template-columns: 320px 1fr; grid-template-rows: 100%;
    }}
    /* ---------- sidebar ---------- */
    #sidebar {{
      background: var(--side); border-right: 1px solid var(--border);
      display: flex; flex-direction: column; min-height: 0;
    }}
    .brand {{ padding: 20px 20px 12px; border-bottom: 1px solid var(--border); }}
    .brand h1 {{ font-size: 17px; margin: 0; line-height: 1.35; }}
    .brand p {{ margin: 4px 0 0; color: var(--muted); font-size: 12.5px; }}
    .search {{ padding: 12px 16px; border-bottom: 1px solid var(--border); }}
    .search input {{
      width: 100%; padding: 7px 10px; border-radius: 6px; border: 1px solid var(--border);
      background: var(--panel); color: var(--text); font: inherit; font-size: 13px;
    }}
    #nav {{ overflow-y: auto; flex: 1; padding: 8px 8px 24px; }}
    #nav ul {{ list-style: none; margin: 0; padding: 0; }}
    .chapter-link {{
      display: flex; gap: 10px; align-items: baseline; padding: 7px 10px; border-radius: 6px;
      color: var(--text); text-decoration: none; font-size: 14px; line-height: 1.4;
    }}
    .chapter-link:hover {{ background: var(--accent-soft); }}
    .chapter-link.active {{ background: var(--accent-soft); color: var(--accent); font-weight: 600; }}
    .chapter-link .num {{ font-variant-numeric: tabular-nums; color: var(--muted); font-size: 12px; min-width: 18px; }}
    .chapter-link.active .num {{ color: var(--accent); }}
    .subtoc {{ display: none; margin: 2px 0 8px 28px !important; border-left: 1px solid var(--border); }}
    .subtoc.open {{ display: block; }}
    .subtoc a {{
      display: block; padding: 3px 10px; color: var(--muted); text-decoration: none;
      font-size: 12.8px; line-height: 1.45; border-left: 2px solid transparent; margin-left: -1px;
    }}
    .subtoc a.h3 {{ padding-left: 22px; font-size: 12.3px; }}
    .subtoc a:hover {{ color: var(--text); }}
    .subtoc a.current {{ color: var(--accent); border-left-color: var(--accent); }}
    .side-foot {{ padding: 10px 16px; border-top: 1px solid var(--border); display: flex; gap: 8px; }}
    .side-foot button {{
      flex: 1; padding: 6px; border-radius: 6px; border: 1px solid var(--border);
      background: var(--panel); color: var(--text); font: inherit; font-size: 12.5px; cursor: pointer;
    }}
    /* ---------- main ---------- */
    #main {{ overflow-y: scroll; min-height: 0; scroll-behavior: smooth; }}
    #main::-webkit-scrollbar {{ width: 12px; }}
    #main::-webkit-scrollbar-track {{ background: var(--scroll-track); }}
    #main::-webkit-scrollbar-thumb {{ background: var(--scroll-thumb); border-radius: 6px; border: 3px solid var(--scroll-track); }}
    #nav::-webkit-scrollbar {{ width: 8px; }}
    #nav::-webkit-scrollbar-thumb {{ background: var(--scroll-thumb); border-radius: 4px; }}
    #main {{ scrollbar-color: var(--scroll-thumb) var(--scroll-track); }}
    .chapter {{
      max-width: 1040px; margin: 0 auto; padding: 40px 56px 120px;
    }}
    .pager {{
      max-width: 1040px; margin: -80px auto 60px; padding: 0 56px; display: flex; justify-content: space-between; gap: 16px;
    }}
    .pager a {{
      flex: 1; border: 1px solid var(--border); border-radius: 8px; padding: 12px 16px; text-decoration: none;
      color: var(--text); background: var(--panel); font-size: 14px;
    }}
    .pager a small {{ display: block; color: var(--muted); font-size: 12px; }}
    .pager a.next {{ text-align: right; }}
    .pager a:hover {{ border-color: var(--accent); }}
    .chapter h1 {{ font-size: 28px; line-height: 1.3; margin: 0 0 16px; padding-bottom: 14px; border-bottom: 2px solid var(--accent); }}
    .chapter h2 {{ font-size: 21px; margin: 44px 0 12px; padding-bottom: 6px; border-bottom: 1px solid var(--border); scroll-margin-top: 20px; }}
    .chapter h3 {{ font-size: 17px; margin: 30px 0 8px; scroll-margin-top: 20px; }}
    .chapter h4 {{ font-size: 15px; margin: 22px 0 6px; }}
    .chapter p, .chapter li {{ max-width: 80ch; }}
    .chapter a {{ color: var(--accent); }}
    .chapter blockquote {{
      margin: 16px 0; padding: 10px 16px; border-left: 3px solid var(--accent);
      background: var(--accent-soft); border-radius: 0 6px 6px 0; color: var(--text);
    }}
    .chapter blockquote p {{ margin: 4px 0; }}
    .chapter code {{
      font-family: "Cascadia Code", Consolas, "D2Coding", monospace; font-size: 0.88em;
      background: var(--code-bg); padding: 1px 5px; border-radius: 4px; word-break: break-word;
    }}
    .chapter pre {{
      background: var(--code-bg); border: 1px solid var(--border); border-radius: 8px;
      padding: 14px 16px; overflow-x: auto; line-height: 1.5;
    }}
    .chapter pre code {{ background: none; padding: 0; font-size: 13px; word-break: normal; }}
    .chapter pre.mermaid {{ background: var(--panel); text-align: center; }}
    .table-wrap {{ overflow-x: auto; margin: 14px 0; border: 1px solid var(--border); border-radius: 8px; }}
    .chapter table {{ border-collapse: collapse; width: 100%; font-size: 13.5px; line-height: 1.5; }}
    .chapter th, .chapter td {{ padding: 7px 10px; border-bottom: 1px solid var(--border); text-align: left; vertical-align: top; }}
    .chapter th {{ background: var(--side); font-weight: 600; position: sticky; top: 0; }}
    .chapter tr:nth-child(even) td {{ background: var(--row-alt); }}
    .chapter tr:last-child td {{ border-bottom: none; }}
    .chapter hr {{ border: none; border-top: 1px solid var(--border); margin: 32px 0; }}
    mark {{ background: #fde68a; color: inherit; border-radius: 2px; }}
    #menuBtn {{ display: none; }}
    @media (max-width: 860px) {{
      body {{ grid-template-columns: 1fr; }}
      #sidebar {{ position: fixed; inset: 0 20% 0 0; z-index: 10; transform: translateX(-100%); transition: transform .2s; }}
      body.menu-open #sidebar {{ transform: none; box-shadow: 0 0 40px rgba(0,0,0,.3); }}
      #menuBtn {{
        display: block; position: fixed; top: 10px; left: 10px; z-index: 11; padding: 6px 10px;
        border-radius: 6px; border: 1px solid var(--border); background: var(--panel); color: var(--text);
      }}
      .chapter {{ padding: 56px 16px 100px; }}
      .pager {{ padding: 0 16px; }}
    }}
    </style>
    </head>
    <body>
    <button id="menuBtn" aria-label="목차">☰ 목차</button>
    <aside id="sidebar">
      <div class="brand">
        <h1>{html.escape(title)}</h1>
        <p>{html.escape(subtitle)}</p>
      </div>
      <div class="search"><input id="search" type="search" placeholder="현재 장에서 찾기 (Enter: 다음)"></div>
      <nav id="nav"><ul>{nav_items}</ul></nav>
      <div class="side-foot">
        <button id="themeBtn">테마 전환</button>
        <button id="topBtn">맨 위로</button>
      </div>
    </aside>
    <main id="main">
    {articles}
    <div class="pager" id="pager"></div>
    </main>
    <script>{mermaid_js}</script>
    <script>
    const chapters = {json.dumps([[cid, short_title(cid, t)] for cid, t, _ in chapters], ensure_ascii=False)};
    const main = document.getElementById('main');
    let current = null, rendered = new Set(), spyHeads = [];

    function isDark() {{
      const t = document.documentElement.dataset.theme;
      return t ? t === 'dark' : matchMedia('(prefers-color-scheme: dark)').matches;
    }}
    function initMermaid() {{
      mermaid.initialize({{ startOnLoad: false, theme: isDark() ? 'dark' : 'default', securityLevel: 'loose', flowchart: {{ useMaxWidth: true }} }});
    }}
    async function renderMermaid(art) {{
      if (rendered.has(art.id)) return;
      rendered.add(art.id);
      const nodes = art.querySelectorAll('pre.mermaid');
      nodes.forEach(n => {{ if (!n.dataset.src) n.dataset.src = n.textContent; }});
      try {{ await mermaid.run({{ nodes }}); }} catch (e) {{ console.warn(e); }}
    }}

    function buildToc(cid) {{
      const ul = document.getElementById('toc-' + cid);
      if (ul.dataset.built) return;
      ul.dataset.built = '1';
      document.getElementById(cid).querySelectorAll('h2, h3').forEach(h => {{
        const a = document.createElement('a');
        a.href = '#' + h.id;
        a.textContent = h.textContent;
        a.className = h.tagName.toLowerCase();
        a.dataset.target = h.id;
        const li = document.createElement('li'); li.appendChild(a); ul.appendChild(li);
      }});
    }}

    function show(cid, anchor) {{
      if (!document.getElementById(cid)) cid = chapters[0][0];
      if (current !== cid) {{
        document.querySelectorAll('.chapter').forEach(a => a.hidden = a.id !== cid);
        document.querySelectorAll('.chapter-link').forEach(a => a.classList.toggle('active', a.dataset.ch === cid));
        document.querySelectorAll('.subtoc').forEach(u => u.classList.toggle('open', u.id === 'toc-' + cid));
        buildToc(cid);
        current = cid;
        const art = document.getElementById(cid);
        spyHeads = [...art.querySelectorAll('h2, h3')];
        renderMermaid(art);
        const i = chapters.findIndex(c => c[0] === cid);
        const prev = chapters[i - 1], next = chapters[i + 1];
        document.getElementById('pager').innerHTML =
          (prev ? `<a href="#${{prev[0]}}"><small>← 이전 장</small>${{prev[0].slice(2)}}. ${{prev[1]}}</a>` : '<span style="flex:1"></span>') +
          (next ? `<a class="next" href="#${{next[0]}}"><small>다음 장 →</small>${{next[0].slice(2)}}. ${{next[1]}}</a>` : '<span style="flex:1"></span>');
        clearMarks();
        main.style.scrollBehavior = 'auto';
        main.scrollTop = 0;
        main.style.scrollBehavior = '';
        document.getElementById('search').value = '';
        document.querySelector('.chapter-link.active')?.scrollIntoView({{ block: 'nearest' }});
      }}
      if (anchor) {{
        const el = document.getElementById(anchor);
        if (el) el.scrollIntoView({{ behavior: 'smooth', block: 'start' }});
      }}
      document.body.classList.remove('menu-open');
      spy();
    }}

    function route() {{
      const h = decodeURIComponent(location.hash.slice(1));
      if (!h) return show(chapters[0][0]);
      const m = h.match(/^(ch\\d\\d)(-.*)?$/);
      if (m) show(m[1], m[2] ? h : null); else show(chapters[0][0]);
    }}
    addEventListener('hashchange', route);

    function spy() {{
      if (!spyHeads.length) return;
      const top = main.getBoundingClientRect().top + 80;
      let cur = spyHeads[0];
      for (const h of spyHeads) {{ if (h.getBoundingClientRect().top <= top) cur = h; else break; }}
      document.querySelectorAll('.subtoc a.current').forEach(a => a.classList.remove('current'));
      const link = document.querySelector(`.subtoc a[data-target="${{CSS.escape(cur.id)}}"]`);
      if (link) {{ link.classList.add('current'); link.scrollIntoView({{ block: 'nearest' }}); }}
    }}
    let spyTimer;
    main.addEventListener('scroll', () => {{ clearTimeout(spyTimer); spyTimer = setTimeout(spy, 50); }});

    // ---- search within the open chapter ----
    let marks = [], markIdx = -1, lastQuery = '';
    function clearMarks() {{
      marks.forEach(m => {{ const t = document.createTextNode(m.textContent); m.replaceWith(t); t.parentNode.normalize(); }});
      marks = []; markIdx = -1; lastQuery = '';
    }}
    function doSearch(q) {{
      clearMarks();
      if (q.length < 2) return;
      const art = document.getElementById(current);
      const walker = document.createTreeWalker(art, NodeFilter.SHOW_TEXT, {{
        acceptNode: n => n.parentElement.closest('pre.mermaid, svg') ? NodeFilter.FILTER_REJECT : NodeFilter.FILTER_ACCEPT
      }});
      const lower = q.toLowerCase(), hits = [];
      while (walker.nextNode()) if (walker.currentNode.nodeValue.toLowerCase().includes(lower)) hits.push(walker.currentNode);
      hits.forEach(node => {{
        const parts = node.nodeValue.split(new RegExp('(' + q.replace(/[.*+?^${{}}()|[\\]\\\\]/g, '\\\\$&') + ')', 'i'));
        const frag = document.createDocumentFragment();
        parts.forEach((p, i) => {{
          if (i % 2) {{ const m = document.createElement('mark'); m.textContent = p; marks.push(m); frag.appendChild(m); }}
          else if (p) frag.appendChild(document.createTextNode(p));
        }});
        node.replaceWith(frag);
      }});
      lastQuery = q;
    }}
    const search = document.getElementById('search');
    search.addEventListener('keydown', e => {{
      if (e.key !== 'Enter') return;
      const q = search.value.trim();
      if (q !== lastQuery) doSearch(q);
      if (!marks.length) return;
      markIdx = (markIdx + 1) % marks.length;
      marks[markIdx].scrollIntoView({{ block: 'center' }});
      marks.forEach((m, i) => m.style.outline = i === markIdx ? '2px solid var(--accent)' : '');
    }});

    document.getElementById('topBtn').onclick = () => main.scrollTo({{ top: 0 }});
    document.getElementById('menuBtn').onclick = () => document.body.classList.toggle('menu-open');
    document.getElementById('themeBtn').onclick = async () => {{
      document.documentElement.dataset.theme = isDark() ? 'light' : 'dark';
      try {{ localStorage.setItem('fn-theme', document.documentElement.dataset.theme); }} catch (e) {{}}
      // Re-render diagrams in the new theme.
      initMermaid();
      document.querySelectorAll('pre.mermaid[data-src]').forEach(n => {{ n.removeAttribute('data-processed'); n.innerHTML = ''; n.textContent = n.dataset.src; }});
      rendered.clear();
      await renderMermaid(document.getElementById(current));
    }};
    try {{ const t = localStorage.getItem('fn-theme'); if (t) document.documentElement.dataset.theme = t; }} catch (e) {{}}
    initMermaid();
    route();
    </script>
    </body>
    </html>
    """

    open(out_path, "w", encoding="utf-8").write(page)
    print(f"[report] {out_path} ({os.path.getsize(out_path) / 1024:.0f} KB, {len(chapters)}장)")
    return out_path
