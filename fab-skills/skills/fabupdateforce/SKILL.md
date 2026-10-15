---
name: fabupdateforce
description: fab 스킬 세트를 GitHub 최신 버전으로 강제 업데이트한다. /fabupdate와 달리 사용자가 고친 filters.md 같은 유지 대상 파일까지 모두 저장소 버전으로 덮어쓴다(백업 없음). "/fabupdateforce", "fab 스킬 강제 업데이트", "filters.md 초기화" 요청에서 트리거.
disable-model-invocation: true
---

# /fabupdateforce — fab 스킬 세트 강제 업데이트

`/fabupdate`와 같은 스크립트를 `/force`를 붙여 실행한다. `preserve.txt`에 적힌 파일(예: `fab/reference/filters.md`)도 사용자가 고쳤는지와 상관없이 저장소 버전으로 바뀐다. **백업은 남기지 않는다.** 사용자가 고친 내용은 되돌릴 수 없게 사라진다.

## 1. 실행

확인 창을 띄우지 않고 바로 실행한다. 사용자가 강제 업데이트를 명시적으로 요청했다.
```
D="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
MSYS_NO_PATHCONV=1 cmd /c "$(cygpath -w "$D/fabupdate/scripts/update.bat")" /quiet /force
```

## 2. 결과 알리기

| 종료 코드 | 사용자에게 |
|---|---|
| 0 | `이전 -> 새 버전`을 알리고, 유지 대상 파일도 저장소 버전으로 바뀌었다고 한 줄로 말한다. "Claude Code를 새로 시작하면 적용된다" |
| 1 | `[ERROR]` 줄을 보여 주고 원인을 설명한다 |
| 2 | 설치돼 있지 않다. `fab-skills\install.bat` 또는 `/fabinstall`을 안내한다 |
