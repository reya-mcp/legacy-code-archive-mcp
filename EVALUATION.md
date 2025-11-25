# 레거시 코드 아카이브 MCP 서버 평가 시나리오

## 개요

이 문서는 레거시 코드 아카이브 MCP 서버의 효과성을 테스트하기 위한 평가 시나리오를 포함합니다.

## 사전 요구사항

1. 샘플 코드 파일이 있는 테스트 프로젝트 디렉토리 생성
2. `PROJECT_PATHS` 환경 변수를 테스트 디렉토리로 설정
3. `OPENAI_API_KEY` 설정
4. 초기 인덱싱 실행

## 평가 시나리오

### 시나리오 1: 기본 인덱싱

**목표:** 서버가 코드 파일을 성공적으로 인덱싱할 수 있는지 확인

**설정:**
```bash
# 테스트 프로젝트 생성
mkdir -p /tmp/test-project/src
echo "public class HelloWorld { public static void main(String[] args) { System.out.println(\"Hello\"); } }" > /tmp/test-project/src/HelloWorld.java

# 환경 설정
export PROJECT_PATHS=/tmp/test-project
export OPENAI_API_KEY=sk-your-key
```

**테스트:**
```
사용자: "코드 프로젝트 인덱싱해줘"
예상: index_codebase 도구 호출
성공 기준:
- total_files >= 1 반환
- total_chunks >= 1 반환
- errors 배열에 오류 없음
```

### 시나리오 2: 언어 감지

**목표:** 다양한 파일 타입에 대한 올바른 언어 감지 확인

**설정:**
다양한 확장자의 파일 생성:
- Java: `Calculator.java`
- TypeScript: `utils.ts`
- Vue: `App.vue`
- JavaScript: `helper.js`

**테스트:**
인덱싱 후 언어별 패턴을 검색하고 결과에 올바른 언어 메타데이터가 포함되어 있는지 확인.

**성공 기준:**
- .java 파일이 "java"로 감지됨
- .ts/.tsx 파일이 "ts"로 감지됨
- .vue 파일이 "vue"로 감지됨
- .js/.jsx 파일이 "js"로 감지됨

### 시나리오 3: 시맨틱 검색 - Java Excel 파싱

**목표:** Java Excel 유틸리티에 대한 시맨틱 검색 테스트

**설정:**
Excel 파싱 코드가 있는 Java 파일 생성:
```java
import org.apache.poi.ss.usermodel.*;
public class ExcelParser {
    public List<String> parseExcel(String filePath) {
        // Excel 파싱 로직
    }
}
```

**테스트:**
```
사용자: "Java Excel 파싱 코드 찾아줘"
예상: search_legacy_code 호출, query="java excel parsing"
성공 기준:
- 결과에 ExcelParser.java 포함
- 내용에 "Excel" 또는 "poi" 키워드 포함
- 유사도 점수 > 0.5
```

### 시나리오 4: 증분 인덱싱

**목표:** 수정된 파일만 재인덱싱되는지 확인

**설정:**
1. 초기 인덱싱: 10개 파일
2. 1개 파일 수정
3. 재인덱싱 실행

**테스트:**
```
초기 인덱싱: 10개 파일
1개 파일 수정
재인덱싱
예상 결과:
- total_files: 10
- new_files: 0
- updated_files: 1
- deleted_files: 0
```

**성공 기준:**
- 수정된 파일만 재처리됨
- 수정되지 않은 파일은 건너뜀
- 전체 시간이 초기 인덱싱보다 훨씬 짧음

### 시나리오 5: 프로젝트 필터링

**목표:** 프로젝트별 검색 결과 필터링 테스트

**설정:**
두 개의 프로젝트:
- /tmp/project-a: `utils.ts` 포함
- /tmp/project-b: `helpers.ts` 포함

**테스트:**
```
사용자: "project-a에서만 유틸리티 검색해줘"
예상: search_legacy_code(query="utilities", project_filter="/tmp/project-a")
성공 기준:
- 결과에 /tmp/project-a의 파일만 포함
- /tmp/project-b의 결과 없음
```

### 시나리오 6: Vue 컴포넌트 검색

**목표:** Vue.js 컴포넌트 검색 테스트

**설정:**
Vue SFC 생성:
```vue
<template>
  <div class="login-form">
    <input type="email" v-model="email" />
  </div>
</template>
<script>
export default {
  data() {
    return { email: '' }
  }
}
</script>
```

**테스트:**
```
사용자: "Vue 인증 컴포넌트 찾아줘"
예상: search_legacy_code(query="vue authentication login")
성공 기준:
- .vue 파일 반환
- 내용에 login/auth 관련 코드 포함
- template과 script 섹션 모두 보존
```

### 시나리오 7: 제외 패턴

**목표:** 제외된 디렉토리가 인덱싱되지 않는지 확인

**설정:**
프로젝트 구조 생성:
```
/tmp/test-project/
  src/Main.java          (인덱싱되어야 함)
  node_modules/lib.js    (제외되어야 함)
  dist/bundle.js         (제외되어야 함)
```

**테스트:**
EXCLUDE_PATTERNS="node_modules,dist"로 인덱싱 후

**성공 기준:**
- Main.java가 인덱싱됨
- lib.js가 인덱싱되지 않음
- bundle.js가 인덱싱되지 않음

### 시나리오 8: 빈/잘못된 파일

**목표:** 엣지 케이스를 우아하게 처리

**설정:**
- 빈 파일: `empty.java` (0 바이트)
- 매우 큰 파일: `huge.java` (> 1MB)
- 잘못된 UTF-8: `corrupted.java`

**테스트:**
인덱싱 실행

**성공 기준:**
- 빈 파일은 건너뜀 (0개 청크)
- 큰 파일은 적절히 청킹됨
- 손상된 파일은 오류를 생성하지만 서버를 중단시키지 않음
- 오류가 errors 배열에 보고됨

### 시나리오 9: 다중 언어 프로젝트

**목표:** 다국어 프로젝트 인덱싱 테스트

**설정:**
혼합 언어 프로젝트:
- Java 백엔드
- Vue 프론트엔드
- TypeScript 유틸리티

**테스트:**
"API client" 검색 시 여러 언어의 결과 반환

**성공 기준:**
- 결과에 Java, Vue, TypeScript 파일 포함
- 각 결과에 올바른 언어 메타데이터
- 순위는 언어가 아닌 시맨틱 관련성 기반

### 시나리오 10: 장시간 인덱싱 진행률

**목표:** 대규모 프로젝트에 대한 진행률 보고 확인

**설정:**
100개 이상의 파일이 있는 대규모 프로젝트

**테스트:**
인덱싱 중 진행률 모니터링

**성공 기준:**
- 진행률 업데이트 보고됨 (0.1, ..., 1.0)
- Info 로그에 스캔 및 완료 메시지 표시
- 최종 결과에 정확한 통계 포함

## 성능 벤치마크

### 인덱싱 성능

| 파일 수 | 청크 수 | 시간 (초) | 비용 ($) |
|---------|---------|-----------|----------|
| 10      | ~50     | ~5        | ~$0.01   |
| 100     | ~500    | ~30       | ~$0.10   |
| 1000    | ~5000   | ~300      | ~$1.00   |

### 검색 성능

- 쿼리 임베딩: < 1초
- 벡터 검색: < 0.5초
- 전체 응답: < 2초

## 오류 처리 테스트

### 테스트 1: API 키 누락
```
OPENAI_API_KEY 설정 해제
서버 실행
예상: 명확한 오류 메시지와 함께 ValueError 발생
```

### 테스트 2: 잘못된 프로젝트 경로
```
PROJECT_PATHS=/nonexistent/path 설정
index_codebase 실행
예상: ValueError 또는 오류 메시지가 포함된 빈 결과
```

### 테스트 3: 속도 제한
```
많은 동시 요청 전송
예상: 우아한 재시도 또는 오류 메시지
```

## 성공 기준 요약

✅ 모든 도구를 검색하고 호출할 수 있음
✅ 증분 인덱싱으로 비용 90% 이상 절감
✅ 검색이 관련 결과 반환 (점수 > 0.5)
✅ 지원되는 타입에 대해 언어 감지가 100% 정확
✅ 프로젝트 필터링이 올바르게 작동
✅ 제외 패턴이 원치 않는 파일 인덱싱 방지
✅ 진행률 보고가 유용한 피드백 제공
✅ 오류 처리가 견고하고 정보 제공
✅ 성능이 벤치마크를 충족

## 평가 실행

### 자동화된 테스트 (향후)
```bash
# 테스트 의존성 설치
pip install pytest pytest-asyncio

# 테스트 스위트 실행
pytest tests/

# 커버리지와 함께 실행
pytest --cov=src tests/
```

### 수동 테스트
1. 테스트 프로젝트 설정
2. 환경 변수 구성
3. 각 시나리오 실행
4. 성공 기준 확인
5. 결과 문서화

## 참고 사항

- 모든 시나리오는 독립적이고 반복 가능해야 함
- 테스트 프로젝트에 임시 디렉토리 사용
- 평가 후 테스트 데이터 정리
- 테스트 중 API 비용 모니터링
