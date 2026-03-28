#!/usr/bin/env python3
"""
Planning wireframe orchestrator for SubAgent-based workflow.

Author: JunyoungJung
Date: 2026-03-28
"""

from __future__ import annotations

import argparse
import json
from typing import Any

from question_flow import STEP_SEQUENCE
from session_state import (
    ensure_defaults,
    has_figma_targets,
    load_session,
    validate_state,
)


# Phase 정의: 각 phase는 독립적인 SubAgent로 실행
PHASES = {
    "basic": {
        "name": "기본 정보 수집",
        "steps": ["meta", "screens", "policies"],
        "completion_step": "areas",
        "description": "문서 메타데이터, 화면 목록, 공통 정책 수집",
    },
    "areas": {
        "name": "영역 정의",
        "steps": ["areas"],
        "completion_step": "requirements",
        "description": "플랫폼별, 화면별 영역 정의 및 좌표 설정",
    },
    "requirements": {
        "name": "요구사항 작성",
        "steps": ["requirements"],
        "completion_step": "rules",
        "description": "영역별 요구사항 수집 (조건/동작/예외)",
    },
    "rules": {
        "name": "규칙 정리",
        "steps": ["rules"],
        "completion_step": "testcases",
        "description": "공통 규칙 추출 및 정리",
    },
    "testcases": {
        "name": "테스트케이스 작성",
        "steps": ["testcases"],
        "completion_step": "document_generation",
        "description": "요구사항별 테스트케이스 생성",
    },
    "document": {
        "name": "문서 생성",
        "steps": ["document_generation"],
        "completion_step": "review",
        "description": "수집된 데이터를 기반으로 마크다운 문서 생성",
    },
    "figma": {
        "name": "Figma 처리",
        "steps": ["review"],
        "completion_step": "figma_completed",
        "description": "Figma 스크린샷 다운로드 및 주석 이미지 생성",
    },
}

PHASE_ORDER = ["basic", "areas", "requirements", "rules", "testcases", "document", "figma"]


def get_current_phase(state: dict[str, Any]) -> str | None:
    """현재 상태에서 실행해야 할 phase를 반환합니다."""
    normalized = ensure_defaults(state)

    for phase_id in PHASE_ORDER:
        if not is_phase_complete(normalized, phase_id):
            return phase_id

    return None


def get_step_index(step: str) -> int:
    """STEP_SEQUENCE 기준 단계 순서를 반환합니다."""
    try:
        return STEP_SEQUENCE.index(step)
    except ValueError:
        return len(STEP_SEQUENCE)


def has_reached_step(state: dict[str, Any], target_step: str) -> bool:
    """현재 세션이 특정 단계 이상으로 진행됐는지 반환합니다."""
    normalized = ensure_defaults(state)
    current_step = normalized["progress"]["current_step"]
    completed_steps = normalized["progress"].get("completed_steps", [])
    return (
        current_step == target_step
        or target_step in completed_steps
        or get_step_index(current_step) > get_step_index(target_step)
    )


def is_phase_complete(state: dict[str, Any], phase: str) -> bool:
    """Phase가 실제 진행 상태 기준으로 완료되었는지 반환합니다."""
    normalized = ensure_defaults(state)

    if phase == "figma" and not has_figma_targets(normalized):
        return has_reached_step(normalized, "review")

    return has_reached_step(normalized, PHASES[phase]["completion_step"])


def validate_phase_completion(state: dict[str, Any], phase: str) -> tuple[bool, list[str]]:
    """Phase 완료 여부를 검증합니다."""
    normalized = ensure_defaults(state)
    errors: list[str] = []
    
    if phase == "basic":
        # meta 검증
        metadata = normalized.get("metadata", {})
        required_meta = ["title", "purpose", "target_readers", "author", "platforms"]
        for key in required_meta:
            if not metadata.get(key):
                errors.append(f"메타데이터 누락: {key}")
        
        # screens 검증 (선택사항이지만 있으면 필드 검증)
        screens = normalized.get("screens", [])
        for idx, screen in enumerate(screens):
            if not screen.get("name"):
                errors.append(f"화면 {idx}번: 화면명 누락")
    
    elif phase == "areas":
        # areas 검증
        areas = normalized.get("areas", [])
        if not areas:
            errors.append("영역이 하나도 정의되지 않았습니다")
        for idx, area in enumerate(areas):
            if not area.get("id"):
                errors.append(f"영역 {idx}번: ID 누락")
            if not area.get("name"):
                errors.append(f"영역 {idx}번: 이름 누락")
    
    elif phase == "requirements":
        # requirements 검증
        requirements = normalized.get("requirements", [])
        if not requirements:
            errors.append("요구사항이 하나도 작성되지 않았습니다")
        for idx, req in enumerate(requirements):
            if not req.get("condition"):
                errors.append(f"요구사항 {idx}번: 조건 누락")
            if not req.get("action"):
                errors.append(f"요구사항 {idx}번: 동작 누락")
    
    elif phase == "rules":
        # rules 검증 (선택사항이므로 경고만)
        rules = normalized.get("rules", [])
        if not rules:
            errors.append("⚠️ 규칙이 없습니다 (계속 진행 가능)")
    
    elif phase == "testcases":
        # testcases 검증
        testcases = normalized.get("testcases", [])
        if not testcases:
            errors.append("테스트케이스가 하나도 작성되지 않았습니다")
    
    elif phase == "document":
        # document 검증
        document = normalized.get("document", {})
        if not document.get("path"):
            errors.append("문서 경로가 설정되지 않았습니다")
    
    elif phase == "figma":
        # figma 검증 (선택사항이므로 경고만)
        screens_with_figma = [
            s for s in normalized.get("screens", [])
            if s.get("figma_url")
        ]
        if not screens_with_figma:
            errors.append("⚠️ Figma URL이 설정된 화면이 없습니다")

    if not is_phase_complete(normalized, phase):
        completion_step = PHASES[phase]["completion_step"]
        current_step = normalized["progress"]["current_step"]
        errors.append(
            "진행 상태 미완료: "
            f"current_step='{current_step}', "
            f"expected completion_step='{completion_step}'"
        )
    
    # 경고(⚠️)는 에러로 취급하지 않음
    critical_errors = [e for e in errors if not e.startswith("⚠️")]
    return len(critical_errors) == 0, errors


def build_phase_prompt(state: dict[str, Any], phase: str) -> str:
    """SubAgent에게 전달할 phase별 프롬프트를 생성합니다."""
    normalized = ensure_defaults(state)
    session_id = normalized["session_id"]
    phase_info = PHASES[phase]
    
    base_instructions = f"""
당신은 planning-wireframe 플러그인의 '{phase_info['name']}' phase를 담당하는 SubAgent입니다.

**세션 ID**: {session_id}

**Phase 목적**: {phase_info['description']}

**담당 단계**: {', '.join(phase_info['steps'])}

**작업 방식**:
1. `python3 skills/planning-wireframe/scripts/planning_runner.py next {session_id}` 로 질문 확인
2. 사용자에게 질문을 전달하고 답변 수집
3. `python3 skills/planning-wireframe/scripts/planning_runner.py answer {session_id} --text "답변"` 로 반영
4. 해당 phase의 모든 단계가 완료될 때까지 반복

**중요 규칙**:
- 사용자 응답은 한국어로 간결하게 정리
- 제어 입력(없음, done, next, auto, skip)을 적절히 안내
- phase 완료 시 명확히 알림
- 다른 phase의 작업은 절대 수행하지 말 것
"""
    
    # Phase별 추가 가이드
    if phase == "basic":
        base_instructions += """
**Phase 가이드**:
- meta: 필수 항목(제목, 목적, 독자, 작성자, 플랫폼) 모두 입력 필요
- screens: 여러 화면을 한 번에 입력 가능 (빈 줄 또는 --- 구분)
- policies: 공통 정책 수집, 없으면 '없음' 입력

**완료 조건**:
- meta의 모든 필수 항목 입력 완료
- current_step이 'areas'로 변경됨
"""
    
    elif phase == "areas":
        base_instructions += """
**Phase 가이드**:
- 네이밍 규칙 먼저 확정 (기본값 DW 또는 사용자 정의)
- 플랫폼 x 화면 조합별로 영역 정의
- 좌표는 0.0~1.0 범위 (x0,y0,x1,y1)
- 'next'로 현재 화면 건너뛰기 가능

**완료 조건**:
- 모든 플랫폼/화면 조합 처리 완료
- current_step이 'requirements'로 변경됨
"""
    
    elif phase == "requirements":
        base_instructions += """
**Phase 가이드**:
- 각 영역별로 요구사항 작성
- 조건/동작/예외 형식
- 'next' 또는 '없음'으로 영역 건너뛰기 가능

**완료 조건**:
- 모든 영역에 대해 처리 완료 (건너뛰기 포함)
- current_step이 'rules'로 변경됨
"""
    
    elif phase == "rules":
        base_instructions += """
**Phase 가이드**:
- 'auto' 입력 시 자동 생성 추천
- 수동 입력 시 플랫폼/규칙 형식
- 규칙이 없으면 '없음' 또는 'done' 입력

**완료 조건**:
- current_step이 'testcases'로 변경됨
"""
    
    elif phase == "testcases":
        base_instructions += """
**Phase 가이드**:
- 각 요구사항별로 테스트케이스 작성
- 'auto' 입력 시 자동 생성 추천
- 'skip' 또는 'next'로 요구사항 건너뛰기 가능

**완료 조건**:
- 모든 요구사항 처리 완료
- current_step이 'document_generation'으로 변경됨
"""
    
    elif phase == "document":
        base_instructions += f"""
**Phase 가이드**:
- `python3 skills/planning-wireframe/scripts/planning_runner.py render-doc {session_id}` 실행
- 생성된 문서 경로 확인

**완료 조건**:
- 문서 생성 성공
- Figma 대상이 있으면 status가 'review'로 변경됨
- Figma 대상이 없으면 status가 'completed'로 변경됨
"""
    
    elif phase == "figma":
        base_instructions += f"""
**Phase 가이드**:
1. Figma manifest 생성:
   `python3 skills/planning-wireframe/scripts/planning_runner.py figma-manifest {session_id}`

2. 각 화면별로 Figma 스크린샷 다운로드 (plugin-figma-figma MCP 사용):
   - manifest의 figma_url, node_id, output_path 사용
   - get_screenshot 호출하여 이미지 저장

3. 스크린샷 경로 연결:
   `python3 skills/planning-wireframe/scripts/planning_runner.py attach-screenshot {session_id} --screen-name "..." --image-path "..."`

4. 주석 이미지 생성:
   `python3 skills/planning-wireframe/scripts/planning_runner.py annotate {session_id} --image-root 홈화면\\ 기획문서/이미지 --output-root 홈화면\\ 기획문서/이미지-주석-영역-한글`

5. 주석 생성 없이 Figma phase만 완료 처리해야 한다면:
   `python3 skills/planning-wireframe/scripts/planning_runner.py complete-figma {session_id}`

**완료 조건**:
- 모든 스크린샷 다운로드 및 주석 생성 완료
- current_step이 'figma_completed'로 변경됨
"""
    
    # 현재 상태 요약 추가
    status_summary = f"""
**현재 상태**:
- status: {normalized['status']}
- current_step: {normalized['progress']['current_step']}
- screens: {len(normalized.get('screens', []))}개
- policies: {len(normalized.get('policies', []))}개
- areas: {len(normalized.get('areas', []))}개
- requirements: {len(normalized.get('requirements', []))}개
- rules: {len(normalized.get('rules', []))}개
- testcases: {len(normalized.get('testcases', []))}개
"""
    
    return base_instructions + "\n" + status_summary


def command_run(args: argparse.Namespace) -> int:
    """특정 phase를 SubAgent로 실행합니다."""
    session_id = args.session_id
    phase = args.phase
    
    if phase not in PHASES:
        print(f"오류: 유효하지 않은 phase입니다: {phase}")
        print(f"사용 가능한 phase: {', '.join(PHASES.keys())}")
        return 1
    
    state = load_session(session_id)
    if not state:
        print(f"오류: 세션을 찾을 수 없습니다: {session_id}")
        return 1
    
    errors = validate_state(state)
    if errors:
        print("세션 상태 검증 실패:")
        for error in errors:
            print(f"  - {error}")
        return 1
    
    # Phase 프롬프트 생성 및 출력
    prompt = build_phase_prompt(state, phase)
    
    output = {
        "session_id": session_id,
        "phase": phase,
        "phase_name": PHASES[phase]["name"],
        "description": PHASES[phase]["description"],
        "prompt": prompt,
    }
    
    print(json.dumps(output, ensure_ascii=False, indent=2))
    return 0


def command_validate_phase(args: argparse.Namespace) -> int:
    """Phase 완료 여부를 검증합니다."""
    session_id = args.session_id
    phase = args.phase
    
    if phase not in PHASES:
        print(f"오류: 유효하지 않은 phase입니다: {phase}")
        return 1
    
    state = load_session(session_id)
    if not state:
        print(f"오류: 세션을 찾을 수 없습니다: {session_id}")
        return 1
    
    is_valid, errors = validate_phase_completion(state, phase)
    
    if is_valid:
        print(f"✅ Phase '{phase}' 완료 검증 통과")
        for error in errors:
            if error.startswith("⚠️"):
                print(error)
    else:
        print(f"❌ Phase '{phase}' 완료 검증 실패:")
        for error in errors:
            print(f"  - {error}")
        return 1
    
    return 0


def command_next_phase(args: argparse.Namespace) -> int:
    """현재 phase 다음에 실행할 phase를 출력합니다."""
    session_id = args.session_id
    
    state = load_session(session_id)
    if not state:
        print(f"오류: 세션을 찾을 수 없습니다: {session_id}")
        return 1
    
    current_phase = get_current_phase(state)
    if not current_phase:
        print("모든 phase가 완료되었습니다.")
        return 0
    
    current_idx = PHASE_ORDER.index(current_phase)
    if current_idx >= len(PHASE_ORDER) - 1:
        print(f"현재 phase '{current_phase}'가 마지막입니다.")
        return 0
    
    next_phase = PHASE_ORDER[current_idx + 1]
    print(f"다음 phase: {next_phase} ({PHASES[next_phase]['name']})")
    return 0


def command_status(args: argparse.Namespace) -> int:
    """세션의 phase별 진행 상태를 출력합니다."""
    session_id = args.session_id
    
    state = load_session(session_id)
    if not state:
        print(f"오류: 세션을 찾을 수 없습니다: {session_id}")
        return 1
    
    current_phase = get_current_phase(state)
    current_step = state["progress"]["current_step"]
    
    print(f"세션 ID: {session_id}")
    print(f"현재 단계: {current_step}")
    print(f"현재 Phase: {current_phase or '완료'}")
    print("\nPhase별 진행 상태:")
    
    for phase_id in PHASE_ORDER:
        phase = PHASES[phase_id]
        is_current = phase_id == current_phase

        is_completed = is_phase_complete(state, phase_id)
        status_icon = "✅" if is_completed else ("🔄" if is_current else "⏳")
        print(f"{status_icon} {phase_id}: {phase['name']}")
    
    return 0


def command_auto_run(args: argparse.Namespace) -> int:
    """모든 phase를 순차적으로 SubAgent로 실행합니다."""
    session_id = args.session_id
    
    state = load_session(session_id)
    if not state:
        print(f"오류: 세션을 찾을 수 없습니다: {session_id}")
        return 1
    
    current_phase = get_current_phase(state)
    if not current_phase:
        print("모든 phase가 이미 완료되었습니다.")
        return 0
    
    phases_to_run = PHASE_ORDER[PHASE_ORDER.index(current_phase):]
    
    print(f"실행할 phase: {', '.join(phases_to_run)}")
    print("\n각 phase는 독립적인 SubAgent로 실행됩니다.")
    print("에이전트가 Task tool을 사용하여 각 phase를 순차적으로 실행하도록 해야 합니다.\n")
    
    for phase in phases_to_run:
        phase_info = PHASES[phase]
        print(f"📋 Phase: {phase} ({phase_info['name']})")
        print(f"   설명: {phase_info['description']}")
        print(f"   단계: {', '.join(phase_info['steps'])}")
        print()
    
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Planning wireframe orchestrator for SubAgent workflow"
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # run: 특정 phase 실행
    run_parser = subparsers.add_parser(
        "run",
        help="특정 phase를 SubAgent로 실행 (프롬프트 출력)"
    )
    run_parser.add_argument("session_id", help="세션 ID")
    run_parser.add_argument("phase", choices=list(PHASES.keys()), help="실행할 phase")
    run_parser.set_defaults(func=command_run)
    
    # validate-phase: phase 완료 검증
    validate_parser = subparsers.add_parser(
        "validate-phase",
        help="특정 phase의 완료 여부 검증"
    )
    validate_parser.add_argument("session_id", help="세션 ID")
    validate_parser.add_argument("phase", choices=list(PHASES.keys()), help="검증할 phase")
    validate_parser.set_defaults(func=command_validate_phase)
    
    # next-phase: 다음 phase 확인
    next_parser = subparsers.add_parser(
        "next-phase",
        help="다음 실행할 phase 확인"
    )
    next_parser.add_argument("session_id", help="세션 ID")
    next_parser.set_defaults(func=command_next_phase)
    
    # status: phase별 진행 상태
    status_parser = subparsers.add_parser(
        "status",
        help="세션의 phase별 진행 상태 확인"
    )
    status_parser.add_argument("session_id", help="세션 ID")
    status_parser.set_defaults(func=command_status)
    
    # auto-run: 전체 phase 자동 실행 가이드
    auto_parser = subparsers.add_parser(
        "auto-run",
        help="모든 phase를 순차적으로 실행하기 위한 가이드 출력"
    )
    auto_parser.add_argument("session_id", help="세션 ID")
    auto_parser.set_defaults(func=command_auto_run)
    
    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        return args.func(args)
    except ValueError as error:
        print(f"오류: {error}")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
