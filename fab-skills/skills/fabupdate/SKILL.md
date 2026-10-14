---
name: fabupdate
description: 설치된 fab 스킬 세트(/fab, /fabfilterupdate 등)를 GitHub 최신 버전으로 업데이트한다. 사용자가 고친 filters.md 같은 유지 대상 파일은 그대로 둔다. "/fabupdate", "fab 스킬 업데이트" 요청에서 트리거.
disable-model-invocation: true
---

# /fabupdate — fab 스킬 세트 업데이트

이 스킬 폴더의 `scripts/update.bat`을 실행한다. 스크립트가 GitHub(`repo.cfg`에 적힌 저장소)에서 최신 fab-skills를 받아 설치된 스킬을 바꾼다. 로컬 저장소 폴더는 필요 없다.
사용자가 고친 유지 대상 파일(예: `fab/reference/filters.md`)은 유지된다. 그것까지 저장소 버전으로 덮어쓰려면 `/fabupdateforce`를 쓰라고 안내한다.

## 1. 실행

Bash 도구로 실행한다.
```
D="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
MSYS_NO_PATHCONV=1 cmd /c "$(cygpath -w "$D/fabupdate/scripts/update.bat")" /quiet
```
- `/quiet`를 반드시 붙인다. 없으면 키 입력을 기다리며 멈춘다.
- 인터넷(GitHub) 접속이 필요하다. git이 있으면 git으로, 없으면 ZIP으로 받는다.

## 2. 결과 알리기

| 종료 코드 / 출력 | 사용자에게 |
|---|---|
| 0 | `이전 -> 새 버전`과 유지된 파일(`kept ...` 줄)을 요약하고, "Claude Code를 새로 시작하면 적용된다"고 알린다 |
| 출력에 `[CHECK]` | 사용자가 고친 파일을 새 버전도 바꿨다. 설치된 파일과 `_backup\<날짜-시각>\_new\` 아래 새 버전을 비교해 새 버전에만 있는 변경을 요약하고, 합칠지 묻는다. 합칠 때 사용자가 고친 내용은 지우지 않는다 |
| 1 | `[ERROR]` 줄을 그대로 보여 주고 원인을 설명한다. 다운로드 실패면 네트워크나 사내 프록시를 의심하고, `repo.cfg` 주소가 맞는지 확인한다 |
| 2 | 설치돼 있지 않다. 저장소를 받아 `fab-skills\install.bat`을 실행하거나, 저장소 폴더를 Claude Code로 열고 `/fabinstall`을 쓰라고 안내한다 |
