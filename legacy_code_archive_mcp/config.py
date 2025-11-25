"""레거시 코드 아카이브 MCP 서버의 구성 관리

서버 운영에 필요한 환경 변수를 로드하고 검증합니다.
"""

import os
from typing import List
from pydantic import BaseModel, Field, field_validator


class Config(BaseModel):
    """환경 변수에서 로드된 서버 구성"""

    project_paths: List[str] = Field(
        default_factory=list,
        description="인덱싱할 프로젝트 루트 경로 목록"
    )
    included_extensions: List[str] = Field(
        default_factory=lambda: [".ts", ".js", ".vue", ".java"],
        description="인덱싱에 포함할 파일 확장자"
    )
    exclude_patterns: List[str] = Field(
        default_factory=lambda: ["node_modules", "dist", ".git", "__pycache__", "build", "target"],
        description="인덱싱에서 제외할 패턴"
    )
    openai_api_key: str = Field(
        ...,
        description="임베딩을 위한 OpenAI API 키"
    )
    lancedb_path: str = Field(
        default="./lancedb_data",
        description="LanceDB 저장 디렉토리 경로"
    )
    chunk_size: int = Field(
        default=1000,
        description="최대 청크 크기(문자 수)"
    )
    chunk_overlap: int = Field(
        default=200,
        description="청크 간 중복 문자 수"
    )
    embedding_model: str = Field(
        default="text-embedding-3-small",
        description="사용할 OpenAI 임베딩 모델"
    )
    embedding_batch_size: int = Field(
        default=100,
        description="단일 배치에서 임베딩할 청크 수"
    )

    @field_validator('project_paths', mode='before')
    @classmethod
    def parse_project_paths(cls, v):
        """환경 변수에서 쉼표로 구분된 프로젝트 경로를 파싱합니다."""
        if isinstance(v, str):
            if not v.strip():
                return []
            return [p.strip() for p in v.split(",") if p.strip()]
        return v

    @field_validator('included_extensions', mode='before')
    @classmethod
    def parse_extensions(cls, v):
        """쉼표로 구분된 파일 확장자를 파싱합니다."""
        if isinstance(v, str):
            return [ext.strip() for ext in v.split(",") if ext.strip()]
        return v

    @field_validator('exclude_patterns', mode='before')
    @classmethod
    def parse_exclude_patterns(cls, v):
        """쉼표로 구분된 제외 패턴을 파싱합니다."""
        if isinstance(v, str):
            return [p.strip() for p in v.split(",") if p.strip()]
        return v


def load_config() -> Config:
    """환경 변수에서 구성을 로드합니다.

    Returns:
        Config: 검증된 구성 객체

    Raises:
        ValueError: 필수 환경 변수가 누락된 경우
    """
    project_paths = os.environ.get("PROJECT_PATHS", "")
    included_extensions = os.environ.get("INCLUDED_EXTENSIONS", ".ts,.js,.vue,.java")
    exclude_patterns = os.environ.get("EXCLUDE_PATTERNS", "node_modules,dist,.git,__pycache__")
    openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    lancedb_path = os.environ.get("LANCEDB_PATH", "./lancedb_data")

    if not openai_api_key:
        raise ValueError("OPENAI_API_KEY environment variable is required")

    if not project_paths:
        raise ValueError("PROJECT_PATHS environment variable is required")

    return Config(
        project_paths=project_paths,
        included_extensions=included_extensions,
        exclude_patterns=exclude_patterns,
        openai_api_key=openai_api_key,
        lancedb_path=lancedb_path
    )
