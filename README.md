# Planning Wireframe

인터뷰 기반으로 구조화된 기획 문서와 와이어프레임 산출물을 만드는 `skill + plugin metadata + Python CLI` 저장소입니다.

GitHub: `https://github.com/Jimmy-Jung/plugin-planning-wireframe`

## 무엇을 하는 저장소인가

이 저장소는 Cursor 플러그인과 Claude Code 플러그인 마켓플레이스 양쪽을 겨냥한 `skill + plugin metadata + Python CLI` 저장소입니다.

### 주요 특징

- **인터뷰 기반 질문 흐름**: 9단계 구조화된 질문으로 기획 데이터 수집
- **SubAgent 기반 워크플로우**: Context window 절약을 위한 phase별 독립 실행
- **상태 기반 재개**: YAML 기반 세션 저장으로 중단/재개 가능
- **Figma 통합**: 스크린샷 자동 다운로드 및 주석 이미지 생성
- **문서 자동 생성**: 수집된 데이터를 기반으로 마크다운 문서 생성

### 워크플로우 모드

1. **기본 워크플로우**: 단일 세션에서 순차 실행 (간단한 프로젝트)
2. **SubAgent 워크플로우**: Phase별 독립 실행 (복잡한 프로젝트, 권장)

### 스킬 구조

- `skills/planning-wireframe/SKILL.md`: 스킬 정의 (YAML frontmatter + 워크플로우)
- `skills/planning-wireframe/scripts/planning_runner.py`: 실제 실행을 담당하는 CLI 러너
- `.cursor-plugin/plugin.json`: Cursor 플러그인 메타데이터
- `.claude-plugin/marketplace.json`: Claude Code 마켓플레이스 메타데이터
- `.claude-plugin/plugin.json`: Claude Code 플러그인 메타데이터
- `commands/planning-wireframe.md`: Claude Code 플러그인 커맨드

### 마켓플레이스 준비 완료

- ✅ SKILL.md with YAML frontmatter (name, description)
- ✅ Claude Code marketplace metadata
- ✅ Claude Code plugin metadata
- ✅ Claude Code command
- ✅ Scripts for execution
- ✅ Templates and references
- ✅ Validation passed

주요 기능:

- 인터뷰 기반 질문 흐름 관리
- 세션 상태 YAML 저장 및 재개
- 구조화된 마크다운 기획 문서 생성
- Figma 스크린샷 manifest 생성
- 화면별 스크린샷 연결
- 주석 이미지 생성

## 설치 방법

### Cursor에서 로컬 플러그인으로 사용

이 저장소는 로컬 플러그인 패키지로 사용하는 것을 기준으로 합니다.

1. 저장소를 로컬에 클론합니다.
2. Cursor에서 로컬 플러그인 또는 개발용 플러그인 추가 흐름을 엽니다.
3. 플러그인 경로로 아래 디렉터리를 지정합니다.

```text
<plugin-root>
```

4. Cursor가 `.cursor-plugin/plugin.json`을 읽으면 플러그인으로 인식할 수 있습니다.

예시:

```text
<plugin-root> = /path/to/plugin-planning-wireframe
```

즉, 원격 GitHub URL 설치보다 로컬 저장소 경로를 직접 지정하는 방식으로 사용하는 문서 기준입니다.

### Claude Code에서 플러그인 마켓플레이스로 설치

1. Claude Code에서 마켓플레이스를 추가합니다.

```text
/plugin marketplace add <plugin-root>
```

2. 플러그인을 설치합니다.

```text
/plugin install planning-wireframe@jimmy-jung-plugins
```

3. 설치 후 `planning-wireframe` 스킬과 커맨드를 사용할 수 있습니다.

즉, Claude Code에서도 `MCP`가 아니라 `플러그인 마켓플레이스` 방식으로 설치할 수 있습니다.

예시:

```text
/plugin marketplace add /path/to/plugin-planning-wireframe
```

### 수동 설치 (로컬 개발용)

#### 1. 저장소 클론

```bash
git clone https://github.com/Jimmy-Jung/plugin-planning-wireframe.git
cd plugin-planning-wireframe
```

#### 2. Python 의존성 설치

요구사항:

- Python 3.8+
- `pip`

설치:

```bash
python3 -m pip install -r requirements.txt
```

현재 의존성은 아래 두 개입니다.

- `Pillow`
- `PyYAML`

#### 3. 설치 확인

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py --help
python3 skills/planning-wireframe/scripts/validate_skill.py
```

정상 설치라면 CLI 도움말이 출력되고, 스킬 구조 검증이 통과해야 합니다.

## 에이전트 연결 구조

이 저장소는 아래처럼 도구별 연결 파일과 실제 스킬 로직이 분리되어 있습니다.

- `.cursor-plugin/plugin.json`: Cursor용 플러그인 메타데이터
- `.claude-plugin/marketplace.json`: Claude Code 마켓플레이스 정의
- `.claude-plugin/plugin.json`: Claude Code 플러그인 정의
- `.cursor/rules/planning-wireframe.mdc`: Cursor 프로젝트 규칙
- `CLAUDE.md`: Claude Code 프로젝트 메모리
- `.claude/commands/planning-wireframe.md`: 로컬 개발용 Claude Code 커맨드
- `commands/planning-wireframe.md`: Claude Code 플러그인 커맨드
- `skills/planning-wireframe/`: 스킬 문서, 템플릿, 상태 스키마, Python 스크립트

정리하면:

- Cursor는 `.cursor-plugin/plugin.json`을 포함한 플러그인 패키지 관점으로 설명할 수 있습니다.
- Claude Code는 `.claude-plugin/marketplace.json`을 통해 마켓플레이스로 등록하고, `planning-wireframe` 플러그인으로 설치할 수 있습니다.
- 로컬 개발 중에는 `CLAUDE.md`와 `.claude/commands/`로 같은 워크플로우를 바로 테스트할 수 있습니다.
- 실제 실행은 공통적으로 `planning_runner.py`가 담당합니다.

## 스킬 사용법

### 워크플로우 선택

Planning Wireframe은 두 가지 워크플로우를 제공합니다:

#### 1. 기본 워크플로우 (순차 실행)

단일 세션에서 모든 단계를 순차적으로 처리합니다.

**적합한 경우**:
- 간단한 프로젝트 (3-5개 화면)
- 학습 및 테스트 목적
- 빠른 프로토타이핑

#### 2. SubAgent 워크플로우 (권장)

각 phase를 독립적인 SubAgent로 실행하여 context window를 절약합니다.

**적합한 경우**:
- 복잡한 프로젝트 (5개 이상 화면)
- 긴 인터뷰 세션
- 프로덕션 품질 문서 생성

**장점**:
- Context window 최대 80% 절약
- Phase별 중단/재개 가능
- 독립적인 검증
- 병렬 세션 처리 가능

### 전체 흐름 (SubAgent 워크플로우)

#### Phase 0: 세션 생성

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py init \
  --title "홈탭 기획" \
  --author "홍길동"

# 세션 ID 확인 (예: planning-2026-03-28-1304)
python3 skills/planning-wireframe/scripts/planning_runner.py list
```

#### Phase 1-5: 데이터 수집 (SubAgent)

각 phase를 독립적인 SubAgent로 실행합니다:

```bash
# Phase 진행 상태 확인
python3 skills/planning-wireframe/scripts/planning_orchestrator.py status <session-id>

# Phase별 실행 (에이전트가 Task tool로 호출)
# - basic: 메타데이터, 화면, 정책
# - areas: 영역 정의
# - requirements: 요구사항
# - rules: 규칙 정리
# - testcases: 테스트케이스
```

**SubAgent 실행 예시**:

```python
# 에이전트가 Task tool 사용
Task(
    description="기본 정보 수집",
    prompt="""
    세션 <session-id>의 basic phase를 완료하세요.
    
    1. 프롬프트 가져오기:
       python3 skills/planning-wireframe/scripts/planning_orchestrator.py run <session-id> basic
    
    2. 프롬프트 지시사항에 따라 질문/답변 진행
    
    3. 완료 후 검증:
       python3 skills/planning-wireframe/scripts/planning_orchestrator.py validate-phase <session-id> basic
    """,
    subagent_type="generalPurpose"
)
```

#### Phase 6: 문서 생성

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py render-doc <session-id>
```

#### Phase 7: Figma 처리

```bash
# 1. Manifest 생성
python3 skills/planning-wireframe/scripts/planning_runner.py figma-manifest <session-id>

# 2. 스크린샷 다운로드 (에이전트가 Figma MCP 사용)

# 3. 경로 연결
python3 skills/planning-wireframe/scripts/planning_runner.py attach-screenshot <session-id> \
  --screen-name "홈 메인 화면" \
  --image-path "홈화면 기획문서/이미지/홈-메인-화면.png"

# 4. 주석 이미지 생성
python3 skills/planning-wireframe/scripts/planning_runner.py annotate <session-id> \
  --image-root "홈화면 기획문서/이미지" \
  --output-root "홈화면 기획문서/이미지-주석-영역-한글"
```

### 전체 흐름 (기본 워크플로우)

표준 흐름은 아래 순서입니다.

1. 세션 생성
2. 질문 확인
3. 답변 반영
4. 문서 생성
5. Figma 스크린샷 manifest 출력
6. 스크린샷 경로 연결
7. 주석 이미지 생성

### 1. 세션 생성

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py init
```

필요하면 제목과 작성자를 초기값으로 넣을 수 있습니다.

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py init \
  --title "홈탭 기획" \
  --author "홍길동"
```

저장된 세션 확인:

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py list
python3 skills/planning-wireframe/scripts/planning_runner.py status <session-id>
```

### 2. 질문 진행

현재 질문 확인:

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py next <session-id>
```

답변 반영:

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py answer <session-id> --text "답변"
```

멀티라인 입력 예시:

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py answer <session-id> --text $'문서 제목: 홈탭 기획\n문서 목적: 홈 화면 구조와 동작을 정의한다\n대상 독자: 기획자, QA, 개발자\n작성자: 모바일팀_홍길동\n대상 플랫폼: iPhone\n범위 제외: 타임테이블 기능'
```

질문 단계는 아래 순서로 진행됩니다.

1. `meta`
2. `screens`
3. `policies`
4. `areas`
5. `requirements`
6. `rules`
7. `testcases`
8. `document_generation`
9. `review`

제어 입력:

- `없음`: 현재 항목 비움
- `done`: 현재 단계 입력 종료
- `next`: 현재 대상만 건너뜀
- `auto`: 규칙 또는 테스트케이스 자동 생성
- `skip`: 테스트케이스 단계에서 현재 요구사항 건너뜀

### 3. 문서 생성

질문 수집이 끝나면 문서를 생성합니다.

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py render-doc <session-id>
```

문서는 기본적으로 아래 위치에 생성됩니다.

```text
홈화면 기획문서/기획자용/{slugified-title}.md
```

### 4. Figma 스크린샷 연동

필요한 스크린샷 목록을 먼저 출력합니다.

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py figma-manifest <session-id>
```

예시 출력:

```json
[
  {
    "screen_name": "홈 메인 화면",
    "figma_url": "https://figma.com/design/abc123/Home?node-id=1-2",
    "file_key": "abc123",
    "node_id": "1:2",
    "output_path": "홈화면 기획문서/이미지/홈-메인-화면.png"
  }
]
```

이 manifest를 기준으로 에이전트나 별도 도구가 Figma 스크린샷을 저장한 뒤, 저장 경로를 세션에 연결합니다.

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py attach-screenshot <session-id> \
  --screen-name "홈 메인 화면" \
  --image-path "홈화면 기획문서/이미지/홈-메인-화면.png"
```

주석 이미지 생성:

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py annotate <session-id> \
  --image-root "홈화면 기획문서/이미지" \
  --output-root "홈화면 기획문서/이미지-주석-영역-한글"
```

기본 경로는 Figma MCP `get_screenshot` 기반 흐름을 전제로 하며, Python 스크립트가 MCP를 직접 호출하지는 않습니다.

## 저장소 구조

```text
plugin-planning-wireframe/
├── .claude/
│   └── commands/
├── .claude-plugin/
│   ├── marketplace.json
│   └── plugin.json
├── .cursor/
│   └── rules/
├── .cursor-plugin/
│   └── plugin.json
├── CLAUDE.md
├── commands/
├── skills/
│   └── planning-wireframe/
│       ├── SKILL.md
│       ├── USAGE.md
│       ├── state-schema.md
│       ├── references/
│       ├── templates/
│       └── scripts/
├── .planning-wireframe/
├── .gitignore
├── CONTRIBUTING.md
├── LICENSE
├── README.md
└── requirements.txt
```

핵심 디렉터리 역할:

- `.claude-plugin/marketplace.json`: Claude Code 마켓플레이스 정의
- `.claude-plugin/plugin.json`: Claude Code 플러그인 정의
- `.cursor-plugin/plugin.json`: Cursor 플러그인 메타데이터
- `.cursor/rules/planning-wireframe.mdc`: Cursor 프로젝트 규칙
- `CLAUDE.md`: Claude Code 프로젝트 메모리
- `.claude/commands/planning-wireframe.md`: 로컬 개발용 Claude Code 커맨드
- `commands/planning-wireframe.md`: Claude Code 플러그인 커맨드
- `skills/planning-wireframe/SKILL.md`: 스킬 설명과 표준 사용 규칙
- `skills/planning-wireframe/USAGE.md`: 실제 명령 예시
- `skills/planning-wireframe/state-schema.md`: 세션 YAML 구조 설명
- `skills/planning-wireframe/templates/`: 최종 문서 템플릿
- `skills/planning-wireframe/references/`: 보조 참고 문서
- `skills/planning-wireframe/scripts/`: 질문, 저장, 렌더링, 검증 로직
- `.planning-wireframe/state/`: 세션 상태 YAML
- `.planning-wireframe/output/`: 런타임 출력 기본 경로
- `.planning-wireframe/tmp/`: 임시 파일
- `.planning-wireframe/scratch/`: 작업 메모
- `.planning-wireframe/debug/`: 디버그 산출물

## 동작 원리

### 1. `planning_runner.py`가 전체 흐름을 오케스트레이션

공개 엔트리포인트는 아래 명령 하나입니다.

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py <command>
```

지원 명령:

- `list`
- `init`
- `status`
- `next`
- `answer`
- `render-doc`
- `figma-manifest`
- `attach-screenshot`
- `annotate`
- `validate`

도구별 역할:

- Cursor는 `.cursor-plugin/plugin.json`과 `.cursor/rules/planning-wireframe.mdc`를 통해 워크플로우를 인식합니다.
- Claude Code는 `.claude-plugin/marketplace.json`과 `.claude-plugin/plugin.json`을 통해 마켓플레이스/플러그인으로 설치할 수 있습니다.
- Claude Code 로컬 개발 환경에서는 `CLAUDE.md`와 `.claude/commands/planning-wireframe.md`를 통해 같은 워크플로우를 바로 테스트할 수 있습니다.
- 실제 상태 변경, 문서 생성, 후처리는 모두 Python CLI가 수행합니다.

### 2. 질문 흐름은 코드로 고정

`question_flow.py`가 질문 순서, 질문 포맷, 제어 입력, 완료 판정을 관리합니다.  
즉, 사용자는 자유 입력을 하더라도 저장 구조는 정해진 단계와 라벨에 맞춰 정규화됩니다.

### 3. 세션 상태는 YAML로 저장

모든 진행 상태는 아래 경로에 저장됩니다.

```text
.planning-wireframe/state/{session_id}.yaml
```

`session_state.py`가 기본 상태 생성, 누락 키 보정, 저장, 로드, 검증을 담당합니다. 이 구조 덕분에 작업을 중간에 멈췄다가 같은 세션 ID로 다시 이어서 진행할 수 있습니다.

### 4. 문서 생성은 상태 기반 렌더링

`document_renderer.py`는 세션 상태를 읽어 템플릿에 맞는 마크다운 문서로 렌더링합니다.  
즉, 문서 생성은 대화 로그를 그대로 붙이는 방식이 아니라, 정규화된 상태 데이터를 표와 섹션으로 재구성하는 방식입니다.

### 5. Figma 연동은 manifest 중심

이 저장소의 Python 코드는 Figma MCP를 직접 호출하지 않습니다.

대신 아래 흐름으로 동작합니다.

1. `figma-manifest`가 필요한 스크린샷 목록을 JSON으로 출력
2. 외부 에이전트 또는 도구가 해당 정보를 바탕으로 스크린샷 저장
3. `attach-screenshot`이 저장 경로를 세션에 반영
4. `annotate`가 저장된 정보와 영역 좌표를 바탕으로 주석 이미지 생성

즉, Figma 캡처와 문서 워크플로우를 느슨하게 분리해서 운영할 수 있는 구조입니다.

## 주요 스크립트

- `planning_runner.py`: 공개 CLI 엔트리포인트
- **`planning_orchestrator.py`: SubAgent 워크플로우 오케스트레이터**
- `question_flow.py`: 단계별 질문, 파서, 완료 판정
- `session_state.py`: 세션 상태 생성/저장/로드/검증
- `storage_paths.py`: 런타임 경로 유틸리티
- `document_renderer.py`: 최종 문서 렌더링
- `figma_utils.py`: Figma URL 파싱과 manifest 생성
- `generate_image_annotations.py`: 주석 이미지 생성
- `section_patch.py`: 문서 섹션 패치 유틸
- `validate_skill.py`: 스킬 구조 검증
- `smoke_test.py`: 비대화형 E2E 스모크 테스트

## 환경 변수

기본 저장 경로를 바꾸고 싶다면 아래 환경 변수를 사용할 수 있습니다.

```bash
export PLANNING_WIREFRAME_STATE_DIR="/path/to/state"
export PLANNING_WIREFRAME_OUTPUT_DIR="/path/to/output"
```

## 검증

```bash
python3 -m py_compile skills/planning-wireframe/scripts/*.py
python3 skills/planning-wireframe/scripts/validate_skill.py
python3 skills/planning-wireframe/scripts/smoke_test.py
```

권장 순서:

1. `validate_skill.py`로 구조 검증
2. `smoke_test.py`로 CLI 흐름 검증
3. 실제 세션 생성 후 `render-doc`까지 수동 확인

## 참고 문서

- `skills/planning-wireframe/SKILL.md`
- `skills/planning-wireframe/USAGE.md`
- `skills/planning-wireframe/state-schema.md`
- `skills/planning-wireframe/scripts/README.md`

## 라이선스

MIT License. 자세한 내용은 `LICENSE`를 참고하세요.
