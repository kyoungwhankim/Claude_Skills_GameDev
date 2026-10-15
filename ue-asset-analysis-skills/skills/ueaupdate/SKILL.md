---
name: ueaupdate
description: 설치된 ue-asset-analysis 스킬(툴킷 포함)을 GitHub 최신 버전으로 업데이트한다. "/ueaupdate", "ue-asset-analysis 업데이트" 요청에서 트리거.
disable-model-invocation: true
---

# /ueaupdate — ue-asset-analysis 스킬 업데이트

이 스킬 폴더의 `scripts/update.bat`을 실행한다. 스크립트가 GitHub(`repo.cfg`에 적힌 저장소)에서 최신 버전을 받아 설치된 스킬과 툴킷을 그 자리에서 바꾼다. 백업은 남기지 않는다. 로컬 저장소 폴더는 필요 없다.

분석 워크스페이스(`uetk --out` 폴더)와 덤프 결과는 스킬 폴더 밖에 있으므로 업데이트의 영향을 받지 않는다.

## 1. 실행

Bash 도구로 실행한다.
```
D="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills"
MSYS_NO_PATHCONV=1 cmd /c "$(cygpath -w "$D/ueaupdate/scripts/update.bat")" /quiet
```
- `/quiet`를 반드시 붙인다. 없으면 키 입력을 기다리며 멈춘다.
- 인터넷(GitHub) 접속이 필요하다. git이 있으면 git으로, 없으면 ZIP으로 받는다.

## 2. 결과 알리기

| 종료 코드 | 사용자에게 |
|---|---|
| 0 | `이전 -> 새 버전`을 알리고 "Claude Code를 새로 시작하면 적용된다"고 말한다. 덤프 플러그인 소스(`toolkit\plugin\GraphDumper`)가 바뀌었으면, 기존 워크스페이스는 플러그인을 다시 복사하고 `uetk build`를 해야 반영된다고 한 줄로 알린다 |
| 1 | `[ERROR]` 줄을 그대로 보여 주고 원인을 설명한다. 다운로드 실패면 네트워크나 사내 프록시를 의심한다 |
| 2 | 설치돼 있지 않다. 저장소를 받아 `ue-asset-analysis-skills\install.bat`을 실행하거나, 저장소 폴더를 Claude Code로 열고 `/ueainstall`을 쓰라고 안내한다 |
