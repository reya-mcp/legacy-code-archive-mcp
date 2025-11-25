"""코드 파일 스캔 및 처리를 위한 인덱싱 로직"""

import os
import uuid
import time
from pathlib import Path
from typing import List, Set, Dict, Any
from legacy_code_archive_mcp.config import Config
from legacy_code_archive_mcp.models import IndexingResult
from legacy_code_archive_mcp.database import DatabaseService
from legacy_code_archive_mcp.embeddings import EmbeddingService
from legacy_code_archive_mcp.chunking import ChunkingService


class IndexingService:
    """코드 파일을 인덱싱하는 서비스"""

    def __init__(
        self,
        config: Config,
        db_service: DatabaseService,
        embedding_service: EmbeddingService,
        chunking_service: ChunkingService
    ):
        """인덱싱 서비스를 초기화합니다.

        Args:
            config: 구성 객체
            db_service: 데이터베이스 서비스 인스턴스
            embedding_service: 임베딩 서비스 인스턴스
            chunking_service: 청킹 서비스 인스턴스
        """
        self.config = config
        self.db = db_service
        self.embeddings = embedding_service
        self.chunker = chunking_service

    def _should_exclude(self, path: Path) -> bool:
        """제외 패턴을 기반으로 경로를 제외해야 하는지 확인합니다.

        Args:
            path: 확인할 경로

        Returns:
            경로를 제외해야 하는 경우 True
        """
        path_str = str(path)
        for pattern in self.config.exclude_patterns:
            if pattern in path_str:
                return True
        return False

    def _scan_project(self, project_path: str) -> List[Path]:
        """코드 파일에 대해 프로젝트 디렉토리를 스캔합니다.

        Args:
            project_path: 프로젝트의 루트 경로

        Returns:
            인덱싱할 파일 경로 리스트
        """
        project_root = Path(project_path).resolve()

        if not project_root.exists():
            raise ValueError(f"Project path does not exist: {project_path}")

        files_to_index = []

        # 디렉토리 순회
        for ext in self.config.included_extensions:
            for file_path in project_root.rglob(f"*{ext}"):
                if file_path.is_file() and not self._should_exclude(file_path):
                    files_to_index.append(file_path)

        return files_to_index

    async def index_file(
        self,
        file_path: Path,
        project_path: str
    ) -> tuple[int, List[str]]:
        """단일 파일을 인덱싱합니다.

        Args:
            file_path: 파일 경로
            project_path: 프로젝트의 루트 경로

        Returns:
            (생성된 청크 수, 오류 리스트) 튜플
        """
        errors = []

        try:
            # 파일 내용 읽기
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()

            # 빈 파일 건너뛰기
            if not content.strip():
                return 0, errors

            # 파일 메타데이터 가져오기
            file_stat = file_path.stat()
            last_modified = file_stat.st_mtime

            # 청크로 분할
            chunks = self.chunker.split_file(str(file_path), content)

            if not chunks:
                return 0, errors

            # 모든 청크에 대한 임베딩 생성
            embeddings = await self.embeddings.generate_embeddings_batch(chunks)

            # 데이터베이스용 데이터 준비
            project_id = self.db.compute_project_id(project_path)
            language = self.chunker.detect_language(str(file_path))

            chunks_data = []
            for chunk, embedding in zip(chunks, embeddings):
                chunk_data = {
                    "id": str(uuid.uuid4()),
                    "vector": embedding,
                    "content": chunk,
                    "filePath": str(file_path),
                    "projectId": project_id,
                    "projectPath": project_path,
                    "language": language,
                    "lastModified": last_modified
                }
                chunks_data.append(chunk_data)

            # 데이터베이스에 저장
            await self.db.upsert_chunks(chunks_data)

            return len(chunks), errors

        except Exception as e:
            error_msg = f"Error indexing {file_path}: {str(e)}"
            errors.append(error_msg)
            return 0, errors

    async def index_projects(self) -> IndexingResult:
        """구성에 정의된 모든 프로젝트를 인덱싱합니다.

        증분 인덱싱 전략 구현:
        - lastModified 시간 비교
        - 변경된 파일 재인덱싱
        - 새 파일 추가
        - 삭제된 파일 제거

        Returns:
            통계가 포함된 IndexingResult
        """
        start_time = time.time()

        total_files = 0
        new_files = 0
        updated_files = 0
        deleted_files = 0
        total_chunks = 0
        all_errors = []

        # 현재 인덱싱된 파일 가져오기
        indexed_files_metadata = await self.db.get_all_indexed_files()
        indexed_files: Dict[str, float] = {
            item["filePath"]: item["lastModified"]
            for item in indexed_files_metadata
        }

        # 현재 스캔에서 발견된 파일 추적
        current_files: Set[str] = set()

        # 각 프로젝트 스캔 및 인덱싱
        for project_path in self.config.project_paths:
            try:
                # 파일 스캔
                files = self._scan_project(project_path)
                total_files += len(files)

                # 각 파일 처리
                for file_path in files:
                    file_path_str = str(file_path)
                    current_files.add(file_path_str)

                    # 현재 파일 수정 시간 가져오기
                    current_mtime = file_path.stat().st_mtime

                    # 파일 인덱싱 필요 여부 확인
                    if file_path_str in indexed_files:
                        indexed_mtime = indexed_files[file_path_str]

                        # 수정되지 않은 경우 건너뛰기
                        if abs(current_mtime - indexed_mtime) < 1:  # 1초 허용 오차
                            continue

                        # 파일이 수정됨 - 이전 청크 삭제 후 재인덱싱
                        await self.db.delete_by_file_path(file_path_str)
                        chunks_created, errors = await self.index_file(file_path, project_path)
                        updated_files += 1
                        total_chunks += chunks_created
                        all_errors.extend(errors)
                    else:
                        # 새 파일 - 인덱싱
                        chunks_created, errors = await self.index_file(file_path, project_path)
                        new_files += 1
                        total_chunks += chunks_created
                        all_errors.extend(errors)

            except Exception as e:
                error_msg = f"Error scanning project {project_path}: {str(e)}"
                all_errors.append(error_msg)

        # 삭제된 파일 찾기 및 제거
        deleted_file_paths = set(indexed_files.keys()) - current_files
        for deleted_path in deleted_file_paths:
            try:
                await self.db.delete_by_file_path(deleted_path)
                deleted_files += 1
            except Exception as e:
                error_msg = f"Error deleting {deleted_path}: {str(e)}"
                all_errors.append(error_msg)

        elapsed_time = time.time() - start_time

        return IndexingResult(
            total_files=total_files,
            new_files=new_files,
            updated_files=updated_files,
            deleted_files=deleted_files,
            total_chunks=total_chunks,
            elapsed_time=elapsed_time,
            errors=all_errors
        )
