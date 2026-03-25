# Planning Wireframe

인터뷰 기반으로 구조화된 기획 문서와 와이어프레임 산출물을 만드는 `skill + Python CLI` 저장소입니다.

GitHub: `https://github.com/Jimmy-Jung/plugin-planning-wireframe`

## 무엇을 하는 저장소인가

이 저장소는 일반적인 VS Code 마켓플레이스 확장 프로그램이 아닙니다. 핵심은 아래 두 가지입니다.

- `skills/planning-wireframe/SKILL.md`: 에이전트가 따라야 할 스킬 정의
- `skills/planning-wireframe/scripts/planning_runner.py`: 실제 실행을 담당하는 CLI 러너

즉, 이 저장소는 "설치형 UI 플러그인"보다 "기획 문서 작성 워크플로우를 재사용 가능한 스킬과 스크립트로 묶은 저장소"에 가깝습니다.

주요 기능:

- 인터뷰 기반 질문 흐름 관리
- 세션 상태 YAML 저장 및 재개
- 구조화된 마크다운 기획 문서 생성
- Figma 스크린샷 manifest 생성
- 화면별 스크린샷 연결
- 주석 이미지 생성

## 설치 방법

### Cursor에서 플러그인으로 설치

1. Cursor 설정 열기
2. Plugins 섹션으로 이동
3. "Add from URL" 클릭
4. GitHub URL 입력: `https://github.com/Jimmy-Jung/plugin-planning-wireframe`

설치 후 스킬이 자동으로 사용 가능해집니다.

### Claude Desktop에서 설치

MCP 설정 파일(`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS)에 추가:

```json
{
  "mcpServers": {
    "planning-wireframe": {
      "command": "npx",
      "args": ["-y", "@cursor/planning-wireframe-mcp"]
    }
  }
}
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

## 플러그인 구조

이 저장소는 Cursor 플러그인으로 동작하도록 설계되었습니다.

- `.cursor-plugin/plugin.json`: 플러그인 메타데이터
- `skills/`: 에이전트가 사용할 스킬 정의
- `scripts/`: Python CLI 실행 스크립트

플러그인 설치 시 에이전트가 자동으로 스킬을 인식하고 사용할 수 있습니다.

## 스킬 사용법

### 전체 흐름

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
├── .cursor-plugin/
│   └── plugin.json
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
