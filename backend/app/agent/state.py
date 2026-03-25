"""
Agent 状态定义模块

定义 LangGraph Agent 工作流中使用的状态数据结构：
- TicketInfo: 工单信息数据结构
- AgentState: Agent 完整状态，包含所有工作流所需的信息
"""

from typing import TypedDict, List, Optional
from dataclasses import dataclass, field


@dataclass
class TicketInfo:
    """
    工单信息数据结构

    用于在 Agent 工作流中存储和传递工单相关的信息。
    这些信息在多轮对话中逐步收集和完善。
    """
    title: str = ""              # 工单标题
    category: str = ""           # 分类（网络/软件/硬件/权限）
    priority: str = ""          # 优先级（low/medium/high）
    description: str = ""        # 工单描述
    device_type: str = ""       # 设备类型（笔记本/台式机/打印机）
    os: str = ""                # 操作系统
    error_message: str = ""     # 错误信息
    urgency: str = ""           # 紧急程度


@dataclass
class AgentState(TypedDict):
    """
    Agent 工作流状态

    整个工作流中传递的状态对象，包含：
    - 消息历史
    - 意图识别结果
    - 检索到的文档
    - 工单信息
    - 各种标志位
    """
    messages: List[dict]                    # 对话消息历史 [{"role": "user/assistant", "content": "..."}]
    intent: Optional[str]                  # 识别出的用户意图（faq/incident/service_request/ticket_query/handoff）
    retrieved_docs: List[dict]              # 从知识库检索到的相关文档
    ticket_info: TicketInfo                # 工单信息（在多轮对话中逐步填充）
    needs_clarification: bool              # 是否需要更多信息（补全工单字段）
    clarification_field: Optional[str]       # 需要补全的字段名
    should_handoff: bool                   # 是否应该转人工
    handoff_reason: Optional[str]           # 转人工原因
    should_submit_ticket: bool              # 是否应该提交工单
    submitted_ticket_id: Optional[str]      # 已提交的 Jira 工单 ID
    response: Optional[str]                 # 返回给用户的响应内容
