"""Running Python inside a running Unreal Editor of the workspace (PythonScriptPlugin remote execution)."""
import os
import sys
import time

from . import engine


def run(cfg, code):
    mod_dir = engine.python_remote_module_dir(cfg["engine_root"])
    if not mod_dir:
        raise SystemExit("엔진에서 remote_execution.py 를 찾지 못했습니다.")
    sys.path.insert(0, mod_dir)
    import remote_execution as rex  # noqa: E402

    if "import unreal" not in code:
        code = "import unreal\n" + code
    hint = os.path.normcase(os.path.dirname(cfg["uproject"]))
    remote = rex.RemoteExecution()
    remote.start()
    try:
        node = None
        for _ in range(50):
            node = next((n for n in remote.remote_nodes
                         if os.path.normcase(os.path.normpath(n.get("project_root", ""))).startswith(hint)), None)
            if node:
                break
            time.sleep(0.1)
        if not node:
            raise SystemExit(f"이 워크스페이스의 에디터가 실행 중이 아닙니다. 발견된 노드: {[n.get('project_name') for n in remote.remote_nodes]}")
        remote.open_command_connection(node["node_id"])
        result = remote.run_command(code, unattended=True, exec_mode=rex.MODE_EXEC_FILE)
        for entry in result.get("output", []):
            text = entry.get("output", "")
            print(text, end="" if text.endswith("\n") else "\n")
        if not result.get("success"):
            raise SystemExit(f"실패: {result.get('result')}")
    finally:
        remote.stop()
