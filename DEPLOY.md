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

---

## 개발 워크플로우 (uv + taskipy)

이 프로젝트는 `uv` 패키지 관리자와 `taskipy` 작업 러너를 사용합니다.

### 1. 개발 환경 설정

먼저 uv를 설치하세요 (위의 "uv 설치" 섹션 참고)

### 2. 프로젝트 의존성 설치

```bash
# 프로젝트 루트에서 실행
uv sync
```

### 3. 사용 가능한 스크립트

```bash
# 개발 서버 실행
uv run task dev     # 또는 uv run task d

# 테스트 실행
uv run task test    # 또는 uv run task t
uv run task test-cov  # 커버리지 포함

# 코드 품질 검사
uv run task lint    # 또는 uv run task l
uv run task format  # 또는 uv run task f
uv run task type-check

# 빌드 & 정리
uv run task build
uv run task clean

# 전체 검사 (CI용)
uv run task check   # lint + type-check + test
```

### 4. 로컬 개발 모드로 설치

```bash
# 편집 가능 모드로 설치
uv pip install -e .
```

---

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

## GitHub Actions 자동 배포 (권장)

이 프로젝트는 GitHub Actions를 통한 자동 배포를 지원합니다.

### 설정된 워크플로우

#### 1. 자동 테스트 (`.github/workflows/test.yml`)

PR 및 main 브랜치 push 시 자동 실행:
- Python 3.11, 3.12 매트릭스 테스트
- 린트, 타입 체크, 테스트 실행
- 코드 품질 자동 검증

#### 2. 자동 PyPI 배포 (`.github/workflows/publish.yml`)

GitHub Release 생성 시 자동으로 PyPI에 배포:
- 전체 검사 실행 (lint + type-check + test)
- 패키지 빌드
- PyPI 자동 업로드

### GitHub Secrets 설정

배포를 위해 다음 Secret을 설정해야 합니다:

1. **PyPI API 토큰 발급**
   - https://pypi.org/manage/account/token/ 접속
   - "Add API token" 클릭
   - Token name: `legacy-code-archive-mcp`
   - Scope: "Entire account" (첫 배포) 또는 프로젝트 선택
   - 생성된 토큰 복사 (⚠️ 한 번만 표시됨!)

2. **GitHub Secret 추가**
   - GitHub 저장소 → **Settings** → **Secrets and variables** → **Actions**
   - **New repository secret** 클릭
   - Name: `PYPI_API_TOKEN`
   - Secret: 위에서 복사한 PyPI API 토큰 붙여넣기
   - **Add secret** 클릭

### 릴리스 생성 및 자동 배포

#### 방법 1: GitHub UI 사용

1. GitHub 저장소 → **Releases** → **Create a new release**
2. **Choose a tag** → 새 태그 생성 (예: `v1.0.0`)
3. Release title: `v1.0.0 - Initial Release`
4. 릴리스 노트 작성
5. **Publish release** 클릭
6. GitHub Actions가 자동으로 PyPI에 배포 🚀

#### 방법 2: Git 명령어 사용

```bash
# 1. 버전 번호 업데이트
# pyproject.toml의 version을 수정

# 2. 변경사항 커밋
git add pyproject.toml
git commit -m "Bump version to 1.0.1"

# 3. 태그 생성
git tag v1.0.1

# 4. 푸시
git push origin main --tags

# 5. GitHub에서 Release 생성
# 또는 gh CLI 사용:
gh release create v1.0.1 --title "v1.0.1 - Bug fixes" --notes "버그 수정 및 성능 개선"
```

### 배포 상태 확인

- **Actions 탭**: 워크플로우 실행 상태 확인
- **PyPI**: https://pypi.org/project/legacy-code-archive-mcp/
- **배지**: README.md에서 배포 상태 확인

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
