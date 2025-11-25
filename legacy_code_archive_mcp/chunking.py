"""LangChain을 사용한 텍스트 청킹 유틸리티"""

from pathlib import Path
from typing import List
from langchain_text_splitters import RecursiveCharacterTextSplitter, Language
from legacy_code_archive_mcp.config import Config


class ChunkingService:
    """코드 파일을 청크로 분할하는 서비스"""

    def __init__(self, config: Config):
        """청킹 서비스를 초기화합니다.

        Args:
            config: 청크 크기와 중복을 포함하는 구성 객체
        """
        self.config = config
        self.chunk_size = config.chunk_size
        self.chunk_overlap = config.chunk_overlap

        # 각 언어별 분할기 생성
        self.splitters = {
            "java": RecursiveCharacterTextSplitter.from_language(
                language=Language.JAVA,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            ),
            "js": RecursiveCharacterTextSplitter.from_language(
                language=Language.JS,
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            ),
            "ts": RecursiveCharacterTextSplitter.from_language(
                language=Language.JS,  # TypeScript는 JS 분할기 사용
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            ),
            "vue": RecursiveCharacterTextSplitter.from_language(
                language=Language.JS,  # Vue SFC는 JS 분할기 사용
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            ),
            "default": RecursiveCharacterTextSplitter(
                chunk_size=self.chunk_size,
                chunk_overlap=self.chunk_overlap
            )
        }

    def detect_language(self, file_path: str) -> str:
        """파일 확장자에서 프로그래밍 언어를 감지합니다.

        Args:
            file_path: 파일 경로

        Returns:
            언어 식별자 (java, js, ts, vue 또는 default)
        """
        ext = Path(file_path).suffix.lower()

        language_map = {
            ".java": "java",
            ".js": "js",
            ".jsx": "js",
            ".ts": "ts",
            ".tsx": "ts",
            ".vue": "vue"
        }

        return language_map.get(ext, "default")

    def split_text(self, text: str, language: str = "default") -> List[str]:
        """언어에 따라 텍스트를 청크로 분할합니다.

        Args:
            text: 분할할 텍스트 내용
            language: 프로그래밍 언어 식별자

        Returns:
            텍스트 청크 리스트
        """
        splitter = self.splitters.get(language, self.splitters["default"])
        chunks = splitter.split_text(text)
        return chunks

    def split_file(self, file_path: str, content: str) -> List[str]:
        """파일 내용을 청크로 분할합니다.

        Args:
            file_path: 파일 경로 (언어 감지용)
            content: 파일 내용

        Returns:
            텍스트 청크 리스트
        """
        language = self.detect_language(file_path)
        return self.split_text(content, language)
