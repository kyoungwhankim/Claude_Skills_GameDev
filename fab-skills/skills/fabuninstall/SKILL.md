---
name: fabuninstall
description: 설치된 fab 스킬 세트(/fab, /fabfilterupdate, /fabupdate, /fabupdateforce, /fabuninstall)를 제거한다. Windows 휴지통으로 보내고 스킬 폴더에는 아무것도 남기지 않는다. "/fabuninstall", "fab 스킬 삭제" 요청에서 트리거.
disable-model-invocation: true
---

# /fabuninstall — fab 스킬 세트 제거

이 스킬 폴더의 `scripts/uninstall.bat`을 실행한다. 스킬 폴더들을 Windows 휴지통으로 보내고, 스킬 폴더 안에는 백업을 남기지 않는다. 확인 창을 띄우지 않고 바로 실행한다. 사용자가 명시적으로 요청했다.

## 1. 실행

```
D="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
MSYS_NO_PATHCONV=1 cmd /c "$(cygpath -w "$D/fabuninstall/scripts/uninstall.bat")" /quiet
```

## 2. 결과 알리기

- 제거한 스킬을 알리고, 휴지통에서 되살릴 수 있다고 한 줄로 말한다.
- "Claude Code를 새로 시작하면 명령어 목록에서 사라진다"고 알린다.
- 다시 설치하려면 저장소를 받아 `fab-skills\install.bat`을 실행하거나 `/fabinstall`을 쓰면 된다고 안내한다.
- `[ERROR]`가 나오면 그 줄을 보여 주고, 해당 폴더를 사용 중인 프로그램(탐색기, 에디터)이 있는지 확인하라고 안내한다.
