import sys
sys.path.insert(0, '/app')

from qdrant_client import QdrantClient

client = QdrantClient(host="qdrant", port=6333)

# 获取集合信息
collection = client.get_collection("it_support_docs")
print(f"集合名称: it_support_docs")
print(f"向量数量: {collection.points_count}")

# 检索所有文档
results = client.query_points(
    collection_name="it_support_docs",
    query=[0.0] * 1536,  # 全零向量作为查询
    limit=100
)

print(f"\n文档列表:")
for i, hit in enumerate(results.points):
    print(f"\n--- 文档 {i+1} ---")
    print(f"来源: {hit.payload.get('source', 'N/A')}")
    print(f"内容预览: {hit.payload.get('content', '')[:300]}...")