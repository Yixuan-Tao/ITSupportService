"""
Embedding 服务模块

提供文本向量嵌入功能：
- 单文本嵌入：get_embedding()
- 批量文本嵌入：get_embeddings()

使用 Qwen Embedding API 生成向量。
向量用于后续的相似度检索（RAG）。
"""

import os
from typing import List
import httpx


class EmbeddingService:
    """
    文本嵌入服务类

    使用 Qwen API 将文本转换为高维向量。
    这些向量可以用于文本相似度计算和向量检索。
    """

    def __init__(self):
        # Qwen API 配置
        self.base_url = os.getenv("QWEN_API_BASE_URL", "https://dashscope.aliyuncs.com/compatible-mode/v1")
        self.api_key = os.getenv("QWEN_API_KEY", "")
        # 使用的嵌入模型
        self.model = os.getenv("QWEN_EMBEDDING_MODEL", "text-embedding-v3")
        # 向量维度（text-embedding-v3 输出 1024 维）
        self.dimension = 1024

    async def get_embedding(self, text: str) -> List[float]:
        """
        将单个文本转换为向量

        Args:
            text: 输入文本

        Returns:
            1536 维浮点数向量列表

        Raises:
            httpx.HTTPStatusError: API 调用失败时抛出
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/embeddings",
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "input": text,
                    "model": self.model
                },
                timeout=30.0
            )
            # 检查 HTTP 状态码
            response.raise_for_status()
            # 解析响应 JSON
            data = response.json()
            # 返回嵌入向量
            return data["data"][0]["embedding"]

    async def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        将多个文本批量转换为向量

        Args:
            texts: 文本列表

        Returns:
            多个向量组成的列表
        """
        embeddings = []
        for text in texts:
            embedding = await self.get_embedding(text)
            embeddings.append(embedding)
        return embeddings


# 全局单例实例，供其他模块导入使用
embedding_service = EmbeddingService()
