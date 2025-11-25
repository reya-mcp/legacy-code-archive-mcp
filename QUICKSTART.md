# 빠른 시작 가이드

## 방법 1: uvx 사용 (권장 - 가장 간편!)

### 1. uv 설치

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Claude Desktop 설정

`claude_desktop_config.json`에 다음을 추가:

**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`
**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`

```json
{
  "mcpServers": {
    "legacy-code-archive": {
      "command": "uvx",
      "args": [
        "--from",
        "git+https://github.com/yourusername/legacy-code-archive-mcp",
        "legacy-code-archive-mcp"
      ],
      "env": {
        "OPENAI_API_KEY": "sk-your-openai-api-key",
        "PROJECT_PATHS": "C:\\Projects\\old-project1,C:\\Projects\\old-project2"
      }
    }
  }
}
```

### 3. Claude Desktop 재시작

설정을 저장하고 Claude Desktop을 재시작하면 끝! 🎉

---

## 방법 2: 로컬 개발 모드 (uv + taskipy)

### 1. uv 설치

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. 프로젝트 의존성 설치

```bash
# 프로젝트 루트에서 실행
uv sync
```

### 3. 환경 설정

`.env` 파일을 생성하세요:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
PROJECT_PATHS=/path/to/your/legacy/project
```

### 4. 개발 스크립트 실행

```bash
# 개발 서버 실행
uv run task dev

# 테스트 실행
uv run task test

# 코드 포맷팅
uv run task format

# 전체 검사 (lint + type-check + test)
uv run task check
```

**사용 가능한 모든 스크립트:**
- `dev` / `d` - 개발 서버 실행
- `test` / `t` - 테스트 실행
- `test-cov` - 커버리지 포함 테스트
- `lint` / `l` - 코드 품질 검사
- `format` / `f` - 자동 포맷팅
- `type-check` - 타입 체크
- `build` - 패키지 빌드
- `clean` - 빌드 파일 정리
- `check` - 전체 검사 (CI용)

### 5. Claude Desktop 통합

```json
{
  "mcpServers": {
    "legacy-code-archive": {
      "command": "python",
      "args": ["C:\\Work\\RnD\\legacy-code-archive-mcp\\legacy_code_archive_mcp\\server.py"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key",
        "PROJECT_PATHS": "C:\\Projects\\old-project1,C:\\Projects\\old-project2"
      }
    }
  }
}
```

---

## Claude에서 사용하기

```
사용자: "레거시 프로젝트 인덱싱해줘"
Claude: [index_codebase 도구 실행]

사용자: "Java Excel 파싱 유틸리티 찾아줘"
Claude: [검색하여 관련 코드 스니펫 반환]
```

## 다음 단계

- 자세한 사용법은 [USAGE.md](USAGE.md) 참고
- 테스트 시나리오는 [EVALUATION.md](EVALUATION.md) 참고
- 아키텍처 상세 정보는 [README.md](README.md) 참고
