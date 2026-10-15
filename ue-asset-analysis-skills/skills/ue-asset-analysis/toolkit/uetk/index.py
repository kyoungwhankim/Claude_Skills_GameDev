"""Dump/INDEX.md (inventory, hubs, logic assets per folder) and Dump/deps.dot/.svg from Dump/manifest.json."""
import json
import os
import shutil
import subprocess
from collections import Counter, defaultdict

LOGIC = {"Blueprint", "WidgetBlueprint", "AnimBlueprint", "NiagaraSystem", "NiagaraScript", "NiagaraEmitter", "Material",
         "MaterialFunction", "TextureRenderTarget2D", "NiagaraDataChannelAsset", "UserDefinedEnum", "UserDefinedStruct",
         "MaterialParameterCollection", "PCGGraph", "PCGGraphInstance", "DataTable", "ControlRigBlueprint", "StateTree"}
COLORS = {"Blueprint": "lightblue", "WidgetBlueprint": "lightcyan", "NiagaraSystem": "orange", "NiagaraScript": "gold",
          "Material": "palegreen", "MaterialFunction": "darkseagreen", "TextureRenderTarget2D": "pink",
          "NiagaraDataChannelAsset": "plum", "PCGGraph": "khaki"}
EXTS = (".props.txt", ".graph.txt", ".t3d", ".hlsl", ".niagara.hlsl")


def build(cfg):
    dump = os.path.join(cfg["ws"], "Dump")
    m = json.load(open(os.path.join(dump, "manifest.json"), encoding="utf-8"))
    root = cfg["content_root"].rstrip("/")
    pkgs = {a["package"]: a for a in m}
    cls = {a["package"]: a["class"].split(".")[-1] for a in m}
    internal = lambda p: p.startswith(root + "/")

    def files_for(pkg):
        rel = pkg[len("/Game/"):] if pkg.startswith("/Game/") else pkg.lstrip("/")
        return [e.lstrip(".") for e in EXTS if os.path.exists(os.path.join(dump, "assets", rel + e))]

    L = [f"# {cfg.get('title', '')} 에셋 덤프 인덱스", "", f"루트: `{root}` · 패키지 {len(m)}개", "", "## 클래스"]
    L += [f"- {c}: {n}" for c, n in Counter(cls.values()).most_common()]

    L += ["", "## 많이 참조되는 에셋 (내부 참조자 수)"]
    for n, p in sorted(((sum(internal(r) for r in a["referencers"]), a["package"]) for a in m), reverse=True)[:60]:
        if n:
            L.append(f"- {n:4d}  {p}  ({cls[p]})")

    L += ["", "## 로직 에셋과 의존 요약"]
    for p in sorted(pkgs):
        if cls[p] in ("Blueprint", "WidgetBlueprint", "AnimBlueprint", "NiagaraSystem", "PCGGraph") or cls[p].endswith("_C"):
            deps = [d for d in pkgs[p]["dependencies"] if internal(d)]
            kinds = Counter(cls.get(d, "?") for d in deps)
            L.append(f"- **{p}** ({cls[p]}) deps={len(deps)} " + ", ".join(f"{k}:{v}" for k, v in kinds.most_common()))

    by_folder = defaultdict(list)
    for p in sorted(pkgs):
        by_folder[p.rsplit("/", 1)[0]].append(p)
    L += ["", "## 폴더별 에셋"]
    for f in sorted(by_folder):
        L.append(f"\n### {f}")
        L += [f"- {p.rsplit('/', 1)[1]} — {cls[p]} — [{', '.join(files_for(p))}]" for p in by_folder[f]]
    open(os.path.join(dump, "INDEX.md"), "w", encoding="utf-8").write("\n".join(L) + "\n")

    dot = os.path.join(dump, "deps.dot")
    keep = lambda p: p in pkgs and cls[p] in LOGIC and "/Levels/" not in p
    with open(dot, "w", encoding="utf-8") as f:
        f.write('digraph deps {\n rankdir=LR; node [shape=box, style=filled, fontsize=9];\n')
        for p in pkgs:
            if keep(p):
                f.write(f' "{p}" [label="{p.rsplit("/", 1)[1]}\\n{cls[p]}", fillcolor="{COLORS.get(cls[p], "white")}"];\n')
        for p in pkgs:
            if keep(p):
                for d in pkgs[p]["dependencies"]:
                    if keep(d):
                        f.write(f' "{p}" -> "{d}";\n')
        f.write("}\n")
    exe = shutil.which("dot") or (r"C:\Program Files\Graphviz\bin\dot.exe" if os.path.exists(r"C:\Program Files\Graphviz\bin\dot.exe") else None)
    if exe:
        subprocess.call([exe, "-Tsvg", dot, "-o", dot[:-4] + ".svg"])
    print(f"[index] INDEX.md, deps.dot{' + deps.svg' if exe else ' (Graphviz 없음: svg 생략)'}")
