#!/usr/bin/env python3
"""
Planning wireframe storage path utilities.

Author: JunyoungJung
Date: 2026-03-25
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Final


def get_project_root() -> Path:
    """프로젝트 루트 디렉토리를 반환합니다."""
    return Path(__file__).resolve().parents[3]


def get_skill_root() -> Path:
    """스킬 루트 디렉토리를 반환합니다."""
    return Path(__file__).resolve().parents[1]


def get_state_dir() -> Path:
    """
    세션 상태 저장 디렉토리를 반환합니다.
    환경 변수로 변경 가능합니다.
    """
    custom_dir = os.environ.get("PLANNING_WIREFRAME_STATE_DIR")
    if custom_dir:
        return Path(custom_dir)
    
    return get_project_root() / ".planning-wireframe/state"


def get_output_dir() -> Path:
    """
    문서 출력 디렉토리를 반환합니다.
    환경 변수로 변경 가능합니다.
    """
    custom_dir = os.environ.get("PLANNING_WIREFRAME_OUTPUT_DIR")
    if custom_dir:
        return Path(custom_dir)
    
    return get_project_root() / ".planning-wireframe/output"


def get_tmp_dir() -> Path:
    """임시 파일 디렉토리를 반환합니다."""
    return get_project_root() / ".planning-wireframe/tmp"


def get_scratch_dir() -> Path:
    """작업 메모 디렉토리를 반환합니다."""
    return get_project_root() / ".planning-wireframe/scratch"


def get_debug_dir() -> Path:
    """디버그 산출물 디렉토리를 반환합니다."""
    return get_project_root() / ".planning-wireframe/debug"


def get_templates_dir() -> Path:
    """템플릿 디렉토리를 반환합니다."""
    return get_skill_root() / "templates"


def get_references_dir() -> Path:
    """참고 자료 디렉토리를 반환합니다."""
    return get_skill_root() / "references"


def get_scripts_dir() -> Path:
    """스크립트 디렉토리를 반환합니다."""
    return get_skill_root() / "scripts"


def ensure_runtime_dirs() -> None:
    """런타임 디렉토리가 존재하지 않으면 생성합니다."""
    for get_dir in [
        get_state_dir,
        get_output_dir,
        get_tmp_dir,
        get_scratch_dir,
        get_debug_dir,
    ]:
        path = get_dir()
        path.mkdir(parents=True, exist_ok=True)


# 상수
PROJECT_ROOT: Final[Path] = get_project_root()
SKILL_ROOT: Final[Path] = get_skill_root()
SESSION_DIR: Final[Path] = get_state_dir()
OUTPUT_DIR: Final[Path] = get_output_dir()
TMP_DIR: Final[Path] = get_tmp_dir()
SCRATCH_DIR: Final[Path] = get_scratch_dir()
DEBUG_DIR: Final[Path] = get_debug_dir()
TEMPLATES_DIR: Final[Path] = get_templates_dir()
REFERENCES_DIR: Final[Path] = get_references_dir()
SCRIPTS_DIR: Final[Path] = get_scripts_dir()
