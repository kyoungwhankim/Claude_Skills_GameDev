# UE Analysis Toolkit (uetk)

언리얼 엔진 플러그인·프로젝트를 **블루프린트 / 머티리얼 / 나이아가라 등 바이너리 에셋 기반으로 분석**하기 위한 툴킷이다.
Claude Code 스킬 `ue-asset-analysis` 폴더 안의 `toolkit\`에 설치되고, 스킬이 이 툴킷을 실행한다.

핵심 아이디어: `.uasset` 은 바이너리라 그대로는 읽을 수 없으므로, 원본을 복사한 분석용 워크스페이스에 덤프 플러그인을 넣고
모든 에셋을 사람이(그리고 Claude 가) 읽을 수 있는 텍스트로 꺼낸다.

| 산출물 | 내용 |
|---|---|
| `*.graph.txt` | 노드 그래프 (BP·나이아가라 EdGraph: 노드·핀·연결·기본값 / 머티리얼: 표현식·연결·최종 출력) |
| `*.props.txt` | 패키지 안 모든 오브젝트의 프로퍼티(아키타입 대비 변경값, 긴 배열은 원소별) |
| `*.t3d` | 에디터 Ctrl+C 와 같은 노드 원문 (에디터에 붙여넣기 가능) |
| `*.hlsl` | 머티리얼 번역 HLSL |
| `*.niagara.hlsl` | 나이아가라 시스템 컴파일 HLSL (CPU/GPU, 시뮬레이션 스테이지별) |
| `manifest.json`, `INDEX.md`, `deps.svg` | 에셋 목록·의존/참조·허브 에셋·폴더 구조·의존성 그래프 |
| `Dump/vars/*.md` | 블루프린트 변수표 (카테고리·타입·툴팁·기본값) |
| `Analysis/*.html` | 분석 마크다운 → 사이드바형 단일 HTML 보고서 (오프라인) |

## 요구 사항
- Windows, Unreal Engine 5.x (5.5 / 5.8 검증, 5.1+ 예상, UE4 미지원)
- Visual Studio 2022 C++ (덤프 플러그인 빌드)
- Python 3.10+ 와 `pip install markdown html2text` (선택: `yt-dlp`, Graphviz, RenderDoc)

`uetk doctor` 로 한 번에 점검한다.

## 빠른 시작
```bat
cd /d "%USERPROFILE%\.claude\skills\ue-asset-analysis\toolkit"

:: 1) 프로젝트 분석 (원본은 건드리지 않고 --out 에 복사본 생성)
uetk all --project "D:\UEProjects\SomeProject\SomeProject.uproject" --out D:\UEProjects\SomeAnalysis --title SomeProject

:: 2) Fab/Vault 플러그인 폴더 분석 (호스트 프로젝트 자동 생성, 콘텐츠 루트 /<플러그인명>)
uetk all --plugin "D:\Vault\CoolPlugin" --engine 5.8 --out D:\UEProjects\CoolPluginAnalysis

:: 3) 엔진 내장 플러그인 분석
uetk all --engine-plugin NiagaraFluids --engine 5.8 --out D:\UEProjects\NiagaraFluidsAnalysis
```
`--out` 워크스페이스는 반드시 이 툴킷(스킬) 폴더 밖에 둔다. 스킬 폴더는 업데이트할 때 통째로 교체된다.

`all` = setup → build → dump → niagara → index → vars → brief. 에셋 수에 따라 수 분~수십 분.
나이아가라는 에디터 틱 안에서만 컴파일되기 때문에, 이 단계는 렌더러 없는 에디터(`-nullrhi`)를 잠시 띄워 처리한다.
이 단계가 실패해도 `all` 은 나머지 단계를 계속한다.

## 명령
| 명령 | 설명 |
|---|---|
| `uetk engines` | 설치된 엔진 목록 (런처 등록 + 일반 설치 경로) |
| `uetk doctor` | 필요 도구 점검 |
| `uetk setup --project/--plugin/--engine-plugin ... --out DIR [--engine 5.x] [--title]` | 워크스페이스 생성 |
| `uetk build --ws DIR` | 덤프 플러그인 포함 에디터 타깃 빌드 (원본 에디터가 열려 있어도 동작) |
| `uetk dump --ws DIR [--root /Game/Sub] [--filter 문자열] [--no-hlsl] [--no-maps]` | 헤드리스 전체 덤프 |
| `uetk niagara --ws DIR [--timeout 분] [--startup-timeout 분] [--with-rhi]` | 나이아가라 HLSL 덤프 (기본 -nullrhi) |
| `uetk index --ws DIR` | INDEX.md, deps.dot/svg |
| `uetk vars --ws DIR [/Game/패키지 ...]` | 블루프린트 변수표 (생략 시 전체) |
| `uetk docs --ws DIR URL... [--youtube ID...]` | 참고 문서를 `Docs/` 에 md 로 수집, 유튜브 자막 |
| `uetk brief --ws DIR` | 분석 에이전트 공통 브리프 `Analysis/AGENT_BRIEF.md` 생성 |
| `uetk report --ws DIR [--title] [--subtitle] [--out]` | `Analysis/00_*.md` + `Analysis/sections/*.md` → 단일 HTML |
| `uetk exec --ws DIR "python 코드"` / `-f script.py` | 실행 중인 워크스페이스 에디터에서 Python 원격 실행 |
| `uetk clean --ws DIR [--all]` | 빌드 중간 산출물·캐시 삭제 (덤프/분석 결과 유지, `--all` 은 Binaries 까지) |

`--ws` 를 생략하면 현재 폴더를 워크스페이스로 본다. 워크스페이스 설정은 `<ws>\uetk.json`.

## 워크스페이스 구조
```
<ws>/
  uetk.json                 엔진 경로, uproject, 콘텐츠 루트, 빌드 타깃
  <Project>.uproject        Python/EditorScripting/RenderDoc/GraphDumper 활성화됨
  Plugins/GraphDumper/      덤프 플러그인 (커맨드릿 -run=GraphDump, 콘솔 GraphDump.NiagaraHLSL)
  Source/                   콘텐츠 전용 프로젝트면 빈 모듈을 자동 추가
  Dump/                     덤프 결과 (assets/, manifest.json, INDEX.md, deps.svg, vars/)
  Docs/                     수집한 문서
  Analysis/                 AGENT_BRIEF.md, 00_*.md(통합), sections/NN_*.md(장별), *.html
  Saved/uetk/*.log          build / dump / niagara 로그
```

## Claude Code 로 분석하기
Claude Code 에서 "이 플러그인 기능 분석해줘" 처럼 요청하면 `ue-asset-analysis` 스킬이
툴킷 실행 → 공식 문서 수집 → 서브시스템별 병렬 에이전트 분석 → 핵심 주장 검증 → 통합 보고서(Markdown + HTML) 순서로 진행한다.
절차는 스킬 폴더의 `SKILL.md`, 보고서 뼈대는 `templates/OVERVIEW_TEMPLATE.md`, 에이전트 지침은 `templates/AGENT_BRIEF.md`.

## 검증 이력
| 대상 | 모드 | 엔진 | 결과 |
|---|---|---|---|
| Fab 상용 나이아가라 플러그인 (콘텐츠 전용) | project | 5.8 | 1,806 패키지, 나이아가라 68, 전체 분석·HTML 보고서 완료 |
| CassiniSample | project (C++) | 5.5 | 1,352 패키지(엔진 예외 4건 격리), 나이아가라 7 |
| NiagaraFluids | engine-plugin | 5.8 | 530 패키지, 나이아가라 28 |

워크스페이스 하나가 원본 크기 + 빌드 중간 산출물(수 GB)을 차지한다. 덤프 후 `uetk clean` 을 권장한다.

## 알려진 한계와 문제 해결
- 머티리얼 인스턴스는 HLSL 을 따로 뽑지 않는다(부모 HLSL + props 의 스위치/파라미터로 해석).
- 엔진 함수가 비정상 에셋에서 죽는 경우(예: UE 5.5 `ObjectPositionWS` 노드)는 해당 오브젝트/노드만 건너뛰고 `Dump/dump_errors.txt` 에 기록한다.
- 엔진 셰이더 캐시가 비어 있는 엔진에서 렌더러를 켠 에디터를 띄우면 시작에 수 시간이 걸릴 수 있다. 그래서 나이아가라 단계 기본값이 `-nullrhi` 이고, 시작이 20분을 넘으면 중단한다.
- 월드 파티션 외부 액터(`__ExternalActors__`)는 맵 덤프에 포함되지 않는다.
- 빌드 LNK1104(DLL 잠김): 툴킷이 잠긴 DLL 을 `.old` 로 이름을 바꿔 피한다. 남은 프로세스가 있으면 워크스페이스 경로가 커맨드라인에 있는 것만 종료할 것.
- Git Bash 에서 `/Game/...` 인자는 MSYS 가 Windows 경로로 바꾸는데, uetk 가 되돌린다.
- 엔진 버전 간 API 차이로 덤프 플러그인 컴파일이 실패하면 `plugin/GraphDumper` 를 고친 뒤 워크스페이스의 `Plugins/GraphDumper/Source` 를 교체하고 `uetk build`.

## 폴더
```
uetk.py / uetk.bat     진입점
uetk/                  engine, workspace, run, index, bpvars, report, docs, remote, cli
plugin/GraphDumper/    덤프 플러그인 소스
templates/             AGENT_BRIEF.md, OVERVIEW_TEMPLATE.md
vendor/mermaid.min.js  HTML 보고서용 (오프라인 내장, MIT 라이선스: vendor/LICENSE-mermaid.txt)
```
