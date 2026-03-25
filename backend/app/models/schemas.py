"""
Pydantic 数据模型定义

用于 API 请求和响应的数据验证和序列化：
- 请求模型：接收客户端数据
- 响应模型：返回给客户端数据
- 配置模型：用于配置和数据传输
"""

from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class UserBase(BaseModel):
    """用户基础模型"""
    name: str
    email: str
    role: str = "user"


class UserCreate(UserBase):
    """用户创建请求模型"""
    pass


class UserResponse(UserBase):
    """用户响应模型"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MessageBase(BaseModel):
    """消息基础模型"""
    role: str
    content: str


class MessageCreate(MessageBase):
    """消息创建请求模型"""
    conversation_id: Optional[int] = None


class MessageResponse(MessageBase):
    """消息响应模型"""
    id: int
    conversation_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ConversationBase(BaseModel):
    """会话基础模型"""
    user_id: int


class ConversationCreate(ConversationBase):
    """会话创建请求模型"""
    pass


class ConversationResponse(ConversationBase):
    """会话响应模型"""
    id: int
    status: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageResponse] = []

    class Config:
        from_attributes = True


class TicketBase(BaseModel):
    """工单基础模型"""
    title: str
    category: str
    priority: str
    description: str
    device_type: Optional[str] = None
    os: Optional[str] = None
    error_message: Optional[str] = None
    urgency: Optional[str] = None


class TicketCreate(TicketBase):
    """工单创建请求模型"""
    pass


class TicketResponse(TicketBase):
    """工单响应模型"""
    id: int
    jira_id: Optional[str]
    status: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class DocumentBase(BaseModel):
    """文档基础模型"""
    title: str
    content: str
    source_type: str = "manual"
    source_url: Optional[str] = None
    access_level: str = "internal"


class DocumentCreate(DocumentBase):
    """文档创建请求模型"""
    pass


class DocumentResponse(DocumentBase):
    """文档响应模型"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    """
    聊天请求模型

    Attributes:
        message: 用户输入的消息内容
        conversation_id: 会话 ID（可选，用于多轮对话）
        user_id: 用户 ID（可选）
    """
    message: str
    conversation_id: Optional[int] = None
    user_id: Optional[int] = None


class ChatResponse(BaseModel):
    """
    聊天响应模型

    Attributes:
        response: Agent 生成的回答
        conversation_id: 会话 ID
        intent: 识别出的用户意图
        references: 知识库引用的文档列表
    """
    response: str
    conversation_id: int
    intent: Optional[str] = None
    references: List[str] = []


class FeedbackCreate(BaseModel):
    """反馈创建请求模型"""
    conversation_id: int
    solved: bool
    rating: int


class FeedbackResponse(FeedbackCreate):
    """反馈响应模型"""
    id: int
    created_at: datetime

    class Config:
        from_attributes = True
