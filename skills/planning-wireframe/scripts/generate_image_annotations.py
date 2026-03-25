#!/usr/bin/env python3
"""
Planning wireframe image annotation generator.

이 스크립트는 planning-wireframe 스킬의 세션 상태 파일과 이미지를 읽어
주석이 표시된 이미지를 자동으로 생성합니다.

Author: JunyoungJung
Date: 2026-03-25
"""

from __future__ import annotations

import math
import sys
import unicodedata
from pathlib import Path
from typing import Any

from PIL import Image, ImageColor, ImageDraw, ImageFont

from session_state import load_state_file, project_path, validate_state


COLORS = {
    "blue": ImageColor.getrgb("#2563EB"),
    "orange": ImageColor.getrgb("#F59E0B"),
    "red": ImageColor.getrgb("#DC2626"),
    "blue_fill": (37, 99, 235, 30),
    "orange_fill": (245, 158, 11, 34),
    "red_fill": (220, 38, 38, 30),
    "black": ImageColor.getrgb("#1F2937"),
    "white": ImageColor.getrgb("#FFFFFF"),
    "marker_fill": ImageColor.getrgb("#FDE047"),
    "canvas_bg": ImageColor.getrgb("#EEF2F7"),
    "image_card": ImageColor.getrgb("#F8FAFC"),
    "image_card_border": ImageColor.getrgb("#D6DEE8"),
    "image_card_shadow": (148, 163, 184, 72),
}

HEADER_HEIGHT = 96
SIDE_MARGIN = 92
TOP_MARGIN = 176
TARGET_CONTENT_WIDTH = 375
TARGET_CONTENT_HEIGHT = 812
OUTLINE_RADIUS = 16
OUTLINE_WIDTH = 4
SHADOW_WIDTH = 3
ARROW_WIDTH = 3
RANGE_WIDTH = 4
MARKER_OUTLINE_WIDTH = 2
MARKER_GAP = 56
MARKER_EDGE_PADDING = 36
IMAGE_CARD_PADDING = 12
IMAGE_CARD_RADIUS = 26


def load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """시스템 폰트를 로드합니다."""
    candidates = [
        "/System/Library/Fonts/AppleSDGothicNeo.ttc",
        "/System/Library/Fonts/Supplemental/NotoSansGothic-Regular.ttf",
        "/System/Library/Fonts/SFNS.ttf",
        "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/System/Library/Fonts/Supplemental/Helvetica.ttc",
    ]
    for candidate in candidates:
        path = Path(candidate)
        if path.exists():
            return ImageFont.truetype(str(path), size=size)
    return ImageFont.load_default()


TITLE_FONT = load_font(32)
LABEL_FONT = load_font(22)


def normalize_text(value: str) -> str:
    """텍스트를 정규화합니다."""
    return unicodedata.normalize("NFKD", value)


def fit_font(
    text: str, max_width: int, initial_size: int, min_size: int
) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """텍스트를 최대 너비에 맞는 폰트 크기로 조정합니다."""
    probe = ImageDraw.Draw(Image.new("RGBA", (1, 1), (255, 255, 255, 0)))
    for size in range(initial_size, min_size - 1, -2):
        font = load_font(size)
        bbox = probe.textbbox((0, 0), text, font=font)
        if bbox[2] - bbox[0] <= max_width:
            return font
    return load_font(min_size)


def resize_by_width(image: Image.Image, target_width: int) -> Image.Image:
    """이미지를 목표 너비에 맞춰 리사이즈합니다."""
    if image.width == target_width:
        return image

    scale = target_width / image.width
    target_height = max(1, int(round(image.height * scale)))
    return image.resize((target_width, target_height), Image.Resampling.LANCZOS)


def resize_by_height(image: Image.Image, target_height: int) -> Image.Image:
    """이미지를 목표 높이에 맞춰 리사이즈합니다."""
    if image.height == target_height:
        return image

    scale = target_height / image.height
    target_width = max(1, int(round(image.width * scale)))
    return image.resize((target_width, target_height), Image.Resampling.LANCZOS)


def resolve_source(image_root: Path, path_hint: str) -> Path:
    """이미지 소스 경로를 해결합니다."""
    explicit_path = Path(path_hint)
    if explicit_path.is_absolute() and explicit_path.exists():
        return explicit_path

    project_relative = project_path(path_hint)
    if project_relative.exists():
        return project_relative

    if "*" in path_hint:
        matches = sorted(image_root.glob(path_hint))
        if len(matches) == 1:
            return matches[0]

        normalized_parts = [normalize_text(part) for part in path_hint.split("*") if part]
        candidates = []
        for candidate in image_root.rglob("*.png"):
            normalized_name = normalize_text(str(candidate.relative_to(image_root)))
            if all(part in normalized_name for part in normalized_parts):
                candidates.append(candidate)

        if len(candidates) != 1:
            raise FileNotFoundError(
                f"Expected exactly one match for {path_hint}, got {len(candidates)}"
            )
        return candidates[0]

    source = image_root / path_hint
    if source.exists():
        return source

    if path_hint.startswith(f"{image_root.name}/"):
        nested_source = image_root.parent / path_hint
        if nested_source.exists():
            return nested_source

    normalized_hint = normalize_text(path_hint)
    for candidate in image_root.rglob("*.png"):
        if normalize_text(str(candidate.relative_to(image_root))) == normalized_hint:
            return candidate
    raise FileNotFoundError(f"Missing source image: {source}")


def to_abs_box(
    size: tuple[int, int],
    box: tuple[float, float, float, float],
    origin: tuple[int, int] = (0, 0),
) -> tuple[int, int, int, int]:
    """상대 좌표를 절대 좌표로 변환합니다."""
    width, height = size
    x0, y0, x1, y1 = box
    origin_x, origin_y = origin
    return (
        origin_x + int(width * x0),
        origin_y + int(height * y0),
        origin_x + int(width * x1),
        origin_y + int(height * y1),
    )


def clamp(value: int, minimum: int, maximum: int) -> int:
    """값을 범위 내로 제한합니다."""
    return max(minimum, min(value, maximum))


def place_marker(
    marker: tuple[int, int],
    tip: tuple[int, int],
    side: str,
    layout_state: dict[str, list[int]],
    canvas_size: tuple[int, int],
) -> tuple[tuple[int, int], tuple[int, int]]:
    """마커 위치를 충돌 회피 알고리즘으로 배치합니다."""
    axis = 1 if side in {"left", "right"} else 0
    minimum = MARKER_EDGE_PADDING
    maximum = canvas_size[axis] - MARKER_EDGE_PADDING
    base = marker[axis]
    used = layout_state.setdefault(side, [])
    offsets = [0]
    for step in range(1, 7):
        offsets.extend([step * MARKER_GAP, -step * MARKER_GAP])

    resolved = clamp(base, minimum, maximum)
    for offset in offsets:
        candidate = clamp(base + offset, minimum, maximum)
        if all(abs(candidate - placed) >= MARKER_GAP for placed in used):
            resolved = candidate
            break

    used.append(resolved)

    if axis == 0:
        return (resolved, marker[1]), tip
    return (marker[0], resolved), tip


def draw_header(draw: ImageDraw.ImageDraw, width: int, title: str) -> None:
    """헤더를 그립니다."""
    top = 28
    draw.rounded_rectangle(
        (24, top, width - 24, top + HEADER_HEIGHT),
        radius=24,
        fill=(31, 41, 55, 236),
    )
    title_font = fit_font(title, width - 120, initial_size=34, min_size=24)
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]
    draw.text(
        (width // 2 - title_width // 2, top + HEADER_HEIGHT // 2 - title_height // 2),
        title,
        font=title_font,
        fill=COLORS["white"],
    )


def draw_number_marker(draw: ImageDraw.ImageDraw, center: tuple[int, int], number: str) -> None:
    """번호 마커를 그립니다."""
    probe_bbox = draw.textbbox((0, 0), number, font=LABEL_FONT)
    label_width = probe_bbox[2] - probe_bbox[0]
    label_height = probe_bbox[3] - probe_bbox[1]
    box_width = max(48, label_width + 24)
    box_height = max(40, label_height + 18)
    box = (
        center[0] - box_width // 2,
        center[1] - box_height // 2,
        center[0] + box_width // 2,
        center[1] + box_height // 2,
    )
    shadow_box = (box[0] + 2, box[1] + 3, box[2] + 2, box[3] + 3)
    draw.rounded_rectangle(shadow_box, radius=10, fill=(31, 41, 55, 56))
    draw.rounded_rectangle(
        box, radius=10, fill=COLORS["marker_fill"], outline=COLORS["black"], width=MARKER_OUTLINE_WIDTH
    )
    marker_font = fit_font(number, box_width - 14, initial_size=22, min_size=16)
    label_bbox = draw.textbbox((0, 0), number, font=marker_font)
    label_width = label_bbox[2] - label_bbox[0]
    label_height = label_bbox[3] - label_bbox[1]
    draw.text(
        (center[0] - label_width // 2, center[1] - label_height // 2 - 1),
        number,
        font=marker_font,
        fill=COLORS["black"],
    )


def draw_arrow_between(
    draw: ImageDraw.ImageDraw, start_abs: tuple[int, int], end_abs: tuple[int, int], color: str
) -> None:
    """두 점 사이에 화살표를 그립니다."""
    draw.line((start_abs, end_abs), fill=COLORS[color], width=ARROW_WIDTH)
    dx = end_abs[0] - start_abs[0]
    dy = end_abs[1] - start_abs[1]
    length = math.hypot(dx, dy)
    if length == 0:
        return

    ux = dx / length
    uy = dy / length
    head = 12
    side = 7
    base_x = end_abs[0] - ux * head
    base_y = end_abs[1] - uy * head
    px = -uy
    py = ux
    draw.polygon(
        [
            end_abs,
            (int(base_x + px * side), int(base_y + py * side)),
            (int(base_x - px * side), int(base_y - py * side)),
        ],
        fill=COLORS[color],
    )


def draw_area_outline(
    draw: ImageDraw.ImageDraw,
    size: tuple[int, int],
    box: tuple[float, float, float, float],
    color: str,
    number: str,
    side: str,
    origin: tuple[int, int],
    canvas_size: tuple[int, int],
    layout_state: dict[str, list[int]],
) -> None:
    """영역 아웃라인을 그립니다."""
    left, top, right, bottom = to_abs_box(size, box, origin)
    outline_box = (left, top, right, bottom)
    shadow_box = (left + 3, top + 3, right + 3, bottom + 3)
    draw.rounded_rectangle(shadow_box, radius=OUTLINE_RADIUS, outline=(31, 41, 55, 48), width=SHADOW_WIDTH)
    draw.rounded_rectangle(outline_box, radius=OUTLINE_RADIUS, outline=COLORS[color], width=OUTLINE_WIDTH)

    if side == "left":
        marker = (origin[0] - SIDE_MARGIN // 2, (top + bottom) // 2)
        tip = (left - 12, (top + bottom) // 2)
    elif side == "right":
        marker = (canvas_size[0] - SIDE_MARGIN // 2, (top + bottom) // 2)
        tip = (right + 12, (top + bottom) // 2)
    elif side == "top":
        marker = ((left + right) // 2, origin[1] - 42)
        tip = ((left + right) // 2, top - 12)
    else:
        marker = ((left + right) // 2, bottom + 42)
        tip = ((left + right) // 2, bottom + 12)

    marker, tip = place_marker(marker, tip, side, layout_state, canvas_size)
    draw.line((marker, tip), fill=COLORS[color], width=ARROW_WIDTH)
    draw_number_marker(draw, marker, number)


def draw_callout(
    draw: ImageDraw.ImageDraw,
    size: tuple[int, int],
    box: tuple[float, float, float, float],
    color: str,
    number: str,
    side: str,
    origin: tuple[int, int],
    canvas_size: tuple[int, int],
    layout_state: dict[str, list[int]],
) -> None:
    """포인트 콜아웃을 그립니다."""
    abs_box = to_abs_box(size, box, origin)
    left, top, right, bottom = abs_box
    if side == "left":
        marker = (origin[0] - SIDE_MARGIN // 2, (top + bottom) // 2)
        tip = (left - 10, (top + bottom) // 2)
    elif side == "right":
        marker = (canvas_size[0] - SIDE_MARGIN // 2, (top + bottom) // 2)
        tip = (right + 10, (top + bottom) // 2)
    elif side == "top":
        marker = ((left + right) // 2, origin[1] - 42)
        tip = ((left + right) // 2, top - 12)
    else:
        marker = ((left + right) // 2, bottom + 42)
        tip = ((left + right) // 2, bottom + 12)

    marker, tip = place_marker(marker, tip, side, layout_state, canvas_size)
    draw_arrow_between(draw, marker, tip, color)
    draw_number_marker(draw, marker, number)


def draw_range_callout(
    draw: ImageDraw.ImageDraw,
    size: tuple[int, int],
    box: tuple[float, float, float, float],
    color: str,
    number: str,
    side: str,
    origin: tuple[int, int],
    canvas_size: tuple[int, int],
    layout_state: dict[str, list[int]],
) -> None:
    """범위 콜아웃을 그립니다."""
    abs_box = to_abs_box(size, box, origin)
    left, top, right, bottom = abs_box
    center_y = (top + bottom) // 2
    if side == "left":
        x = origin[0] - SIDE_MARGIN // 2
        draw.line((x, top, x, bottom), fill=COLORS[color], width=RANGE_WIDTH)
        draw_arrow_between(draw, (x, top), (x, top - 1), color)
        draw_arrow_between(draw, (x, bottom), (x, bottom + 1), color)
        marker = (x - 18, center_y)
    else:
        x = canvas_size[0] - SIDE_MARGIN // 2
        draw.line((x, top, x, bottom), fill=COLORS[color], width=RANGE_WIDTH)
        draw_arrow_between(draw, (x, top), (x, top - 1), color)
        draw_arrow_between(draw, (x, bottom), (x, bottom + 1), color)
        marker = (x + 18, center_y)
    marker, _ = place_marker(marker, marker, side, layout_state, canvas_size)
    draw_number_marker(draw, marker, number)


def get_area_color(area_type: str, index: int) -> str:
    """영역 타입과 인덱스에 따라 색상을 결정합니다."""
    color_sequence = ["blue", "orange", "red"]
    return color_sequence[index % len(color_sequence)]


def generate_annotation_image(
    screen_name: str,
    image_path: Path,
    areas: list[dict[str, Any]],
    output_path: Path,
    platform: str,
) -> None:
    """주석이 표시된 이미지를 생성합니다."""
    image = Image.open(image_path).convert("RGBA")

    if "iPad" in platform or "ipad" in platform.lower():
        image = resize_by_height(image, TARGET_CONTENT_HEIGHT)
    else:
        image = resize_by_width(image, TARGET_CONTENT_WIDTH)

    canvas_width = image.width + SIDE_MARGIN * 2
    canvas_height = image.height + TOP_MARGIN
    origin = (SIDE_MARGIN, TOP_MARGIN)
    canvas = Image.new("RGBA", (canvas_width, canvas_height), COLORS["canvas_bg"])
    base_draw = ImageDraw.Draw(canvas)

    card_box = (
        origin[0] - IMAGE_CARD_PADDING,
        origin[1] - IMAGE_CARD_PADDING,
        origin[0] + image.width + IMAGE_CARD_PADDING,
        origin[1] + image.height + IMAGE_CARD_PADDING,
    )
    shadow_box = (
        card_box[0] + 8,
        card_box[1] + 10,
        card_box[2] + 8,
        card_box[3] + 10,
    )
    base_draw.rounded_rectangle(
        shadow_box,
        radius=IMAGE_CARD_RADIUS,
        fill=COLORS["image_card_shadow"],
    )
    base_draw.rounded_rectangle(
        card_box,
        radius=IMAGE_CARD_RADIUS,
        fill=COLORS["image_card"],
        outline=COLORS["image_card_border"],
        width=2,
    )
    canvas.alpha_composite(image, origin)

    overlay = Image.new("RGBA", canvas.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)
    marker_layout: dict[str, list[int]] = {}

    draw_header(draw, canvas_width, screen_name)

    for idx, area in enumerate(areas):
        area_type = area.get("type", "영역").lower()
        area_id = area.get("id", f"AREA-{idx + 1}")
        color = get_area_color(area_type, idx)

        box_data = area.get("box")
        if not box_data:
            continue

        box = (
            box_data.get("x0", 0.0),
            box_data.get("y0", 0.0),
            box_data.get("x1", 1.0),
            box_data.get("y1", 1.0),
        )
        side = area.get("marker_side", "right")

        if area_type == "포인트" or area_type == "point":
            draw_callout(draw, image.size, box, color, area_id, side, origin, canvas.size, marker_layout)
        elif area_type == "범위" or area_type == "range" or area_type == "span":
            draw_range_callout(draw, image.size, box, color, area_id, side, origin, canvas.size, marker_layout)
        else:
            draw_area_outline(draw, image.size, box, color, area_id, side, origin, canvas.size, marker_layout)

    merged = Image.alpha_composite(canvas, overlay).convert("RGB")
    output_path.parent.mkdir(parents=True, exist_ok=True)
    merged.save(output_path, quality=95)


def generate_all_annotations(
    session_file: Path,
    image_root: Path,
    output_root: Path,
) -> None:
    """세션 상태 파일을 기반으로 모든 주석 이미지를 생성합니다."""
    state = load_state_file(session_file)
    errors = validate_state(state)
    if errors:
        print("Error: 세션 상태 형식이 올바르지 않습니다.")
        for error in errors:
            print(f"- {error}")
        sys.exit(1)
    screens = state.get("screens", [])
    areas = state.get("areas", [])

    for screen in screens:
        screen_name = screen["name"]
        screen_areas = [area for area in areas if area.get("screen") == screen_name]

        if not screen_areas:
            print(f"Skip {screen_name}: 영역이 정의되지 않음")
            continue

        image_hint = screen.get("image_path", f"{screen_name}.png")
        try:
            image_path = resolve_source(image_root, image_hint)
        except FileNotFoundError as e:
            print(f"Skip {screen_name}: {e}")
            continue

        platform = screen_areas[0].get("platform", "iPhone")
        output_filename = f"{screen_name.replace(' ', '-').replace('/', '-')}.png"
        output_path = output_root / output_filename

        generate_annotation_image(screen_name, image_path, screen_areas, output_path, platform)
        print(f"Generated: {output_path}")


def main() -> None:
    """메인 진입점."""
    if len(sys.argv) < 4:
        print("Usage: generate_image_annotations.py <session_file> <image_root> <output_root>")
        sys.exit(1)

    session_file = Path(sys.argv[1])
    image_root = Path(sys.argv[2])
    output_root = Path(sys.argv[3])

    if not session_file.exists():
        print(f"Error: 세션 파일을 찾을 수 없습니다: {session_file}")
        sys.exit(1)

    if not image_root.exists():
        print(f"Error: 이미지 폴더를 찾을 수 없습니다: {image_root}")
        sys.exit(1)

    generate_all_annotations(session_file, image_root, output_root)


if __name__ == "__main__":
    main()
