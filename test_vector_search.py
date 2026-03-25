import os
import asyncio

os.environ['QWEN_API_KEY'] = 'sk-1f5cf64ec535477685d2ba4bf2cd26cd'
os.environ['QWEN_API_BASE_URL'] = 'https://dashscope.aliyuncs.com/compatible-mode/v1'
os.environ['QDRANT_HOST'] = 'qdrant'
os.environ['QDRANT_PORT'] = '6333'

from app.services.vector_store import vector_store

async def test():
    print("=" * 50)
    print("向量数据库检索测试")
    print("=" * 50)

    query = "VPN连接问题"
    print(f"\n查询: {query}")

    docs = await vector_store.search(query, top_k=3)

    print(f"\n找到 {len(docs)} 个相关文档:\n")

    for i, doc in enumerate(docs, 1):
        print(f"[{i}] 来源: {doc['source']}")
        print(f"    相似度: {doc['score']:.3f}")
        content = doc['content'][:150].replace('\n', ' ')
        print(f"    内容: {content}...")
        print()

asyncio.run(test())
