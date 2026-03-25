#!/usr/bin/env python3
"""
Planning wireframe Figma helpers.

Author: JunyoungJung
Date: 2026-03-25
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from session_state import ensure_defaults, slugify


FIGMA_DESIGN_PATTERN = re.compile(
    r"https?://(?:www\.)?figma\.com/design/(?P<file_key>[^/?#]+)/(?P<file_name>[^?#]+)\?node-id=(?P<node_id>\d+-\d+)"
)
FIGMA_BRANCH_PATTERN = re.compile(
    r"https?://(?:www\.)?figma\.com/design/(?P<file_key>[^/?#]+)/branch/(?P<branch_key>[^/?#]+)/(?P<file_name>[^?#]+)\?node-id=(?P<node_id>\d+-\d+)"
)


def parse_figma_url(figma_url: str) -> tuple[str, str]:
    """Figma URL에서 fileKey와 nodeId를 추출합니다."""
    url = figma_url.strip()
    branch_match = FIGMA_BRANCH_PATTERN.fullmatch(url)
    if branch_match:
        return branch_match.group("branch_key"), branch_match.group("node_id").replace("-", ":")

    design_match = FIGMA_DESIGN_PATTERN.fullmatch(url)
    if design_match:
        return design_match.group("file_key"), design_match.group("node_id").replace("-", ":")

    raise ValueError(f"지원하지 않는 Figma URL 형식입니다: {figma_url}")


def build_screenshot_path(screen_name: str) -> str:
    """화면명 기준 스크린샷 저장 경로를 생성합니다."""
    return f"홈화면 기획문서/이미지/{slugify(screen_name)}.png"


def build_figma_manifest(state: dict[str, Any]) -> list[dict[str, str]]:
    """스크린샷 다운로드 대상 manifest를 생성합니다."""
    normalized = ensure_defaults(state)
    manifest: list[dict[str, str]] = []

    for screen in normalized["screens"]:
        figma_url = (screen.get("figma_url") or "").strip()
        if not figma_url or screen.get("image_path"):
            continue

        file_key, node_id = parse_figma_url(figma_url)
        manifest.append(
            {
                "screen_name": screen["name"],
                "figma_url": figma_url,
                "file_key": file_key,
                "node_id": node_id,
                "output_path": build_screenshot_path(screen["name"]),
            }
        )

    return manifest


def attach_screenshot_path(
    state: dict[str, Any],
    screen_name: str,
    image_path: str,
) -> dict[str, Any]:
    """특정 화면에 다운로드된 이미지 경로를 기록합니다."""
    normalized = ensure_defaults(state)

    for screen in normalized["screens"]:
        if screen["name"] == screen_name:
            screen["image_path"] = image_path
            figma_url = (screen.get("figma_url") or "").strip()
            if figma_url and not normalized["figma"].get("file_key"):
                try:
                    file_key, _ = parse_figma_url(figma_url)
                    normalized["figma"]["file_key"] = file_key
                except ValueError:
                    pass
            return normalized

    raise ValueError(f"화면을 찾을 수 없습니다: {screen_name}")


def image_output_root() -> Path:
    """기본 스크린샷 루트 경로를 반환합니다."""
    return Path("홈화면 기획문서/이미지")
