"""
数据库模型定义模块

定义所有 SQLAlchemy ORM 模型类，对应 PostgreSQL 数据库中的表：
- User: 用户信息
- Conversation: 对话会话
- Message: 消息记录
- Document: 知识库文档
- Ticket: 工单
- AgentRun: Agent 运行记录
- Feedback: 用户反馈
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, ForeignKey, Boolean
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime
import os

# 数据库连接 URL，从环境变量读取，默认为本地 PostgreSQL
DATABASE_URL = os.getenv("DATABASE_URL", "postgresql://postgres:postgres@localhost:5432/it_support")

# 创建数据库引擎
engine = create_engine(DATABASE_URL)

# 创建会话工厂，用于获取数据库连接
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 创建声明性基类，所有模型类都继承此类
Base = declarative_base()


class User(Base):
    """用户模型"""
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100))                       # 用户姓名
    email = Column(String(255), unique=True, index=True)  # 邮箱，唯一索引
    role = Column(String(50))                       # 角色（admin/user/it_support）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间


class Conversation(Base):
    """对话会话模型"""
    __tablename__ = "conversations"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))  # 关联用户 ID
    status = Column(String(50), default="active")      # 会话状态（active/closed）
    created_at = Column(DateTime, default=datetime.utcnow)   # 创建时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间

    # 与 Message 的反向关系，一个会话包含多条消息
    messages = relationship("Message", back_populates="conversation")
    # 与 User 的关系
    user = relationship("User")


class Message(Base):
    """消息记录模型"""
    __tablename__ = "messages"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))  # 所属会话 ID
    role = Column(String(20))      # 角色（user/assistant）
    content = Column(Text)         # 消息内容
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间

    # 与 Conversation 的反向关系
    conversation = relationship("Conversation", back_populates="messages")


class Document(Base):
    """知识库文档模型"""
    __tablename__ = "documents"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255))         # 文档标题
    content = Column(Text)               # 文档内容
    source_type = Column(String(50))     # 来源类型（manual/wiki/api）
    source_url = Column(String(500))     # 原文链接
    access_level = Column(String(50))    # 访问级别（internal/public/restricted）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间


class Ticket(Base):
    """工单模型"""
    __tablename__ = "tickets"

    id = Column(Integer, primary_key=True, index=True)
    jira_id = Column(String(100))        # Jira 工单 ID（如 IT-123）
    title = Column(String(255))          # 工单标题
    category = Column(String(100))       # 分类（网络/软件/硬件/权限）
    priority = Column(String(20))        # 优先级（low/medium/high/critical）
    status = Column(String(50), default="open")  # 状态（open/in_progress/resolved/closed）
    description = Column(Text)            # 工单描述
    device_type = Column(String(100))    # 设备类型（笔记本/台式机/打印机）
    os = Column(String(100))             # 操作系统（Windows/Mac/Linux）
    error_message = Column(Text)         # 错误信息
    urgency = Column(String(20))         # 紧急程度
    created_at = Column(DateTime, default=datetime.utcnow)   # 创建时间
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)  # 更新时间


class AgentRun(Base):
    """Agent 运行记录模型"""
    __tablename__ = "agent_runs"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))  # 关联会话 ID
    route = Column(String(50))          # 路由类型（faq/incident/service_request）
    tools_used = Column(Text)           # 使用的工具列表（JSON 格式）
    latency = Column(Integer)            # 响应延迟（毫秒）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间


class Feedback(Base):
    """用户反馈模型"""
    __tablename__ = "feedback"

    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))  # 关联会话 ID
    solved = Column(Boolean, default=False)  # 问题是否已解决
    rating = Column(Integer)                # 评分（1-5）
    created_at = Column(DateTime, default=datetime.utcnow)  # 创建时间


def init_db():
    """
    初始化数据库

    创建所有表结构（如果表不存在）
    在应用启动时调用
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    获取数据库会话的依赖函数

    用法：在 FastAPI 路由参数中使用 Depends(get_db)
    确保请求结束后正确关闭数据库连接
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
