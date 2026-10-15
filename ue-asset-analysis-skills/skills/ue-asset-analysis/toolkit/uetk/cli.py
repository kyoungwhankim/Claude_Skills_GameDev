"""uetk — Unreal Engine asset analysis toolkit (Blueprint / Material / Niagara as text)."""
import argparse
import re
import os
import shutil
import subprocess
import sys

from . import engine, workspace

TOOLKIT = workspace.TOOLKIT


def cmd_engines(a):
    for v, p in engine.installed_engines().items():
        print(f"{v:6} {p}")


def cmd_doctor(a):
    ok = lambda b: "OK " if b else "-- "
    engines = engine.installed_engines()
    print(ok(engines), "Unreal Engine:", ", ".join(engines) or "없음")
    vswhere = os.path.expandvars(r"%ProgramFiles(x86)%\Microsoft Visual Studio\Installer\vswhere.exe")
    vs = subprocess.run([vswhere, "-latest", "-requires", "Microsoft.VisualStudio.Component.VC.Tools.x86.x64", "-property", "displayName"],
                        capture_output=True, text=True).stdout.strip() if os.path.exists(vswhere) else ""
    print(ok(vs), "Visual Studio C++:", vs or "없음 (덤프 플러그인 빌드에 필요)")
    for mod, why in (("markdown", "HTML 보고서"), ("html2text", "docs 수집"), ("yt_dlp", "유튜브 자막(선택)")):
        try:
            __import__(mod)
            print(ok(True), f"python {mod}")
        except ImportError:
            print(ok(False), f"python {mod} — {why}: python -m pip install {mod.replace('_', '-')}")
    dot = shutil.which("dot") or os.path.exists(r"C:\Program Files\Graphviz\bin\dot.exe")
    print(ok(dot), "Graphviz (의존성 그래프 svg, 선택)")
    print(ok(os.path.exists(r"C:\Program Files\RenderDoc\renderdoccmd.exe")), "RenderDoc (프레임 캡처, 선택)")
    # The toolkit ships inside the skill folder: <skills>/ue-asset-analysis/toolkit
    skill = os.path.join(os.path.dirname(TOOLKIT), "SKILL.md")
    print(ok(os.path.exists(skill)), "Claude Code 스킬 ue-asset-analysis",
          "" if os.path.exists(skill) else "(저장소의 ue-asset-analysis-skills\\install.bat 으로 설치)")


def cmd_setup(a):
    if sum(bool(x) for x in (a.project, a.plugin, a.engine_plugin)) != 1:
        raise SystemExit("--project, --plugin, --engine-plugin 중 하나만 지정하세요.")
    if a.project:
        cfg = workspace.setup_project(a.project, a.out, a.engine)
    elif a.plugin:
        cfg = workspace.setup_plugin(a.plugin, a.out, a.engine)
    else:
        cfg = workspace.setup_engine_plugin(a.engine_plugin, a.out, a.engine)
    if a.title:
        cfg["title"] = a.title
        workspace.save(a.out, cfg)
    print(f"[setup] 완료: {a.out}  (엔진 {cfg['engine_root']}, 루트 {cfg['content_root']}, 타깃 {cfg['editor_target']})")
    return cfg


def _unmangle(path):
    # Git Bash (MSYS) rewrites "/Game/X" arguments into "C:/Program Files/Git/Game/X"; undo that.
    if not path:
        return path
    return re.sub(r"^[A-Za-z]:[/\\](?:Program Files[/\\])?Git(?=[/\\])", "", path).replace("\\", "/")


def _ws(a):
    return workspace.load(a.ws)


def cmd_build(a):
    from . import run
    run.build(_ws(a))


def cmd_dump(a):
    from . import run
    run.dump(_ws(a), _unmangle(a.root), _unmangle(a.filter), a.no_hlsl, a.no_maps)


def cmd_niagara(a):
    from . import run
    if not run.niagara(_ws(a), _unmangle(a.root), a.timeout, a.startup_timeout, not a.with_rhi):
        raise SystemExit(1)


def cmd_index(a):
    from . import index
    index.build(_ws(a))


def cmd_vars(a):
    from . import bpvars
    bpvars.build(_ws(a), [_unmangle(p) for p in a.packages])


def cmd_brief(a):
    cfg = _ws(a)
    tpl = open(os.path.join(TOOLKIT, "templates", "AGENT_BRIEF.md"), encoding="utf-8").read()
    docs = [os.path.relpath(p, cfg["ws"]) for p in sorted(_glob(os.path.join(cfg["ws"], "Docs", "**", "*.md")))]
    text = (tpl.replace("{{TITLE}}", cfg.get("title", "")).replace("{{WS}}", cfg["ws"])
            .replace("{{ROOT}}", cfg["content_root"]).replace("{{ROOT_REL}}", _root_rel(cfg["content_root"]))
            .replace("{{DOCS}}", "\n".join(f"- {d}" for d in docs) or "- (수집된 문서 없음 — `uetk docs` 로 추가)"))
    path = os.path.join(cfg["ws"], "Analysis", "AGENT_BRIEF.md")
    os.makedirs(os.path.dirname(path), exist_ok=True)
    open(path, "w", encoding="utf-8").write(text)
    print(f"[brief] {path}")


def _glob(pattern):
    import glob
    return glob.glob(pattern, recursive=True)


def _root_rel(root):
    return root[len("/Game/"):] if root.startswith("/Game/") else ("" if root == "/Game" else root.lstrip("/"))


def cmd_report(a):
    from . import report
    cfg = _ws(a)
    title = a.title or f"{cfg.get('title', '')} 기능 분석 보고서"
    out = a.out or os.path.join(cfg["ws"], "Analysis", f"{cfg.get('title', 'report')}_분석보고서.html")
    report.build(os.path.join(cfg["ws"], "Analysis"), out, title, a.subtitle or "")


def cmd_docs(a):
    from . import docs
    cfg = _ws(a)
    if a.urls:
        docs.fetch(cfg, a.urls)
    if a.youtube:
        docs.youtube(cfg, a.youtube)


def cmd_exec(a):
    from . import remote
    code = open(a.file, encoding="utf-8").read() if a.file else " ".join(a.code)
    remote.run(_ws(a), code)


def cmd_clean(a):
    cfg = _ws(a)
    targets = ["Intermediate", "DerivedDataCache", os.path.join("Saved", "Autosaves"), os.path.join("Saved", "Crashes")]
    targets += [os.path.join("Plugins", "GraphDumper", "Intermediate")]
    if a.all:
        targets += ["Binaries", os.path.join("Plugins", "GraphDumper", "Binaries")]
    freed = 0
    for t in targets:
        path = os.path.join(cfg["ws"], t)
        if os.path.isdir(path):
            for dp, _, fs in os.walk(path):
                freed += sum(os.path.getsize(os.path.join(dp, f)) for f in fs if os.path.exists(os.path.join(dp, f)))
            shutil.rmtree(path, ignore_errors=True)
    print(f"[clean] {freed / 2**30:.1f} GB 정리" + ("" if a.all else " (Binaries 유지: 재빌드 없이 dump/niagara 가능)"))


def cmd_all(a):
    from . import index, run, bpvars
    cfg = cmd_setup(a)
    run.build(cfg)
    run.dump(cfg)
    if not a.no_niagara and not run.niagara(cfg):
        print("[all] 나이아가라 HLSL 단계 실패 — 나머지 단계는 계속합니다. 나중에 `uetk niagara --ws` 로 다시 시도하세요.")
    index.build(cfg)
    bpvars.build(cfg)
    a.ws = a.out
    cmd_brief(a)
    print(f"\n완료. 다음 단계: {a.out}\\Dump\\INDEX.md 를 보고 분석을 시작하세요 (Claude Code 에서는 ue-asset-analysis 스킬).")


def main(argv=None):
    p = argparse.ArgumentParser(prog="uetk", description=__doc__)
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("engines", help="설치된 언리얼 엔진 목록").set_defaults(fn=cmd_engines)
    sub.add_parser("doctor", help="필요 도구 점검").set_defaults(fn=cmd_doctor)

    def add_setup_args(s):
        s.add_argument("--project", help="분석할 .uproject (복사본을 만든다)")
        s.add_argument("--plugin", help="분석할 플러그인 폴더(.uplugin 포함) — 호스트 프로젝트를 만든다")
        s.add_argument("--engine-plugin", help="엔진에 설치된 플러그인 이름 — 호스트 프로젝트에서 활성화")
        s.add_argument("--engine", help="엔진 버전(5.8) 또는 엔진 루트 경로. 프로젝트는 EngineAssociation 사용")
        s.add_argument("--out", required=True, help="워크스페이스 폴더(비어 있어야 함)")
        s.add_argument("--title", help="보고서 등에 쓸 이름")

    s = sub.add_parser("setup", help="분석 워크스페이스 생성")
    add_setup_args(s)
    s.set_defaults(fn=cmd_setup)

    s = sub.add_parser("all", help="setup → build → dump → niagara → index → vars → brief 한 번에")
    add_setup_args(s)
    s.add_argument("--no-niagara", action="store_true", help="나이아가라 HLSL 패스 생략")
    s.set_defaults(fn=cmd_all)

    def ws_parser(name, help_, fn):
        s = sub.add_parser(name, help=help_)
        s.add_argument("--ws", default=".", help="워크스페이스 폴더 (기본: 현재 폴더)")
        s.set_defaults(fn=fn)
        return s

    ws_parser("build", "덤프 플러그인 포함 에디터 타깃 빌드", cmd_build)
    s = ws_parser("dump", "모든 에셋을 텍스트로 덤프 (헤드리스)", cmd_dump)
    s.add_argument("--root", help="콘텐츠 루트 (기본: 워크스페이스 설정)")
    s.add_argument("--filter", help="패키지 경로 부분 문자열")
    s.add_argument("--no-hlsl", action="store_true")
    s.add_argument("--no-maps", action="store_true")
    s = ws_parser("niagara", "나이아가라 시스템 컴파일 후 HLSL 덤프 (에디터 창 사용)", cmd_niagara)
    s.add_argument("--root")
    s.add_argument("--timeout", type=int, default=180, help="전체 제한 시간(분)")
    s.add_argument("--startup-timeout", type=int, default=20, help="에디터 시작 제한 시간(분)")
    s.add_argument("--with-rhi", action="store_true", help="-nullrhi 없이 실행 (기본은 렌더러 없이 실행)")
    ws_parser("index", "INDEX.md / 의존성 그래프 생성", cmd_index)
    s = ws_parser("vars", "블루프린트 변수표 생성 (Dump/vars)", cmd_vars)
    s.add_argument("packages", nargs="*", help="/Game/... 패키지 경로 (생략 시 모든 블루프린트)")
    s = ws_parser("clean", "빌드 중간 산출물·캐시 삭제 (덤프/분석 결과는 유지)", cmd_clean)
    s.add_argument("--all", action="store_true", help="Binaries 까지 삭제 (다시 쓰려면 uetk build 필요)")
    ws_parser("brief", "분석 에이전트 공통 브리프(Analysis/AGENT_BRIEF.md) 생성", cmd_brief)
    s = ws_parser("report", "Analysis/*.md → 사이드바형 단일 HTML", cmd_report)
    s.add_argument("--title")
    s.add_argument("--subtitle")
    s.add_argument("--out")
    s = ws_parser("docs", "참고 문서 수집 (웹 페이지 → md, 유튜브 자막)", cmd_docs)
    s.add_argument("urls", nargs="*")
    s.add_argument("--youtube", nargs="*", default=[])
    s = ws_parser("exec", "실행 중인 워크스페이스 에디터에서 Python 실행", cmd_exec)
    s.add_argument("code", nargs="*")
    s.add_argument("-f", "--file")

    a = p.parse_args(argv)
    a.fn(a)


if __name__ == "__main__":
    sys.exit(main())
