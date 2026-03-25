"""
向量存储服务模块

基于 Qdrant 向量数据库提供：
- 集合管理（创建、删除）
- 文档写入（add_documents）
- 向量检索（search）

用于 RAG 系统的文档存储和相似度检索。
"""

import os
import uuid
from typing import List
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.services.embedding import embedding_service


class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST", "localhost"),
            port=int(os.getenv("QDRANT_PORT", "6333"))
        )
        self.collection_name = "it_support_docs"

    def create_collection(self, vector_size: int = 1024):
        self.client.recreate_collection(
            collection_name=self.collection_name,
            vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
        )

    async def add_documents(self, documents: List[dict], start_id: int = None):
        points = []
        for i, doc in enumerate(documents):
            embedding = await embedding_service.get_embedding(doc["content"])
            doc_id = (start_id + i) if start_id is not None else i
            points.append(
                PointStruct(
                    id=doc_id,
                    vector=embedding,
                    payload={
                        "content": doc["content"],
                        "source": doc.get("source", ""),
                        "title": doc.get("title", "")
                    }
                )
            )
        if points:
            self.client.upsert(
                collection_name=self.collection_name,
                points=points
            )

    async def search(self, query: str, top_k: int = 5) -> List[dict]:
        query_embedding = await embedding_service.get_embedding(query)

        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k
        )

        return [
            {
                "content": hit.payload.get("content", ""),
                "source": hit.payload.get("source", ""),
                "score": hit.score
            }
            for hit in results.points
        ]


vector_store = VectorStore()
