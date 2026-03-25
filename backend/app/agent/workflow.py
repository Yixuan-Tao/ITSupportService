"""
LangGraph Agent 工作流定义模块

使用 LangGraph 库定义和构建 Agent 工作流图：
- 创建 StateGraph 图
- 添加各个处理节点
- 定义节点之间的连接关系
- 编译生成可执行的工作流
"""

from langgraph.graph import StateGraph, END
from app.agent.state import AgentState
from app.agent.nodes import (
    router_node, retrieval_node, clarification_node,
    ticket_builder_node, ticket_submit_node, handoff_node
)


def create_workflow():
    """
    创建并配置 Agent 工作流

    工作流图结构：
    router -> retrieval -> clarification -> ticket_builder -> ticket_submit -> END
        |
        v
      handoff -> END

    节点说明：
    - router: 意图识别与路由（工作流入口）
    - retrieval: 从知识库检索相关文档
    - clarification: 信息补全（多轮对话追问）
    - ticket_builder: 生成结构化工单
    - ticket_submit: 提交 Jira 工单
    - handoff: 转人工服务

    Returns:
        compiled: 编译后的工作流图，可直接调用
    """
    # 创建状态图，指定状态类型为 AgentState
    workflow = StateGraph(AgentState)

    # 添加各个处理节点
    workflow.add_node("router", router_node)           # 意图路由
    workflow.add_node("retrieval", retrieval_node)     # 知识检索
    workflow.add_node("clarification", clarification_node)  # 信息补全
    workflow.add_node("ticket_builder", ticket_builder_node)  # 工单生成
    workflow.add_node("ticket_submit", ticket_submit_node)  # 工单提交
    workflow.add_node("handoff", handoff_node)         # 人工升级

    # 设置工作流入口点（第一个执行的节点）
    workflow.set_entry_point("router")

    # 定义节点之间的边（执行顺序）
    workflow.add_edge("router", "retrieval")          # router 之后执行 retrieval
    workflow.add_edge("retrieval", "clarification")   # retrieval 之后执行 clarification
    workflow.add_edge("clarification", "ticket_builder")  # clarification 之后执行 ticket_builder
    workflow.add_edge("ticket_builder", "ticket_submit")  # ticket_builder 之后执行 ticket_submit
    workflow.add_edge("ticket_submit", END)           # ticket_submit 后结束

    # handoff 节点单独处理，从 router 直接进入（条件路由）
    workflow.add_edge("handoff", END)                 # handoff 后直接结束

    # 编译工作流，生成可执行的工作流对象
    return workflow.compile()


# 创建并编译工作流实例，供外部调用
agent_workflow = create_workflow()
