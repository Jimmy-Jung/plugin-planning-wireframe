#!/usr/bin/env python3
"""
Planning wireframe smoke test.

Author: JunyoungJung
Date: 2026-03-25
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

from PIL import Image


ROOT = Path(__file__).resolve().parent
RUNNER = ROOT / "planning_runner.py"
PROJECT_ROOT = ROOT.parents[3]
SESSION_ID = "planning-smoke-test"
SESSION_FILE = PROJECT_ROOT / ".cursor/project/state/planning-sessions" / f"{SESSION_ID}.yaml"
DOC_FILE = PROJECT_ROOT / "홈화면 기획문서/기획자용" / "스모크-테스트-기획.md"
IMAGE_DIR = PROJECT_ROOT / "홈화면 기획문서/이미지"
ANNOTATION_DIR = PROJECT_ROOT / "홈화면 기획문서/이미지-주석-영역-한글"
DUMMY_IMAGE = IMAGE_DIR / "홈-메인-화면.png"
ANNOTATED_IMAGE = ANNOTATION_DIR / "홈-메인-화면.png"


def run_command(*args: str) -> str:
    result = subprocess.run(
        [sys.executable, str(RUNNER), *args],
        check=True,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def cleanup() -> None:
    if SESSION_FILE.exists():
        SESSION_FILE.unlink()
    if DOC_FILE.exists():
        DOC_FILE.unlink()
    if DUMMY_IMAGE.exists():
        DUMMY_IMAGE.unlink()
    if ANNOTATED_IMAGE.exists():
        ANNOTATED_IMAGE.unlink()
    for folder in (IMAGE_DIR, ANNOTATION_DIR):
        if folder.exists() and not any(folder.iterdir()):
            shutil.rmtree(folder)


def main() -> int:
    cleanup()

    run_command("init", "--session-id", SESSION_ID)
    run_command("next", SESSION_ID)
    run_command(
        "answer",
        SESSION_ID,
        "--text",
        "\n".join(
            [
                "문서 제목: 스모크 테스트 기획",
                "문서 목적: CLI 러너 연결을 검증한다",
                "대상 독자: 기획자, 개발자",
                "작성자: JunyoungJung",
                "대상 플랫폼: iPhone",
                "범위 제외: 없음",
            ]
        ),
    )
    run_command("next", SESSION_ID)
    run_command(
        "answer",
        SESSION_ID,
        "--text",
        "\n".join(
            [
                "화면명: 홈 메인 화면",
                "목적: 핵심 상태를 보여준다",
                "핵심 노출: 상단 카드, 일정 리스트",
                "상태 차이: 오늘/비오늘 분기",
                "주요 액션: 탭, 실행",
                "Figma URL: https://figma.com/design/abc123/Home?node-id=1-2",
                "비고: 스모크 테스트",
            ]
        ),
    )
    run_command("next", SESSION_ID)
    run_command(
        "answer",
        SESSION_ID,
        "--text",
        "\n".join(
            [
                "정책명: 오늘 여부",
                "설명: 오늘 날짜에서만 실행 버튼을 노출한다",
                "추적 참조: RULE-DW-IPHONE-001",
            ]
        ),
    )
    run_command("next", SESSION_ID)
    run_command("answer", SESSION_ID, "--text", "Y")
    run_command("next", SESSION_ID)
    run_command(
        "answer",
        SESSION_ID,
        "--text",
        "\n".join(
            [
                "영역 ID: DW01",
                "유형: 영역",
                "영역명: 상단 요약 카드",
                "정책 요약: 누적 시간을 보여준다",
                "좌표: 0.08,0.19,0.92,0.29",
                "마커 위치: left",
            ]
        ),
    )
    run_command("next", SESSION_ID)
    run_command(
        "answer",
        SESSION_ID,
        "--text",
        "\n".join(
            [
                "조건: 홈 진입 시",
                "동작: 총 학습 시간을 표시한다",
                "예외: 데이터가 없으면 00:00:00을 표시한다",
            ]
        ),
    )
    run_command("next", SESSION_ID)
    run_command("answer", SESSION_ID, "--text", "auto")
    run_command("next", SESSION_ID)
    run_command("answer", SESSION_ID, "--text", "auto")
    run_command("render-doc", SESSION_ID)
    manifest_output = run_command("figma-manifest", SESSION_ID)

    IMAGE_DIR.mkdir(parents=True, exist_ok=True)
    Image.new("RGB", (375, 812), "#FFFFFF").save(DUMMY_IMAGE)
    run_command(
        "attach-screenshot",
        SESSION_ID,
        "--screen-name",
        "홈 메인 화면",
        "--image-path",
        "홈화면 기획문서/이미지/홈-메인-화면.png",
    )
    run_command(
        "annotate",
        SESSION_ID,
        "--image-root",
        str(IMAGE_DIR),
        "--output-root",
        str(ANNOTATION_DIR),
    )

    if not SESSION_FILE.exists():
        raise AssertionError("세션 파일이 생성되지 않았습니다.")
    if not DOC_FILE.exists():
        raise AssertionError("문서 파일이 생성되지 않았습니다.")
    if '"file_key": "abc123"' not in manifest_output or '"node_id": "1:2"' not in manifest_output:
        raise AssertionError("Figma manifest 출력이 올바르지 않습니다.")
    if not ANNOTATED_IMAGE.exists():
        raise AssertionError("주석 이미지가 생성되지 않았습니다.")

    cleanup()
    print("planning-wireframe smoke test passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
