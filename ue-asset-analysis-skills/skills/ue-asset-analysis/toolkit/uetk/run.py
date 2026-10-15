"""Building the workspace and running the dump passes."""
import glob
import json
import os
import subprocess
import time

from . import engine


def _log_path(cfg, name):
    d = os.path.join(cfg["ws"], "Saved", "uetk")
    os.makedirs(d, exist_ok=True)
    return os.path.join(d, name)


def _unlock_plugin_binaries(ws):
    # A previous editor/commandlet may still hold the DLL; renaming a locked file works on Windows, deleting does not.
    for f in glob.glob(os.path.join(ws, "Plugins", "GraphDumper", "Binaries", "Win64", "*")):
        if f.endswith(".old"):
            try:
                os.remove(f)
            except OSError:
                pass
        elif f.lower().endswith((".dll", ".pdb")):
            try:
                os.replace(f, f + f".{int(time.time())}.old")
            except OSError:
                pass


def build(cfg):
    _unlock_plugin_binaries(cfg["ws"])
    log = _log_path(cfg, "build.log")
    args = [engine.build_bat(cfg["engine_root"]), cfg["editor_target"], "Win64", "Development",
            f"-Project={cfg['uproject']}", "-WaitMutex", "-NoHotReloadFromIDE"]
    print(f"[build] {cfg['editor_target']} (로그: {log})")
    with open(log, "w", encoding="utf-8", errors="replace") as f:
        rc = subprocess.call(args, stdout=f, stderr=subprocess.STDOUT)
    tail = open(log, encoding="utf-8", errors="replace").read().splitlines()
    errors = [l for l in tail if " error " in l or "error C" in l or "): error" in l]
    if rc != 0:
        print("\n".join(errors[:30] or tail[-30:]))
        raise SystemExit(f"[build] 실패 (exit {rc})")
    print("[build] 성공")


def dump(cfg, root=None, filter_=None, no_hlsl=False, no_maps=False):
    root = root or cfg["content_root"]
    out = os.path.join(cfg["ws"], "Dump")
    log = _log_path(cfg, "dump.log")
    args = [engine.editor_exe(cfg["engine_root"], cmd=True), cfg["uproject"], "-run=GraphDump",
            f"-Root={root}", f"-Out={out}", "-culture=en", "-unattended", "-nopause", "-nosplash",
            "-NoLiveCoding", "-stdout", "-FullStdOutLogOutput"]
    if filter_:
        args.append(f"-Filter={filter_}")
    if no_hlsl:
        args.append("-NoHLSL")
    if no_maps:
        args.append("-NoMaps")
    print(f"[dump] {root} -> {out} (로그: {log})")
    with open(log, "w", encoding="utf-8", errors="replace") as f:
        subprocess.call(args, stdout=f, stderr=subprocess.STDOUT)
    lines = [l for l in open(log, encoding="utf-8", errors="replace") if "LogGraphDump" in l]
    done = [l for l in lines if "GraphDump finished" in l]
    if not done:
        print("".join(lines[-10:]))
        raise SystemExit("[dump] 완료 메시지가 없습니다. 로그를 확인하세요.")
    print("[dump]", done[-1].split("Display:")[-1].strip())


def _kill_tree(proc):
    # The editor spawns ShaderCompileWorker children; take them down too.
    subprocess.call(["taskkill", "/F", "/T", "/PID", str(proc.pid)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def niagara(cfg, root=None, timeout_min=180, startup_min=20, nullrhi=True):
    """Compiles every NiagaraSystem under root in a ticking editor and dumps the generated HLSL.

    Returns True on success. Runs with -nullrhi by default: HLSL translation needs no renderer, and skipping it avoids
    compiling thousands of global/default-material shaders on a cold engine DDC (which can stall startup for hours).
    """
    root = root or cfg["content_root"]
    manifest = os.path.join(cfg["ws"], "Dump", "manifest.json")
    if os.path.isfile(manifest):
        systems = [a for a in json.load(open(manifest, encoding="utf-8")) if a["class"].endswith(".NiagaraSystem")]
        if not systems:
            print("[niagara] NiagaraSystem 이 없어 건너뜁니다.")
            return True
        print(f"[niagara] 시스템 {len(systems)}개 컴파일 → HLSL{'' if nullrhi else ' (에디터 창이 잠시 열립니다)'}")
    out = os.path.join(cfg["ws"], "Dump").replace("\\", "/")
    log = _log_path(cfg, "niagara.log")
    if os.path.exists(log):
        os.remove(log)
    args = [engine.editor_exe(cfg["engine_root"]), cfg["uproject"], "/Engine/Maps/Entry", "-culture=en",
            "-unattended", "-nosplash", "-NoLiveCoding", "-NoSound",
            f"-ExecCmds=GraphDump.NiagaraHLSL {root} {out} Quit", "-log", f"-abslog={log}"]
    if nullrhi:
        args.append("-nullrhi")
    proc = subprocess.Popen(args)
    start, finished_at, last_count = time.time(), None, -1
    while proc.poll() is None:
        time.sleep(5)
        text = open(log, encoding="utf-8", errors="replace").read() if os.path.exists(log) else ""
        started = "NiagaraHLSL: " in text
        count = text.count("NiagaraHLSL: [")
        if count != last_count and started:
            print(f"[niagara] 진행 {count}개")
            last_count = count
        if not started and time.time() - start > startup_min * 60:
            _kill_tree(proc)
            pending = [l for l in text.splitlines() if "Shaders left" in l or "Hung shadermap" in l][-1:]
            print(f"[niagara] 에디터가 {startup_min}분 안에 시작을 끝내지 못해 중단했습니다. " +
                  ("셰이더 컴파일 대기: " + pending[0].split("]")[-1].strip() if pending else f"로그: {log}"))
            return False
        if "NiagaraHLSL finished" in text and finished_at is None:
            finished_at = time.time()
        if finished_at and time.time() - finished_at > 120:
            _kill_tree(proc)  # finished but the editor did not exit
        if time.time() - start > timeout_min * 60:
            _kill_tree(proc)
            print(f"[niagara] 전체 시간 초과({timeout_min}분). 로그: {log}")
            return False
    text = open(log, encoding="utf-8", errors="replace").read() if os.path.exists(log) else ""
    count, timeouts = text.count("NiagaraHLSL: ["), text.count(" TIMEOUT")
    print(f"[niagara] {count}개 덤프, 타임아웃 {timeouts}개")
    return count > 0 and "NiagaraHLSL finished" in text
