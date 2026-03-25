#!/usr/bin/env python3
"""
Planning wireframe markdown document renderer.

Author: JunyoungJung
Date: 2026-03-25
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Iterable

from session_state import ensure_defaults
from storage_paths import TEMPLATES_DIR


DEFAULT_TEMPLATE_PATH = TEMPLATES_DIR / "기획-템플릿.md"


def md(value: Any) -> str:
    """표와 문단에 안전한 마크다운 문자열로 정규화합니다."""
    if value is None:
        return ""
    text = str(value).strip()
    return text.replace("|", "\\|").replace("\n", "<br>")


def join_codes(values: Iterable[str]) -> str:
    """코드 목록을 쉼표로 연결합니다."""
    items = [value for value in values if value]
    if not items:
        return "-"
    return ", ".join(f"`{item}`" for item in items)


def render_table(headers: list[str], rows: list[list[Any]]) -> str:
    """공통 표 렌더러입니다."""
    header_line = "| " + " | ".join(headers) + " |"
    separator = "| " + " | ".join(["---"] * len(headers)) + " |"
    rendered_rows = [
        "| " + " | ".join(md(cell) for cell in row) + " |"
        for row in rows
    ]
    return "\n".join([header_line, separator, *rendered_rows])


def render_metadata_block(state: dict[str, Any]) -> str:
    metadata = state["metadata"]
    readers = ", ".join(metadata.get("target_readers", [])) or "-"
    references = render_reference_list(state["screens"])

    lines = [
        f"> 문서 목적: {metadata.get('purpose') or '-'}",
        ">",
        f"> 대상 독자: {readers}",
        ">",
        f"> 작성자: {metadata.get('author') or '-'}",
        ">",
        f"> 작성일: {state.get('created_at', '')[:10] or '-'}",
        ">",
        f"> 관련 원본 문서: {references or '-'}",
        ">",
        f"> 참고: {metadata.get('exclusions') or '범위 제외 사항 없음'}",
    ]
    return "\n".join(lines)


def render_reference_list(screens: list[dict[str, Any]]) -> str:
    links = [
        screen.get("figma_url", "").strip()
        for screen in screens
        if screen.get("figma_url")
    ]
    return ", ".join(links)


def render_figma_links(state: dict[str, Any]) -> str:
    screens = state["screens"]
    grouped: dict[str, list[dict[str, Any]]] = {}
    for platform in state["metadata"].get("platforms", []):
        grouped[platform] = []

    fallback_platform = state["metadata"].get("platforms", ["공통"])[0] if state["metadata"].get("platforms") else "공통"

    for screen in screens:
        grouped.setdefault(fallback_platform, []).append(screen)

    blocks: list[str] = []
    for platform, platform_screens in grouped.items():
        blocks.append(f"### {platform} 화면 링크\n")
        if not platform_screens:
            blocks.append("- 등록된 화면이 없습니다.\n")
            continue

        for screen in platform_screens:
            url = screen.get("figma_url") or "-"
            blocks.append(f"- {screen['name']}: {url}")
        blocks.append("")

    return "\n".join(blocks).strip()


def render_annotation_sections(state: dict[str, Any]) -> str:
    sections: list[str] = []
    screens = state["screens"]
    areas = state["areas"]
    if not screens:
        return "주석 이미지가 아직 없습니다."

    for index, screen in enumerate(screens, start=1):
        slug = screen["name"].replace(" ", "-").replace("/", "-")
        screen_areas = [area for area in areas if area.get("screen") == screen["name"]]
        sections.append(f"## {index:02d}-{screen['name']}")
        sections.append("")
        sections.append(f"![{screen['name']}](./이미지-주석-영역-한글/{slug}.png)")
        sections.append(f"> 설명: {screen.get('purpose') or '설명 없음'}")
        if screen.get("figma_url"):
            sections.append(f"> Figma: {screen['figma_url']}")
        if screen_areas:
            sections.append("")
            sections.append("영역 목록:")
            for area in screen_areas:
                sections.append(f"- `{area['id']}` {area['name']}")
        sections.append("")

    return "\n".join(sections).strip()


def render_summary(state: dict[str, Any]) -> str:
    screens = len(state["screens"])
    policies = len(state["policies"])
    requirements = len(state["requirements"])
    return "\n".join(
        [
            f"- 화면 {screens}개가 정의되어 있습니다.",
            f"- 공통 정책 {policies}개가 정리되어 있습니다.",
            f"- 요구사항 {requirements}개를 기준으로 규칙과 테스트케이스를 추적합니다.",
            "- 이미지 주석 유형은 `포인트=화살표`, `영역=테두리`, `범위=범위 화살표`로 고정합니다.",
            "- 이미지 주석은 추론 기반이므로 디자이너 확인이 필요합니다.",
        ]
    )


def render_screens_table(screens: list[dict[str, Any]]) -> str:
    rows = [
        [
            screen["name"],
            screen.get("purpose", ""),
            screen.get("key_exposure", ""),
            screen.get("state_diff", ""),
            screen.get("actions", ""),
            screen.get("notes", ""),
        ]
        for screen in screens
    ]
    return render_table(
        ["화면", "목적", "핵심 노출", "상태 차이", "주요 액션", "비고"],
        rows or [["-", "-", "-", "-", "-", "-"]],
    )


def render_policies_table(policies: list[dict[str, Any]]) -> str:
    rows = [
        [
            policy["name"],
            policy.get("description", ""),
            join_codes(policy.get("tracking_refs", [])),
        ]
        for policy in policies
    ]
    return render_table(["정책", "설명", "추적 참조"], rows or [["-", "-", "-"]])


def render_platform_areas(areas: list[dict[str, Any]], platform: str) -> str:
    platform_areas = [area for area in areas if area.get("platform") == platform]
    rows = [
        [
            f"`{area['id']}`",
            f"`{area.get('type', '')}`",
            area.get("screen", ""),
            area.get("name", ""),
            area.get("policy_summary", ""),
        ]
        for area in platform_areas
    ]
    return render_table(
        ["영역 ID", "유형", "화면", "영역명", "정책 요약"],
        rows or [["-", "-", "-", "-", "-"]],
    )


def render_platform_requirements(requirements: list[dict[str, Any]], platform: str) -> str:
    platform_reqs = [item for item in requirements if item.get("platform") == platform]
    rows = [
        [
            f"`{item['id']}`",
            f"`{item.get('area_id', '')}` {item.get('area_name', '')}".strip(),
            item.get("condition", ""),
            item.get("action", ""),
            item.get("exception", ""),
        ]
        for item in platform_reqs
    ]
    return render_table(
        ["REQ-ID", "대상 영역", "조건", "보여줄 내용·동작", "예외"],
        rows or [["-", "-", "-", "-", "-"]],
    )


def render_platform_rules(rules: list[dict[str, Any]], platform: str) -> str:
    platform_rules = [item for item in rules if item.get("platform") == platform]
    rows = [[f"`{item['id']}`", item.get("content", "")] for item in platform_rules]
    return render_table(["RULE-ID", "규칙"], rows or [["-", "-"]])


def render_platform_testcases(testcases: list[dict[str, Any]], platform: str) -> str:
    platform_cases = [item for item in testcases if item.get("platform") == platform]
    rows = [
        [
            f"`{item['id']}`",
            f"`{item.get('req_id', '')}`",
            item.get("scenario", ""),
            item.get("expected", ""),
        ]
        for item in platform_cases
    ]
    return render_table(
        ["TC-ID", "연계 REQ-ID", "시나리오", "기대 결과"],
        rows or [["-", "-", "-", "-"]],
    )


def render_tracking_table(state: dict[str, Any]) -> str:
    rows: list[list[str]] = []
    for policy in state["policies"]:
        refs = join_codes(policy.get("tracking_refs", []))
        rows.append(["공통 정책", f"{policy['name']} / {refs}"])

    for platform in state["metadata"].get("platforms", []):
        platform_reqs = [item["id"] for item in state["requirements"] if item.get("platform") == platform]
        platform_rules = [item["id"] for item in state["rules"] if item.get("platform") == platform]
        platform_cases = [item["id"] for item in state["testcases"] if item.get("platform") == platform]
        rows.append(
            [
                f"{platform} 추적",
                ", ".join(
                    part
                    for part in (
                        join_codes(platform_reqs),
                        join_codes(platform_rules),
                        join_codes(platform_cases),
                    )
                    if part
                )
                or "-",
            ]
        )

    return render_table(["구분", "설명"], rows or [["-", "-"]])


def render_decisions(state: dict[str, Any]) -> str:
    pending = state["progress"].get("pending_questions", [])
    if not pending:
        return "현재 미확정 이슈 없음. 주요 정책은 공통 정책과 규칙에 명시되어 있습니다."
    lines = []
    for item in pending:
        question = item.get("question") or item.get("prompt") or "질문 없음"
        context = item.get("context", "")
        lines.append(f"- {question}: {context}" if context else f"- {question}")
    return "\n".join(lines)


def render_references(state: dict[str, Any]) -> str:
    links = [
        screen.get("figma_url", "").strip()
        for screen in state["screens"]
        if screen.get("figma_url")
    ]
    if not links:
        return "- 원본 링크가 아직 없습니다."
    return "\n".join(f"- {link}" for link in links)


def render_document(
    state: dict[str, Any],
    template_path: str | Path = DEFAULT_TEMPLATE_PATH,
) -> str:
    """상태를 기반으로 최종 마크다운 문서를 생성합니다."""
    template = Path(template_path)
    if not template.exists():
        raise FileNotFoundError(f"템플릿 파일을 찾을 수 없습니다: {template}")

    normalized = ensure_defaults(state)
    lines = [
        f"# {normalized['metadata'].get('title') or '기획 문서'}",
        "",
        render_metadata_block(normalized),
        "",
        "## 피그마 링크",
        "",
        render_figma_links(normalized),
        "",
        "## 화면별 주석 이미지",
        "",
        render_annotation_sections(normalized),
        "",
        "## 한눈에 보기",
        "",
        render_summary(normalized),
        "",
        "## 화면 설명",
        "",
        render_screens_table(normalized["screens"]),
        "",
        "## 공통 정책",
        "",
        render_policies_table(normalized["policies"]),
    ]

    for platform in normalized["metadata"].get("platforms", []):
        lines.extend(
            [
                "",
                f"## {platform} 영역 정의",
                "",
                render_platform_areas(normalized["areas"], platform),
                "",
                f"## {platform} 요구사항",
                "",
                render_platform_requirements(normalized["requirements"], platform),
                "",
                f"## {platform} 규칙",
                "",
                render_platform_rules(normalized["rules"], platform),
                "",
                f"## {platform} 테스트케이스",
                "",
                render_platform_testcases(normalized["testcases"], platform),
            ]
        )

    lines.extend(
        [
            "",
            "## 추적 참조",
            "",
            render_tracking_table(normalized),
            "",
            "## 결정 필요",
            "",
            render_decisions(normalized),
            "",
            "## 원본 참고",
            "",
            render_references(normalized),
            "",
        ]
    )
    return "\n".join(lines)


def write_document(
    state: dict[str, Any],
    output_path: str | Path,
    template_path: str | Path = DEFAULT_TEMPLATE_PATH,
) -> Path:
    """문서를 파일로 저장합니다."""
    target = Path(output_path)
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(render_document(state, template_path=template_path), encoding="utf-8")
    return target
