# Claude_Skills_GameDev 저장소 안내 (Claude용)

게임 개발자용 Claude Code 스킬을 모아 둔 저장소다. 스킬 세트마다 하위 폴더가 있다.

| 폴더 | 내용 | 설명서 |
|---|---|---|
| `fab-skills/` | Epic Fab 에셋 검색 스킬 세트 (`/fab` 등) | `fab-skills/README.md` |

## 사용자가 설치·업데이트·삭제를 요청할 때

스킬 파일을 손으로 복사하거나 지우지 않는다. 아래 스크립트를 실행한다.

| 요청 예 | 할 일 |
|---|---|
| "fab 스킬 설치해줘" | `/fabinstall` 스킬의 절차대로 `fab-skills/install.bat /quiet` 실행 |
| "업데이트해줘" | 설치돼 있으면 `/fabupdate` 절차(설치된 `fabupdate/scripts/update.bat /quiet`) |
| "강제 업데이트", "filters.md 초기화" | `/fabupdateforce` 절차 (`update.bat /quiet /force`) |
| "삭제해줘" | `/fabuninstall` 절차 (설치된 `fabuninstall/scripts/uninstall.bat /quiet`) |

- Bash 도구(Git Bash)에서는 `MSYS_NO_PATHCONV=1 cmd /c "<Windows 경로>" /quiet` 형태로 실행한다. Windows 경로는 `cygpath -w`로 만든다.
- `/quiet`를 반드시 붙인다. 없으면 키 입력을 기다리며 멈춘다.
- 종료 코드: 0 성공, 1 실패(`[ERROR]` 줄을 보여 준다), 2 상태 불일치(설치 시 이미 설치됨 / 업데이트 시 설치 안 됨).

## 이 저장소의 스킬을 고칠 때

- `fab-skills/skills/` 아래를 고친 뒤 `fab-skills/VERSION`을 올리라고 안내한다.
- `update.bat`, `uninstall.bat`, `install.bat`, `repo.cfg`, `preserve.txt`는 CRLF 줄바꿈이어야 한다 (`.gitattributes`가 보장한다).
- 공개 저장소다. 개인 정보, 사내 주소, 토큰을 넣지 않는다.
