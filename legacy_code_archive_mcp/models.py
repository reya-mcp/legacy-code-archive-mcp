"""레거시 코드 아카이브 MCP 서버의 데이터 모델"""

from typing import List, Optional
from pydantic import BaseModel, Field


class CodeSnippet(BaseModel):
    """LanceDB에 저장되는 코드 스니펫 스키마"""

    id: str = Field(..., description="고유 식별자 (UUID)")
    vector: List[float] = Field(..., description="OpenAI 임베딩 벡터 (1536차원)")
    content: str = Field(..., description="코드 내용 (청크)")
    filePath: str = Field(..., description="절대 파일 경로")
    projectId: str = Field(..., description="프로젝트 경로의 MD5 해시")
    projectPath: str = Field(..., description="프로젝트 루트 절대 경로")
    language: str = Field(..., description="프로그래밍 언어 (java, ts, vue 등)")
    lastModified: float = Field(..., description="파일 수정 시간 (Unix 타임스탬프)")


class IndexingResult(BaseModel):
    """인덱싱 작업 결과"""

    total_files: int = Field(..., description="처리된 전체 파일 수")
    new_files: int = Field(..., description="새로 인덱싱된 파일 수")
    updated_files: int = Field(..., description="재인덱싱된 업데이트 파일 수")
    deleted_files: int = Field(..., description="인덱스에서 제거된 삭제 파일 수")
    total_chunks: int = Field(..., description="생성된 전체 청크 수")
    elapsed_time: float = Field(..., description="소요 시간(초)")
    errors: List[str] = Field(default_factory=list, description="발생한 오류 목록")


class SearchResult(BaseModel):
    """단일 검색 결과"""

    content: str = Field(..., description="코드 스니펫 내용")
    filePath: str = Field(..., description="파일 경로")
    projectPath: str = Field(..., description="프로젝트 경로")
    language: str = Field(..., description="프로그래밍 언어")
    score: float = Field(..., description="유사도 점수")
