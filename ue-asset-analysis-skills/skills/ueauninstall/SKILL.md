---
name: ueauninstall
description: 설치된 ue-asset-analysis 스킬 세트(/ue-asset-analysis, /ueaupdate, /ueauninstall)를 제거한다. Windows 휴지통으로 보내고 스킬 폴더에는 아무것도 남기지 않는다. "/ueauninstall", "ue-asset-analysis 삭제" 요청에서 트리거.
disable-model-invocation: true
---

# /ueauninstall — ue-asset-analysis 스킬 제거

이 스킬 폴더의 `scripts/uninstall.bat`을 실행한다. 스킬 폴더들(툴킷 포함)을 Windows 휴지통으로 보내고, 스킬 폴더 안에는 백업을 남기지 않는다. 확인 창을 띄우지 않고 바로 실행한다. 사용자가 명시적으로 요청했다.

분석 워크스페이스(`uetk --out` 폴더)와 덤프 결과는 스킬 폴더 밖에 있어서 지우지 않는다.

## 1. 실행

```
D="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
MSYS_NO_PATHCONV=1 cmd /c "$(cygpath -w "$D/ueauninstall/scripts/uninstall.bat")" /quiet
```

## 2. 결과 알리기

- 제거한 스킬을 알리고, 휴지통에서 되살릴 수 있다고 한 줄로 말한다.
- "Claude Code를 새로 시작하면 명령어 목록에서 사라진다"고 알린다.
- 분석 워크스페이스는 그대로 남아 있으니, 필요 없으면 직접 지우라고 안내한다.
- 다시 설치하려면 저장소를 받아 `ue-asset-analysis-skills\install.bat`을 실행하거나 `/ueainstall`을 쓰면 된다고 안내한다.
- `[ERROR]`가 나오면 그 줄을 보여 주고, 해당 폴더를 사용 중인 프로그램(탐색기, 에디터, 실행 중인 uetk)이 있는지 확인하라고 안내한다.
