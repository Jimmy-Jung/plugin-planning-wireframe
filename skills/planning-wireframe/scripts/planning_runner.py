#!/usr/bin/env python3
"""
Planning wireframe CLI runner.

Author: JunyoungJung
Date: 2026-03-25
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from document_renderer import DEFAULT_TEMPLATE_PATH, write_document
from figma_utils import attach_screenshot_path, build_figma_manifest
from generate_image_annotations import generate_all_annotations
from question_flow import (
    STEP_SEQUENCE,
    apply_answer,
    build_roadmap_text,
    get_prompt_payload,
)
from session_state import (
    clear_active_prompt,
    ensure_defaults,
    generate_session_id,
    has_figma_targets,
    list_sessions,
    load_session,
    mark_document_sections_completed,
    save_session,
    set_active_prompt,
    slugify,
    project_path,
    update_progress,
    validate_state,
)
from validate_skill import main as validate_skill_main


RUNNER_PATH = "skills/planning-wireframe/scripts/planning_runner.py"
FIGMA_COMPLETED_STEP = "figma_completed"


def load_required_session(session_id: str) -> dict:
    state = load_session(session_id)
    if not state:
        raise ValueError(f"세션을 찾을 수 없습니다: {session_id}")
    errors = validate_state(state)
    if errors:
        raise ValueError(" / ".join(errors))
    return state


def finalize_figma_phase(state: dict) -> dict:
    """Figma 후속 작업을 완료 상태로 전환합니다."""
    finalized = clear_active_prompt(state)
    finalized["status"] = "completed"
    return update_progress(finalized, FIGMA_COMPLETED_STEP)


def command_list(_: argparse.Namespace) -> int:
    sessions = list_sessions()
    if not sessions:
        print("저장된 planning 세션이 없습니다.")
        return 0

    for item in sessions:
        print(
            f"- {item['session_id']} | {item['title'] or '(제목 없음)'} | "
            f"status={item['status']} | updated={item['last_updated']}"
        )
    return 0


def command_init(args: argparse.Namespace) -> int:
    session_id = args.session_id or generate_session_id()
    state = ensure_defaults(
        {
            "session_id": session_id,
            "metadata": {
                "author": args.author or "",
                "title": args.title or "",
            },
        }
    )
    save_session(state)
    print(f"세션이 생성되었습니다: {session_id}")
    print(f"다음 명령: python3 {RUNNER_PATH} next {session_id}")
    return 0


def build_status_summary(state: dict) -> str:
    progress = state["progress"]
    completed = ", ".join(progress.get("completed_steps", [])) or "-"
    counts = {
        "screens": len(state["screens"]),
        "policies": len(state["policies"]),
        "areas": len(state["areas"]),
        "requirements": len(state["requirements"]),
        "rules": len(state["rules"]),
        "testcases": len(state["testcases"]),
    }
    count_text = ", ".join(f"{key}={value}" for key, value in counts.items())

    next_action = f"python3 {RUNNER_PATH} next {state['session_id']}"
    if state["progress"]["current_step"] == "document_generation":
        next_action = f"python3 {RUNNER_PATH} render-doc {state['session_id']}"
    elif state["progress"]["current_step"] == "review":
        if has_figma_targets(state):
            next_action = (
                f"python3 {RUNNER_PATH} figma-manifest {state['session_id']} "
                f"또는 python3 {RUNNER_PATH} complete-figma {state['session_id']}"
            )
        else:
            next_action = f"python3 {RUNNER_PATH} complete-figma {state['session_id']}"
    elif state["progress"]["current_step"] == FIGMA_COMPLETED_STEP:
        next_action = "-"

    lines = [
        f"session_id: {state['session_id']}",
        f"status: {state['status']}",
        f"current_step: {progress['current_step']}",
        f"completed_steps: {completed}",
        f"active_prompt_id: {progress.get('active_prompt_id') or '-'}",
        f"counts: {count_text}",
        f"next_action: {next_action}",
    ]
    return "\n".join(lines)


def command_status(args: argparse.Namespace) -> int:
    state = load_required_session(args.session_id)
    print(build_status_summary(state))
    return 0


def command_next(args: argparse.Namespace) -> int:
    state = load_required_session(args.session_id)
    current_step = state["progress"]["current_step"]

    if current_step == FIGMA_COMPLETED_STEP:
        print("모든 phase가 완료되었습니다.")
        return 0

    if current_step == "document_generation":
        print("질문 수집이 완료되었습니다. 다음 명령으로 문서를 생성하세요.")
        print(f"python3 {RUNNER_PATH} render-doc {args.session_id}")
        return 0

    if current_step == "review":
        if has_figma_targets(state):
            print("문서 생성이 완료되었습니다. 이제 Figma 후속 작업을 진행하세요.")
            print(f"python3 {RUNNER_PATH} figma-manifest {args.session_id}")
            print(
                f"python3 {RUNNER_PATH} annotate {args.session_id} "
                "--image-root 홈화면\\ 기획문서/이미지 --output-root 홈화면\\ 기획문서/이미지-주석-영역-한글"
            )
        else:
            print("Figma 대상 화면이 없습니다. 완료 처리만 하면 됩니다.")
            print(f"python3 {RUNNER_PATH} complete-figma {args.session_id}")
        return 0

    prompt = get_prompt_payload(state)
    if not prompt:
        print("현재 진행할 질문이 없습니다.")
        return 0

    state = set_active_prompt(
        state,
        prompt_id=prompt["id"],
        step=prompt["step"],
        prompt=prompt["prompt"],
        answer_format=prompt["answer_format"],
        context=prompt["context"],
    )

    lines = []
    if not state["progress"].get("roadmap_shown"):
        lines.append(build_roadmap_text(state))
        lines.append("")
        state["progress"]["roadmap_shown"] = True

    lines.extend(
        [
            f"[{prompt['step']}] {prompt['id']}",
            prompt["prompt"],
            "",
            f"답변 형식: {prompt['answer_format']}",
        ]
    )
    if prompt.get("context"):
        lines.append(f"문맥: {prompt['context']}")

    save_session(state)
    print("\n".join(lines))
    return 0


def command_answer(args: argparse.Namespace) -> int:
    state = load_required_session(args.session_id)
    updated, message = apply_answer(state, args.text)
    save_session(updated)
    print(message)
    print(f"현재 단계: {updated['progress']['current_step']}")
    if updated["progress"]["current_step"] == "document_generation":
        print(f"다음 명령: python3 {RUNNER_PATH} render-doc {args.session_id}")
    else:
        print(f"다음 명령: python3 {RUNNER_PATH} next {args.session_id}")
    return 0


def document_output_path(state: dict) -> Path:
    title = state["metadata"].get("title") or state["session_id"]
    return project_path("홈화면 기획문서", "기획자용", f"{slugify(title)}.md")


def command_render_doc(args: argparse.Namespace) -> int:
    state = load_required_session(args.session_id)
    title = state["metadata"].get("title") or state["session_id"]
    relative_output_path = Path("홈화면 기획문서/기획자용") / f"{slugify(title)}.md"
    output_path = document_output_path(state)

    state = clear_active_prompt(state)
    write_document(state, output_path, template_path=DEFAULT_TEMPLATE_PATH)

    state["document"]["path"] = str(relative_output_path)
    state = mark_document_sections_completed(state)
    if has_figma_targets(state):
        state["status"] = "review"
        state = update_progress(state, "review")
    else:
        state = finalize_figma_phase(state)
    save_session(state)

    print(f"문서가 생성되었습니다: {relative_output_path}")
    return 0


def command_figma_manifest(args: argparse.Namespace) -> int:
    state = load_required_session(args.session_id)
    manifest = build_figma_manifest(state)
    print(json.dumps(manifest, ensure_ascii=False, indent=2))
    return 0


def command_attach_screenshot(args: argparse.Namespace) -> int:
    state = load_required_session(args.session_id)
    state = attach_screenshot_path(
        state,
        screen_name=args.screen_name,
        image_path=args.image_path,
    )
    save_session(state)
    print(f"스크린샷 경로를 기록했습니다: {args.screen_name} -> {args.image_path}")
    return 0


def command_annotate(args: argparse.Namespace) -> int:
    state = load_required_session(args.session_id)
    session_path = project_path(".cursor", "project", "state", "planning-sessions", f"{state['session_id']}.yaml")
    generate_all_annotations(
        session_path,
        Path(args.image_root),
        Path(args.output_root),
    )
    state = finalize_figma_phase(state)
    save_session(state)
    print("주석 이미지 생성이 완료되었습니다.")
    return 0


def command_complete_figma(args: argparse.Namespace) -> int:
    state = load_required_session(args.session_id)
    state = finalize_figma_phase(state)
    save_session(state)
    print("Figma phase를 완료 처리했습니다.")
    return 0


def command_validate(_: argparse.Namespace) -> int:
    return validate_skill_main()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Planning wireframe runner")
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser("list", help="세션 목록 조회")
    list_parser.set_defaults(func=command_list)

    init_parser = subparsers.add_parser("init", help="세션 생성")
    init_parser.add_argument("--session-id", help="명시적 세션 ID")
    init_parser.add_argument("--title", help="초기 제목")
    init_parser.add_argument("--author", help="초기 작성자")
    init_parser.set_defaults(func=command_init)

    status_parser = subparsers.add_parser("status", help="세션 상태 조회")
    status_parser.add_argument("session_id")
    status_parser.set_defaults(func=command_status)

    next_parser = subparsers.add_parser("next", help="다음 질문 출력")
    next_parser.add_argument("session_id")
    next_parser.set_defaults(func=command_next)

    answer_parser = subparsers.add_parser("answer", help="현재 질문 답변 반영")
    answer_parser.add_argument("session_id")
    answer_parser.add_argument("--text", required=True, help="멀티라인 답변 텍스트")
    answer_parser.set_defaults(func=command_answer)

    render_parser = subparsers.add_parser("render-doc", help="문서 생성")
    render_parser.add_argument("session_id")
    render_parser.set_defaults(func=command_render_doc)

    manifest_parser = subparsers.add_parser("figma-manifest", help="Figma 다운로드 manifest 출력")
    manifest_parser.add_argument("session_id")
    manifest_parser.set_defaults(func=command_figma_manifest)

    attach_parser = subparsers.add_parser("attach-screenshot", help="화면별 스크린샷 경로 기록")
    attach_parser.add_argument("session_id")
    attach_parser.add_argument("--screen-name", required=True)
    attach_parser.add_argument("--image-path", required=True)
    attach_parser.set_defaults(func=command_attach_screenshot)

    annotate_parser = subparsers.add_parser("annotate", help="주석 이미지 생성")
    annotate_parser.add_argument("session_id")
    annotate_parser.add_argument("--image-root", required=True)
    annotate_parser.add_argument("--output-root", required=True)
    annotate_parser.set_defaults(func=command_annotate)

    complete_figma_parser = subparsers.add_parser("complete-figma", help="Figma phase 완료 처리")
    complete_figma_parser.add_argument("session_id")
    complete_figma_parser.set_defaults(func=command_complete_figma)

    validate_parser = subparsers.add_parser("validate", help="스킬 검증")
    validate_parser.set_defaults(func=command_validate)

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
