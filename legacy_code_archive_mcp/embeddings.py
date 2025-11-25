"""코드 청크에 대한 OpenAI 임베딩 생성"""

from typing import List
import httpx
from openai import AsyncOpenAI
from legacy_code_archive_mcp.config import Config


class EmbeddingService:
    """OpenAI API를 사용하여 임베딩을 생성하는 서비스"""

    def __init__(self, config: Config):
        """임베딩 서비스를 초기화합니다.

        Args:
            config: API 키와 모델 이름을 포함하는 구성 객체
        """
        self.config = config
        self.client = AsyncOpenAI(
            api_key=config.openai_api_key,
            http_client=httpx.AsyncClient()
        )
        self.model = config.embedding_model
        self.batch_size = config.embedding_batch_size

    async def generate_embedding(self, text: str) -> List[float]:
        """단일 텍스트에 대한 임베딩을 생성합니다.

        Args:
            text: 임베딩할 텍스트

        Returns:
            임베딩 벡터를 나타내는 float 리스트 (1536차원)
        """
        response = await self.client.embeddings.create(
            model=self.model,
            input=text
        )
        return response.data[0].embedding

    async def generate_embeddings_batch(self, texts: List[str]) -> List[List[float]]:
        """배치 텍스트에 대한 임베딩을 생성합니다.

        Args:
            texts: 임베딩할 텍스트 리스트

        Returns:
            임베딩 벡터 리스트
        """
        if not texts:
            return []

        # 속도 제한을 피하기 위해 배치로 처리
        all_embeddings = []

        for i in range(0, len(texts), self.batch_size):
            batch = texts[i:i + self.batch_size]
            response = await self.client.embeddings.create(
                model=self.model,
                input=batch
            )
            batch_embeddings = [item.embedding for item in response.data]
            all_embeddings.extend(batch_embeddings)

        return all_embeddings

    async def close(self):
        """HTTP 클라이언트를 종료합니다."""
        await self.client.close()
