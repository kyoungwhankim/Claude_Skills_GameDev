# Claude_Skills_GameDev 저장소 안내 (Claude용)

게임 개발자용 Claude Code 스킬을 모아 둔 저장소다. 스킬 세트마다 하위 폴더가 있다.

| 폴더 | 내용 | 설명서 |
|---|---|---|
| `fab-skills/` | Epic Fab 에셋 검색 스킬 세트 (`/fab` 등) | `fab-skills/README.md` |
| `ue-asset-analysis-skills/` | UE 에셋 기반 기능 분석 스킬과 uetk 툴킷 | `ue-asset-analysis-skills/README.md` |

## 사용자가 설치·업데이트·삭제를 요청할 때

스킬 파일을 손으로 복사하거나 지우지 않는다. 아래 스크립트를 실행한다. 어느 스킬 세트인지 모호하면 묻는다.

| 요청 예 | fab-skills | ue-asset-analysis-skills |
|---|---|---|
| 설치 | `/fabinstall` 절차 (`fab-skills/install.bat /quiet`) | `/ueainstall` 절차 (`ue-asset-analysis-skills/install.bat /quiet`) |
| 업데이트 | `/fabupdate` 절차 (설치된 `fabupdate/scripts/update.bat /quiet`) | `/ueaupdate` 절차 (설치된 `ueaupdate/scripts/update.bat /quiet`) |
| 강제 업데이트 | `/fabupdateforce` 절차 (`update.bat /quiet /force`) | 해당 없음 (유지 대상 파일이 없다) |
| 삭제 | `/fabuninstall` 절차 (설치된 `fabuninstall/scripts/uninstall.bat /quiet`) | `/ueauninstall` 절차 (설치된 `ueauninstall/scripts/uninstall.bat /quiet`) |

- Bash 도구(Git Bash)에서는 `MSYS_NO_PATHCONV=1 cmd /c "<Windows 경로>" /quiet` 형태로 실행한다. Windows 경로는 `cygpath -w`로 만든다.
- `/quiet`를 반드시 붙인다. 없으면 키 입력을 기다리며 멈춘다.
- 종료 코드: 0 성공, 1 실패(`[ERROR]` 줄을 보여 준다), 2 상태 불일치(설치 시 이미 설치됨 / 업데이트 시 설치 안 됨).

## 이 저장소의 스킬을 고칠 때

- 스킬 세트의 `skills/` 아래를 고친 뒤 그 세트의 `VERSION`을 올리라고 안내한다.
- ue-asset-analysis의 분석 워크스페이스·덤프 결과·보고서는 절대 이 저장소에 넣지 않는다. 상용 에셋에서 나온 결과물일 수 있다.
- `update.bat`, `uninstall.bat`, `install.bat`, `repo.cfg`, `preserve.txt`는 CRLF 줄바꿈이어야 한다 (`.gitattributes`가 보장한다).
- 공개 저장소다. 개인 정보, 사내 주소, 토큰을 넣지 않는다.
