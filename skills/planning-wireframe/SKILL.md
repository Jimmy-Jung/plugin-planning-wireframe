---
name: planning-wireframe
description: Interview-based planning document and wireframe generation skill. Guides users through structured questioning to collect requirements, screens, policies, and test cases, then generates professional documentation with Figma screenshot integration. Use when creating planning documents, product requirements, wireframes, screen definitions, or structured documentation workflows.
---

# Planning Wireframe 스킬

> @-tracking: skills planning-wireframe

`/기획-와이어`는 실행형 CLI 러너를 중심으로 동작합니다. 질문 흐름, 상태 저장, 문서 생성, Figma 스크린샷 매핑, 주석 이미지 생성까지 모두 `planning_runner.py`가 오케스트레이션합니다.

## 핵심 원칙

- 질문 흐름은 CLI가 관리합니다.
- 세션 상태는 YAML로 저장합니다.
- 문서 생성은 `document_renderer.py`를 통해 수행합니다.
- Figma 표준 경로는 `plugin-figma-figma/get_screenshot` 입니다.
- Talk to Figma + WebSocket은 대안 경로로만 취급합니다.
- **SubAgent 기반 워크플로우를 통해 context window 절약**

## 워크플로우 선택

### 기본 워크플로우 (순차 실행)

단일 세션에서 모든 단계를 순차적으로 처리합니다. 간단한 프로젝트나 학습용으로 적합합니다.

### SubAgent 워크플로우 (권장)

각 phase를 독립적인 SubAgent로 실행하여 context window를 절약합니다. 복잡한 프로젝트나 긴 인터뷰에 적합합니다.

**Phase 구조**:
- `basic`: 메타데이터, 화면 목록, 공통 정책
- `areas`: 영역 정의
- `requirements`: 요구사항 작성
- `rules`: 규칙 정리
- `testcases`: 테스트케이스 작성
- `document`: 문서 생성
- `figma`: Figma 스크린샷 처리

**오케스트레이터 명령**:

```bash
# Phase별 진행 상태 확인
python3 skills/planning-wireframe/scripts/planning_orchestrator.py status {session_id}

# 특정 phase 실행 (SubAgent 프롬프트 출력)
python3 skills/planning-wireframe/scripts/planning_orchestrator.py run {session_id} {phase}

# Phase 완료 검증
python3 skills/planning-wireframe/scripts/planning_orchestrator.py validate-phase {session_id} {phase}

# 다음 phase 확인
python3 skills/planning-wireframe/scripts/planning_orchestrator.py next-phase {session_id}

# 전체 phase 자동 실행 가이드
python3 skills/planning-wireframe/scripts/planning_orchestrator.py auto-run {session_id}
```

## 표준 명령

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py list
python3 skills/planning-wireframe/scripts/planning_runner.py init
python3 skills/planning-wireframe/scripts/planning_runner.py status {session_id}
python3 skills/planning-wireframe/scripts/planning_runner.py next {session_id}
python3 skills/planning-wireframe/scripts/planning_runner.py answer {session_id} --text "..."
python3 skills/planning-wireframe/scripts/planning_runner.py render-doc {session_id}
python3 skills/planning-wireframe/scripts/planning_runner.py figma-manifest {session_id}
python3 skills/planning-wireframe/scripts/planning_runner.py attach-screenshot {session_id} --screen-name "..." --image-path "..."
python3 skills/planning-wireframe/scripts/planning_runner.py annotate {session_id} --image-root 홈화면\ 기획문서/이미지 --output-root 홈화면\ 기획문서/이미지-주석-영역-한글
python3 skills/planning-wireframe/scripts/planning_runner.py validate
```

## 실행 순서 (기본 워크플로우)

### Phase 0. 세션 준비

1. 기존 세션 확인:
   ```bash
   python3 skills/planning-wireframe/scripts/planning_runner.py list
   ```
2. 새 세션 시작:
   ```bash
   python3 skills/planning-wireframe/scripts/planning_runner.py init
   ```
3. 현재 상태 확인:
   ```bash
   python3 skills/planning-wireframe/scripts/planning_runner.py status {session_id}
   ```

### Phase 1. 질문 수집

질문 흐름은 아래 순서로 고정됩니다.

1. `meta`
2. `screens`
3. `policies`
4. `areas`
5. `requirements`
6. `rules`
7. `testcases`
8. `document_generation`
9. `review`

각 단계는 아래 두 명령으로 진행합니다.

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py next {session_id}
python3 skills/planning-wireframe/scripts/planning_runner.py answer {session_id} --text "답변"
```

### 제어 입력

러너는 아래 제어 입력을 지원합니다.

- `없음`: 현재 단계의 값을 비워 두고 진행
- `done`: 현재 단계 입력 종료
- `next`: 현재 대상만 건너뛰고 다음 대상으로 이동
- `auto`: 규칙/테스트케이스 자동 생성
- `skip`: 테스트케이스 단계에서 현재 요구사항 건너뛰기

### 입력 규칙

- `screens`, `policies`, `areas`의 여러 항목은 빈 줄 또는 `---`로 구분합니다.
- `areas`는 네이밍 규칙 질문을 먼저 처리한 뒤 `플랫폼 x 화면` 순서로 진행합니다.
- `requirements`는 `areas` 순서대로 한 영역씩 입력합니다.
- `rules`는 `auto` 또는 수동 블록 입력을 받습니다.
- `testcases`는 `requirements` 순서대로 한 요구사항씩 입력합니다.

## 문서 생성

질문 수집이 끝나면 `current_step=document_generation` 상태가 됩니다.

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py render-doc {session_id}
```

동작:

- `document_renderer.py`로 문서 생성
- 문서 경로를 `홈화면 기획문서/기획자용/{slugified-title}.md`로 고정
- `document.path`, `document.sections`, `status`, `progress.current_step` 갱신
- 완료 후 `status=review`, `current_step=review`

## Figma 스크린샷 경로

표준 경로는 Python이 직접 MCP를 호출하지 않고 manifest를 출력하는 방식입니다.

1. 필요한 스크린샷 manifest 출력:
   ```bash
   python3 skills/planning-wireframe/scripts/planning_runner.py figma-manifest {session_id}
   ```
2. 에이전트가 `plugin-figma-figma/get_screenshot` 호출
3. 저장된 이미지 경로를 세션에 기록:
   ```bash
   python3 skills/planning-wireframe/scripts/planning_runner.py attach-screenshot {session_id} \
     --screen-name "홈 메인 화면" \
     --image-path "홈화면 기획문서/이미지/홈-메인-화면.png"
   ```
4. 주석 이미지 생성:
   ```bash
   python3 skills/planning-wireframe/scripts/planning_runner.py annotate {session_id} \
     --image-root 홈화면\ 기획문서/이미지 \
     --output-root 홈화면\ 기획문서/이미지-주석-영역-한글
   ```

## 상태 파일

세션은 아래 경로에 저장됩니다.

```text
.planning-wireframe/state/{session_id}.yaml
```

실제 구현은 `scripts/session_state.py`와 `scripts/storage_paths.py`를 사용합니다.

## 검증

```bash
python3 -m py_compile skills/planning-wireframe/scripts/*.py
python3 skills/planning-wireframe/scripts/validate_skill.py
python3 skills/planning-wireframe/scripts/smoke_test.py
```

## SubAgent 워크플로우 상세

### Phase별 실행 방법

각 phase는 `Task` tool을 사용하여 독립적인 SubAgent로 실행합니다.

```python
# 예시: basic phase 실행
Task(
    description="기본 정보 수집",
    prompt="""
    planning-2026-03-28-1304 세션의 basic phase를 완료하세요.
    
    1. 오케스트레이터로 phase 프롬프트 가져오기:
       python3 skills/planning-wireframe/scripts/planning_orchestrator.py run planning-2026-03-28-1304 basic
    
    2. 출력된 프롬프트의 지시사항을 따라 작업 수행
    
    3. 완료 후 검증:
       python3 skills/planning-wireframe/scripts/planning_orchestrator.py validate-phase planning-2026-03-28-1304 basic
    """,
    subagent_type="generalPurpose"
)
```

### Phase 간 상태 공유

모든 phase는 동일한 세션 YAML 파일을 공유합니다. 각 SubAgent는:
1. 세션 상태를 로드
2. 담당 phase의 작업 수행
3. 상태를 저장
4. 다음 phase로 자동 전환

### 장점

- **Context Window 절약**: 각 phase가 독립적인 context를 사용
- **중단/재개**: 각 phase 완료 후 중단하고 나중에 재개 가능
- **병렬 실험**: 여러 세션을 동시에 진행 가능
- **검증**: Phase별 완료 검증으로 품질 보장

## 참고 파일

- 템플릿: `skills/planning-wireframe/templates/기획-템플릿.md`
- 세션 상태 유틸: `skills/planning-wireframe/scripts/session_state.py`
- 경로 유틸: `skills/planning-wireframe/scripts/storage_paths.py`
- 질문 흐름: `skills/planning-wireframe/scripts/question_flow.py`
- 러너: `skills/planning-wireframe/scripts/planning_runner.py`
- **오케스트레이터: `skills/planning-wireframe/scripts/planning_orchestrator.py`**
- Figma 유틸: `skills/planning-wireframe/scripts/figma_utils.py`
- 문서 렌더러: `skills/planning-wireframe/scripts/document_renderer.py`
- 주석 생성기: `skills/planning-wireframe/scripts/generate_image_annotations.py`
