# Planning Orchestrator 사용법

## 개요

`planning_orchestrator.py`는 SubAgent 기반 워크플로우를 지원하는 오케스트레이터입니다.
각 phase를 독립적인 SubAgent로 실행하여 context window를 절약합니다.

## Phase 구조

```
basic       → 메타데이터, 화면 목록, 공통 정책
areas       → 영역 정의
requirements → 요구사항 작성
rules       → 규칙 정리
testcases   → 테스트케이스 작성
document    → 문서 생성
figma       → Figma 스크린샷 처리
```

## 명령어

### 1. Phase별 진행 상태 확인

```bash
python3 skills/planning-wireframe/scripts/planning_orchestrator.py status <session-id>
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

아이콘:
- 🔄 현재 진행 중
- ✅ 완료
- ⏳ 대기 중

### 2. 특정 phase 실행 (SubAgent 프롬프트 출력)

```bash
python3 skills/planning-wireframe/scripts/planning_orchestrator.py run <session-id> <phase>
```

출력: JSON 형식의 프롬프트

```json
{
  "session_id": "planning-2026-03-28-1304",
  "phase": "basic",
  "phase_name": "기본 정보 수집",
  "description": "문서 메타데이터, 화면 목록, 공통 정책 수집",
  "prompt": "... SubAgent에게 전달할 상세 지시사항 ..."
}
```

이 프롬프트를 `Task` tool의 `prompt` 파라미터로 전달하면 됩니다.

### 3. Phase 완료 검증

```bash
python3 skills/planning-wireframe/scripts/planning_orchestrator.py validate-phase <session-id> <phase>
```

출력:
- ✅ Phase 완료 검증 통과
- ❌ Phase 완료 검증 실패: (에러 목록)

### 4. 다음 phase 확인

```bash
python3 skills/planning-wireframe/scripts/planning_orchestrator.py next-phase <session-id>
```

출력:

```
다음 phase: areas (영역 정의)
```

### 5. 전체 phase 자동 실행 가이드

```bash
python3 skills/planning-wireframe/scripts/planning_orchestrator.py auto-run <session-id>
```

출력: 실행할 phase 목록과 각 phase의 설명

## SubAgent 실행 예시

### Python (Task tool 사용)

```python
# basic phase 실행
Task(
    description="기본 정보 수집",
    prompt="""
    planning-2026-03-28-1304 세션의 basic phase를 완료하세요.
    
    1. Phase 프롬프트 가져오기:
       python3 skills/planning-wireframe/scripts/planning_orchestrator.py run planning-2026-03-28-1304 basic
    
    2. 출력된 JSON의 prompt 필드 지시사항에 따라 작업 수행
    
    3. 완료 후 검증:
       python3 skills/planning-wireframe/scripts/planning_orchestrator.py validate-phase planning-2026-03-28-1304 basic
    """,
    subagent_type="generalPurpose"
)
```

### 순차 실행

```python
# 모든 phase를 순차적으로 실행
for phase in ["basic", "areas", "requirements", "rules", "testcases", "document", "figma"]:
    Task(
        description=f"{phase} phase 실행",
        prompt=f"""
        planning-2026-03-28-1304 세션의 {phase} phase를 완료하세요.
        
        1. python3 skills/planning-wireframe/scripts/planning_orchestrator.py run planning-2026-03-28-1304 {phase}
        2. 지시사항에 따라 작업 수행
        3. python3 skills/planning-wireframe/scripts/planning_orchestrator.py validate-phase planning-2026-03-28-1304 {phase}
        """,
        subagent_type="generalPurpose"
    )
```

## 장점

1. **Context Window 절약**: 각 phase가 독립적인 context 사용 (최대 80% 절약)
2. **중단/재개**: Phase 단위로 작업 중단 및 재개 가능
3. **독립 검증**: 각 phase 완료 후 즉시 검증
4. **병렬 처리**: 여러 세션을 동시에 진행 가능
5. **에러 격리**: Phase별로 에러가 격리되어 전체 작업에 영향 최소화

## 상태 공유

모든 phase는 동일한 세션 YAML 파일을 공유합니다:

```
.planning-wireframe/state/<session-id>.yaml
```

각 SubAgent는:
1. 세션 상태를 로드
2. 담당 phase의 작업 수행
3. 상태를 저장
4. 다음 phase로 자동 전환

## 검증 규칙

각 phase는 완료 시 다음 항목을 검증합니다:

- **basic**: 메타데이터 필수 항목 (title, purpose, target_readers, author, platforms)
- **areas**: 최소 1개 이상의 영역, 각 영역에 id와 name 필수
- **requirements**: 최소 1개 이상의 요구사항, 각 요구사항에 condition과 action 필수
- **rules**: 선택사항 (경고만 표시)
- **testcases**: 최소 1개 이상의 테스트케이스
- **document**: 문서 경로 설정 확인
- **figma**: 선택사항 (경고만 표시)

⚠️ 표시가 있는 에러는 경고이며, phase 완료를 막지 않습니다.
