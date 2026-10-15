# fab-skills

Epic Games [Fab](https://www.fab.com)에서 원하는 에셋을 찾는 Claude Code 스킬 세트.

| 명령 | 하는 일 |
|---|---|
| `/fab` | 원하는 에셋을 말로 설명하면 몇 가지를 되물은 뒤, Fab 검색 필터가 적용된 링크 표를 만들어 준다 |
| `/fabfilterupdate` | 브라우저에서 모은 Fab 검색 URL을 근거로 `/fab`이 쓰는 필터 규칙 문서를 갱신한다 |
| `/fabupdate` | 스킬 세트를 GitHub 최신 버전으로 업데이트한다. 사용자가 고친 필터 규칙은 유지한다 |
| `/fabupdateforce` | 필터 규칙까지 모두 GitHub 버전으로 강제 업데이트한다 |
| `/fabuninstall` | 스킬 세트를 제거한다 |

## 설치 (Windows, 처음 한 번)

**방법 1. Claude에게 맡기기**
1. 저장소를 받는다: `git clone https://github.com/kyoungwhankim/Claude_Skills_GameDev.git`
2. Claude Code에서 받은 폴더(`Claude_Skills_GameDev`)를 연다.
3. `/fabinstall`을 입력한다.

**방법 2. 직접 실행**
1. 저장소를 받는다 (`git clone` 또는 GitHub에서 **Code → Download ZIP** 후 압축 해제).
2. `fab-skills\install.bat`을 더블클릭한다.

설치가 끝나면 Claude Code를 새로 시작한다. **설치 후에는 받은 저장소 폴더를 지워도 된다.** 업데이트와 제거에 필요한 스크립트는 설치된 스킬 안에 들어 있고, 업데이트는 GitHub에서 직접 받는다.

이미 설치돼 있으면 `install.bat`은 아무것도 바꾸지 않고 멈춘다. 그때는 `/fabupdate`를 쓴다.

## 업데이트·제거

| 하고 싶은 것 | Claude Code에서 | 직접 실행 |
|---|---|---|
| 업데이트 | `/fabupdate` | `%USERPROFILE%\.claude\skills\fabupdate\scripts\update.bat` |
| 강제 업데이트 | `/fabupdateforce` | 위 파일에 `/force` |
| 제거 | `/fabuninstall` | `%USERPROFILE%\.claude\skills\fabuninstall\scripts\uninstall.bat` |

`CLAUDE_CONFIG_DIR` 환경변수를 쓰고 있으면 `%USERPROFILE%\.claude` 대신 그 경로다.

### 업데이트해도 유지되는 파일

`preserve.txt`에 적힌 파일은 **사용자가 고친 경우** 업데이트해도 그대로 남는다. 지금은 `/fabfilterupdate`가 고치는 필터 규칙 문서(`fab/reference/filters.md`) 하나다.

| 상황 | `/fabupdate` 결과 |
|---|---|
| 사용자가 고친 적 없음 | 새 버전으로 바뀐다 (새 필터 규칙을 받는다) |
| 사용자가 고침, 새 버전은 그 파일을 안 바꿈 | 사용자 파일 유지 |
| 사용자가 고침, 새 버전도 그 파일을 바꿈 | 사용자 파일 유지 + `[CHECK]`로 알림. Claude가 GitHub의 새 버전과 비교해서 합칠지 묻는다 |

`/fabupdateforce`는 이 구분 없이 모두 GitHub 버전으로 바꾼다. 사용자가 고친 내용은 사라진다.

### 백업을 남기지 않는다

업데이트는 설치된 스킬을 그 자리에서 바꾸고, 이전 버전을 따로 남기지 않는다.
제거는 스킬 폴더를 Windows 휴지통으로 보낸다. 실수로 제거했으면 휴지통에서 되살릴 수 있다.

## 요구 사항

- Windows 10 이상 (robocopy, PowerShell 기본 포함)
- Claude Code (CLI 또는 데스크탑 앱)
- 업데이트할 때 GitHub 접속. Git이 있으면 git으로, 없으면 ZIP으로 받는다
- `/fabfilterupdate`의 URL 대조 스크립트를 쓰려면 Python 3

## 원칙

- `/fab`은 **검색 URL만 만든다.** Fab 사이트에 접속하거나 데이터를 수집하지 않는다.
  Fab 서비스 약관 1.8조는 자동화된 수단으로 Fab 데이터를 수집·분석하는 것을 금지한다.
- `/fab`이 쓰는 URL 파라미터는 Fab의 공식 기능이 아니라서 예고 없이 바뀔 수 있다.
  링크가 이상하게 동작하면 `/fabfilterupdate`로 규칙을 갱신한다.

## 배포하는 사람

1. `skills\` 아래를 고친다. 스킬을 새로 추가하면 폴더만 만들면 된다 (설치·업데이트가 `skills\` 아래 폴더를 모두 복사한다).
2. `VERSION`을 올린다 (예: 1.0.0 → 1.1.0). 업데이트 결과에 `이전 -> 새 버전`으로 표시된다.
3. 사용자 수정을 유지해야 하는 파일이 생기면 `preserve.txt`에 한 줄 추가한다.
4. 커밋하고 `main`에 push 한다. 사용자는 `/fabupdate`로 받는다.

## 구조

```
fab-skills/
├─ install.bat              ← 처음 설치 (저장소에만 있음)
├─ VERSION
├─ preserve.txt             ← 업데이트해도 사용자 수정을 유지할 파일 목록
└─ skills/                  ← 이 아래 폴더가 통째로 설치된다
   ├─ fab/                  ← /fab (reference/filters.md: 필터 규칙)
   ├─ fabfilterupdate/      ← /fabfilterupdate (scripts/compare_urls.py)
   ├─ fabupdate/            ← /fabupdate (repo.cfg, scripts/update.bat)
   ├─ fabupdateforce/       ← /fabupdateforce (fabupdate의 스크립트를 /force로 실행)
   └─ fabuninstall/         ← /fabuninstall (scripts/uninstall.bat)
```
