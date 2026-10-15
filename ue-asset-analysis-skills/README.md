# ue-asset-analysis-skills

언리얼 엔진 플러그인·프로젝트의 기능을 블루프린트·머티리얼·나이아가라 같은 **바이너리 에셋 기반으로 분석**하는 Claude Code 스킬 세트.
`.uasset`을 텍스트(노드 그래프, 프로퍼티, 컴파일된 HLSL)로 덤프한 뒤, 서브시스템별 병렬 에이전트 분석과 검증을 거쳐 통합 보고서(Markdown + 단일 HTML)를 만든다.

| 명령 | 하는 일 |
|---|---|
| `/ue-asset-analysis` | 분석 실행. "이 플러그인 기능 분석해줘"처럼 말해도 시작된다 |
| `/ueaupdate` | 스킬과 툴킷을 GitHub 최신 버전으로 업데이트한다 |
| `/ueauninstall` | 스킬 세트를 제거한다 (휴지통으로 이동) |

## 요구 사항

- Windows, Unreal Engine 5.x (5.5 / 5.8 검증, 5.1 이상 예상, UE4 미지원)
- Visual Studio 2022 C++ (덤프 플러그인 빌드)
- Python 3.10+ 와 `pip install markdown html2text` (선택: `yt-dlp`, Graphviz, RenderDoc)
- 분석 워크스페이스용 디스크 공간: 원본 크기 + 수 GB

설치 후 필요 도구를 한 번에 점검한다.
```
python "%USERPROFILE%\.claude\skills\ue-asset-analysis\toolkit\uetk.py" doctor
```

## 설치 (Windows, 처음 한 번)

**방법 1. Claude에게 맡기기**
1. `git clone https://github.com/kyoungwhankim/Claude_Skills_GameDev.git`
2. Claude Code에서 받은 폴더를 열고 `/ueainstall`을 입력한다.

**방법 2. 직접 실행**
저장소를 받아(`git clone` 또는 Download ZIP) `ue-asset-analysis-skills\install.bat`을 더블클릭한다.

설치가 끝나면 Claude Code를 새로 시작한다. 설치 후에는 받은 저장소 폴더를 지워도 된다.
이미 설치돼 있으면 `install.bat`은 아무것도 바꾸지 않고 멈춘다. 그때는 `/ueaupdate`를 쓴다.

## 업데이트·제거

| 하고 싶은 것 | Claude Code에서 | 직접 실행 |
|---|---|---|
| 업데이트 | `/ueaupdate` | `%USERPROFILE%\.claude\skills\ueaupdate\scripts\update.bat` |
| 제거 | `/ueauninstall` | `%USERPROFILE%\.claude\skills\ueauninstall\scripts\uninstall.bat` |

- 업데이트는 설치된 스킬과 툴킷을 그 자리에서 바꾸고 백업을 남기지 않는다.
- 제거는 스킬 폴더를 Windows 휴지통으로 보낸다.
- 분석 워크스페이스는 스킬 폴더 밖에 있어서 업데이트·제거의 영향을 받지 않는다.

## 분석 결과물 다루기

- 분석 워크스페이스(`uetk --out` 폴더)는 **스킬 폴더와 이 저장소 밖**에 만든다.
- 덤프 결과(`Dump/`, `*.graph.txt`, `*.props.txt`, `*.hlsl` 등)와 보고서는 이 저장소에 커밋하지 않는다. 저장소 루트의 `.gitignore`가 한 번 더 막는다.
- Fab 등에서 받은 상용 에셋을 덤프한 결과물은 판매자 콘텐츠에서 나온 것이다. 공개 저장소나 외부에 올리지 않는다.

## 구조

```
ue-asset-analysis-skills/
├─ install.bat                ← 처음 설치 (저장소에만 있음)
├─ VERSION
└─ skills/                    ← 이 아래 폴더가 통째로 설치된다
   ├─ ue-asset-analysis/
   │  ├─ SKILL.md             ← 분석 절차
   │  └─ toolkit/             ← uetk 툴킷 (자세한 명령은 toolkit/README.md)
   │     ├─ uetk.py, uetk.bat, uetk/
   │     ├─ plugin/GraphDumper/   ← UE 덤프 커맨드렛 플러그인 소스
   │     ├─ templates/            ← 에이전트 지침·보고서 템플릿
   │     └─ vendor/               ← mermaid.min.js (MIT, LICENSE-mermaid.txt)
   ├─ ueaupdate/              ← /ueaupdate (repo.cfg, scripts/update.bat)
   └─ ueauninstall/           ← /ueauninstall (scripts/uninstall.bat)
```

## 배포하는 사람

1. `skills\` 아래를 고친다.
2. `VERSION`을 올린다.
3. 커밋하고 `main`에 push 한다. 사용자는 `/ueaupdate`로 받는다.
