# Planning Wireframe 사용 예시

## 1. 세션 생성

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py init
python3 skills/planning-wireframe/scripts/planning_runner.py status planning-2026-03-25-1100
```

## 2. 질문 진행

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py next planning-2026-03-25-1100
python3 skills/planning-wireframe/scripts/planning_runner.py answer planning-2026-03-25-1100 --text $'문서 제목: 홈탭 기획\n문서 목적: 홈 화면 구조와 동작을 정의한다\n대상 독자: 기획자, QA, 개발자\n작성자: 모바일팀_홍길동\n대상 플랫폼: iPhone\n범위 제외: 타임테이블 기능'
```

다음 단계도 같은 방식으로 반복합니다.

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py next planning-2026-03-25-1100
python3 skills/planning-wireframe/scripts/planning_runner.py answer planning-2026-03-25-1100 --text $'화면명: 홈 메인 화면\n목적: 오늘의 일정과 학습 현황을 보여준다\n핵심 노출: 상단 카드, 일정 리스트, 타이머\n상태 차이: 오늘이면 실행 버튼 표시\n주요 액션: 일정 탭, 타이머 시작\nFigma URL: https://figma.com/design/abc123/Home?node-id=1-2\n비고: 없음'
```

## 3. 문서 생성

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py render-doc planning-2026-03-25-1100
```

생성 결과:

- 문서 경로: `홈화면 기획문서/기획자용/홈탭-기획.md`
- 상태: `review`

## 4. Figma manifest 출력

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py figma-manifest planning-2026-03-25-1100
```

예시 출력:

```json
[
  {
    "screen_name": "홈 메인 화면",
    "figma_url": "https://figma.com/design/abc123/Home?node-id=1-2",
    "file_key": "abc123",
    "node_id": "1:2",
    "output_path": "홈화면 기획문서/이미지/홈-메인-화면.png"
  }
]
```

이 JSON을 기준으로 에이전트가 MCP `get_screenshot`을 호출하고 이미지를 저장합니다.

## 5. 스크린샷 연결 및 주석 생성

```bash
python3 skills/planning-wireframe/scripts/planning_runner.py attach-screenshot planning-2026-03-25-1100 \
  --screen-name "홈 메인 화면" \
  --image-path "홈화면 기획문서/이미지/홈-메인-화면.png"

python3 skills/planning-wireframe/scripts/planning_runner.py annotate planning-2026-03-25-1100 \
  --image-root 홈화면\ 기획문서/이미지 \
  --output-root 홈화면\ 기획문서/이미지-주석-영역-한글
```

## Talk to Figma 대안 경로

기본 경로는 `plugin-figma-figma/get_screenshot` 입니다. Talk to Figma를 써야 하는 경우는 대안 경로로만 취급합니다.

- 별도 터미널에서 `bun socket` 실행
- Figma 플러그인 연결
- 필요한 이미지/프레임을 수동 또는 별도 플로우로 확보

이 경우에도 세션 상태 갱신은 `attach-screenshot`을 사용합니다.
