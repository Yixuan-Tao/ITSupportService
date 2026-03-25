"""
知识库向量数据库导入脚本

将 source/it_support_data 中的文档导入到 Qdrant 向量数据库
"""

import os
import sys
from pathlib import Path

backend_path = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_path))

os.environ["ANTHROPIC_API_KEY"] = os.environ.get("ANTHROPIC_API_KEY", "")
os.environ["ANTHROPIC_BASE_URL"] = os.environ.get("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic")
os.environ["QDRANT_HOST"] = os.environ.get("QDRANT_HOST", "localhost")
os.environ["QDRANT_PORT"] = os.environ.get("QDRANT_PORT", "6333")

from app.services.embedding import embedding_service
from app.services.vector_store import vector_store
from app.services.document_processor import document_processor


def load_documents(data_dir: Path):
    documents = []
    kb_dir = data_dir / "it_support_data"

    if not kb_dir.exists():
        print(f"目录不存在: {kb_dir}")
        return documents

    for md_file in kb_dir.rglob("*.md"):
        if md_file.name == "file_index.json":
            continue

        try:
            content = md_file.read_text(encoding="utf-8")
            title = md_file.stem
            source = str(md_file.relative_to(kb_dir.parent))

            documents.append({
                "title": title,
                "content": content,
                "source": source
            })
            print(f"加载: {md_file.name}")
        except Exception as e:
            print(f"读取失败 {md_file.name}: {e}")

    return documents


async def main():
    print("=" * 50)
    print("知识库向量数据库导入")
    print("=" * 50)

    print("\n1. 检查 Qdrant 连接...")
    try:
        test_results = vector_store.client.search(
            collection_name=vector_store.collection_name,
            query_vector=[0.0] * 1024,
            limit=1
        )
        print("   ✓ Qdrant 连接正常")
    except Exception as e:
        print(f"   ✗ Qdrant 连接失败: {e}")
        print("\n请确保 Qdrant 服务正在运行")
        return

    print("\n2. 创建向量集合...")
    try:
        vector_store.create_collection(vector_size=1024)
        print("   ✓ 集合创建成功")
    except Exception as e:
        print(f"   ! 集合可能已存在: {e}")

    print("\n3. 加载文档...")
    script_dir = Path(__file__).parent.parent
    data_dir = script_dir / "source"
    documents = load_documents(data_dir)
    print(f"   共加载 {len(documents)} 个文档")

    if not documents:
        print("   ✗ 没有找到文档")
        return

    print("\n4. 处理文档并生成向量...")
    all_chunks = []
    for doc in documents:
        chunks = document_processor.process_document(
            title=doc["title"],
            content=doc["content"],
            source=doc["source"]
        )
        all_chunks.extend(chunks)
        print(f"   {doc['title']}: {len(chunks)} 个块")

    print(f"   共 {len(all_chunks)} 个文本块")

    print("\n5. 导入向量数据库 (这可能需要几分钟)...")
    batch_size = 10
    total = len(all_chunks)

    for i in range(0, total, batch_size):
        batch = all_chunks[i:i+batch_size]
        await vector_store.add_documents(batch)
        progress = min(i + batch_size, total)
        print(f"   进度: {progress}/{total} ({progress*100//total}%)")

    print("\n" + "=" * 50)
    print("✓ 导入完成!")
    print("=" * 50)


if __name__ == "__main__":
    import asyncio
    asyncio.run(main())
