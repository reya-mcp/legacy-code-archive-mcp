# 배포 가이드

## uvx를 사용한 간편 실행 (권장)

이제 `uvx`를 사용하여 패키지 설치 없이 바로 실행할 수 있습니다!

### 1. uv 설치

```bash
# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"

# macOS/Linux
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### 2. Claude Desktop 설정

`claude_desktop_config.json` 파일에 다음을 추가:

**Windows**: `%APPDATA%\Claude\claude_desktop_config.json`
**macOS**: `~/Library/Application Support/Claude/claude_desktop_config.json`

#### PyPI에 배포한 경우:
```json
{
  "mcpServers": {
    "legacy-code-archive": {
      "command": "uvx",
      "args": ["legacy-code-archive-mcp"],
      "env": {
        "OPENAI_API_KEY": "sk-your-openai-api-key",
        "PROJECT_PATHS": "C:\\Projects\\old-java,C:\\Projects\\vue-admin"
      }
    }
  }
}
```

#### GitHub에서 직접 실행:
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
        "PROJECT_PATHS": "C:\\Projects\\old-java"
      }
    }
  }
}
```

### 3. Claude Desktop 재시작

설정을 저장하고 Claude Desktop을 재시작하면 자동으로 서버가 로드됩니다!

## PyPI 배포 (패키지 게시)

### 1. 빌드 도구 설치

```bash
pip install build twine
```

### 2. 패키지 빌드

```bash
# 프로젝트 루트에서 실행
python -m build
```

이 명령은 `dist/` 디렉토리에 다음 파일들을 생성합니다:
- `legacy_code_archive_mcp-1.0.0.tar.gz` (소스 배포)
- `legacy_code_archive_mcp-1.0.0-py3-none-any.whl` (휠 배포)

### 3. TestPyPI에 업로드 (테스트)

```bash
twine upload --repository testpypi dist/*
```

### 4. PyPI에 업로드 (실제 배포)

```bash
twine upload dist/*
```

### 5. 배포 후 사용

사용자는 이제 다음과 같이 설치할 수 있습니다:

```bash
# 일반 설치
pip install legacy-code-archive-mcp

# 또는 uvx로 바로 실행
uvx legacy-code-archive-mcp
```

## GitHub Actions 자동 배포 (선택)

`.github/workflows/publish.yml` 파일 생성:

```yaml
name: Publish to PyPI

on:
  release:
    types: [published]

jobs:
  deploy:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install build twine

    - name: Build package
      run: python -m build

    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

### GitHub Secrets 설정:
1. GitHub 저장소 → Settings → Secrets and variables → Actions
2. `PYPI_API_TOKEN` 추가 (PyPI에서 발급받은 API 토큰)

## 전통적인 방법 (pip install)

### 로컬 설치 (개발용)

```bash
# 편집 가능 모드로 설치
pip install -e .

# 개발 의존성 포함
pip install -e ".[dev]"
```

### Claude Desktop 설정 (전통적인 방법)

```json
{
  "mcpServers": {
    "legacy-code-archive": {
      "command": "python",
      "args": ["-m", "legacy_code_archive_mcp.server"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key",
        "PROJECT_PATHS": "C:\\Projects\\old-java"
      }
    }
  }
}
```

## 배포 전 체크리스트

- [ ] 모든 테스트 통과 확인
- [ ] 버전 번호 업데이트 (`pyproject.toml`, `__init__.py`)
- [ ] README.md 업데이트
- [ ] CHANGELOG 작성 (선택)
- [ ] LICENSE 파일 확인
- [ ] `.gitignore`에 빌드 디렉토리 추가
  ```
  dist/
  build/
  *.egg-info/
  ```

## 버전 관리 전략

- **패치** (1.0.0 → 1.0.1): 버그 수정
- **마이너** (1.0.0 → 1.1.0): 새 기능 추가 (하위 호환성 유지)
- **메이저** (1.0.0 → 2.0.0): 주요 변경 (하위 호환성 없음)

## 문제 해결

### uvx가 없는 경우
```bash
# uv 설치 확인
uv --version

# 없으면 위의 "uv 설치" 섹션 참고
```

### 패키지를 찾을 수 없는 경우
```bash
# PyPI에 배포되었는지 확인
pip search legacy-code-archive-mcp

# 또는 직접 확인
# https://pypi.org/project/legacy-code-archive-mcp/
```

### Claude Desktop에서 서버가 로드되지 않는 경우
1. Claude Desktop 로그 확인
2. 환경 변수가 올바른지 확인
3. Python 경로 확인

## 추가 리소스

- [uv 공식 문서](https://github.com/astral-sh/uv)
- [PyPI 패키징 가이드](https://packaging.python.org/tutorials/packaging-projects/)
- [FastMCP 문서](https://github.com/jlowin/fastmcp)
