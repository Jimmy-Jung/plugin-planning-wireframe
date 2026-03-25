<!-- Author: JunyoungJung | Date: 2026-03-25 -->

# Planning Wireframe 프로젝트 메모리

먼저 아래 파일을 읽습니다.

- @README.md
- @skills/planning-wireframe/SKILL.md
- @skills/planning-wireframe/USAGE.md
- @skills/planning-wireframe/state-schema.md

## 이 저장소의 목적

- 인터뷰 기반으로 구조화된 기획 문서와 와이어프레임 산출물을 생성한다.
- 실제 실행은 `skills/planning-wireframe/scripts/planning_runner.py`로 한다.
- 세션 상태는 YAML로 저장하며, 질문 흐름은 고정된 단계로 진행한다.

## 작업 원칙

- 기획 문서, 화면 정의, 정책, 요구사항, 규칙, 테스트케이스, Figma 스크린샷 연동 요청이면 이 워크플로우를 우선 사용한다.
- 먼저 `list` 또는 `status`로 세션 존재 여부를 확인한다.
- 세션이 없으면 `init`으로 생성한다.
- 질문 흐름은 `next`와 `answer`를 반복한다.
- 문서 생성은 `render-doc`를 사용한다.
- Figma 작업은 `figma-manifest` -> `attach-screenshot` -> `annotate` 순서로 처리한다.
- Python 스크립트는 Figma MCP를 직접 호출하지 않는다.
- 사용자 응답은 한국어로 간결하게 정리한다.

## 표준 명령

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py list
python3 skills/planning-wireframe/scripts/planning_runner.py init
python3 skills/planning-wireframe/scripts/planning_runner.py status <session-id>
python3 skills/planning-wireframe/scripts/planning_runner.py next <session-id>
python3 skills/planning-wireframe/scripts/planning_runner.py answer <session-id> --text "..."
python3 skills/planning-wireframe/scripts/planning_runner.py render-doc <session-id>
python3 skills/planning-wireframe/scripts/planning_runner.py figma-manifest <session-id>
python3 skills/planning-wireframe/scripts/planning_runner.py attach-screenshot <session-id> --screen-name "..." --image-path "..."
python3 skills/planning-wireframe/scripts/planning_runner.py annotate <session-id> --image-root "홈화면 기획문서/이미지" --output-root "홈화면 기획문서/이미지-주석-영역-한글"
```
