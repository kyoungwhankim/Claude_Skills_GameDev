"""Creating an analysis workspace: a copy (or host) project with the GraphDumper plugin injected."""
import glob
import json
import os
import re
import shutil

from . import engine

TOOLKIT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PLUGIN_SRC = os.path.join(TOOLKIT, "plugin", "GraphDumper")
CONFIG = "uetk.json"
ANALYSIS_PLUGINS = ["PythonScriptPlugin", "EditorScriptingUtilities", "RenderDocPlugin", "GraphDumper"]
PY_REMOTE_INI = """
[/Script/PythonScriptPlugin.PythonScriptPluginSettings]
bRemoteExecution=True
bDeveloperMode=True
"""


def load(ws):
    path = os.path.join(ws, CONFIG)
    if not os.path.isfile(path):
        raise SystemExit(f"{ws} 는 uetk 워크스페이스가 아닙니다 ({CONFIG} 없음). 먼저 `uetk setup` 을 실행하세요.")
    cfg = json.load(open(path, encoding="utf-8"))
    cfg["ws"] = os.path.abspath(ws)
    return cfg


def save(ws, cfg):
    data = {k: v for k, v in cfg.items() if k != "ws"}
    json.dump(data, open(os.path.join(ws, CONFIG), "w", encoding="utf-8"), indent=2, ensure_ascii=False)


def _ignore(top):
    # Build products and caches are regenerated; root Binaries only (plugin Binaries may be precompiled-only).
    def fn(d, names):
        skip = {n for n in names if n in ("Saved", "Intermediate", "DerivedDataCache", ".vs", ".git", ".idea")}
        if os.path.abspath(d) == os.path.abspath(top):
            skip |= {n for n in names if n == "Binaries" or n.endswith((".sln", ".slnx"))}
        return skip
    return fn


def _ident(name):
    s = re.sub(r"\W", "", name)
    return s if s and not s[0].isdigit() else "P" + s


def _write_stub_module(ws, module):
    src = os.path.join(ws, "Source")
    os.makedirs(os.path.join(src, module), exist_ok=True)
    for kind, ttype in (("", "Game"), ("Editor", "Editor")):
        open(os.path.join(src, f"{module}{kind}.Target.cs"), "w", encoding="utf-8").write(
            f"""using UnrealBuildTool;

public class {module}{kind}Target : TargetRules
{{
	public {module}{kind}Target(TargetInfo Target) : base(Target)
	{{
		Type = TargetType.{ttype};
		DefaultBuildSettings = BuildSettingsVersion.Latest;
		IncludeOrderVersion = EngineIncludeOrderVersion.Latest;
		ExtraModuleNames.Add("{module}");
	}}
}}
""")
    open(os.path.join(src, module, f"{module}.Build.cs"), "w", encoding="utf-8").write(
        f"""using UnrealBuildTool;

public class {module} : ModuleRules
{{
	public {module}(ReadOnlyTargetRules Target) : base(Target)
	{{
		PCHUsage = PCHUsageMode.UseExplicitOrSharedPCHs;
		PublicDependencyModuleNames.AddRange(new string[] {{ "Core", "CoreUObject", "Engine" }});
	}}
}}
""")
    open(os.path.join(src, module, f"{module}.cpp"), "w", encoding="utf-8").write(
        f'#include "Modules/ModuleManager.h"\n\nIMPLEMENT_PRIMARY_GAME_MODULE(FDefaultGameModuleImpl, {module}, "{module}");\n')


def _editor_target(ws):
    targets = glob.glob(os.path.join(ws, "Source", "*Editor.Target.cs"))
    if not targets:
        raise SystemExit("Source/*Editor.Target.cs 를 찾지 못했습니다.")
    return os.path.basename(targets[0]).replace(".Target.cs", "")


def _patch_uproject(uproject, extra_plugins, ensure_module):
    data = json.load(open(uproject, encoding="utf-8-sig"))
    plugins = data.setdefault("Plugins", [])
    names = {p["Name"] for p in plugins}
    for name in extra_plugins:
        if name in names:
            for p in plugins:
                if p["Name"] == name:
                    p["Enabled"] = True
        else:
            plugins.append({"Name": name, "Enabled": True})
    if ensure_module and not data.get("Modules"):
        data["Modules"] = [{"Name": ensure_module, "Type": "Runtime", "LoadingPhase": "Default"}]
    json.dump(data, open(uproject, "w", encoding="utf-8"), indent="\t")


def _finish(ws, cfg, extra_plugins):
    uproject = cfg["uproject"]
    module = None
    if not glob.glob(os.path.join(ws, "Source", "*Editor.Target.cs")):
        module = _ident(os.path.splitext(os.path.basename(uproject))[0])
        _write_stub_module(ws, module)
    _patch_uproject(uproject, extra_plugins + ANALYSIS_PLUGINS, module)

    dst = os.path.join(ws, "Plugins", "GraphDumper")
    if os.path.isdir(os.path.join(dst, "Source")):
        shutil.rmtree(os.path.join(dst, "Source"))
    shutil.copytree(PLUGIN_SRC, dst, dirs_exist_ok=True)

    ini = os.path.join(ws, "Config", "DefaultEngine.ini")
    os.makedirs(os.path.dirname(ini), exist_ok=True)
    text = open(ini, encoding="utf-8-sig").read() if os.path.isfile(ini) else ""
    if "bRemoteExecution" not in text:
        open(ini, "a", encoding="utf-8").write(PY_REMOTE_INI)

    for d in ("Dump", "Docs", "Analysis/sections"):
        os.makedirs(os.path.join(ws, d), exist_ok=True)
    cfg["editor_target"] = _editor_target(ws)
    save(ws, cfg)
    cfg["ws"] = ws
    return cfg


def setup_project(src_uproject, out, engine_arg=None):
    src_uproject = os.path.abspath(src_uproject)
    src_dir = os.path.dirname(src_uproject)
    if os.path.exists(out) and os.listdir(out):
        raise SystemExit(f"출력 폴더가 비어 있지 않습니다: {out}")
    data = json.load(open(src_uproject, encoding="utf-8-sig"))
    root = engine.resolve(engine_arg or data.get("EngineAssociation", ""))
    print(f"[setup] 프로젝트 복사: {src_dir} -> {out}")
    shutil.copytree(src_dir, out, ignore=_ignore(src_dir))
    cfg = {
        "mode": "project", "source": src_uproject, "engine_root": root,
        "uproject": os.path.join(os.path.abspath(out), os.path.basename(src_uproject)),
        "content_root": "/Game", "title": os.path.splitext(os.path.basename(src_uproject))[0],
    }
    return _finish(os.path.abspath(out), cfg, [])


def _host_project(out, name, engine_arg, plugin_name):
    root = engine.resolve(engine_arg)
    version = next((v for v, p in engine.installed_engines().items() if os.path.normcase(p) == os.path.normcase(root)), engine_arg)
    os.makedirs(out, exist_ok=True)
    uproject = os.path.join(out, f"{name}.uproject")
    json.dump({"FileVersion": 3, "EngineAssociation": version, "Category": "", "Description": "uetk analysis host",
               "Plugins": [{"Name": plugin_name, "Enabled": True}], "TargetPlatforms": ["Windows"]},
              open(uproject, "w", encoding="utf-8"), indent="\t")
    return root, uproject


def setup_plugin(plugin_dir, out, engine_arg):
    plugin_dir = os.path.abspath(plugin_dir)
    upl = glob.glob(os.path.join(plugin_dir, "*.uplugin"))
    if not upl:
        raise SystemExit(f".uplugin 이 없습니다: {plugin_dir}")
    pname = os.path.splitext(os.path.basename(upl[0]))[0]
    meta = json.load(open(upl[0], encoding="utf-8-sig"))
    engine_arg = engine_arg or meta.get("EngineVersion", "")[:3]
    if os.path.exists(out) and os.listdir(out):
        raise SystemExit(f"출력 폴더가 비어 있지 않습니다: {out}")
    ws = os.path.abspath(out)
    root, uproject = _host_project(ws, _ident(pname) + "Host", engine_arg, pname)
    print(f"[setup] 플러그인 복사: {plugin_dir} -> {ws}\\Plugins\\{pname}")
    shutil.copytree(plugin_dir, os.path.join(ws, "Plugins", pname), ignore=_ignore(plugin_dir))
    if not meta.get("CanContainContent", False):
        print("[setup] 경고: 이 플러그인은 CanContainContent=false 입니다. 분석할 에셋이 없을 수 있습니다.")
    cfg = {"mode": "plugin", "source": plugin_dir, "engine_root": root, "uproject": uproject,
           "content_root": f"/{pname}", "title": pname}
    return _finish(ws, cfg, [])


def setup_engine_plugin(name, out, engine_arg):
    root = engine.resolve(engine_arg)
    if not engine.engine_plugin_exists(root, name):
        raise SystemExit(f"엔진에 {name}.uplugin 이 없습니다: {root}")
    if os.path.exists(out) and os.listdir(out):
        raise SystemExit(f"출력 폴더가 비어 있지 않습니다: {out}")
    ws = os.path.abspath(out)
    root, uproject = _host_project(ws, _ident(name) + "Host", engine_arg, name)
    cfg = {"mode": "engine-plugin", "source": name, "engine_root": root, "uproject": uproject,
           "content_root": f"/{name}", "title": name}
    return _finish(ws, cfg, [])
