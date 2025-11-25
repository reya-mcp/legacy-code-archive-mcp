# Legacy Code Archive MCP Server

> OpenAI 임베딩과 LanceDB를 활용한 레거시 코드 시맨틱 검색 MCP 서버

[![Python 3.11+](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/downloads/)
[![FastMCP](https://img.shields.io/badge/FastMCP-2.13+-green.svg)](https://github.com/jlowin/fastmcp)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## 🚀 빠른 시작

### uvx로 간편 실행 (권장)

```bash
# 1. uv 설치
curl -LsSf https://astral.sh/uv/install.sh | sh  # macOS/Linux
# 또는
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"  # Windows

# 2. Claude Desktop 설정에 추가
# claude_desktop_config.json에:
{
  "mcpServers": {
    "legacy-code-archive": {
      "command": "uvx",
      "args": ["--from", "git+https://github.com/yourusername/legacy-code-archive-mcp", "legacy-code-archive-mcp"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key",
        "PROJECT_PATHS": "/path/to/project1,/path/to/project2"
      }
    }
  }
}
```

더 자세한 설치 방법은 [QUICKSTART.md](QUICKSTART.md) 및 [DEPLOY.md](DEPLOY.md)를 참고하세요.

---

## 1. 개요 (Overview)

### 1.1 목적

* 로컬에 분산된 과거 프로젝트(Legacy Projects)의 소스 코드를 벡터화하여 인덱싱한다.
* LLM이 사용자의 개발 맥락에 맞춰 과거의 코드 스니펫을 검색하고 재사용할 수 있도록 지원한다.

### 1.2 주요 변경 사항 (v2.0)

* **Framework 전환:** SDK 직접 사용 → **FastMCP** (개발 생산성 및 유지보수성 향상).
* **설정 주도권 이전:** MCP 서버 내부 설정 파일 제거 → **클라이언트(Claude Desktop 등) 환경 변수 주입** 방식.
* **지원 언어 확장:** TypeScript/JavaScript 외 **Java, Vue.js**에 대한 명시적 지원 및 청킹 전략 최적화.
* **임베딩 모델 확정:** OpenAI `text-embedding-3-small` (코드 검색 효율성 최우선).

-----

## 2. 시스템 아키텍처 (System Architecture)

### 2.1 구성도

설정 값이 클라이언트에서 서버로 주입되는 흐름이 핵심입니다.

```mermaid
graph LR
    A[Client: Claude Desktop] -- "1. Env Vars Injection (Config)" --> B[FastMCP Server Instance]
    B -- "2. File Scan" --> C[Local File System]
    C -- "3. Read Content" --> B
    B -- "4. Embedding Request" --> D[OpenAI API]
    D -- "5. Vector" --> B
    B -- "6. Upsert" --> E[LanceDB (Local File)]

    subgraph Configuration
    P[PROJECT_PATHS]
    X[EXCLUDE_PATTERNS]
    I[INCLUDED_EXTENSIONS]
    end

    P --> A
    X --> A
    I --> A
```

### 2.2 기술 스택

* **Language:** `Python 3.11+`
* **Framework:** `FastMCP` (Python MCP Server Framework)
* **Database:** `LanceDB` (Embedded Vector DB)
* **Embedding:** `OpenAI text-embedding-3-small`
* **Processing:** `LangChain` (RecursiveCharacterTextSplitter)
* **HTTP Client:** `httpx` (비동기 API 호출)
* **Validation:** `Pydantic` (자동 스키마 생성)

-----

## 3. 인터페이스 및 설정 설계 (Interface & Config Design)

### 3.1 환경 변수 명세 (Environment Variables)

이 서버는 별도의 설정 파일을 읽지 않으며, 오직 환경 변수에 의존합니다. 클라이언트(`claude_desktop_config.json`)에서 이 값을 `env` 필드로 전달해야 합니다.

| 변수명 | 타입 | 설명 | 기본값 (Fallback) |
| :--- | :--- | :--- | :--- |
| **`PROJECT_PATHS`** | String (CSV) | 인덱싱할 프로젝트 루트 경로들을 쉼표로 구분. (필수) <br> 예: `/Users/me/old-java,/Users/me/vue-admin` | `""` (작동 안함) |
| **`INCLUDED_EXTENSIONS`** | String (CSV) | 인덱싱 대상 확장자 목록. <br> 예: `.ts,.vue,.java` | `.ts,.js,.vue,.java` |
| **`EXCLUDE_PATTERNS`** | String (CSV) | 파일 스캔 시 무시할 패턴 목록. <br> 예: `node_modules,dist,.git,__pycache__` | `node_modules`, `dist`, `.git`, `__pycache__` 등 표준 제외 목록 |
| **`OPENAI_API_KEY`** | String | OpenAI API 키 | (Required) |

### 3.2 제공 도구 (Tools)

Python FastMCP의 데코레이터(`@mcp.tool`) 기반 패턴을 사용하여 간결하게 구현합니다.

#### 3.2.1 `index_codebase`

* **설명:** 환경 변수(`PROJECT_PATHS`)에 정의된 모든 경로를 스캔하여 증분 인덱싱을 수행합니다.
* **입력:** 없음 (환경 변수 기반으로 동작)
* **출력:** 처리된 파일 수, 생성된 청크 수, 업데이트된 파일 수, 소요 시간이 포함된 JSON 형식 문자열.
* **구현 예시:**
  ```python
  @mcp.tool
  async def index_codebase() -> str:
      """Scan and index all projects defined in PROJECT_PATHS environment variable."""
      # 구현 로직
  ```

#### 3.2.2 `search_legacy_code`

* **설명:** 인덱싱된 코드 베이스에서 의미론적(Semantic) 검색을 수행합니다.
* **입력:**
  * `query` (str): 검색할 자연어 질문 또는 코드 키워드.
  * `limit` (int): 반환할 코드 조각 개수 (Default: 5).
  * `project_filter` (Optional[str]): 특정 프로젝트로 필터링 (프로젝트 경로).
* **출력:** 코드 스니펫 + 메타데이터(프로젝트 경로, 파일 경로, 언어)가 Markdown 형식으로 포맷팅된 텍스트.
* **구현 예시:**
  ```python
  @mcp.tool
  async def search_legacy_code(
      query: str,
      limit: int = 5,
      project_filter: Optional[str] = None
  ) -> str:
      """Search for code snippets using semantic similarity."""
      # 구현 로직
  ```

-----

## 4. 상세 처리 로직 (Detailed Logic)

### 4.1 언어별 청킹 전략 (Chunking Strategy)

각 언어의 문법적 특성을 고려하여 LangChain Python의 `RecursiveCharacterTextSplitter.from_language()`를 사용합니다.

| 언어 | 확장자 | Splitter 설정 (LangChain Python) | 비고 |
| :--- | :--- | :--- | :--- |
| **Java** | `.java` | `RecursiveCharacterTextSplitter.from_language(Language.JAVA, ...)` | 클래스, 메서드 단위 보존이 중요함. |
| **TypeScript** | `.ts`, `.tsx` | `RecursiveCharacterTextSplitter.from_language(Language.JS, ...)` | JS 문법 기반으로 분할. |
| **JavaScript** | `.js`, `.jsx` | `RecursiveCharacterTextSplitter.from_language(Language.JS, ...)` | - |
| **Vue.js** | `.vue` | `RecursiveCharacterTextSplitter.from_language(Language.JS, ...)` | Vue SFC(Single File Component)는 HTML/JS/CSS가 섞여있으나, 주로 `<script>` 로직 검색이 목적이므로 JS Splitter가 가장 무난함. (HTML 태그도 어느 정도 보존됨) |
| **기타** | 그 외 | `RecursiveCharacterTextSplitter(...)` | 개행 문자 위주로 분할. |

* **Chunk Size:** 1000 characters (코드의 맥락을 충분히 담기 위함)
* **Overlap:** 200 characters (함수 경계 등에서 문맥 손실 방지)

**Python 구현 예시:**
```python
from langchain.text_splitter import RecursiveCharacterTextSplitter, Language

# Java 파일 청킹
java_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.JAVA,
    chunk_size=1000,
    chunk_overlap=200
)

# JavaScript/TypeScript 파일 청킹
js_splitter = RecursiveCharacterTextSplitter.from_language(
    language=Language.JS,
    chunk_size=1000,
    chunk_overlap=200
)
```

### 4.2 인덱싱 파이프라인 (Indexing Pipeline)

1. **Load Config:** `os.environ`에서 설정 로드 및 파싱.
2. **Incremental Indexing:** `index_codebase` 호출 시, 증분 업데이트 전략 사용:
      * 기존 인덱싱된 파일들의 `lastModified` 시간과 현재 파일 시스템의 수정 시간 비교.
      * 변경된 파일만 기존 벡터 삭제 후 재임베딩.
      * 새로운 파일은 추가 인덱싱.
      * 삭제된 파일은 DB에서 제거.
      * OpenAI API 비용 절감 및 인덱싱 속도 향상.
3. **Glob Scan:** Python `pathlib.Path.rglob()` 또는 `glob.glob()`을 사용하여 파일 스캔.
4. **Language Detection:** 파일 확장자 기반으로 적절한 Splitter 선택.
5. **Embedding & Storage:**
      * 비용 효율성을 위해 문서는 100개 단위 등 Batch로 묶어 OpenAI API 호출.
      * LanceDB에 벡터와 메타데이터 저장.

-----

## 5. 데이터 스키마 (LanceDB Schema)

LanceDB는 NoSQL처럼 유연하지만, 명확한 검색을 위해 다음 스키마를 준수합니다.

```python
from typing import TypedDict
from typing_extensions import NotRequired

class CodeSnippet(TypedDict):
    """LanceDB에 저장되는 코드 스니펫 스키마"""
    id: str              # UUID
    vector: list[float]  # OpenAI Embedding (1536 dim)
    content: str         # 코드 내용 (Chunk)

    # Metadata for Filtering & Context
    filePath: str        # 파일 절대 경로
    projectId: str       # 프로젝트 경로의 MD5 해시 (필터링 및 고유 식별 용도)
    projectPath: str     # 프로젝트 루트 절대 경로 (검색 시 컨텍스트 제공)
    language: str        # java, ts, vue 등
    lastModified: float  # 파일 수정 시각 (Unix timestamp, 증분 업데이트용)
```

**Pydantic 모델 버전:**
```python
from pydantic import BaseModel, Field

class CodeSnippetModel(BaseModel):
    """코드 스니펫 Pydantic 모델 (validation용)"""
    id: str = Field(..., description="고유 식별자 (UUID)")
    vector: list[float] = Field(..., description="OpenAI 임베딩 벡터 (1536 dim)")
    content: str = Field(..., description="코드 내용 (청크)")
    filePath: str = Field(..., description="파일 절대 경로")
    projectId: str = Field(..., description="프로젝트 경로의 MD5 해시")
    projectPath: str = Field(..., description="프로젝트 루트 절대 경로")
    language: str = Field(..., description="프로그래밍 언어 (java, ts, vue 등)")
    lastModified: float = Field(..., description="파일 수정 시각 (Unix timestamp)")
```

-----

## 6. 예상 사용 시나리오 (Usage Flow)

1. **설정:** 사용자가 `claude_desktop_config.json`에 `env` 변수로 프로젝트 A, B의 경로를 입력.
2. **초기화:** Claude에게 "내 프로젝트 코드들 인덱싱해줘"라고 요청 -\> `index_codebase` 실행.
3. **개발 중 질문:**
      * 사용자: "이전 자바 프로젝트에서 엑셀 파일 파싱하던 유틸 클래스 찾아줘."
      * MCP: `search_legacy_code(query: "java excel parsing utility class")` 실행.
      * 결과: `ExcelParser.java`의 핵심 메서드 부분 반환.
4. **적용:** 사용자는 반환된 코드를 보고 현재 프로젝트에 맞게 리팩토링하여 적용.
