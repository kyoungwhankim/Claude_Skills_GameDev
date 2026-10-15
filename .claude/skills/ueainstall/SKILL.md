---
name: ueainstall
description: 이 저장소(Claude_Skills_GameDev)의 ue-asset-analysis 스킬 세트(툴킷 포함)를 사용자 Claude Code에 설치한다. 저장소 폴더를 열었을 때만 쓸 수 있다. "/ueainstall", "ue-asset-analysis 설치" 요청에서 트리거.
disable-model-invocation: true
---

# /ueainstall — ue-asset-analysis 스킬 세트 설치

저장소의 `ue-asset-analysis-skills/install.bat`을 실행한다. 이 스킬은 저장소 루트의 `.claude/skills/`에 있어서 저장소 폴더를 Claude Code로 열었을 때만 보인다.

## 1. 실행

```
R="$(git rev-parse --show-toplevel 2>/dev/null || pwd)"
ls "$R/ue-asset-analysis-skills/install.bat" && MSYS_NO_PATHCONV=1 cmd /c "$(cygpath -w "$R/ue-asset-analysis-skills/install.bat")" /quiet
```
- `install.bat`이 보이지 않으면 저장소 루트가 아닌 곳에서 실행한 것이다. 이 스킬 파일에서 세 단계 위(`.claude/skills/ueainstall/` → 루트)를 저장소 루트로 쓴다.
- `/quiet`를 반드시 붙인다.

## 2. 결과 알리기

| 종료 코드 | 사용자에게 |
|---|---|
| 0 | 설치한 버전과 명령어(`/ue-asset-analysis`, `/ueaupdate`, `/ueauninstall`)를 알린다. "Claude Code를 새로 시작하면 명령어가 나타난다." 출력에 `[NOTE]`가 있으면 Python 등 요구 사항을 안내하고, 필요 도구 점검 명령(`uetk.py doctor`)을 실행해 볼지 묻는다. 설치 후에는 저장소 폴더를 지워도 된다 |
| 2 | 이미 설치돼 있다. 아무것도 바꾸지 않았다고 알리고, 최신으로 바꾸려면 `/ueaupdate`를 쓰라고 안내한다. 예전 방식으로 설치돼 `/ueaupdate`가 없으면, 기존 `ue-asset-analysis` 폴더를 휴지통으로 보낸 뒤 다시 설치할지 묻는다 |
| 1 | `[ERROR]` 줄을 그대로 보여 주고 원인을 설명한다 |
