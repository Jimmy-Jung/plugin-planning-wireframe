#!/usr/bin/env python3
"""
Planning wireframe markdown section patch helpers.

Author: JunyoungJung
Date: 2026-03-25
"""

from __future__ import annotations

from pathlib import Path


def heading_line(section_name: str) -> str:
    """섹션 제목 라인을 반환합니다."""
    return f"## {section_name.strip()}"


def find_section(lines: list[str], section_name: str) -> tuple[int, int] | None:
    """정확한 `##` 섹션 범위를 찾습니다."""
    target = heading_line(section_name)
    start_idx: int | None = None

    for index, line in enumerate(lines):
        stripped = line.strip()
        if stripped == target:
            start_idx = index
            continue

        if start_idx is not None and stripped.startswith("## "):
            return start_idx, index

    if start_idx is None:
        return None
    return start_idx, len(lines)


def build_section_lines(section_name: str, content: str) -> list[str]:
    """섹션 라인 블록을 생성합니다."""
    normalized = content.rstrip("\n")
    return [f"{heading_line(section_name)}\n", "\n", f"{normalized}\n", "\n"]


def patch_section_lines(lines: list[str], section_name: str, content: str) -> list[str]:
    """메모리 상의 라인 배열에서 섹션을 교체합니다."""
    new_lines = build_section_lines(section_name, content)
    current_range = find_section(lines, section_name)

    if current_range is None:
        if lines and lines[-1].strip():
            lines = [*lines, "\n"]
        return [*lines, *new_lines]

    start_idx, end_idx = current_range
    return [*lines[:start_idx], *new_lines, *lines[end_idx:]]


def read_section(doc_path: str | Path, section_name: str) -> str | None:
    """문서에서 특정 섹션 내용만 읽습니다."""
    path = Path(doc_path)
    if not path.exists():
        return None

    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    current_range = find_section(lines, section_name)
    if current_range is None:
        return None

    start_idx, end_idx = current_range
    return "".join(lines[start_idx + 1 : end_idx]).strip()


def patch_multiple_sections(
    doc_path: str | Path,
    sections: dict[str, str],
    create_backup: bool = True,
) -> dict[str, bool]:
    """여러 섹션을 한 번에 패치합니다."""
    path = Path(doc_path)
    if not path.exists():
        return {name: False for name in sections}

    original = path.read_text(encoding="utf-8")
    updated_lines = original.splitlines(keepends=True)
    backup_path = path.with_suffix(path.suffix + ".backup")

    if create_backup:
        backup_path.write_text(original, encoding="utf-8")

    try:
        for section_name, content in sections.items():
            updated_lines = patch_section_lines(updated_lines, section_name, content)
        path.write_text("".join(updated_lines), encoding="utf-8")
        return {name: True for name in sections}
    except Exception:
        if create_backup and backup_path.exists():
            path.write_text(backup_path.read_text(encoding="utf-8"), encoding="utf-8")
        return {name: False for name in sections}


def patch_section(
    doc_path: str | Path,
    section_name: str,
    new_content: str,
    create_backup: bool = True,
) -> bool:
    """단일 섹션만 패치합니다."""
    return patch_multiple_sections(
        doc_path,
        {section_name: new_content},
        create_backup=create_backup,
    )[section_name]
