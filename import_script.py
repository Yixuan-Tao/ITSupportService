import os
import sys
from pathlib import Path

sys.path.insert(0, '/app')

os.environ['QWEN_API_KEY'] = os.environ.get('QWEN_API_KEY', '')
os.environ['QWEN_API_BASE_URL'] = os.environ.get('QWEN_API_BASE_URL', 'https://dashscope.aliyuncs.com/compatible-mode/v1')
os.environ['QDRANT_HOST'] = 'qdrant'
os.environ['QDRANT_PORT'] = '6333'

from app.services.vector_store import vector_store
from app.services.document_processor import document_processor

def load_docs():
    docs = []
    kb = Path('/app/it_support_data')
    for f in kb.rglob('*.md'):
        if f.name == 'file_index.json':
            continue
        docs.append({
            'title': f.stem,
            'content': f.read_text(encoding='utf-8'),
            'source': str(f)
        })
    return docs

def main():
    print('=' * 50)
    print('知识库向量数据库导入')
    print('=' * 50)

    print('\n1. 加载文档...')
    docs = load_docs()
    print(f'   找到 {len(docs)} 个文档')

    print('\n2. 创建向量集合...')
    try:
        vector_store.create_collection(1024)
        print('   ✓ 集合创建成功')
    except Exception as e:
        print(f'   ! 集合可能已存在: {e}')

    print('\n3. 处理文档...')
    all_chunks = []
    for d in docs:
        chunks = document_processor.process_document(d['title'], d['content'], d['source'])
        all_chunks.extend(chunks)
        print(f'   {d["title"]}: {len(chunks)} 个块')
    print(f'   共 {len(all_chunks)} 个文本块')

    print('\n4. 导入向量数据库...')
    import asyncio

    async def import_chunks():
        total = len(all_chunks)
        for i in range(0, total, 10):
            batch = all_chunks[i:i+10]
            await vector_store.add_documents(batch)
            progress = min(i + 10, total)
            print(f'   进度: {progress}/{total} ({progress*100//total}%)')

    asyncio.run(import_chunks())

    print('\n' + '=' * 50)
    print('✓ 导入完成!')
    print('=' * 50)

if __name__ == '__main__':
    main()
