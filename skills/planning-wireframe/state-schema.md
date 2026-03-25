# Planning Wireframe 상태 스키마

세션 상태는 `.planning-wireframe/state/{session_id}.yaml`에 저장됩니다. 실제 구현은 `./scripts/session_state.py`와 `./scripts/storage_paths.py`가 담당합니다.

## 최상위 구조

```yaml
session_id: string
status: draft | in_progress | review | completed
template_type: string
created_at: string
last_updated: string

metadata:
  title: string
  purpose: string
  target_readers: array[string]
  author: string
  platforms: array[string]
  exclusions: string

progress:
  completed_steps: array[string]
  current_step: meta | screens | policies | areas | requirements | rules | testcases | document_generation | review
  pending_questions:
    - id: string
      step: string
      prompt: string
      answer_format: string
      context: string
  roadmap_shown: boolean
  active_prompt_id: string
  naming_rules_confirmed: boolean
  cursors:
    platform_index: integer
    screen_index: integer
    area_index: integer
    requirement_index: integer
    testcase_index: integer

figma:
  file_key: string
  wireframe_page: string
  annotation_page: string
  channel_name: string
  nodes: array[object]

document:
  path: string
  sections:
    meta: string
    figma_links: string
    overview_image: string
    quick_summary: string
    screens: string
    policies: string
    areas: string
    requirements: string
    rules: string
    testcases: string
    tracking: string
    decisions: string
    references: string

screens: array[object]
policies: array[object]
areas: array[object]
requirements: array[object]
rules: array[object]
testcases: array[object]

naming_rules:
  area_prefix: string
  req_prefix: string
  rule_prefix: string
  tc_prefix: string
```

## 컬렉션 상세

### screens

```yaml
- name: string
  purpose: string
  key_exposure: string
  state_diff: string
  actions: string
  figma_url: string
  notes: string
  image_path: string
```

### policies

```yaml
- name: string
  description: string
  tracking_refs: array[string]
```

### areas

```yaml
- id: string
  type: 영역 | 포인트 | 범위
  screen: string
  name: string
  policy_summary: string
  platform: string
  box:
    x0: float
    y0: float
    x1: float
    y1: float
  marker_side: left | right | top | bottom
```

### requirements

```yaml
- id: string
  area_id: string
  area_name: string
  condition: string
  action: string
  exception: string
  platform: string
```

### rules

```yaml
- id: string
  content: string
  platform: string
```

### testcases

```yaml
- id: string
  req_id: string
  scenario: string
  expected: string
  platform: string
```

## CLI와 상태의 관계

- `init`는 기본 상태를 생성합니다.
- `next`는 `pending_questions`, `active_prompt_id`를 채웁니다.
- `answer`는 현재 질문 결과를 컬렉션에 반영하고 `current_step` 또는 `cursors`를 갱신합니다.
- `render-doc`는 `document.path`, `document.sections`, `status`, `current_step`을 갱신합니다.
- `attach-screenshot`는 `screens[].image_path`를 기록합니다.

## 관련 구현

- 세션 유틸: `./scripts/session_state.py`
- 질문 흐름: `./scripts/question_flow.py`
- 러너: `./scripts/planning_runner.py`
