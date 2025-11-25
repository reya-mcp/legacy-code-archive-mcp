# 사용 가이드 - 레거시 코드 아카이브 MCP 서버

## 설치

### 1. Python 의존성 설치

pip 사용:
```bash
pip install -r requirements.txt
```

또는 uv 사용 (권장):
```bash
uv pip install -r requirements.txt
```

### 2. 환경 변수 설정

예시 환경 파일 복사:
```bash
cp .env.example .env
```

`.env` 파일을 편집하여 다음을 설정:
- `OPENAI_API_KEY`: OpenAI API 키
- `PROJECT_PATHS`: 레거시 프로젝트 경로 (쉼표로 구분)

예시:
```env
OPENAI_API_KEY=sk-proj-xxxxxxxxxxxxx
PROJECT_PATHS=/Users/me/old-java-project,/Users/me/vue-admin
```

## 서버 실행

### 로컬 개발 (stdio transport)

```bash
python src/server.py
```

### Claude Desktop 통합

`claude_desktop_config.json`에 다음을 추가하세요:

**macOS:** `~/Library/Application Support/Claude/claude_desktop_config.json`
**Windows:** `%APPDATA%\Claude\claude_desktop_config.json`

```json
{
  "mcpServers": {
    "legacy-code-archive": {
      "command": "python",
      "args": ["C:\\Work\\RnD\\legacy-code-archive-mcp\\src\\server.py"],
      "env": {
        "OPENAI_API_KEY": "sk-your-key-here",
        "PROJECT_PATHS": "C:\\Projects\\old-java,C:\\Projects\\vue-admin",
        "INCLUDED_EXTENSIONS": ".ts,.js,.vue,.java",
        "EXCLUDE_PATTERNS": "node_modules,dist,.git,__pycache__"
      }
    }
  }
}
```

## 사용 가능한 도구

### 1. index_codebase

`PROJECT_PATHS`에 정의된 모든 프로젝트를 스캔하고 인덱싱합니다.

**기능:**
- 증분 인덱싱 (변경된 파일만 처리)
- 자동 언어 감지
- 배치 임베딩 생성
- 진행률 보고

**Claude에서 사용:**
```
"레거시 프로젝트 인덱싱해줘"
"코드 인덱스 업데이트해줘"
```

**반환값:**
```json
{
  "total_files": 150,
  "new_files": 10,
  "updated_files": 5,
  "deleted_files": 2,
  "total_chunks": 850,
  "elapsed_time": 45.32,
  "errors": []
}
```

### 2. search_legacy_code

시맨틱 유사도를 사용하여 인덱싱된 코드를 검색합니다.

**파라미터:**
- `query` (문자열): 자연어 또는 코드 관련 키워드
- `limit` (정수, 기본값=5): 반환할 결과 수
- `project_filter` (문자열, 선택): 프로젝트 경로로 필터링

**Claude에서 사용:**
```
"Java Excel 파싱 유틸리티 찾아줘"
"Vue 인증 컴포넌트 검색해줘"
"TypeScript 이메일 검증 함수 보여줘"
```

**반환값:**
다음을 포함하는 Markdown 형식:
- 코드 스니펫 내용
- 파일 경로
- 프로젝트 경로
- 프로그래밍 언어
- 유사도 점수

## 사용 예시

1. **초기 인덱싱:**
   ```
   사용자: "레거시 프로젝트 인덱싱해줘"
   Claude: [index_codebase 도구 호출]
   결과: 150개 파일 인덱싱, 850개 청크 생성
   ```

2. **코드 검색:**
   ```
   사용자: "Java Excel 파싱 유틸리티 찾아줘"
   Claude: [search_legacy_code 호출, query="java excel parsing utility"]
   결과: 가장 관련성 높은 5개 코드 스니펫 반환
   ```

3. **검색 결과 필터링:**
   ```
   사용자: "old-java 프로젝트에서만 검색해줘"
   Claude: [project_filter와 함께 search_legacy_code 호출]
   결과: 특정 프로젝트의 필터링된 결과
   ```

## 지원 언어

- Java (`.java`)
- TypeScript (`.ts`, `.tsx`)
- JavaScript (`.js`, `.jsx`)
- Vue.js (`.vue`)

언어별 텍스트 분할은 다음을 보존합니다:
- 클래스 및 메서드 경계
- 함수 정의
- 제어 흐름 구조

## 성능 팁

1. **증분 인덱싱:** 서버가 파일 수정을 자동으로 추적하므로, 재인덱싱 시 변경된 파일만 처리됩니다.

2. **API 비용:** OpenAI text-embedding-3-small은 백만 토큰당 $0.02입니다. 일반적인 비용:
   - 1,000개 파일 ≈ $0.50
   - 10,000개 파일 ≈ $5.00

3. **제외 패턴:** `EXCLUDE_PATTERNS`에 빌드 디렉토리와 의존성을 추가하여 인덱싱 시간을 단축하세요.

## 문제 해결

### 오류: "OPENAI_API_KEY environment variable is required"
- `.env` 파일이 존재하고 유효한 API 키가 포함되어 있는지 확인
- 또는 Claude Desktop 설정에서 환경 변수 설정

### 오류: "PROJECT_PATHS environment variable is required"
- `PROJECT_PATHS`에 최소 하나의 프로젝트 경로 추가
- 상대 경로가 아닌 절대 경로 사용

### 검색 결과 없음
- 먼저 `index_codebase` 도구를 실행하여 인덱스 생성
- `PROJECT_PATHS`에 파일이 존재하는지 확인
- 파일 확장자가 `INCLUDED_EXTENSIONS`에 포함되어 있는지 확인

### 인덱싱이 느림
- `PROJECT_PATHS`를 더 적은 프로젝트로 줄이기
- `EXCLUDE_PATTERNS`에 더 많은 패턴 추가
- 설정에서 더 작은 `chunk_size` 사용

## 데이터베이스 저장소

LanceDB는 `LANCEDB_PATH`로 지정된 디렉토리를 생성합니다 (기본값: `./lancedb_data`).

**인덱스 초기화:**
```bash
rm -rf ./lancedb_data
```

그 다음 `index_codebase`를 다시 실행하세요.

## 개발

### 테스트 실행
```bash
pytest
```

### 코드 포맷팅
```bash
black src/
ruff check src/
```

### 타입 체킹
```bash
mypy src/
```
