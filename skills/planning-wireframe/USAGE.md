# Planning Wireframe 사용 예시

## 기본 워크플로우 (순차 실행)

### 1. 세션 생성

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py init
python3 skills/planning-wireframe/scripts/planning_runner.py status planning-2026-03-25-1100
```

## 2. 질문 진행

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py next planning-2026-03-25-1100
python3 skills/planning-wireframe/scripts/planning_runner.py answer planning-2026-03-25-1100 --text $'문서 제목: 홈탭 기획\n문서 목적: 홈 화면 구조와 동작을 정의한다\n대상 독자: 기획자, QA, 개발자\n작성자: 모바일팀_홍길동\n대상 플랫폼: iPhone\n범위 제외: 타임테이블 기능'
```

다음 단계도 같은 방식으로 반복합니다.

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py next planning-2026-03-25-1100
python3 skills/planning-wireframe/scripts/planning_runner.py answer planning-2026-03-25-1100 --text $'화면명: 홈 메인 화면\n목적: 오늘의 일정과 학습 현황을 보여준다\n핵심 노출: 상단 카드, 일정 리스트, 타이머\n상태 차이: 오늘이면 실행 버튼 표시\n주요 액션: 일정 탭, 타이머 시작\nFigma URL: https://figma.com/design/abc123/Home?node-id=1-2\n비고: 없음'
```

## 3. 문서 생성

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py render-doc planning-2026-03-25-1100
```

생성 결과:

- 문서 경로: `홈화면 기획문서/기획자용/홈탭-기획.md`
- 상태: `review`

## 4. Figma manifest 출력

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py figma-manifest planning-2026-03-25-1100
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

이 JSON을 기준으로 에이전트가 MCP `get_screenshot`을 호출하고 이미지를 저장합니다.

## SubAgent 워크플로우 (권장)

Context window를 절약하기 위해 각 phase를 독립적인 SubAgent로 실행하는 방식입니다.

### 1. 세션 생성 및 상태 확인

```bash
# 세션 생성
python3 skills/planning-wireframe/scripts/planning_runner.py init \
  --title "홈탭 기획" \
  --author "모바일팀_홍길동"

# 세션 ID: planning-2026-03-28-1304

# Phase별 진행 상태 확인
python3 skills/planning-wireframe/scripts/planning_orchestrator.py status planning-2026-03-28-1304
```

출력 예시:

```
세션 ID: planning-2026-03-28-1304
현재 단계: meta
현재 Phase: basic

Phase별 진행 상태:
🔄 basic: 기본 정보 수집
⏳ areas: 영역 정의
⏳ requirements: 요구사항 작성
⏳ rules: 규칙 정리
⏳ testcases: 테스트케이스 작성
⏳ document: 문서 생성
⏳ figma: Figma 처리
```

### 2. Phase별 SubAgent 실행

#### Phase 1: basic (기본 정보 수집)

```bash
# Phase 프롬프트 가져오기
python3 skills/planning-wireframe/scripts/planning_orchestrator.py run planning-2026-03-28-1304 basic
```

에이전트가 `Task` tool을 사용하여 SubAgent 실행:

```python
Task(
    description="기본 정보 수집",
    prompt="""
    planning-2026-03-28-1304 세션의 basic phase를 완료하세요.
    
    1. Phase 프롬프트 가져오기:
       python3 skills/planning-wireframe/scripts/planning_orchestrator.py run planning-2026-03-28-1304 basic
    
    2. 출력된 JSON의 prompt 필드에 있는 지시사항을 따라 작업 수행
    
    3. 완료 후 검증:
       python3 skills/planning-wireframe/scripts/planning_orchestrator.py validate-phase planning-2026-03-28-1304 basic
    """,
    subagent_type="generalPurpose"
)
```

SubAgent는 다음 작업을 수행합니다:

```bash
# 1. 질문 확인
python3 skills/planning-wireframe/scripts/planning_runner.py next planning-2026-03-28-1304

# 2. 답변 반영 (meta)
python3 skills/planning-wireframe/scripts/planning_runner.py answer planning-2026-03-28-1304 --text $'문서 제목: 홈탭 기획\n문서 목적: 홈 화면 구조와 동작을 정의한다\n대상 독자: 기획자, QA, 개발자\n작성자: 모바일팀_홍길동\n대상 플랫폼: iPhone\n범위 제외: 타임테이블 기능'

# 3. 다음 질문 (screens)
python3 skills/planning-wireframe/scripts/planning_runner.py next planning-2026-03-28-1304

# 4. 답변 반영
python3 skills/planning-wireframe/scripts/planning_runner.py answer planning-2026-03-28-1304 --text $'화면명: 홈 메인 화면\n목적: 오늘의 일정과 학습 현황을 보여준다\n핵심 노출: 상단 카드, 일정 리스트, 타이머\n상태 차이: 오늘이면 실행 버튼 표시\n주요 액션: 일정 탭, 타이머 시작\nFigma URL: https://figma.com/design/abc123/Home?node-id=1-2\n비고: 없음'

# 5. policies 단계도 동일하게 진행...
```

Phase 완료 후 검증:

```bash
python3 skills/planning-wireframe/scripts/planning_orchestrator.py validate-phase planning-2026-03-28-1304 basic
```

#### Phase 2-5: 나머지 데이터 수집

동일한 방식으로 각 phase를 SubAgent로 실행:

```bash
# areas phase
python3 skills/planning-wireframe/scripts/planning_orchestrator.py run planning-2026-03-28-1304 areas

# requirements phase
python3 skills/planning-wireframe/scripts/planning_orchestrator.py run planning-2026-03-28-1304 requirements

# rules phase
python3 skills/planning-wireframe/scripts/planning_orchestrator.py run planning-2026-03-28-1304 rules

# testcases phase
python3 skills/planning-wireframe/scripts/planning_orchestrator.py run planning-2026-03-28-1304 testcases
```

### 3. 문서 생성 (document phase)

```bash
python3 skills/planning-wireframe/scripts/planning_orchestrator.py run planning-2026-03-28-1304 document
```

SubAgent가 실행:

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py render-doc planning-2026-03-28-1304
```

생성 결과:

- 문서 경로: `홈화면 기획문서/기획자용/홈탭-기획.md`
- 상태: `review`

### 4. Figma 처리 (figma phase)

```bash
python3 skills/planning-wireframe/scripts/planning_orchestrator.py run planning-2026-03-28-1304 figma
```

SubAgent가 실행:

```bash
# 1. Manifest 생성
python3 skills/planning-wireframe/scripts/planning_runner.py figma-manifest planning-2026-03-28-1304

# 2. Figma 스크린샷 다운로드 (plugin-figma-figma MCP 사용)
# JSON manifest의 각 항목에 대해:
# - figma_url에서 fileKey, nodeId 추출
# - get_screenshot 호출
# - output_path에 저장

# 3. 경로 연결
python3 skills/planning-wireframe/scripts/planning_runner.py attach-screenshot planning-2026-03-28-1304 \
  --screen-name "홈 메인 화면" \
  --image-path "홈화면 기획문서/이미지/홈-메인-화면.png"

# 4. 주석 이미지 생성
python3 skills/planning-wireframe/scripts/planning_runner.py annotate planning-2026-03-28-1304 \
  --image-root 홈화면\ 기획문서/이미지 \
  --output-root 홈화면\ 기획문서/이미지-주석-영역-한글
```

### 5. 자동 실행 가이드

전체 phase를 순차 실행하려면:

```bash
python3 skills/planning-wireframe/scripts/planning_orchestrator.py auto-run planning-2026-03-28-1304
```

출력:

```
실행할 phase: basic, areas, requirements, rules, testcases, document, figma

각 phase는 독립적인 SubAgent로 실행됩니다.
에이전트가 Task tool을 사용하여 각 phase를 순차적으로 실행하도록 해야 합니다.

📋 Phase: basic (기본 정보 수집)
   설명: 문서 메타데이터, 화면 목록, 공통 정책 수집
   단계: meta, screens, policies

📋 Phase: areas (영역 정의)
   설명: 플랫폼별, 화면별 영역 정의 및 좌표 설정
   단계: areas
...
```

### SubAgent 워크플로우 장점

1. **Context Window 절약**: 각 phase가 독립적인 context 사용 (최대 80% 절약)
2. **중단/재개**: Phase 단위로 작업 중단 및 재개 가능
3. **독립 검증**: 각 phase 완료 후 즉시 검증
4. **병렬 처리**: 여러 세션을 동시에 진행 가능
5. **에러 격리**: Phase별로 에러가 격리되어 전체 작업에 영향 최소화

## 5. 스크린샷 연결 및 주석 생성

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py attach-screenshot planning-2026-03-25-1100 \
  --screen-name "홈 메인 화면" \
  --image-path "홈화면 기획문서/이미지/홈-메인-화면.png"

python3 skills/planning-wireframe/scripts/planning_runner.py annotate planning-2026-03-25-1100 \
  --image-root 홈화면\ 기획문서/이미지 \
  --output-root 홈화면\ 기획문서/이미지-주석-영역-한글
```

## Talk to Figma 대안 경로

기본 경로는 `plugin-figma-figma/get_screenshot` 입니다. Talk to Figma를 써야 하는 경우는 대안 경로로만 취급합니다.

- 별도 터미널에서 `bun socket` 실행
- Figma 플러그인 연결
- 필요한 이미지/프레임을 수동 또는 별도 플로우로 확보

이 경우에도 세션 상태 갱신은 `attach-screenshot`을 사용합니다.
