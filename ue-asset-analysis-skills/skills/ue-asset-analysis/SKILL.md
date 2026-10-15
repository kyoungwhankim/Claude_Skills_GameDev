---
name: ue-asset-analysis
description: 언리얼 엔진 플러그인/프로젝트의 기능을 블루프린트·머티리얼·나이아가라 등 바이너리 에셋 기반으로 상세 분석할 때 사용. uetk 툴킷으로 에셋을 텍스트(노드 그래프, 프로퍼티, 컴파일된 HLSL)로 덤프하고, 서브시스템별 병렬 에이전트 분석 → 검증 → 통합 보고서(Markdown + 사이드바형 단일 HTML)까지 진행한다. "플러그인 분석", "에셋 기반 기능 분석", "블루프린트/나이아가라/머티리얼 분석해줘", "Fab 에셋 구조 파악" 같은 요청에서 트리거.
---

# UE 에셋 기반 기능 분석 (uetk)

툴킷 위치: 이 스킬 폴더 안의 `toolkit\` (아래에서 `<TK>`). 보통 `%USERPROFILE%\.claude\skills\ue-asset-analysis\toolkit`이고, `CLAUDE_CONFIG_DIR`을 쓰면 그 아래 `skills\ue-asset-analysis\toolkit`이다. 전체 명령 설명은 `<TK>\README.md`.
명령은 `python "<TK>\uetk.py" <cmd>` 또는 `"<TK>\uetk.bat" <cmd>`. Bash 도구에서는 `TK="${CLAUDE_CONFIG_DIR:-$HOME/.claude}/skills/ue-asset-analysis/toolkit"` 로 잡는다.
분석 워크스페이스(`--out`)와 덤프 결과는 항상 스킬 폴더 밖에 만든다. 스킬 폴더는 업데이트 때 통째로 교체된다.

.uasset 은 바이너리라 그대로는 읽을 수 없다. 이 스킬의 핵심은 (1) 원본을 건드리지 않고 복사본/호스트 프로젝트에 덤프 플러그인을 넣어 모든 에셋을 텍스트로 꺼내고, (2) 그 텍스트를 근거로 분석하는 것이다.

## 0. 원칙
- 원본 프로젝트/플러그인은 절대 수정하지 않는다. 항상 `--out` 새 폴더에 워크스페이스를 만든다.
- 사용자가 열어 둔 에디터 프로세스는 죽이지 않는다. 툴킷이 띄운 프로세스만 정리한다(커맨드라인에 워크스페이스 경로가 있는지 확인).
- 정적 분석이므로 "확인된 사실"과 "추정"을 구분하고, 주장마다 덤프 파일·그래프·노드 ID 근거를 단다.
- 결과물은 한국어로 쓴다(사용자가 달리 요청하지 않으면).

## 1. 준비
1. `uetk doctor` — 엔진, VS C++, Python 패키지(markdown, html2text), Graphviz 확인. 빠진 Python 패키지는 pip 로 설치.
2. 대상 결정 (불분명하면 사용자에게 묻는다):
   - 프로젝트: `--project <X.uproject>` (EngineAssociation 으로 엔진 자동 선택)
   - 플러그인 폴더(Fab/Vault 등): `--plugin <폴더> --engine 5.x` → 호스트 프로젝트 생성, 루트 `/<플러그인명>`
   - 엔진 내장 플러그인: `--engine-plugin <이름> --engine 5.x`
   - 워크스페이스 위치: 디스크 여유 공간 확인(원본 크기 + 수 GB).
3. 실행 (오래 걸리므로 백그라운드):
   `uetk all --project ... --out <ws> --title <이름>`
   = setup → build → dump(헤드리스) → niagara(에디터 창이 잠시 뜸, 나이아가라 없으면 생략) → index → vars → brief
   단계별 재실행: `uetk build|dump|niagara|index|vars|brief --ws <ws>`. 로그는 `<ws>\Saved\uetk\*.log`.
   덤프가 끝나면 `uetk clean --ws <ws>` 로 빌드 중간 산출물(수 GB)을 지운다(Binaries 는 남아 재실행 가능).
4. 공식 문서 수집: WebSearch 로 매뉴얼/파라미터 문서를 찾고 `uetk docs --ws <ws> <url...>` (유튜브 자막: `--youtube <id...>`). 그 뒤 `uetk brief --ws <ws>` 를 다시 실행해 문서 목록을 브리프에 반영.

## 2. 구조 파악 (직접)
- `<ws>\Dump\INDEX.md`: 클래스 통계, 참조가 많은 허브 에셋, 로직 에셋(BP/Niagara/PCG) 의존 요약, 폴더 구조.
- 허브 BP 의 `#ParentClass`, 큰 그래프 목록(`grep "^################ GRAPH"`)과 파일 크기를 본다.
- 공식 매뉴얼 목차를 훑어 개념/용어를 잡는다.
- 이를 바탕으로 서브시스템 5~8개로 나눈다. 전형적 분할: 코어 로직(가장 큰 Niagara/BP), 메인 컴포넌트/액터 BP(크면 그래프 줄 범위로 2분할), 입력·유틸리티, 출력 머티리얼, 출력 Niagara/이펙트, 공용 타입·프리셋·데이터 에셋, 예제 레벨 카탈로그.

## 3. 병렬 분석 (Agent 도구, 백그라운드, 한 메시지에서 동시에)
각 에이전트 프롬프트:
- "먼저 `<ws>\Analysis\AGENT_BRIEF.md` 를 읽고 그대로 따른다."
- 담당 범위: 정확한 덤프 파일 경로(필요 시 graph.txt 줄 범위와 그래프 이름 목록), 교차 확인할 매뉴얼 장.
- "특히 밝혀낼 것" 목록 4~7개 (수명주기, 데이터 형식/채널, 알고리즘 수식, 파라미터, 다른 서브시스템과의 인터페이스).
- 산출물: `<ws>\Analysis\sections\NN_<이름>.md` (01~08). 09 는 변수 부록용으로 비워 둔다.
범위가 겹치지 않게 나누고, 겹치면 "참조만" 이라고 명시한다.

## 4. 검증과 통합 (직접)
- 에이전트 보고서의 핵심 주장(아키텍처 핵심, 버그 의심)은 덤프/HLSL 원문에서 직접 확인한다. 섹션 간 모순이나 "확인 필요" 항목은 grep 으로 해소하고, 해소 결과를 해당 섹션 끝에 "통합 단계 추가 확인" 블록으로 덧붙인다.
- 메인 BP 변수 부록: `Dump\vars\<BP>.md` 를 이어 붙여 `sections\09_variables_appendix.md` 로 만든다.
- 통합 보고서 `<ws>\Analysis\00_<title>_기능분석.md` 작성 — `<TK>\templates\OVERVIEW_TEMPLATE.md` 구조를 따른다(한눈에 보기, 아키텍처+mermaid 데이터 흐름, 장별 요약, 핵심 데이터 계약 표, 버그·이상 표(검증 여부 열 포함), 성능/제약, 미해결 질문, 장 목록 링크 `sections/NN_*.md`).
- HTML: `uetk report --ws <ws> [--title ...] [--subtitle ...]` → `<ws>\Analysis\<title>_분석보고서.html` (오프라인 단일 파일, 왼쪽 사이드바/오른쪽 스크롤). mermaid 오류가 의심되면 브라우저로 열어 `pre.mermaid svg` 에 "Syntax error" 가 없는지 확인.
  (브라우저 패널은 세션 폴더 밖 file:// 을 못 열 수 있다 → 스크래치패드에 복사 후 `python -m http.server` 로 확인하고 서버를 정리)

## 5. 문제 해결
- 빌드 "Unable to build while Live Coding is active": 툴킷은 `-NoHotReloadFromIDE` 를 붙인다. 그래도 실패하면 로그 확인.
- 링크 LNK1104(DLL 잠김): 이전 커맨드릿/에디터가 남아 있다. 툴킷이 DLL 을 .old 로 이름을 바꿔 피한다. 남은 프로세스는 워크스페이스 경로가 커맨드라인에 있는 것만 종료.
- 나이아가라 HLSL 은 커맨드릿에서 컴파일되지 않아 에디터(-ExecCmds, 기본 -nullrhi)로 처리한다. 엔진 셰이더 캐시가 비어 있으면 렌더러를 켠 에디터는 시작 단계에서 수 시간 멈출 수 있어서 기본값이 -nullrhi 다. 시작이 `--startup-timeout`(기본 20분) 안에 끝나지 않으면 중단하고 셰이더 대기 상태를 알려 준다. `all` 에서는 이 단계가 실패해도 나머지를 계속한다.
- 일부 엔진 함수는 비정상 에셋에서 널 접근으로 죽는다(예: UE 5.5 `MaterialExpressionObjectPositionWS::GetCaption`). 덤프 플러그인은 오브젝트/노드 단위로 예외를 잡아 `Dump\dump_errors.txt` 에 기록하고 계속한다. 이 목록의 노드는 graph.txt 에 `<dump failed>` 로 표시되므로, 분석 시 .t3d 나 props 로 보완한다.
- 덤프 컴파일 오류(엔진 버전 API 차이): `<TK>\plugin\GraphDumper` 소스를 고친 뒤 워크스페이스에 `uetk setup` 대신 플러그인 폴더만 다시 복사하고 `uetk build`. 검증된 엔진: 5.5, 5.8 (5.1+ 예상, UE4 미지원).
- 덤프 값이 "...<clipped N chars>" 로 잘린 경우 해당 원문은 .t3d 에서 찾는다.
- 런타임 동작 검증이 필요하면: 워크스페이스 에디터를 띄우고 `uetk exec --ws <ws> "<python>"` (Remote Python), RenderDoc 플러그인(활성화됨)으로 프레임 캡처.
