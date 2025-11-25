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

## 방법 2: 로컬 개발 모드

### 1. 의존성 설치

```bash
pip install -r requirements.txt
```

### 2. 환경 설정

`.env` 파일을 생성하세요:

```env
OPENAI_API_KEY=sk-your-openai-api-key-here
PROJECT_PATHS=/path/to/your/legacy/project
```

### 3. 서버 로컬 테스트

```bash
# 서버 실행
python legacy_code_archive_mcp/server.py

# 다른 터미널에서 fastmcp CLI로 테스트
fastmcp dev legacy_code_archive_mcp/server.py
```

### 4. Claude Desktop 통합

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
