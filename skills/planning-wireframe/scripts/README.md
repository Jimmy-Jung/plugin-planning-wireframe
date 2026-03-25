# Planning Wireframe Scripts

이 폴더는 `planning-wireframe` 실행형 스킬의 실제 동작을 담당하는 스크립트를 포함합니다.

## 핵심 스크립트

- `planning_runner.py`: 공개 CLI 엔트리포인트
- `question_flow.py`: 단계별 질문, 파서, 완료 판정
- `session_state.py`: 세션 상태 생성/저장/로드/검증
- `storage_paths.py`: 경로 유틸리티
- `figma_utils.py`: Figma URL 파싱 및 manifest 생성
- `document_renderer.py`: 최종 마크다운 문서 렌더링
- `generate_image_annotations.py`: 주석 이미지 생성
- `section_patch.py`: 문서 섹션 패치 유틸
- `validate_skill.py`: 구조/경로/렌더링 검증
- `smoke_test.py`: 비대화형 E2E 스모크 테스트

## 표준 명령

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py list
python3 skills/planning-wireframe/scripts/planning_runner.py init
python3 skills/planning-wireframe/scripts/planning_runner.py next {session_id}
python3 skills/planning-wireframe/scripts/planning_runner.py answer {session_id} --text "..."
python3 skills/planning-wireframe/scripts/planning_runner.py render-doc {session_id}
python3 skills/planning-wireframe/scripts/planning_runner.py figma-manifest {session_id}
python3 skills/planning-wireframe/scripts/planning_runner.py attach-screenshot {session_id} --screen-name "..." --image-path "..."
python3 skills/planning-wireframe/scripts/planning_runner.py annotate {session_id} --image-root 홈화면\ 기획문서/이미지 --output-root 홈화면\ 기획문서/이미지-주석-영역-한글
python3 skills/planning-wireframe/scripts/planning_runner.py validate
```

## Figma 스크린샷 흐름

1. `figma-manifest`로 다운로드 대상 JSON 출력
2. 에이전트가 `plugin-figma-figma/get_screenshot` 호출
3. 저장한 경로를 `attach-screenshot`으로 세션에 반영
4. `annotate`로 주석 이미지 생성

Python 스크립트는 MCP를 직접 호출하지 않습니다.

## 검증

```bash
python3 -m py_compile skills/planning-wireframe/scripts/*.py
python3 skills/planning-wireframe/scripts/validate_skill.py
python3 skills/planning-wireframe/scripts/smoke_test.py
```

## 요구사항

```bash
pip install -r requirements.txt
```
