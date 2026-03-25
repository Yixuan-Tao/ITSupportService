"""
API 路由模块 - 聊天、工单、文档管理接口

提供以下 RESTful API 端点：
- /chat: 聊天接口，处理用户消息并返回 Agent 响应
- /conversations: 会话管理，获取会话列表和详情
- /tickets: 工单管理，创建和查询工单
- /documents: 文档管理，上传和查询知识库文档
- /feedback: 反馈管理，提交用户满意度反馈
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from app.models.database import get_db, Conversation, Message, Ticket, User, Document, Feedback
from app.models.schemas import (
    ChatRequest, ChatResponse, ConversationResponse,
    TicketResponse, TicketCreate, DocumentResponse, DocumentCreate,
    FeedbackCreate, FeedbackResponse
)
from app.services.vector_store import vector_store
from app.services.llm import llm_service
from app.services.jira import jira_service

SYSTEM_PROMPT = """你是一个专业的 IT 支持助手，名字叫"小 IT"。

你的职责：
1. 回答用户关于 IT 技术问题（VPN、软件、网络、硬件等）
2. 引导用户进行简单的故障排查
3. 收集必要信息以便创建工单
4. 无法解决时转人工服务

请根据知识库中的内容回答用户问题。如果知识库中有相关信息，请引用原文。

回答要求：
- 使用中文
- 简洁明了
- 如果需要更多信息才能回答，请礼貌地询问
- 如果问题超出 IT 支持范围，请说明并建议转人工"""

INTENT_KEYWORDS = {
    "faq": ["如何", "怎么", "什么", "请问", "能不能", "可以", "是"],
    "incident": ["无法", "坏了", "故障", "连不上", "打不开", "报错", "错误", "不行"],
    "service_request": ["申请", "需要", "想要", "请帮我", "帮我", "开通", "重置"],
    "ticket_query": ["工单", "ticket", "进度", "状态", "查询"],
    "create_ticket": ["提交工单", "创建工单", "开个工单", "新建工单", "我要提交", "帮我提交工单"],
    "handoff": ["人工", "客服", "投诉", "紧急", "转人工"]
}

PRIORITY_KEYWORDS = {
    "critical": ["紧急", "严重", "崩溃", "完全无法使用"],
    "high": ["很急", "重要", "影响工作"],
    "medium": ["一般", "普通"],
    "low": ["不急", "以后再说"]
}


def classify_intent(message: str) -> str:
    msg_lower = message.lower()

    if any(kw in msg_lower for kw in INTENT_KEYWORDS["create_ticket"]):
        return "create_ticket"

    if any(kw in msg_lower for kw in INTENT_KEYWORDS["handoff"]):
        return "handoff"

    for intent, keywords in INTENT_KEYWORDS.items():
        if intent not in ["create_ticket", "handoff"]:
            if any(kw in msg_lower for kw in keywords):
                return intent
    return "faq"


def classify_priority(message: str) -> str:
    for priority, keywords in PRIORITY_KEYWORDS.items():
        if any(kw in message for kw in keywords):
            return priority.capitalize()
    return "Medium"


def format_references(docs: List[dict], min_score: float = 0.7) -> str:
    if not docs:
        return "\n\n**参考文档：**暂无相关文档"
    filtered = [d for d in docs if d.get('score', 0) >= min_score and '/seed_data/' not in d.get('source', '')]
    if not filtered:
        return "\n\n**参考文档：**暂无相关文档"
    lines = ["\n\n**参考文档：**"]
    for i, doc in enumerate(filtered, 1):
        source = doc.get('source', '未知来源')
        lines.append(f"{i}. {source}")
    return "\n".join(lines)


router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    conversation_id = request.conversation_id

    if conversation_id:
        conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        user_id = request.user_id
        if not user_id:
            default_user = db.query(User).filter(User.email == "default@local").first()
            if not default_user:
                default_user = User(name="Default User", email="default@local", role="user")
                db.add(default_user)
                db.commit()
                db.refresh(default_user)
            user_id = default_user.id

        conversation = Conversation(user_id=user_id, status="active")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        conversation_id = conversation.id

    user_message = Message(
        conversation_id=conversation_id,
        role="user",
        content=request.message
    )
    db.add(user_message)
    db.commit()

    history = db.query(Message).filter(
        Message.conversation_id == conversation_id
    ).order_by(Message.created_at).all()
    history_messages = [{"role": m.role, "content": m.content} for m in history[:-1]]

    intent = classify_intent(request.message)

    try:
        docs = await vector_store.search(request.message, top_k=2)
    except Exception as e:
        print(f"向量检索失败: {e}")
        docs = []

    if docs:
        context = "\n\n".join([d["content"][:500] for d in docs])
        context_prompt = f"\n\n以下是知识库中的相关内容，请结合这些信息回答用户问题：\n{context}"
    else:
        context_prompt = ""

    messages = history_messages + [{
        "role": "user",
        "content": request.message + context_prompt
    }]

    try:
        response_text = await llm_service.generate(messages, system=SYSTEM_PROMPT)
    except Exception as e:
        print(f"LLM 调用失败: {e}")
        response_text = "抱歉，服务暂时繁忙，请稍后再试。"
        jira_issue_key = None

    response_text += format_references(docs)

    jira_issue_key = None
    if intent == "create_ticket":
        try:
            result = jira_service.create_issue(
                project_key="SUBV",
                summary=f"IT工单 - {request.message[:50]}",
                description=f"用户问题：{request.message}\n\n会话历史：\n" + "\n".join([f"{m['role']}: {m['content']}" for m in history_messages[-5:]]),
                issue_type="Task",
                priority=classify_priority(request.message)
            )
            jira_issue_key = result["key"]
            response_text += f"\n\n📝 工单已创建：**{jira_issue_key}**，IT支持团队会尽快处理。"
        except Exception as e:
            print(f"Jira 工单创建失败: {e}")
            response_text += "\n\n⚠️ 工单创建失败，请稍后重试或联系管理员。"

    assistant_message = Message(
        conversation_id=conversation_id,
        role="assistant",
        content=response_text
    )
    db.add(assistant_message)

    if jira_issue_key:
        ticket = Ticket(
            title=request.message[:100],
            description=request.message,
            category=intent,
            priority=classify_priority(request.message),
            status="open",
            jira_id=jira_issue_key
        )
        db.add(ticket)

    db.commit()

    return ChatResponse(
        response=response_text,
        conversation_id=conversation_id,
        intent=intent,
        references=[d.get("source", "") for d in docs]
    )


@router.post("/tickets", response_model=TicketResponse)
async def create_ticket(ticket: TicketCreate, db: Session = Depends(get_db)):
    """
    创建工单

    如果配置了 Jira，会同步创建 Jira 工单
    """
    db_ticket = Ticket(**ticket.model_dump())
    db.add(db_ticket)
    db.commit()

    # 尝试创建 Jira 工单
    jira_issue_key = None
    try:
        result = jira_service.create_issue(
            project_key="SUBV",
            summary=ticket.title,
            description=ticket.description,
            issue_type="Task",
            priority=ticket.priority or "Medium"
        )
        jira_issue_key = result["key"]
        db_ticket.jira_id = jira_issue_key
        db.commit()
        print(f"Jira 工单创建成功: {jira_issue_key}")
    except Exception as e:
        print(f"Jira 工单创建失败: {e}")

    db.refresh(db_ticket)
    return db_ticket


@router.get("/tickets/jira/{jira_key}")
async def get_jira_ticket(jira_key: str):
    """查询 Jira 工单详情"""
    try:
        issue = jira_service.get_issue(jira_key)
        return {
            "key": issue["key"],
            "summary": issue["fields"]["summary"],
            "status": issue["fields"]["status"]["name"],
            "priority": issue["fields"]["priority"]["name"],
            "url": issue["self"]
        }
    except Exception as e:
        raise HTTPException(status_code=404, detail=f"Jira 工单不存在或无法访问: {e}")


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(conversation_id: int, db: Session = Depends(get_db)):
    conversation = db.query(Conversation).filter(Conversation.id == conversation_id).first()
    if not conversation:
        raise HTTPException(status_code=404, detail="Conversation not found")
    return conversation


@router.get("/conversations", response_model=List[ConversationResponse])
async def list_conversations(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    conversations = db.query(Conversation).order_by(Conversation.updated_at.desc()).offset(skip).limit(limit).all()
    return conversations


@router.get("/tickets/{ticket_id}", response_model=TicketResponse)
async def get_ticket(ticket_id: int, db: Session = Depends(get_db)):
    ticket = db.query(Ticket).filter(Ticket.id == ticket_id).first()
    if not ticket:
        raise HTTPException(status_code=404, detail="Ticket not found")
    return ticket


@router.get("/tickets", response_model=List[TicketResponse])
async def list_tickets(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    tickets = db.query(Ticket).order_by(Ticket.created_at.desc()).offset(skip).limit(limit).all()
    return tickets


@router.post("/tickets/sync")
async def sync_tickets_with_jira(db: Session = Depends(get_db)):
    """
    同步本地工单与 Jira 状态

    根据本地工单的 jira_id 直接获取 Jira 工单状态，更新本地记录
    """
    try:
        local_tickets = db.query(Ticket).filter(Ticket.jira_id.isnot(None)).all()

        if not local_tickets:
            return {"success": True, "synced": 0, "updated": []}

        jira_keys = [t.jira_id for t in local_tickets]
        jira_issues = jira_service.get_issues_by_keys(jira_keys)
        jira_issue_map = {issue["key"]: issue for issue in jira_issues}

        synced_count = 0
        updated_list = []

        for ticket in local_tickets:
            if ticket.jira_id in jira_issue_map:
                jira_data = jira_issue_map[ticket.jira_id]
                status_map = {
                    "打开": "open",
                    "To Do": "open",
                    "In Progress": "in_progress",
                    "进行中": "in_progress",
                    "Done": "resolved",
                    "完成": "resolved",
                    "Closed": "closed",
                    "关闭": "closed",
                    "Resolved": "resolved",
                    "已解决": "resolved"
                }
                ticket.status = status_map.get(jira_data["status"], ticket.status)
                ticket.priority = jira_data.get("priority", ticket.priority)
                synced_count += 1
                updated_list.append(ticket.jira_id)
            else:
                ticket.status = "closed"

        db.commit()

        return {
            "success": True,
            "synced": synced_count,
            "updated": updated_list
        }
    except Exception as e:
        return {"success": False, "error": str(e)}


@router.post("/documents", response_model=DocumentResponse)
async def create_document(document: DocumentCreate, db: Session = Depends(get_db)):
    db_document = Document(**document.model_dump())
    db.add(db_document)
    db.commit()
    db.refresh(db_document)
    return db_document


@router.get("/documents", response_model=List[DocumentResponse])
async def list_documents(skip: int = 0, limit: int = 10, db: Session = Depends(get_db)):
    documents = db.query(Document).offset(skip).limit(limit).all()
    return documents


@router.post("/feedback", response_model=FeedbackResponse)
async def create_feedback(feedback: FeedbackCreate, db: Session = Depends(get_db)):
    db_feedback = Feedback(**feedback.model_dump())
    db.add(db_feedback)
    db.commit()
    db.refresh(db_feedback)
    return db_feedback
