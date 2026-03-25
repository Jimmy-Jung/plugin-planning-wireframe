# 문서 섹션별 패치 유틸리티

기획 문서의 특정 섹션만 안전하게 업데이트하는 로직입니다.

## 핵심 원칙

1. **전체 재작성 방지**: 변경된 섹션만 업데이트
2. **섹션 보존**: 다른 섹션은 그대로 유지
3. **포맷 유지**: 마크다운 형식과 들여쓰기 보존
4. **안전성**: 실패 시 백업에서 복구 가능

## 핵심 함수

실제 구현 파일:
`./scripts/section_patch.py`

### 1. 섹션 찾기

```python
def find_section(lines: list[str], section_name: str) -> tuple[int, int] | None:
    """
    문서에서 섹션의 시작과 끝 인덱스를 찾습니다.
    
    Args:
        lines: 문서의 모든 라인 (줄바꿈 포함)
        section_name: 섹션 이름 (## 제외)
    
    Returns:
        (start_idx, end_idx) 또는 None (섹션이 없으면)
        end_idx는 다음 섹션 시작 또는 파일 끝
    """
    start_idx = None
    end_idx = None
    
    for i, line in enumerate(lines):
        # ## 섹션명 찾기 (정확히 2개의 #)
        if line.strip().startswith("## ") and section_name in line:
            # 제목 레벨 확인 (정확히 2개의 #만)
            if line.strip().split()[0] == "##":
                start_idx = i
        # 시작을 찾은 후 다음 같은 레벨의 섹션 찾기
        elif start_idx is not None and line.strip().startswith("## "):
            if line.strip().split()[0] == "##":
                end_idx = i
                break
    
    if start_idx is None:
        return None
    
    if end_idx is None:
        end_idx = len(lines)
    
    return (start_idx, end_idx)
```

### 2. 섹션 패치

```python
def patch_section(doc_path: str, section_name: str, new_content: str, create_backup: bool = True) -> bool:
    """
    문서의 특정 섹션만 업데이트합니다.
    
    Args:
        doc_path: 문서 파일 경로
        section_name: 섹션 이름 (## 제외)
        new_content: 새 내용 (섹션 제목 제외)
        create_backup: 백업 생성 여부
    
    Returns:
        성공 여부
    """
    import os
    from pathlib import Path
    
    doc_path = Path(doc_path)
    
    if not doc_path.exists():
        print(f"❌ 파일이 존재하지 않습니다: {doc_path}")
        return False
    
    # 백업 생성
    if create_backup:
        backup_path = doc_path.with_suffix(doc_path.suffix + ".backup")
        import shutil
        shutil.copy2(doc_path, backup_path)
    
    try:
        # 파일 읽기
        with open(doc_path, "r", encoding="utf-8") as f:
            lines = f.readlines()
        
        # 섹션 찾기
        section_range = find_section(lines, section_name)
        
        # 새 내용 준비 (마지막에 빈 줄 추가)
        new_lines = [f"## {section_name}\n\n", new_content.rstrip() + "\n\n"]
        
        if section_range is None:
            # 섹션이 없으면 파일 끝에 추가
            lines.extend(new_lines)
        else:
            # 섹션 교체
            start_idx, end_idx = section_range
            lines = lines[:start_idx] + new_lines + lines[end_idx:]
        
        # 파일 쓰기
        with open(doc_path, "w", encoding="utf-8") as f:
            f.writelines(lines)
        
        return True
    
    except Exception as e:
        print(f"❌ 섹션 패치 실패: {e}")
        
        # 백업에서 복구
        if create_backup and backup_path.exists():
            print("백업에서 복구 중...")
            import shutil
            shutil.copy2(backup_path, doc_path)
        
        return False
```

### 3. 여러 섹션 일괄 패치

```python
def patch_multiple_sections(doc_path: str, sections: dict[str, str]) -> dict[str, bool]:
    """
    여러 섹션을 한 번에 패치합니다.
    
    Args:
        doc_path: 문서 파일 경로
        sections: {section_name: new_content} 딕셔너리
    
    Returns:
        {section_name: success} 결과 딕셔너리
    """
    results = {}
    
    # 첫 패치만 백업 생성
    first = True
    
    for section_name, content in sections.items():
        success = patch_section(
            doc_path, 
            section_name, 
            content,
            create_backup=first
        )
        results[section_name] = success
        first = False
    
    return results
```

### 4. 섹션 읽기

```python
def read_section(doc_path: str, section_name: str) -> str | None:
    """
    문서에서 특정 섹션의 내용만 읽습니다.
    
    Args:
        doc_path: 문서 파일 경로
        section_name: 섹션 이름 (## 제외)
    
    Returns:
        섹션 내용 (제목 제외) 또는 None
    """
    from pathlib import Path
    
    doc_path = Path(doc_path)
    
    if not doc_path.exists():
        return None
    
    with open(doc_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    section_range = find_section(lines, section_name)
    
    if section_range is None:
        return None
    
    start_idx, end_idx = section_range
    
    # 섹션 제목 다음 줄부터 끝까지
    content_lines = lines[start_idx + 1:end_idx]
    
    return "".join(content_lines).strip()
```

## 상태 기반 문서 생성

### 템플릿 렌더링

```python
def render_template(template_path: str, state: dict) -> str:
    """
    템플릿과 상태를 기반으로 문서를 생성합니다.
    
    Args:
        template_path: 템플릿 파일 경로
        state: 세션 상태 딕셔너리
    
    Returns:
        렌더링된 문서 내용
    """
    with open(template_path, "r", encoding="utf-8") as f:
        template = f.read()
    
    # 메타데이터 치환
    doc = template.replace("{문서 제목}", state["metadata"]["title"])
    doc = doc.replace("{목적 설명}", state["metadata"]["purpose"])
    doc = doc.replace("{독자 목록}", ", ".join(state["metadata"]["target_readers"]))
    doc = doc.replace("{작성자명}", state["metadata"]["author"])
    doc = doc.replace("{YYYY-MM-DD}", state["created_at"][:10])
    
    # 플랫폼 섹션 생성
    for platform in state["metadata"]["platforms"]:
        # 영역 정의 표
        areas_table = generate_areas_table(state["areas"], platform)
        doc = doc.replace(f"## {{플랫폼명}} 영역 정의", f"## {platform} 영역 정의")
        # ... (계속)
    
    return doc
```

### 섹션별 생성 함수

```python
def generate_screens_table(screens: list[dict]) -> str:
    """화면 설명 표를 생성합니다."""
    lines = ["| 화면 | 목적 | 핵심 노출 | 상태 차이 | 주요 액션 | 비고 |"]
    lines.append("| --- | --- | --- | --- | --- | --- |")
    
    for screen in screens:
        row = f"| {screen['name']} | {screen['purpose']} | {screen['key_exposure']} | {screen['state_diff']} | {screen['actions']} | {screen.get('notes', '')} |"
        lines.append(row)
    
    return "\n".join(lines)

def generate_policies_table(policies: list[dict]) -> str:
    """공통 정책 표를 생성합니다."""
    lines = ["| 정책 | 설명 | 추적 참조 |"]
    lines.append("| --- | --- | --- |")
    
    for policy in policies:
        refs = ", ".join(f"`{ref}`" for ref in policy["tracking_refs"])
        row = f"| {policy['name']} | {policy['description']} | {refs} |"
        lines.append(row)
    
    return "\n".join(lines)

def generate_areas_table(areas: list[dict], platform: str) -> str:
    """영역 정의 표를 생성합니다."""
    lines = ["| 영역 ID | 유형 | 화면 | 영역명 | 정책 요약 |"]
    lines.append("| --- | --- | --- | --- | --- |")
    
    platform_areas = [a for a in areas if a["platform"] == platform]
    
    for area in platform_areas:
        row = f"| `{area['id']}` | `{area['type']}` | {area['screen']} | {area['name']} | {area['policy_summary']} |"
        lines.append(row)
    
    return "\n".join(lines)

def generate_requirements_table(requirements: list[dict], platform: str) -> str:
    """요구사항 표를 생성합니다."""
    lines = ["| REQ-ID | 대상 영역 | 조건 | 보여줄 내용·동작 | 예외 |"]
    lines.append("| --- | --- | --- | --- | --- |")
    
    platform_reqs = [r for r in requirements if r["platform"] == platform]
    
    for req in platform_reqs:
        row = f"| `{req['id']}` | `{req['area_id']}` {req['area_name']} | {req['condition']} | {req['action']} | {req['exception']} |"
        lines.append(row)
    
    return "\n".join(lines)

def generate_rules_table(rules: list[dict], platform: str) -> str:
    """규칙 표를 생성합니다."""
    lines = ["| RULE-ID | 규칙 |"]
    lines.append("| --- | --- |")
    
    platform_rules = [r for r in rules if r["platform"] == platform]
    
    for rule in platform_rules:
        row = f"| `{rule['id']}` | {rule['content']} |"
        lines.append(row)
    
    return "\n".join(lines)

def generate_testcases_table(testcases: list[dict], platform: str) -> str:
    """테스트케이스 표를 생성합니다."""
    lines = ["| TC-ID | 연계 REQ-ID | 시나리오 | 기대 결과 |"]
    lines.append("| --- | --- | --- | --- |")
    
    platform_tcs = [t for t in testcases if t["platform"] == platform]
    
    for tc in platform_tcs:
        row = f"| `{tc['id']}` | `{tc['req_id']}` | {tc['scenario']} | {tc['expected']} |"
        lines.append(row)
    
    return "\n".join(lines)
```

### 문서 점진적 업데이트

```python
def update_document_incrementally(state: dict) -> None:
    """
    상태 변경사항을 문서에 점진적으로 반영합니다.
    """
    doc_path = state["document"]["path"]
    
    # 메타데이터 섹션 (인용 블록)
    meta_content = f"""> 문서 목적: {state['metadata']['purpose']}
>
> 대상 독자: {', '.join(state['metadata']['target_readers'])}
>
> 작성자: {state['metadata']['author']}
>
> 작성일: {state['created_at'][:10]}
"""
    patch_section(doc_path, state['metadata']['title'], meta_content)
    
    # 화면 설명 섹션
    if state["document"]["sections"].get("screens") == "completed":
        screens_table = generate_screens_table(state["screens"])
        patch_section(doc_path, "화면 설명", screens_table)
    
    # 공통 정책 섹션
    if state["document"]["sections"].get("policies") == "completed":
        policies_table = generate_policies_table(state["policies"])
        patch_section(doc_path, "공통 정책", policies_table)
    
    # 플랫폼별 섹션
    for platform in state["metadata"]["platforms"]:
        # 영역 정의
        if state["document"]["sections"].get("areas") == "completed":
            areas_table = generate_areas_table(state["areas"], platform)
            patch_section(doc_path, f"{platform} 영역 정의", areas_table)
        
        # 요구사항
        if state["document"]["sections"].get("requirements") == "completed":
            req_table = generate_requirements_table(state["requirements"], platform)
            patch_section(doc_path, f"{platform} 요구사항", req_table)
        
        # 규칙
        if state["document"]["sections"].get("rules") == "completed":
            rules_table = generate_rules_table(state["rules"], platform)
            patch_section(doc_path, f"{platform} 규칙", rules_table)
        
        # 테스트케이스
        if state["document"]["sections"].get("testcases") == "completed":
            tc_table = generate_testcases_table(state["testcases"], platform)
            patch_section(doc_path, f"{platform} 테스트케이스", tc_table)
```

## 사용 예시

### 단일 섹션 업데이트

```python
# 화면 설명 표만 업데이트
screens_table = generate_screens_table(state["screens"])
patch_section("문서.md", "화면 설명", screens_table)
```

### 여러 섹션 일괄 업데이트

```python
sections = {
    "화면 설명": generate_screens_table(state["screens"]),
    "공통 정책": generate_policies_table(state["policies"]),
    "iPhone 영역 정의": generate_areas_table(state["areas"], "iPhone")
}

results = patch_multiple_sections("문서.md", sections)

for section, success in results.items():
    if success:
        print(f"✓ {section} 업데이트 완료")
    else:
        print(f"❌ {section} 업데이트 실패")
```

### 섹션 읽기

```python
# 기존 내용 확인
current_policies = read_section("문서.md", "공통 정책")
print(current_policies)
```

## 에러 처리 및 복구

### 백업 자동 생성

```python
def safe_patch_with_backup(doc_path: str, section_name: str, new_content: str):
    """백업을 생성하고 안전하게 패치합니다."""
    from datetime import datetime
    import shutil
    from pathlib import Path
    
    doc_path = Path(doc_path)
    
    # 타임스탬프 백업
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    backup_path = doc_path.with_suffix(f".{timestamp}.backup")
    shutil.copy2(doc_path, backup_path)
    
    try:
        success = patch_section(doc_path, section_name, new_content, create_backup=False)
        
        if success:
            # 성공 시 백업 삭제 (선택)
            # backup_path.unlink()
            return True
        else:
            # 실패 시 백업에서 복구
            shutil.copy2(backup_path, doc_path)
            return False
    
    except Exception as e:
        print(f"오류 발생: {e}")
        # 백업에서 복구
        shutil.copy2(backup_path, doc_path)
        return False
```

### 섹션 누락 검증

```python
def validate_document_sections(doc_path: str, required_sections: list[str]) -> dict[str, bool]:
    """필수 섹션이 모두 존재하는지 확인합니다."""
    with open(doc_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    results = {}
    for section in required_sections:
        results[section] = find_section(lines, section) is not None
    
    return results
```

## 성능 최적화

### 메모리 효율적인 대용량 문서 처리

```python
def patch_section_streaming(doc_path: str, section_name: str, new_content: str):
    """대용량 문서를 스트리밍 방식으로 처리합니다."""
    import tempfile
    import shutil
    
    with tempfile.NamedTemporaryFile(mode='w', encoding='utf-8', delete=False) as tmp:
        with open(doc_path, 'r', encoding='utf-8') as f:
            in_section = False
            section_found = False
            
            for line in f:
                if line.strip().startswith("## ") and section_name in line:
                    # 섹션 시작
                    tmp.write(f"## {section_name}\n\n")
                    tmp.write(new_content.rstrip() + "\n\n")
                    in_section = True
                    section_found = True
                elif in_section and line.strip().startswith("## "):
                    # 다음 섹션 시작
                    in_section = False
                    tmp.write(line)
                elif not in_section:
                    tmp.write(line)
        
        tmp_path = tmp.name
    
    # 임시 파일을 원본으로 교체
    shutil.move(tmp_path, doc_path)
```

## 참고

- 마크다운 파싱: https://python-markdown.github.io/
- 파일 안전 쓰기: tempfile, shutil 활용
