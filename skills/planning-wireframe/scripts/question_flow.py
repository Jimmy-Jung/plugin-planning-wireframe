#!/usr/bin/env python3
"""
Planning wireframe question flow.

Author: JunyoungJung
Date: 2026-03-25
"""

from __future__ import annotations

import re
from typing import Any

from session_state import (
    advance_cursor,
    clear_active_prompt,
    ensure_defaults,
    reset_cursor,
    update_progress,
)


STEP_SEQUENCE = [
    "meta",
    "screens",
    "policies",
    "areas",
    "requirements",
    "rules",
    "testcases",
    "document_generation",
    "review",
    "figma_completed",
]
PROMPT_IDS = {
    "meta": "meta_overview",
    "screens": "screens_collect",
    "policies": "policies_collect",
    "areas_naming": "areas_naming",
    "areas_collect": "areas_collect",
    "requirements": "requirements_collect",
    "rules": "rules_collect",
    "testcases": "testcases_collect",
}
CONTROL_WORDS = {"없음", "done", "next", "auto", "skip"}


def build_roadmap_text(state: dict[str, Any]) -> str:
    """처음 한 번만 보여줄 로드맵을 생성합니다."""
    title = state.get("metadata", {}).get("title") or "기획 문서"
    return "\n".join(
        [
            "[세션 로드맵]",
            f"이번 세션은 {title}를 구조화된 기획 문서와 와이어프레임 준비 상태로 만드는 과정입니다.",
            "1단계. 메타데이터 정리",
            "2단계. 화면 목록 정의",
            "3단계. 공통 정책 정리",
            "4단계. 화면별 영역 정의",
            "5단계. 영역별 요구사항 작성",
            "6단계. 규칙 압축",
            "7단계. 테스트케이스 작성",
            "이후 문서 생성, Figma 스크린샷 매핑, 주석 생성으로 이어집니다.",
        ]
    )


def current_area_target(state: dict[str, Any]) -> tuple[str, str] | None:
    """현재 영역 정의 대상 플랫폼/화면을 반환합니다."""
    normalized = ensure_defaults(state)
    platforms = normalized["metadata"].get("platforms", []) or ["공통"]
    screens = normalized.get("screens", [])
    cursors = normalized["progress"]["cursors"]

    platform_index = cursors.get("platform_index", 0)
    screen_index = cursors.get("screen_index", 0)

    if platform_index >= len(platforms):
        return None
    if screen_index >= len(screens):
        return None
    return platforms[platform_index], screens[screen_index]["name"]


def current_requirement_target(state: dict[str, Any]) -> dict[str, Any] | None:
    """현재 요구사항 작성 대상 영역을 반환합니다."""
    normalized = ensure_defaults(state)
    index = normalized["progress"]["cursors"].get("requirement_index", 0)
    if index >= len(normalized["areas"]):
        return None
    return normalized["areas"][index]


def current_testcase_target(state: dict[str, Any]) -> dict[str, Any] | None:
    """현재 테스트케이스 작성 대상 요구사항을 반환합니다."""
    normalized = ensure_defaults(state)
    index = normalized["progress"]["cursors"].get("testcase_index", 0)
    if index >= len(normalized["requirements"]):
        return None
    return normalized["requirements"][index]


def has_naming_rules(state: dict[str, Any]) -> bool:
    """영역 네이밍 규칙이 이미 설정되었는지 확인합니다."""
    normalized = ensure_defaults(state)
    return bool(normalized["progress"].get("naming_rules_confirmed"))


def get_prompt_payload(state: dict[str, Any]) -> dict[str, str] | None:
    """현재 상태에서 다음 질문을 반환합니다."""
    normalized = ensure_defaults(state)
    step = normalized["progress"]["current_step"]

    if step == "meta":
        return {
            "id": PROMPT_IDS["meta"],
            "step": "meta",
            "prompt": (
                "문서 메타데이터를 입력해 주세요.\n\n"
                "아래 형식으로 답하면 됩니다.\n"
                "문서 제목: ...\n"
                "문서 목적: ...\n"
                "대상 독자: 기획자, QA, PM\n"
                "작성자: ...\n"
                "대상 플랫폼: iPhone, iPad\n"
                "범위 제외: 없음"
            ),
            "answer_format": "각 항목을 `라벨: 값` 형식으로 한 줄씩 입력",
            "context": "필수 입력: 문서 제목, 문서 목적, 대상 독자, 작성자, 대상 플랫폼",
        }

    if step == "screens":
        return {
            "id": PROMPT_IDS["screens"],
            "step": "screens",
            "prompt": (
                "핵심 화면 목록을 입력해 주세요. 여러 화면을 한 번에 넣을 수 있습니다.\n\n"
                "화면명: ...\n"
                "목적: ...\n"
                "핵심 노출: ...\n"
                "상태 차이: ...\n"
                "주요 액션: ...\n"
                "Figma URL: ...\n"
                "비고: ...\n\n"
                "여러 화면은 빈 줄 또는 `---`로 구분하세요.\n"
                "화면이 없으면 `없음`, 입력을 마치면 `done`을 입력할 수 있습니다."
            ),
            "answer_format": "화면별 블록 입력",
            "context": "블록 구분자: 빈 줄 또는 ---",
        }

    if step == "policies":
        return {
            "id": PROMPT_IDS["policies"],
            "step": "policies",
            "prompt": (
                "공통 정책을 입력해 주세요.\n\n"
                "정책명: ...\n"
                "설명: ...\n"
                "추적 참조: RULE-DW-IPHONE-001, RULE-DW-IPHONE-002\n\n"
                "여러 정책은 빈 줄 또는 `---`로 구분하세요.\n"
                "정책이 없으면 `없음`을 입력하세요."
            ),
            "answer_format": "정책별 블록 입력",
            "context": "블록 구분자: 빈 줄 또는 ---",
        }

    if step == "areas":
        if not normalized["progress"].get("active_prompt_id") and not has_naming_rules(normalized):
            return {
                "id": PROMPT_IDS["areas_naming"],
                "step": "areas",
                "prompt": (
                    "영역 ID 네이밍 규칙을 확정합니다.\n"
                    "기본 접두어는 `DW`입니다.\n"
                    "기본값을 쓰려면 `Y`, 직접 지정하려면 원하는 접두어를 입력하세요."
                ),
                "answer_format": "`Y` 또는 사용자 정의 접두어 한 줄 입력",
                "context": "예: DW, HOME, PLAN",
            }

        target = current_area_target(normalized)
        if target is None:
            normalized = update_progress(clear_active_prompt(normalized), "requirements")
            return get_prompt_payload(normalized)

        platform, screen_name = target
        return {
            "id": PROMPT_IDS["areas_collect"],
            "step": "areas",
            "prompt": (
                f"영역을 정의해 주세요.\n플랫폼: {platform}\n화면: {screen_name}\n\n"
                "영역 ID: ...\n"
                "유형: 영역\n"
                "영역명: ...\n"
                "정책 요약: ...\n"
                "좌표: 0.08,0.19,0.92,0.29\n"
                "마커 위치: left\n\n"
                "여러 영역은 빈 줄 또는 `---`로 구분하세요.\n"
                "이 화면을 건너뛰려면 `next`, 영역이 정말 없으면 `없음`을 입력하세요."
            ),
            "answer_format": "영역별 블록 입력",
            "context": f"{platform} / {screen_name}",
        }

    if step == "requirements":
        area = current_requirement_target(normalized)
        if area is None:
            normalized = update_progress(clear_active_prompt(normalized), "rules")
            return get_prompt_payload(normalized)

        return {
            "id": PROMPT_IDS["requirements"],
            "step": "requirements",
            "prompt": (
                f"요구사항을 작성해 주세요.\n플랫폼: {area['platform']}\n"
                f"영역: {area['id']} - {area['name']}\n\n"
                "조건: ...\n"
                "동작: ...\n"
                "예외: ...\n\n"
                "현재 영역을 건너뛰려면 `next` 또는 `없음`을 입력하세요."
            ),
            "answer_format": "조건/동작/예외 3개 라벨 입력",
            "context": f"{area['id']} / {area['name']}",
        }

    if step == "rules":
        return {
            "id": PROMPT_IDS["rules"],
            "step": "rules",
            "prompt": (
                "규칙을 정리합니다.\n"
                "`auto`를 입력하면 기존 요구사항과 공통 정책을 기준으로 규칙을 자동 생성합니다.\n"
                "수동 입력 시 아래 형식을 사용하세요.\n\n"
                "플랫폼: iPhone\n"
                "규칙: 오늘 날짜에서만 실행 버튼을 노출한다\n\n"
                "여러 규칙은 빈 줄 또는 `---`로 구분합니다.\n"
                "규칙이 없으면 `없음` 또는 `done`을 입력하세요."
            ),
            "answer_format": "`auto` 또는 규칙 블록 입력",
            "context": "자동 생성 시 공통 정책과 요구사항을 함께 사용",
        }

    if step == "testcases":
        requirement = current_testcase_target(normalized)
        if requirement is None:
            normalized = update_progress(clear_active_prompt(normalized), "document_generation")
            return get_prompt_payload(normalized)

        return {
            "id": PROMPT_IDS["testcases"],
            "step": "testcases",
            "prompt": (
                f"테스트케이스를 작성해 주세요.\n플랫폼: {requirement['platform']}\n"
                f"요구사항: {requirement['id']} - {requirement['area_name']}\n"
                f"조건: {requirement['condition']}\n"
                f"동작: {requirement['action']}\n\n"
                "자동 생성하려면 `auto`, 현재 요구사항을 건너뛰려면 `skip` 또는 `next`를 입력하세요.\n"
                "수동 입력 시 아래 형식을 사용합니다.\n"
                "시나리오: ...\n"
                "기대 결과: ..."
            ),
            "answer_format": "`auto`, `skip`, 또는 시나리오/기대 결과 입력",
            "context": requirement["id"],
        }

    return None


def parse_labeled_lines(text: str) -> dict[str, str]:
    """`라벨: 값` 형식 입력을 파싱합니다."""
    parsed: dict[str, str] = {}
    current_key = ""

    for raw_line in text.splitlines():
        line = raw_line.strip().lstrip("-").strip()
        if not line:
            continue
        if ":" in line:
            key, value = line.split(":", 1)
        elif "：" in line:
            key, value = line.split("：", 1)
        else:
            if current_key:
                parsed[current_key] = f"{parsed[current_key]}\n{line}".strip()
            continue
        current_key = normalize_label(key)
        parsed[current_key] = value.strip()

    return parsed


def split_blocks(text: str) -> list[str]:
    """빈 줄 또는 --- 기준으로 블록을 분리합니다."""
    normalized = text.strip()
    if not normalized:
        return []
    blocks = re.split(r"\n\s*---\s*\n|\n\s*\n(?=[^\s])", normalized)
    return [block.strip() for block in blocks if block.strip()]


def normalize_label(label: str) -> str:
    """한글 라벨을 비교용 키로 정규화합니다."""
    return re.sub(r"[\s_/()-]+", "", label).lower()


def split_list_value(value: str) -> list[str]:
    """쉼표/개행 구분 리스트를 파싱합니다."""
    if not value or value.strip() == "없음":
        return []
    return [part.strip() for part in re.split(r"[,\n]+", value) if part.strip()]


def is_control(text: str, keyword: str) -> bool:
    """제어 입력 여부를 확인합니다."""
    return text.strip().lower() == keyword.lower()


def resolve_value(mapping: dict[str, str], *labels: str) -> str:
    """여러 라벨 후보 중 첫 값을 반환합니다."""
    for label in labels:
        key = normalize_label(label)
        if key in mapping:
            return mapping[key]
    return ""


def next_area_id(state: dict[str, Any]) -> str:
    """다음 영역 ID를 생성합니다."""
    normalized = ensure_defaults(state)
    prefix = normalized["naming_rules"]["area_prefix"]
    used_numbers: list[int] = []

    for area in normalized["areas"]:
        area_id = area.get("id", "")
        match = re.fullmatch(rf"{re.escape(prefix)}(\d+)", area_id)
        if match:
            used_numbers.append(int(match.group(1)))

    next_number = max(used_numbers, default=0) + 1
    return f"{prefix}{next_number:02d}"


def next_indexed_id(state: dict[str, Any], prefix_key: str, platform: str, collection: str) -> str:
    """REQ/RULE/TC ID를 생성합니다."""
    normalized = ensure_defaults(state)
    prefix = normalized["naming_rules"][prefix_key]
    current = [
        item["id"]
        for item in normalized.get(collection, [])
        if item.get("platform") == platform
    ]
    next_number = len(current) + 1
    safe_platform = re.sub(r"[^A-Z0-9]+", "-", platform.upper())
    return f"{prefix}-{safe_platform}-{next_number:03d}"


def advance_area_target(state: dict[str, Any]) -> dict[str, Any]:
    """다음 영역 대상 화면/플랫폼으로 이동합니다."""
    normalized = ensure_defaults(state)
    platforms = normalized["metadata"].get("platforms", []) or ["공통"]
    screens = normalized.get("screens", [])
    cursors = normalized["progress"]["cursors"]

    if not screens:
        return update_progress(clear_active_prompt(normalized), "requirements")

    screen_index = cursors.get("screen_index", 0) + 1
    platform_index = cursors.get("platform_index", 0)

    if screen_index >= len(screens):
        screen_index = 0
        platform_index += 1

    cursors["screen_index"] = screen_index
    cursors["platform_index"] = platform_index

    if platform_index >= len(platforms):
        normalized = reset_cursor(normalized, "screen_index")
        normalized = reset_cursor(normalized, "platform_index")
        return update_progress(clear_active_prompt(normalized), "requirements")
    return clear_active_prompt(normalized)


def auto_generate_rules(state: dict[str, Any]) -> list[dict[str, Any]]:
    """공통 정책과 요구사항을 기준으로 규칙 후보를 생성합니다."""
    normalized = ensure_defaults(state)
    generated_rows: list[dict[str, str]] = []

    platforms = normalized["metadata"].get("platforms", []) or ["공통"]
    for platform in platforms:
        platform_requirements = [
            item for item in normalized["requirements"] if item.get("platform") == platform
        ]
        for policy in normalized["policies"]:
            generated_rows.append({"content": policy["description"], "platform": platform})

        repeated_conditions: dict[str, int] = {}
        for requirement in platform_requirements:
            condition = requirement.get("condition", "").strip()
            if condition:
                repeated_conditions[condition] = repeated_conditions.get(condition, 0) + 1

        for condition, count in repeated_conditions.items():
            if count < 2:
                continue
            generated_rows.append(
                {
                    "content": f"{condition} 조건의 요구사항은 동일한 기준으로 처리한다",
                    "platform": platform,
                }
            )

    deduped: list[dict[str, Any]] = []
    seen: set[tuple[str, str]] = set()
    generated_rules = list(normalized["rules"])
    for row in generated_rows:
        key = (row["platform"], row["content"])
        if key in seen:
            continue
        seen.add(key)
        generated_rules.append(
            {
                "id": next_indexed_id(
                    {
                        "naming_rules": normalized["naming_rules"],
                        "rules": generated_rules,
                    },
                    "rule_prefix",
                    row["platform"],
                    "rules",
                ),
                "content": row["content"],
                "platform": row["platform"],
            }
        )
        deduped.append(generated_rules[-1])
    return deduped


def auto_generate_testcase(requirement: dict[str, Any], tc_id: str) -> dict[str, Any]:
    """요구사항에서 테스트케이스를 생성합니다."""
    scenario = f"{requirement['condition']} 상황에서 {requirement['area_name']} 동작을 확인한다"
    expected = requirement["action"]
    if requirement.get("exception"):
        expected = f"{expected} / 예외 시 {requirement['exception']}"
    return {
        "id": tc_id,
        "req_id": requirement["id"],
        "scenario": scenario,
        "expected": expected,
        "platform": requirement["platform"],
    }


def apply_answer(state: dict[str, Any], text: str) -> tuple[dict[str, Any], str]:
    """현재 활성 질문에 대한 답변을 반영합니다."""
    normalized = ensure_defaults(state)
    prompt_id = normalized["progress"].get("active_prompt_id") or ""
    answer = text.strip()

    if not prompt_id:
        raise ValueError("현재 활성 질문이 없습니다. 먼저 `next`를 실행하세요.")

    if prompt_id == PROMPT_IDS["meta"]:
        return apply_meta_answer(normalized, answer)
    if prompt_id == PROMPT_IDS["screens"]:
        return apply_screens_answer(normalized, answer)
    if prompt_id == PROMPT_IDS["policies"]:
        return apply_policies_answer(normalized, answer)
    if prompt_id == PROMPT_IDS["areas_naming"]:
        return apply_area_naming_answer(normalized, answer)
    if prompt_id == PROMPT_IDS["areas_collect"]:
        return apply_areas_answer(normalized, answer)
    if prompt_id == PROMPT_IDS["requirements"]:
        return apply_requirements_answer(normalized, answer)
    if prompt_id == PROMPT_IDS["rules"]:
        return apply_rules_answer(normalized, answer)
    if prompt_id == PROMPT_IDS["testcases"]:
        return apply_testcases_answer(normalized, answer)

    raise ValueError(f"지원하지 않는 질문 ID입니다: {prompt_id}")


def apply_meta_answer(state: dict[str, Any], text: str) -> tuple[dict[str, Any], str]:
    mapping = parse_labeled_lines(text)
    title = resolve_value(mapping, "문서제목", "제목", "title")
    purpose = resolve_value(mapping, "문서목적", "목적", "purpose")
    readers = split_list_value(resolve_value(mapping, "대상독자", "독자", "targetreaders"))
    author = resolve_value(mapping, "작성자", "작성자이름", "author")
    platforms = split_list_value(resolve_value(mapping, "대상플랫폼", "플랫폼", "platforms"))
    exclusions = resolve_value(mapping, "범위제외", "제외", "exclusions")

    missing = []
    if not title:
        missing.append("문서 제목")
    if not purpose:
        missing.append("문서 목적")
    if not readers:
        missing.append("대상 독자")
    if not author:
        missing.append("작성자")
    if not platforms:
        missing.append("대상 플랫폼")
    if missing:
        raise ValueError(f"필수 항목이 누락되었습니다: {', '.join(missing)}")

    state["metadata"]["title"] = title
    state["metadata"]["purpose"] = purpose
    state["metadata"]["target_readers"] = readers
    state["metadata"]["author"] = author
    state["metadata"]["platforms"] = platforms
    state["metadata"]["exclusions"] = exclusions if exclusions and exclusions != "없음" else ""
    state["status"] = "in_progress"
    state = update_progress(clear_active_prompt(state), "screens")
    return state, "메타데이터가 저장되었습니다. 다음 단계는 화면 목록 정의입니다."


def apply_screens_answer(state: dict[str, Any], text: str) -> tuple[dict[str, Any], str]:
    if is_control(text, "없음") or is_control(text, "done"):
        state = update_progress(clear_active_prompt(state), "policies")
        return state, "화면 목록 입력을 마쳤습니다. 다음 단계는 공통 정책입니다."

    blocks = split_blocks(text)
    if not blocks:
        raise ValueError("화면 블록을 하나 이상 입력해 주세요.")

    added = 0
    for block in blocks:
        mapping = parse_labeled_lines(block)
        name = resolve_value(mapping, "화면명", "화면", "name")
        if not name:
            raise ValueError("각 화면 블록에는 `화면명`이 필요합니다.")

        state["screens"].append(
            {
                "name": name,
                "purpose": resolve_value(mapping, "목적", "purpose"),
                "key_exposure": resolve_value(mapping, "핵심노출", "핵심노출", "keyexposure"),
                "state_diff": resolve_value(mapping, "상태차이", "statediff"),
                "actions": resolve_value(mapping, "주요액션", "action", "actions"),
                "figma_url": resolve_value(mapping, "figmaurl", "figma", "url"),
                "notes": resolve_value(mapping, "비고", "notes"),
            }
        )
        added += 1

    state = update_progress(clear_active_prompt(state), "policies")
    return state, f"{added}개 화면이 저장되었습니다. 다음 단계는 공통 정책입니다."


def apply_policies_answer(state: dict[str, Any], text: str) -> tuple[dict[str, Any], str]:
    if is_control(text, "없음") or is_control(text, "done"):
        state = update_progress(clear_active_prompt(state), "areas")
        return state, "공통 정책 입력을 마쳤습니다. 다음 단계는 영역 정의입니다."

    blocks = split_blocks(text)
    if not blocks:
        raise ValueError("정책 블록을 하나 이상 입력해 주세요.")

    added = 0
    for block in blocks:
        mapping = parse_labeled_lines(block)
        name = resolve_value(mapping, "정책명", "정책", "name")
        description = resolve_value(mapping, "설명", "description")
        if not name or not description:
            raise ValueError("각 정책 블록에는 `정책명`, `설명`이 필요합니다.")

        state["policies"].append(
            {
                "name": name,
                "description": description,
                "tracking_refs": split_list_value(resolve_value(mapping, "추적참조", "trackingrefs")),
            }
        )
        added += 1

    state = update_progress(clear_active_prompt(state), "areas")
    return state, f"{added}개 공통 정책이 저장되었습니다. 다음 단계는 영역 정의입니다."


def apply_area_naming_answer(state: dict[str, Any], text: str) -> tuple[dict[str, Any], str]:
    answer = text.strip()
    if not answer:
        raise ValueError("`Y` 또는 사용자 정의 접두어를 입력해 주세요.")

    if answer.lower() in {"y", "yes"}:
        prefix = "DW"
    elif answer.lower() == "n":
        raise ValueError("사용자 정의 접두어를 직접 입력해 주세요. 예: HOME")
    else:
        prefix = re.sub(r"[^A-Za-z0-9]+", "", answer).upper()
        if not prefix:
            raise ValueError("유효한 접두어를 입력해 주세요.")

    state["naming_rules"] = {
        "area_prefix": prefix,
        "req_prefix": f"REQ-{prefix}",
        "rule_prefix": f"RULE-{prefix}",
        "tc_prefix": f"TC-{prefix}",
    }
    state["progress"]["naming_rules_confirmed"] = True
    state = clear_active_prompt(state)
    return state, f"네이밍 규칙이 저장되었습니다. 영역 접두어는 `{prefix}` 입니다."


def apply_areas_answer(state: dict[str, Any], text: str) -> tuple[dict[str, Any], str]:
    target = current_area_target(state)
    if target is None:
        state = update_progress(clear_active_prompt(state), "requirements")
        return state, "영역 정의가 완료되었습니다. 다음 단계는 요구사항입니다."

    if is_control(text, "next") or is_control(text, "없음") or is_control(text, "done"):
        state = advance_area_target(state)
        return state, "현재 화면의 영역 정의를 건너뛰고 다음 대상으로 이동했습니다."

    platform, screen_name = target
    blocks = split_blocks(text)
    if not blocks:
        raise ValueError("영역 블록을 하나 이상 입력해 주세요.")

    added = 0
    for block in blocks:
        mapping = parse_labeled_lines(block)
        area_name = resolve_value(mapping, "영역명", "name")
        if not area_name:
            raise ValueError("각 영역 블록에는 `영역명`이 필요합니다.")

        area_id = resolve_value(mapping, "영역id", "id") or next_area_id(state)
        area_type = resolve_value(mapping, "유형", "type") or "영역"
        policy_summary = resolve_value(mapping, "정책요약", "정책", "policysummary")

        area: dict[str, Any] = {
            "id": area_id,
            "type": area_type,
            "screen": screen_name,
            "name": area_name,
            "policy_summary": policy_summary,
            "platform": platform,
        }

        coordinates = resolve_value(mapping, "좌표", "box")
        if coordinates:
            values = [part.strip() for part in coordinates.split(",") if part.strip()]
            if len(values) == 4:
                try:
                    x0, y0, x1, y1 = [float(value) for value in values]
                    area["box"] = {"x0": x0, "y0": y0, "x1": x1, "y1": y1}
                except ValueError as error:
                    raise ValueError(f"좌표 형식이 올바르지 않습니다: {coordinates}") from error

        marker_side = resolve_value(mapping, "마커위치", "marker", "markerside")
        if marker_side:
            area["marker_side"] = marker_side

        state["areas"].append(area)
        added += 1

    state = advance_area_target(state)
    return state, f"{platform} / {screen_name}에 영역 {added}개를 저장했습니다."


def apply_requirements_answer(state: dict[str, Any], text: str) -> tuple[dict[str, Any], str]:
    area = current_requirement_target(state)
    if area is None:
        state = update_progress(clear_active_prompt(state), "rules")
        return state, "요구사항 작성이 완료되었습니다. 다음 단계는 규칙 정리입니다."

    if is_control(text, "next") or is_control(text, "없음"):
        state = advance_cursor(clear_active_prompt(state), "requirement_index")
        if current_requirement_target(state) is None:
            state = update_progress(state, "rules")
        return state, f"{area['id']} 요구사항을 건너뛰었습니다."

    mapping = parse_labeled_lines(text)
    condition = resolve_value(mapping, "조건", "condition")
    action = resolve_value(mapping, "동작", "보여줄내용동작", "action")
    exception = resolve_value(mapping, "예외", "exception")
    if not condition or not action:
        raise ValueError("`조건`, `동작`은 필수입니다.")

    req_id = next_indexed_id(state, "req_prefix", area["platform"], "requirements")
    state["requirements"].append(
        {
            "id": req_id,
            "area_id": area["id"],
            "area_name": area["name"],
            "condition": condition,
            "action": action,
            "exception": exception,
            "platform": area["platform"],
        }
    )
    state = advance_cursor(clear_active_prompt(state), "requirement_index")
    if current_requirement_target(state) is None:
        state = update_progress(state, "rules")
    return state, f"{req_id} 요구사항이 저장되었습니다."


def apply_rules_answer(state: dict[str, Any], text: str) -> tuple[dict[str, Any], str]:
    if is_control(text, "없음") or is_control(text, "done"):
        state = update_progress(clear_active_prompt(state), "testcases")
        return state, "규칙 정리를 마쳤습니다. 다음 단계는 테스트케이스입니다."

    added = 0
    if is_control(text, "auto"):
        rules = auto_generate_rules(state)
        state["rules"].extend(rules)
        added = len(rules)
    else:
        blocks = split_blocks(text)
        if not blocks:
            raise ValueError("규칙 블록을 입력하거나 `auto`를 사용해 주세요.")
        for block in blocks:
            mapping = parse_labeled_lines(block)
            platform = resolve_value(mapping, "플랫폼", "platform") or (
                state["metadata"].get("platforms", []) or ["공통"]
            )[0]
            content = resolve_value(mapping, "규칙", "내용", "content")
            if not content:
                raise ValueError("각 규칙 블록에는 `규칙` 또는 `내용`이 필요합니다.")

            state["rules"].append(
                {
                    "id": next_indexed_id(state, "rule_prefix", platform, "rules"),
                    "content": content,
                    "platform": platform,
                }
            )
            added += 1

    state = update_progress(clear_active_prompt(state), "testcases")
    return state, f"규칙 {added}개를 저장했습니다. 다음 단계는 테스트케이스입니다."


def apply_testcases_answer(state: dict[str, Any], text: str) -> tuple[dict[str, Any], str]:
    requirement = current_testcase_target(state)
    if requirement is None:
        state = update_progress(clear_active_prompt(state), "document_generation")
        return state, "테스트케이스 작성이 완료되었습니다. 이제 문서를 생성할 수 있습니다."

    if is_control(text, "skip") or is_control(text, "next") or is_control(text, "없음"):
        state = advance_cursor(clear_active_prompt(state), "testcase_index")
        if current_testcase_target(state) is None:
            state = update_progress(state, "document_generation")
        return state, f"{requirement['id']} 테스트케이스를 건너뛰었습니다."

    tc_id = next_indexed_id(state, "tc_prefix", requirement["platform"], "testcases")
    if is_control(text, "auto"):
        testcase = auto_generate_testcase(requirement, tc_id)
    else:
        mapping = parse_labeled_lines(text)
        scenario = resolve_value(mapping, "시나리오", "scenario")
        expected = resolve_value(mapping, "기대결과", "expected")
        if not scenario or not expected:
            raise ValueError("`시나리오`, `기대 결과`는 필수입니다.")
        testcase = {
            "id": tc_id,
            "req_id": requirement["id"],
            "scenario": scenario,
            "expected": expected,
            "platform": requirement["platform"],
        }

    state["testcases"].append(testcase)
    state = advance_cursor(clear_active_prompt(state), "testcase_index")
    if current_testcase_target(state) is None:
        state = update_progress(state, "document_generation")
    return state, f"{tc_id} 테스트케이스가 저장되었습니다."
