"""
文档处理服务模块

提供文档预处理功能：
- 文本分块（chunk_text）：将长文档分割成小块
- 文档处理（process_document）：将文档转换为可索引的块列表

用于在将文档添加到向量数据库前进行预处理，
确保每个块的长度适合嵌入模型。
"""

from typing import List


class DocumentProcessor:
    """
    文档处理器类

    负责将长文档分割成适合嵌入的小块。
    使用滑动窗口策略，相邻块之间有一定重叠以保持上下文连贯性。
    """

    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        """
        初始化文档处理器

        Args:
            chunk_size: 每个文本块的字符数，默认 500
            chunk_overlap: 相邻块之间的重叠字符数，默认 50
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

    def chunk_text(self, text: str) -> List[str]:
        """
        将长文本分割成小块

        使用滑动窗口策略：
        1. 从文本开头开始，每次取 chunk_size 个字符
        2. 下一次从 (end - overlap) 位置开始
        3. 重复直到处理完整个文本

        Args:
            text: 输入文本

        Returns:
            文本块列表
        """
        chunks = []
        start = 0
        # 滑动窗口遍历文本
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            # 移动起始位置（考虑重叠）
            start = end - self.chunk_overlap
        return chunks

    def process_document(self, title: str, content: str, source: str = "") -> List[dict]:
        """
        处理整个文档

        将文档标题、内容和来源转换为块列表，
        每个块包含独立可索引的信息。

        Args:
            title: 文档标题
            content: 文档正文内容
            source: 文档来源标识（如 URL、文件路径等）

        Returns:
            文档块列表，每项包含：
                - title: 文档标题
                - content: 文本块内容
                - source: 来源标识
        """
        # 将正文分割成块
        chunks = self.chunk_text(content)
        # 为每个块构建元数据
        documents = [
            {
                "title": title,
                "content": chunk,
                "source": source
            }
            for chunk in chunks
        ]
        return documents


# 全局单例实例
document_processor = DocumentProcessor()
