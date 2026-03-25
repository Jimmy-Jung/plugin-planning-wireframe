# Contributing to Planning Wireframe

이 저장소는 `planning-wireframe` 스킬과 관련 Python 스크립트를 함께 관리합니다.

## 기여 기본 원칙

- 구조보다 기능을 먼저 추가하지 않습니다. 문서, 스키마, 스크립트가 같은 기준을 보도록 유지합니다.
- 경로는 하드코딩하지 않고 `skills/planning-wireframe/scripts/storage_paths.py`를 사용합니다.
- 인터뷰 질문, 상태 스키마, 템플릿 필드는 서로 일치해야 합니다.
- 기획자가 이해할 수 있는 결과를 우선합니다.

## 개발 환경

```bash
git clone https://github.com/Jimmy-Jung/plugin-planning-wireframe.git
cd plugin-planning-wireframe
python3 -m pip install -r requirements.txt
```

## 작업 전 확인

- `skills/planning-wireframe/` 아래 구조를 먼저 확인합니다.
- 새 문서나 스크립트를 추가할 때 영구 자산인지 런타임 산출물인지 먼저 구분합니다.
- 스킬 내부에는 스킬 문서와 로직만 둡니다.
- 런타임 파일은 `.planning-wireframe/tmp/`, `.planning-wireframe/scratch/`, `.planning-wireframe/debug/` 아래에 둡니다.

## 테스트

변경 전후로 아래 명령을 기준으로 검증합니다.

```bash
python3 skills/planning-wireframe/scripts/validate_skill.py
python3 skills/planning-wireframe/scripts/smoke_test.py
```

수동 확인이 필요할 때:

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py init
python3 skills/planning-wireframe/scripts/planning_runner.py list
python3 skills/planning-wireframe/scripts/planning_runner.py next <session-id>
```

## 코드 스타일

- Python은 PEP 8을 따릅니다.
- 가능한 곳에는 type hint를 사용합니다.
- 함수는 한 가지 책임에 집중하게 유지합니다.
- 한국어 사용자가 읽기 쉬운 변수명과 출력 메시지를 우선합니다.

## 문서 수정 원칙

- README는 실제 저장소 구조만 설명합니다.
- 존재하지 않는 명령, 파일, 배포 방식을 문서에 남기지 않습니다.
- 저장 경로 표기는 `.planning-wireframe/` 기준으로 통일합니다.
- `skills/planning-wireframe/` 아래에 임시 폴더를 다시 만들지 않습니다.

## 제안 가능한 개선 영역

- 추가 템플릿 (서비스 기획, 관리자 도구 등)
- 다양한 주석 스타일 지원
- PDF/DOCX 내보내기
- Figma 플러그인 연동 개선
- 다국어 템플릿

## 이슈와 PR

- 변경 이유를 먼저 설명합니다.
- 문서 변경이면 어떤 사용 흐름이 개선되는지 같이 적습니다.
- 스크립트 변경이면 검증 결과를 함께 남깁니다.

## 경로 관리 규칙

새 스크립트를 작성할 때:

1. `storage_paths.py`에서 경로 함수를 가져옵니다.
2. 직접 `Path(__file__).parents[N]`을 사용하지 않습니다.
3. 런타임 디렉토리가 필요하면 `ensure_runtime_dirs()`를 호출합니다.

```python
from storage_paths import SESSION_DIR, TEMPLATES_DIR, ensure_runtime_dirs

ensure_runtime_dirs()
```
