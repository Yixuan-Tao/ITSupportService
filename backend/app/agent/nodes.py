"""
Agent 工作流节点定义模块

定义 LangGraph Agent 工作流中的各个处理节点：
- router_node: 意图识别与路由
- retrieval_node: 知识库检索
- clarification_node: 信息补全（多轮对话）
- ticket_builder_node: 工单生成
- ticket_submit_node: Jira 工单提交
- handoff_node: 人工升级
"""

from app.agent.state import AgentState, TicketInfo


# 意图识别关键词映射
# 根据用户消息中包含的关键词判断用户意图
INTENT_KEYWORDS = {
    "faq": ["如何", "怎么", "什么", "请问", "能不能", "可以"],  # 常见问题咨询
    "incident": ["无法", "坏了", "故障", "连不上", "打不开", "报错", "错误"],  # 故障报修
    "service_request": ["申请", "需要", "想要", "请帮我", "帮我"],  # 服务请求
    "ticket_query": ["工单", "ticket", "进度", "状态"],  # 工单查询
    "handoff": ["人工", "客服", "投诉", "紧急"]  # 转人工请求
}


def classify_intent(user_message: str) -> str:
    """
    根据用户消息分类用户意图

    通过匹配预设的关键词来判断用户属于哪种意图。
    默认返回 "faq"（常见问题）。

    Args:
        user_message: 用户输入的消息

    Returns:
        意图类型：faq/incident/service_request/ticket_query/handoff
    """
    user_lower = user_message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in user_lower for kw in keywords):
            return intent
    return "faq"


def router_node(state: AgentState) -> AgentState:
    """
    路由节点

    工作流入口节点，负责：
    1. 从消息历史中获取最新用户消息
    2. 调用 classify_intent 进行意图分类
    3. 将分类结果存入状态

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的 Agent 状态
    """
    # 获取最后一条用户消息
    last_message = state["messages"][-1]["content"] if state["messages"] else ""
    # 进行意图分类
    intent = classify_intent(last_message)
    state["intent"] = intent
    return state


def retrieval_node(state: AgentState) -> AgentState:
    """
    知识检索节点

    根据识别出的意图检索相关知识库文档。
    目前仅对 FAQ 和 Incident 类型的问题进行检索。

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的 Agent 状态（包含检索到的文档）
    """
    if state["intent"] in ["faq", "incident"]:
        # TODO: 实际应调用 vector_store.search() 从 Qdrant 检索
        # 目前返回模拟的检索结果
        docs = [
            {"content": "VPN 连接问题：请先检查网络设置，确保在允许的 IP 范围内。", "source": "IT知识库-001"},
            {"content": "重置 VPN 客户端：设置 -> 重置 -> 重新启动", "source": "IT知识库-002"}
        ]
        state["retrieved_docs"] = docs
    return state


# 信息补全所需字段列表
# 这些字段需要在提交工单前从用户处收集
CLARIFICATION_FIELDS = ["device_type", "os", "error_message", "urgency"]


def clarification_node(state: AgentState) -> AgentState:
    """
    信息补全节点

    对于 Incident（故障报修）类问题，需要收集更多信息：
    - device_type: 设备类型
    - os: 操作系统
    - error_message: 错误信息
    - urgency: 紧急程度

    如果某个字段尚未收集，设置标志位并生成追问消息。

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的 Agent 状态（包含是否需要追问的标志和追问内容）
    """
    # 仅对故障报修场景进行信息补全
    if state["intent"] != "incident":
        state["needs_clarification"] = False
        return state

    ticket_info = state["ticket_info"]
    # 检查每个必需字段是否已填写
    for field in CLARIFICATION_FIELDS:
        if not getattr(ticket_info, field):
            # 发现未填写的字段，需要追问
            state["needs_clarification"] = True
            state["clarification_field"] = field
            state["response"] = f"为了更好地帮助您，请问您的{field}是什么？"
            return state

    # 所有字段都已填写，无需追问
    state["needs_clarification"] = False
    return state


def ticket_builder_node(state: AgentState) -> AgentState:
    """
    工单生成节点

    当信息补全完成后，将收集到的信息整理成结构化工单。

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的 Agent 状态（包含待提交的工单信息和提交标志）
    """
    # 仅对故障报修且已完成信息补全的场景生成工单
    if state["intent"] == "incident" and not state["needs_clarification"]:
        last_message = state["messages"][-1]["content"]
        # 设置工单标题和描述
        state["ticket_info"].title = last_message[:100]
        state["ticket_info"].description = last_message
        # 标记可以提交工单
        state["should_submit_ticket"] = True
    return state


import os

# Jira API 配置（从环境变量读取）
JIRA_URL = os.getenv("JIRA_URL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")


def ticket_submit_node(state: AgentState) -> AgentState:
    """
    Jira 工单提交节点

    将结构化工单提交到 Jira 系统。

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的 Agent 状态（包含 Jira 工单 ID 和响应消息）
    """
    # 如果不需要提交工单，直接返回
    if not state["should_submit_ticket"]:
        return state

    ticket = state["ticket_info"]
    # 构建 Jira API payload
    jira_payload = {
        "fields": {
            "project": {"key": "IT"},
            "summary": ticket.title,
            "description": ticket.description,
            "issuetype": {"name": "Task"},
            "priority": {"name": ticket.priority or "Medium"}
        }
    }
    # TODO: 实际应调用 Jira API 创建工单
    # 目前返回模拟的工单 ID
    state["submitted_ticket_id"] = "JIRA-12345"
    state["response"] = f"工单已提交！工单号：JIRA-12345"
    return state


def handoff_node(state: AgentState) -> AgentState:
    """
    人工升级节点

    当用户明确请求人工服务时，触发此节点。

    Args:
        state: 当前 Agent 状态

    Returns:
        更新后的 Agent 状态（包含转人工标志和响应消息）
    """
    if state["intent"] == "handoff":
        state["should_handoff"] = True
        state["handoff_reason"] = "用户请求人工服务"
        state["response"] = "正在为您转接人工客服，请稍候..."
    return state
