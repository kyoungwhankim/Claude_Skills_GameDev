"""Blueprint variable tables (name, type, category, tooltip, default) from .props.txt dumps, as Markdown."""
import glob
import json
import os
import re
import sys
from collections import defaultdict


def field(s, key):
    m = re.search(r'(?<![A-Za-z])' + key + r'=NSLOCTEXT\("[^"]*", "[^"]*", "((?:[^"\\]|\\.)*)"\)', s)
    if m:
        return m.group(1)
    m = re.search(r'(?<![A-Za-z])' + key + r'=(INVTEXT\("((?:[^"\\]|\\.)*)"\)|"((?:[^"\\]|\\.)*)"|[^,()]+)', s)
    if not m:
        return ""
    return m.group(2) if m.group(2) is not None else (m.group(3) if m.group(3) is not None else m.group(1))


def meta(s, key):
    m = re.search(r'\(DataKey="' + key + r'",DataValue="((?:[^"\\]|\\.)*)"\)', s)
    return m.group(1).replace("\\n", " ").replace('\\"', '"') if m else ""


def vtype(s):
    cat = field(s, "PinCategory")
    sub = re.search(r"PinSubCategoryObject=[^']*'([^']+)'", s)
    t = cat
    if sub:
        t += ":" + sub.group(1).rsplit(".", 1)[-1]
    elif field(s, "PinSubCategory"):
        t += ":" + field(s, "PinSubCategory")
    if "ContainerType=Array" in s:
        t = f"Array<{t}>"
    elif "ContainerType=Map" in s:
        t = f"Map<{t}>"
    elif "ContainerType=Set" in s:
        t = f"Set<{t}>"
    return t


def render(path):
    out = []
    print = lambda *a: out.append(" ".join(str(x) for x in a))  # noqa: A001
    lines = open(path, encoding="utf-8").read().splitlines()
    vars_, defaults, cur = [], {}, None
    for ln in lines:
        if ln.startswith("=== "):
            cur = ln
            continue
        m = re.match(r"\s+NewVariables\[\d+\] = (.*)", ln)
        if m:
            vars_.append(m.group(1))
            continue
        if cur and "Default__" in cur and "Default__SKEL_" not in cur:
            m = re.match(r"\s+([^ =]+) = (.*)", ln)
            if m:
                defaults[m.group(1)] = m.group(2)
    name = path.replace("\\", "/").rsplit("/", 1)[-1].replace(".props.txt", "")
    groups = defaultdict(list)
    for v in vars_:
        groups[field(v, "Category") or "Default"].append(v)
    print(f"## {name} 변수 ({len(vars_)}개)\n")
    for cat in sorted(groups, key=lambda c: (c.startswith("NONPUBLIC"), c)):
        print(f"### {cat} ({len(groups[cat])})\n")
        print("| 변수 | 타입 | 기본값(CDO 변경값) | 툴팁 |\n|---|---|---|---|")
        for v in groups[cat]:
            n = field(v, "VarName")
            d = defaults.get(n.replace(" ", "_"), defaults.get(n, ""))
            d = d or "(빈 값: False/None/0)"
            d = (d[:80] + "…") if len(d) > 80 else d
            tip = meta(v, "tooltip") or meta(v, "ToolTip")
            tip = (tip[:220] + "…") if len(tip) > 220 else tip
            cell = lambda x: x.replace("|", "\\|")
            print(f"| `{n}` | {cell(vtype(v))} | {cell(d)} | {cell(tip)} |")
        print()
    return "\n".join(out) + "\n"


def build(cfg, packages=None):
    """Writes Dump/vars/<Asset>.md for the given packages, or for every Blueprint-like asset with variables."""
    dump = os.path.join(cfg["ws"], "Dump")
    manifest = json.load(open(os.path.join(dump, "manifest.json"), encoding="utf-8"))
    if not packages:
        packages = [a["package"] for a in manifest if "Blueprint" in a["class"]]
    out_dir = os.path.join(dump, "vars")
    os.makedirs(out_dir, exist_ok=True)
    written = 0
    for pkg in packages:
        rel = pkg[len("/Game/"):] if pkg.startswith("/Game/") else pkg.lstrip("/")
        src = os.path.join(dump, "assets", rel + ".props.txt")
        if not os.path.isfile(src):
            print(f"[vars] 없음: {src}")
            continue
        md = render(src)
        if "NewVariables" not in open(src, encoding="utf-8").read():
            continue
        open(os.path.join(out_dir, pkg.rsplit("/", 1)[1] + ".md"), "w", encoding="utf-8").write(md)
        written += 1
    print(f"[vars] {written}개 → {out_dir}")
