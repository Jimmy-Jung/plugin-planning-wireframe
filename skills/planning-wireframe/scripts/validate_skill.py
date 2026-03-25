#!/usr/bin/env python3
"""
Planning wireframe skill validator.

Author: JunyoungJung
Date: 2026-03-25
"""

from __future__ import annotations

import sys
from pathlib import Path

from document_renderer import DEFAULT_TEMPLATE_PATH, render_document
from session_state import init_session, validate_state


ROOT = Path(__file__).resolve().parent.parent
REQUIRED_FILES = (
    ROOT / "SKILL.md",
    ROOT / "USAGE.md",
    ROOT / "state-schema.md",
    ROOT / "references" / "section-patch.md",
    ROOT / "scripts" / "README.md",
    ROOT / "scripts" / "storage_paths.py",
    ROOT / "scripts" / "generate_image_annotations.py",
    ROOT / "scripts" / "session_state.py",
    ROOT / "scripts" / "section_patch.py",
    ROOT / "scripts" / "document_renderer.py",
    ROOT / "scripts" / "question_flow.py",
    ROOT / "scripts" / "figma_utils.py",
    ROOT / "scripts" / "planning_runner.py",
    ROOT / "scripts" / "smoke_test.py",
    ROOT / "scripts" / "validate_skill.py",
    ROOT / "templates" / "기획-템플릿.md",
)
DOC_FILES = (
    ROOT / "SKILL.md",
    ROOT / "USAGE.md",
    ROOT / "scripts" / "README.md",
)
DEPRECATED_REFERENCES = (
    "templates/template.md",
    "figma-helpers.md",
)


def build_sample_state() -> dict:
    state = init_session(
        session_id="planning-validate-sample",
        title="검증용 홈탭 기획",
        author="JunyoungJung",
    )
    state["metadata"]["purpose"] = "기획 문서 렌더링 구조를 검증한다"
    state["metadata"]["target_readers"] = ["기획자", "개발자"]
    state["metadata"]["platforms"] = ["iPhone"]
    state["metadata"]["exclusions"] = "없음"
    state["screens"] = [
        {
            "name": "홈 메인 화면",
            "purpose": "주요 상태를 한 화면에서 확인한다",
            "key_exposure": "상단 카드, 리스트, 타이머",
            "state_diff": "오늘/비오늘에 따라 버튼 노출이 다르다",
            "actions": "일정 선택, 타이머 시작",
            "figma_url": "https://figma.com/design/abc123/Home?node-id=1-2",
            "notes": "검증용 데이터",
        }
    ]
    state["policies"] = [
        {
            "name": "오늘 여부",
            "description": "오늘 날짜에서만 실행 버튼을 노출한다",
            "tracking_refs": ["RULE-DW-IPHONE-001"],
        }
    ]
    state["areas"] = [
        {
            "id": "DW01",
            "type": "영역",
            "screen": "홈 메인 화면",
            "name": "상단 요약 카드",
            "policy_summary": "학습 시간과 목표 달성률을 보여준다",
            "platform": "iPhone",
        }
    ]
    state["requirements"] = [
        {
            "id": "REQ-DW-IPHONE-001",
            "area_id": "DW01",
            "area_name": "상단 요약 카드",
            "condition": "홈 진입 시",
            "action": "총 학습 시간을 표시한다",
            "exception": "데이터가 없으면 00:00:00을 표시한다",
            "platform": "iPhone",
        }
    ]
    state["rules"] = [
        {
            "id": "RULE-DW-IPHONE-001",
            "content": "오늘 날짜에서만 실행 버튼을 노출한다",
            "platform": "iPhone",
        }
    ]
    state["testcases"] = [
        {
            "id": "TC-DW-IPHONE-001",
            "req_id": "REQ-DW-IPHONE-001",
            "scenario": "홈에 진입한다",
            "expected": "총 학습 시간이 표시된다",
            "platform": "iPhone",
        }
    ]
    return state


def validate_required_files() -> list[str]:
    errors: list[str] = []
    for path in REQUIRED_FILES:
        if not path.exists():
            errors.append(f"필수 파일 누락: {path}")
    return errors


def validate_doc_references() -> list[str]:
    errors: list[str] = []
    for path in DOC_FILES:
        content = path.read_text(encoding="utf-8")
        for ref in DEPRECATED_REFERENCES:
            if ref in content:
                errors.append(f"폐기 참조 발견: {path} -> {ref}")
    return errors


def validate_rendering() -> list[str]:
    errors: list[str] = []
    state = build_sample_state()
    state_errors = validate_state(state)
    if state_errors:
        return [f"샘플 상태 오류: {error}" for error in state_errors]

    rendered = render_document(state, template_path=DEFAULT_TEMPLATE_PATH)
    required_fragments = (
        "# 검증용 홈탭 기획",
        "## 피그마 링크",
        "## iPhone 영역 정의",
        "REQ-DW-IPHONE-001",
        "TC-DW-IPHONE-001",
    )
    for fragment in required_fragments:
        if fragment not in rendered:
            errors.append(f"렌더링 결과 누락: {fragment}")
    return errors


def main() -> int:
    errors = [
        *validate_required_files(),
        *validate_doc_references(),
        *validate_rendering(),
    ]

    if errors:
        print("planning-wireframe 검증 실패")
        for error in errors:
            print(f"- {error}")
        return 1

    print("planning-wireframe 검증 통과")
    return 0


if __name__ == "__main__":
    sys.exit(main())
