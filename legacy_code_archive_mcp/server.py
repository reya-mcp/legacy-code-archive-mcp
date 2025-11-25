#!/usr/bin/env python3
"""레거시 코드 아카이브 MCP 서버

OpenAI 임베딩과 LanceDB 벡터 저장소를 활용한 시맨틱 검색으로
레거시 코드 프로젝트를 인덱싱하고 검색하는 Model Context Protocol 서버입니다.
"""

import json
from typing import Optional
from fastmcp import FastMCP, Context
from legacy_code_archive_mcp.config import load_config
from legacy_code_archive_mcp.database import DatabaseService
from legacy_code_archive_mcp.embeddings import EmbeddingService
from legacy_code_archive_mcp.chunking import ChunkingService
from legacy_code_archive_mcp.indexing import IndexingService

# FastMCP 서버 초기화
mcp = FastMCP("legacy_code_archive_mcp")

# 설정 로드
config = load_config()

# 서비스 초기화
db_service = DatabaseService(config)
embedding_service = EmbeddingService(config)
chunking_service = ChunkingService(config)
indexing_service = IndexingService(
    config,
    db_service,
    embedding_service,
    chunking_service
)


@mcp.tool(
    name="index_codebase",
    annotations={
        "title": "Index Legacy Code Projects",
        "readOnlyHint": False,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def index_codebase(ctx: Context) -> str:
    """PROJECT_PATHS 환경 변수에 정의된 모든 프로젝트를 스캔하고 인덱싱합니다.

    이 도구는 다음과 같은 증분 인덱싱을 수행합니다:
    - 이전에 인덱싱된 파일과 파일 수정 시간 비교
    - 변경된 파일만 재인덱싱
    - 새 파일을 인덱스에 추가
    - 삭제된 파일을 인덱스에서 제거

    이 접근 방식은 OpenAI API 비용과 인덱싱 시간을 최소화합니다.

    Args:
        ctx: 로깅 및 진행률 보고를 위한 FastMCP 컨텍스트

    Returns:
        str: 다음 내용을 포함하는 JSON 형식 문자열:
        {
            "total_files": int,        # 프로젝트에서 발견된 전체 파일 수
            "new_files": int,          # 새로 인덱싱된 파일 수
            "updated_files": int,      # 재인덱싱된 수정된 파일 수
            "deleted_files": int,      # 제거된 삭제된 파일 수
            "total_chunks": int,       # 생성된 전체 청크 수
            "elapsed_time": float,     # 소요 시간(초)
            "errors": [str]            # 발생한 오류 목록
        }

    Example:
        사용 시기: 사용자가 "레거시 프로젝트 인덱싱해줘" 또는 "코드 인덱스 업데이트해줘"라고 요청할 때
        반환값: 인덱싱 작업에 대한 통계
    """
    await ctx.info("코드베이스 인덱싱 시작...")

    try:
        # 데이터베이스 테이블이 존재하는지 확인
        db_service._ensure_table()

        # 진행률 보고
        await ctx.report_progress(0.1, "프로젝트 디렉토리 스캔 중...")

        # 인덱싱 수행
        result = await indexing_service.index_projects()

        # 완료 보고
        await ctx.report_progress(
            1.0,
            f"{result.new_files}개 신규, {result.updated_files}개 업데이트 파일 인덱싱 완료"
        )

        # 요약 로그
        await ctx.info(
            f"인덱싱 완료: {result.total_files}개 파일에서 {result.total_chunks}개 청크 생성"
        )

        # 포맷된 결과 반환
        return json.dumps({
            "total_files": result.total_files,
            "new_files": result.new_files,
            "updated_files": result.updated_files,
            "deleted_files": result.deleted_files,
            "total_chunks": result.total_chunks,
            "elapsed_time": round(result.elapsed_time, 2),
            "errors": result.errors
        }, indent=2)

    except Exception as e:
        error_msg = f"인덱싱 중 오류 발생: {str(e)}"
        await ctx.error(error_msg)
        return json.dumps({
            "error": error_msg
        }, indent=2)


@mcp.tool(
    name="search_legacy_code",
    annotations={
        "title": "Search Legacy Code",
        "readOnlyHint": True,
        "destructiveHint": False,
        "idempotentHint": True,
        "openWorldHint": False
    }
)
async def search_legacy_code(
    query: str,
    limit: int = 5,
    project_filter: Optional[str] = None,
    ctx: Optional[Context] = None
) -> str:
    """시맨틱 유사도를 사용하여 코드 스니펫을 검색합니다.

    이 도구는 OpenAI 임베딩을 사용하여 모든 인덱싱된 코드 프로젝트에서
    의미론적으로 유사한 코드 스니펫을 찾습니다. 가장 관련성 높은 결과를
    컨텍스트와 함께 반환합니다.

    Args:
        query (str): 검색할 자연어 질문 또는 코드 관련 키워드
            예시:
            - "java excel 파일 파싱 유틸리티 클래스"
            - "Vue 사용자 인증 컴포넌트"
            - "TypeScript 이메일 검증 함수"
        limit (int): 반환할 최대 결과 수 (기본값: 5, 범위: 1-20)
        project_filter (Optional[str]): 특정 프로젝트 경로로 결과 필터링
            예시: "/Users/me/old-java-project"
        ctx: 로깅을 위한 FastMCP 컨텍스트

    Returns:
        str: 다음을 포함하는 Markdown 형식 문자열:
        - 코드 스니펫 내용
        - 파일 경로
        - 프로젝트 경로
        - 프로그래밍 언어
        - 유사도 점수

    Example:
        사용 시기: "Java 프로젝트에서 Excel 파일 파싱 코드 찾아줘"
        query="java excel 파싱"
        반환값: 관련 코드 스니펫의 Markdown 형식 목록

    Error Handling:
        - 검색 결과가 없으면 "결과 없음" 반환
        - 먼저 인덱싱이 필요한 경우 오류 메시지 반환
    """
    if ctx:
        await ctx.info(f"검색 중: {query}")

    try:
        # 데이터베이스 테이블이 존재하는지 확인
        db_service._ensure_table()

        # limit 값 검증
        limit = max(1, min(20, limit))

        # 쿼리 임베딩 생성
        query_embedding = await embedding_service.generate_embedding(query)

        # 데이터베이스 검색
        results = await db_service.search_similar(
            query_vector=query_embedding,
            limit=limit,
            project_filter=project_filter
        )

        if not results:
            return "검색 결과가 없습니다. 먼저 `index_codebase` 도구를 사용하여 코드베이스를 인덱싱하세요."

        # Markdown 형식으로 결과 포맷팅
        output_lines = [f"# '{query}' 검색 결과", ""]
        output_lines.append(f"{len(results)}개의 관련 코드 스니펫을 찾았습니다:")
        output_lines.append("")

        for i, result in enumerate(results, 1):
            output_lines.append(f"## 결과 {i} - {result.language.upper()}")
            output_lines.append(f"**파일:** `{result.filePath}`")
            output_lines.append(f"**프로젝트:** `{result.projectPath}`")
            output_lines.append(f"**유사도 점수:** {result.score:.4f}")
            output_lines.append("")
            output_lines.append("```" + result.language)
            output_lines.append(result.content)
            output_lines.append("```")
            output_lines.append("")
            output_lines.append("---")
            output_lines.append("")

        return "\n".join(output_lines)

    except Exception as e:
        error_msg = f"검색 중 오류 발생: {str(e)}"
        if ctx:
            await ctx.error(error_msg)
        return f"오류: {error_msg}"


def main():
    """패키지 진입점"""
    mcp.run()


# 서버 실행
if __name__ == "__main__":
    main()
