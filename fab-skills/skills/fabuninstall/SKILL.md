---
name: fabuninstall
description: 설치된 fab 스킬 세트(/fab, /fabfilterupdate, /fabupdate, /fabupdateforce, /fabuninstall)를 제거한다. 지우지 않고 _backup으로 옮긴다. "/fabuninstall", "fab 스킬 삭제" 요청에서 트리거.
disable-model-invocation: true
---

# /fabuninstall — fab 스킬 세트 제거

이 스킬 폴더의 `scripts/uninstall.bat`을 실행한다. 확인 창을 띄우지 않고 바로 실행한다. 사용자가 명시적으로 요청했고, 지우지 않고 백업으로 옮기기 때문이다.

## 1. 실행

```
D="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
MSYS_NO_PATHCONV=1 cmd /c "$(cygpath -w "$D/fabuninstall/scripts/uninstall.bat")" /quiet
```

## 2. 결과 알리기

- 제거한 스킬과 백업 위치(`_backup\<날짜-시각>-uninstalled`)를 알린다.
- "Claude Code를 새로 시작하면 명령어 목록에서 사라진다"고 알린다.
- 다시 설치하려면 저장소를 받아 `fab-skills\install.bat`을 실행하거나 `/fabinstall`을 쓰면 된다고 안내한다.
- 백업까지 완전히 지우는 일은 하지 않는다. 사용자가 원하면 `_backup` 폴더를 직접 지우라고 안내한다.
