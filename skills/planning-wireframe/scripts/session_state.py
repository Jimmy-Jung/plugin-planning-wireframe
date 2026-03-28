#!/usr/bin/env python3
"""
Planning wireframe session state helpers.

Author: JunyoungJung
Date: 2026-03-25
"""

from __future__ import annotations

import re
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Final

import yaml

from storage_paths import (
    PROJECT_ROOT,
    SESSION_DIR,
    ensure_runtime_dirs,
)


ensure_runtime_dirs()
DOCUMENT_SECTION_NAMES: Final[tuple[str, ...]] = (
    "meta",
    "figma_links",
    "overview_image",
    "quick_summary",
    "screens",
    "policies",
    "areas",
    "requirements",
    "rules",
    "testcases",
    "tracking",
    "decisions",
    "references",
)
REQUIRED_TOP_LEVEL_KEYS: Final[tuple[str, ...]] = (
    "session_id",
    "status",
    "template_type",
    "created_at",
    "last_updated",
    "metadata",
    "progress",
    "figma",
    "document",
    "screens",
    "policies",
    "areas",
    "requirements",
    "rules",
    "testcases",
    "naming_rules",
)


def utc_now_iso() -> str:
    """UTC ISO 8601 문자열을 반환합니다."""
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def default_document_sections() -> dict[str, str]:
    """문서 섹션 상태 기본값을 반환합니다."""
    return {section: "not_started" for section in DOCUMENT_SECTION_NAMES}


def session_path(session_id: str) -> Path:
    """세션 ID에 해당하는 상태 파일 경로를 반환합니다."""
    return SESSION_DIR / f"{session_id}.yaml"


def project_path(*parts: str) -> Path:
    """프로젝트 루트 기준 절대 경로를 생성합니다."""
    return PROJECT_ROOT.joinpath(*parts)


def init_session(
    session_id: str,
    title: str = "",
    author: str = "",
    template_type: str = "기획-형식",
) -> dict[str, Any]:
    """새 세션 상태를 초기화합니다."""
    now = utc_now_iso()
    return {
        "session_id": session_id,
        "status": "draft",
        "template_type": template_type,
        "created_at": now,
        "last_updated": now,
        "metadata": {
            "title": title,
            "purpose": "",
            "target_readers": [],
            "author": author,
            "platforms": [],
            "exclusions": "",
        },
        "progress": {
            "completed_steps": [],
            "current_step": "meta",
            "pending_questions": [],
            "roadmap_shown": False,
            "active_prompt_id": "",
            "naming_rules_confirmed": False,
            "cursors": {
                "platform_index": 0,
                "screen_index": 0,
                "area_index": 0,
                "requirement_index": 0,
                "testcase_index": 0,
            },
        },
        "figma": {
            "file_key": "",
            "wireframe_page": "",
            "annotation_page": "",
            "channel_name": "",
            "nodes": [],
        },
        "document": {
            "path": "",
            "sections": default_document_sections(),
        },
        "screens": [],
        "policies": [],
        "areas": [],
        "requirements": [],
        "rules": [],
        "testcases": [],
        "naming_rules": {
            "area_prefix": "DW",
            "req_prefix": "REQ-DW",
            "rule_prefix": "RULE-DW",
            "tc_prefix": "TC-DW",
        },
    }


def load_state_file(state_file: str | Path) -> dict[str, Any]:
    """상태 파일 경로로 세션을 로드합니다."""
    path = Path(state_file)
    with open(path, "r", encoding="utf-8") as handle:
        state = yaml.safe_load(handle) or {}
    return ensure_defaults(state)


def load_session(session_id: str) -> dict[str, Any] | None:
    """세션 ID로 상태를 로드합니다."""
    path = session_path(session_id)
    if not path.exists():
        return None
    return load_state_file(path)


def ensure_defaults(state: dict[str, Any]) -> dict[str, Any]:
    """누락된 기본 키를 채워 넣습니다."""
    base = init_session(state.get("session_id", "planning-session"))
    merged = deepcopy(base)
    merged.update(state)

    merged["metadata"] = {**base["metadata"], **state.get("metadata", {})}
    merged["progress"] = {**base["progress"], **state.get("progress", {})}
    merged["figma"] = {**base["figma"], **state.get("figma", {})}
    merged["document"] = {**base["document"], **state.get("document", {})}
    merged["document"]["sections"] = {
        **default_document_sections(),
        **merged["document"].get("sections", {}),
    }
    merged["naming_rules"] = {
        **base["naming_rules"],
        **state.get("naming_rules", {}),
    }
    return merged


def save_session(state: dict[str, Any]) -> Path:
    """세션 상태를 디스크에 저장합니다."""
    normalized = ensure_defaults(state)
    normalized["last_updated"] = utc_now_iso()

    path = session_path(normalized["session_id"])
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        yaml.safe_dump(normalized, handle, allow_unicode=True, sort_keys=False)
    return path


def has_figma_targets(state: dict[str, Any]) -> bool:
    """Figma 후속 작업 대상 화면이 있는지 반환합니다."""
    normalized = ensure_defaults(state)
    return any(screen.get("figma_url") for screen in normalized.get("screens", []))


def update_progress(state: dict[str, Any], next_step: str) -> dict[str, Any]:
    """현재 진행 상태를 다음 단계로 갱신합니다."""
    normalized = ensure_defaults(state)
    current_step = normalized["progress"].get("current_step", "")
    completed = normalized["progress"].setdefault("completed_steps", [])
    if current_step and current_step not in completed:
        completed.append(current_step)
    normalized["progress"]["current_step"] = next_step
    return normalized


def list_sessions() -> list[dict[str, str]]:
    """세션 목록을 최근 업데이트 순으로 반환합니다."""
    if not SESSION_DIR.exists():
        return []

    sessions: list[dict[str, str]] = []
    for state_file in sorted(SESSION_DIR.glob("*.yaml")):
        state = load_state_file(state_file)
        sessions.append(
            {
                "session_id": state["session_id"],
                "title": state["metadata"].get("title", ""),
                "status": state.get("status", ""),
                "last_updated": state.get("last_updated", ""),
            }
        )

    return sorted(sessions, key=lambda item: item["last_updated"], reverse=True)


def validate_state(state: dict[str, Any]) -> list[str]:
    """세션 상태의 기본 구조를 검증합니다."""
    errors: list[str] = []

    for key in REQUIRED_TOP_LEVEL_KEYS:
        if key not in state:
            errors.append(f"top-level 키 누락: {key}")

    metadata = state.get("metadata", {})
    for key in ("title", "purpose", "target_readers", "author", "platforms", "exclusions"):
        if key not in metadata:
            errors.append(f"metadata 키 누락: {key}")

    progress = state.get("progress", {})
    for key in ("completed_steps", "current_step", "pending_questions"):
        if key not in progress:
            errors.append(f"progress 키 누락: {key}")
    for key in ("roadmap_shown", "active_prompt_id", "naming_rules_confirmed", "cursors"):
        if key not in progress:
            errors.append(f"progress 키 누락: {key}")

    cursors = progress.get("cursors", {})
    for key in ("platform_index", "screen_index", "area_index", "requirement_index", "testcase_index"):
        if key not in cursors:
            errors.append(f"progress.cursors 키 누락: {key}")

    document = state.get("document", {})
    sections = document.get("sections", {})
    for key in DOCUMENT_SECTION_NAMES:
        if key not in sections:
            errors.append(f"document.sections 키 누락: {key}")

    for list_key in ("screens", "policies", "areas", "requirements", "rules", "testcases"):
        if not isinstance(state.get(list_key, []), list):
            errors.append(f"{list_key} 는 리스트여야 합니다.")

    return errors


def generate_session_id(prefix: str = "planning") -> str:
    """세션 ID를 생성합니다."""
    return datetime.now().strftime(f"{prefix}-%Y-%m-%d-%H%M")


def slugify(value: str, fallback: str = "untitled") -> str:
    """파일명용 슬러그를 생성합니다."""
    cleaned = re.sub(r"[^\w\s-]", " ", value, flags=re.UNICODE)
    cleaned = re.sub(r"[-\s]+", "-", cleaned.strip(), flags=re.UNICODE)
    return cleaned or fallback


def set_active_prompt(
    state: dict[str, Any],
    prompt_id: str,
    step: str,
    prompt: str,
    answer_format: str,
    context: str = "",
) -> dict[str, Any]:
    """현재 활성 질문을 상태에 기록합니다."""
    normalized = ensure_defaults(state)
    normalized["progress"]["active_prompt_id"] = prompt_id
    normalized["progress"]["pending_questions"] = [
        {
            "id": prompt_id,
            "step": step,
            "prompt": prompt,
            "answer_format": answer_format,
            "context": context,
        }
    ]
    return normalized


def clear_active_prompt(state: dict[str, Any]) -> dict[str, Any]:
    """현재 활성 질문을 제거합니다."""
    normalized = ensure_defaults(state)
    normalized["progress"]["active_prompt_id"] = ""
    normalized["progress"]["pending_questions"] = []
    return normalized


def advance_cursor(state: dict[str, Any], cursor_name: str, amount: int = 1) -> dict[str, Any]:
    """커서를 증가시킵니다."""
    normalized = ensure_defaults(state)
    cursors = normalized["progress"]["cursors"]
    cursors[cursor_name] = max(0, int(cursors.get(cursor_name, 0)) + amount)
    return normalized


def reset_cursor(state: dict[str, Any], cursor_name: str) -> dict[str, Any]:
    """특정 커서를 0으로 초기화합니다."""
    normalized = ensure_defaults(state)
    normalized["progress"]["cursors"][cursor_name] = 0
    return normalized


def mark_document_sections_completed(state: dict[str, Any]) -> dict[str, Any]:
    """문서 섹션 상태를 모두 완료로 표시합니다."""
    normalized = ensure_defaults(state)
    normalized["document"]["sections"] = {
        section: "completed" for section in DOCUMENT_SECTION_NAMES
    }
    return normalized
