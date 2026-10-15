"""Locating installed Unreal Engine versions and their executables."""
import glob
import json
import os
import re

LAUNCHER_DAT = r"C:\ProgramData\Epic\UnrealEngineLauncher\LauncherInstalled.dat"
FALLBACK_DIRS = [r"C:\Program Files\Epic Games", r"D:\Program Files\Epic Games", r"D:\ProgramFiles\EpicGames", r"D:\Epic Games"]


def installed_engines():
    """Returns {"5.8": "C:\\Program Files\\Epic Games\\UE_5.8", ...}."""
    found = {}
    try:
        data = json.load(open(LAUNCHER_DAT, encoding="utf-8"))
        for item in data.get("InstallationList", []):
            m = re.fullmatch(r"UE_(\d+\.\d+)", item.get("AppName", ""))
            if m and os.path.isdir(item["InstallLocation"]):
                found[m.group(1)] = item["InstallLocation"]
    except (OSError, ValueError):
        pass
    for base in FALLBACK_DIRS:
        for d in glob.glob(os.path.join(base, "UE_*")):
            m = re.fullmatch(r"UE_(\d+\.\d+)", os.path.basename(d))
            if m and m.group(1) not in found and os.path.isdir(os.path.join(d, "Engine")):
                found[m.group(1)] = d
    return dict(sorted(found.items(), key=lambda kv: [int(x) for x in kv[0].split(".")]))


def resolve(version_or_path):
    """Accepts "5.8" or an engine root path; returns the engine root."""
    if version_or_path and os.path.isdir(os.path.join(version_or_path, "Engine")):
        return os.path.abspath(version_or_path)
    engines = installed_engines()
    if version_or_path in engines:
        return engines[version_or_path]
    raise SystemExit(f"엔진을 찾을 수 없습니다: {version_or_path!r}. 설치된 엔진: {', '.join(engines) or '없음'} (--engine 에 경로를 직접 줄 수도 있습니다)")


def build_bat(root):
    return os.path.join(root, "Engine", "Build", "BatchFiles", "Build.bat")


def editor_exe(root, cmd=False):
    return os.path.join(root, "Engine", "Binaries", "Win64", "UnrealEditor-Cmd.exe" if cmd else "UnrealEditor.exe")


def python_remote_module_dir(root):
    for sub in ("Experimental", ""):
        d = os.path.join(root, "Engine", "Plugins", sub, "PythonScriptPlugin", "Content", "Python")
        if os.path.isfile(os.path.join(d, "remote_execution.py")):
            return d
    return None


def engine_plugin_exists(root, name):
    return bool(glob.glob(os.path.join(root, "Engine", "Plugins", "**", f"{name}.uplugin"), recursive=True))
