"""벡터 저장 및 검색을 위한 LanceDB 데이터베이스 작업"""

import hashlib
from pathlib import Path
from typing import List, Optional, Dict, Any
import lancedb
from lancedb.table import Table
from legacy_code_archive_mcp.config import Config
from legacy_code_archive_mcp.models import CodeSnippet, SearchResult


class DatabaseService:
    """LanceDB 벡터 데이터베이스 작업을 관리하는 서비스"""

    TABLE_NAME = "code_snippets"

    def __init__(self, config: Config):
        """데이터베이스 서비스를 초기화합니다.

        Args:
            config: 데이터베이스 경로를 포함하는 구성 객체
        """
        self.config = config
        self.db_path = config.lancedb_path
        self.db = lancedb.connect(self.db_path)
        self._table: Optional[Table] = None

    def _ensure_table(self):
        """테이블이 존재하는지 확인하고, 없으면 생성합니다."""
        try:
            self._table = self.db.open_table(self.TABLE_NAME)
        except Exception:
            # 테이블이 존재하지 않으면 첫 삽입 시 생성됨
            self._table = None

    @staticmethod
    def compute_project_id(project_path: str) -> str:
        """고유 식별을 위해 프로젝트 경로의 MD5 해시를 계산합니다.

        Args:
            project_path: 프로젝트 루트의 절대 경로

        Returns:
            MD5 해시 문자열
        """
        return hashlib.md5(project_path.encode()).hexdigest()

    async def upsert_chunks(self, chunks_data: List[Dict[str, Any]]):
        """데이터베이스에 코드 청크를 삽입하거나 업데이트합니다.

        Args:
            chunks_data: 모든 필수 필드를 포함하는 청크 딕셔너리 리스트
        """
        if not chunks_data:
            return

        if self._table is None:
            # 첫 번째 데이터 배치로 테이블 생성
            self._table = self.db.create_table(
                self.TABLE_NAME,
                data=chunks_data,
                mode="overwrite"
            )
        else:
            # 기존 테이블에 추가
            self._table.add(chunks_data)

    async def delete_by_file_path(self, file_path: str):
        """특정 파일과 연관된 모든 청크를 삭제합니다.

        Args:
            file_path: 파일의 절대 경로
        """
        if self._table is None:
            return

        self._table.delete(f'filePath = "{file_path}"')

    async def get_file_metadata(self, file_path: str) -> Optional[Dict[str, Any]]:
        """특정 파일의 메타데이터를 가져옵니다.

        Args:
            file_path: 파일의 절대 경로

        Returns:
            파일 메타데이터 딕셔너리 또는 찾을 수 없는 경우 None
        """
        if self._table is None:
            return None

        results = (
            self._table
            .search()
            .where(f'filePath = "{file_path}"')
            .limit(1)
            .to_list()
        )

        if results:
            return results[0]
        return None

    async def search_similar(
        self,
        query_vector: List[float],
        limit: int = 5,
        project_filter: Optional[str] = None
    ) -> List[SearchResult]:
        """벡터 유사도를 사용하여 유사한 코드 청크를 검색합니다.

        Args:
            query_vector: 검색할 임베딩 벡터
            limit: 반환할 최대 결과 수
            project_filter: 결과를 필터링할 프로젝트 경로 (선택 사항)

        Returns:
            SearchResult 객체 리스트
        """
        if self._table is None:
            return []

        # 검색 쿼리 구성
        search = self._table.search(query_vector).limit(limit)

        # 프로젝트 필터가 지정된 경우 적용
        if project_filter:
            project_id = self.compute_project_id(project_filter)
            search = search.where(f'projectId = "{project_id}"')

        # 검색 실행
        results = search.to_list()

        # SearchResult 객체로 변환
        search_results = []
        for result in results:
            search_results.append(SearchResult(
                content=result.get("content", ""),
                filePath=result.get("filePath", ""),
                projectPath=result.get("projectPath", ""),
                language=result.get("language", ""),
                score=result.get("_distance", 0.0)  # LanceDB returns _distance
            ))

        return search_results

    async def get_all_indexed_files(self) -> List[Dict[str, Any]]:
        """인덱싱된 모든 파일의 메타데이터를 가져옵니다.

        Returns:
            파일 메타데이터 딕셔너리 리스트
        """
        if self._table is None:
            return []

        # 최신 수정 시간과 함께 모든 고유 파일 경로 가져오기
        results = self._table.to_pandas()

        if results.empty:
            return []

        # filePath별로 그룹화하고 첫 번째 항목 가져오기 (모두 동일한 메타데이터를 가져야 함)
        file_metadata = (
            results.groupby("filePath")
            .first()
            .reset_index()
            [["filePath", "projectPath", "projectId", "lastModified"]]
            .to_dict("records")
        )

        return file_metadata

    async def count_chunks(self) -> int:
        """데이터베이스의 전체 청크 수를 계산합니다.

        Returns:
            전체 청크 수
        """
        if self._table is None:
            return 0

        return self._table.count_rows()

    async def close(self):
        """데이터베이스 연결을 종료합니다."""
        # LanceDB 연결은 일반적으로 자동으로 관리됨
        pass
