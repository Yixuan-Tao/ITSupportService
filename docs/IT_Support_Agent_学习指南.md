# IT Support Agent 系统学习指南

## 目录
1. [系统架构概述](#1-系统架构概述)
2. [后端核心组件](#2-后端核心组件)
3. [前端核心组件](#3-前端核心组件)
4. [数据库设计](#4-数据库设计)
5. [向量数据库与RAG](#5-向量数据库与rag)
6. [Jira集成](#6-jira集成)
7. [面试考点与题目](#7-面试考点与题目)

---

## 1. 系统架构概述

### 1.1 技术栈

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Frontend  │────▶│   Backend   │────▶│ PostgreSQL │
│  (Next.js)  │     │  (FastAPI)  │     │  Database   │
└─────────────┘     └──────┬──────┘     └─────────────┘
                          │
              ┌───────────┼───────────┐
              ▼           ▼           ▼
        ┌──────────┐ ┌──────────┐ ┌──────────┐
        │  Qdrant  │ │ MiniMax  │ │   Jira   │
        │ (Vector) │ │  (LLM)   │ │   API    │
        └──────────┘ └──────────┘ └──────────┘
```

### 1.2 组件作用

| 组件 | 作用 | 技术 |
|------|------|------|
| Frontend | 用户交互界面 | Next.js + React + TailwindCSS |
| Backend | 业务逻辑处理 | FastAPI + Python |
| PostgreSQL | 关系型数据存储 | 会话、工单、用户数据 |
| Qdrant | 向量数据库 | RAG 知识检索 |
| LLM API | 大语言模型 | Claude via MiniMax 代理 |
| Jira | 工单系统 | IT 工单同步 |

---

## 2. 后端核心组件

### 2.1 FastAPI 应用入口

**文件**: `backend/app/main.py`

```python
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.routers import chat, conversations, tickets, documents, feedback

app = FastAPI(title="IT Support Agent API")

# CORS 中间件配置
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 注册路由
app.include_router(chat.router, prefix="/api")
app.include_router(conversations.router, prefix="/api")
app.include_router(tickets.router, prefix="/api")
```

**面试考点**:
- FastAPI 路由注册方式
- CORS 中间件作用
- 异步框架优势

### 2.2 聊天路由 (`chat.py`)

**文件**: `backend/app/routers/chat.py`

#### 2.2.1 意图识别

```python
INTENT_KEYWORDS = {
    "faq": ["如何", "怎么", "什么", "请问"],
    "incident": ["无法", "坏了", "故障", "报错"],
    "service_request": ["申请", "需要", "想要", "开通"],
    "create_ticket": ["提交工单", "创建工单"],
    "handoff": ["人工", "客服", "转人工"]
}

def classify_intent(message: str) -> str:
    """根据关键词分类用户意图"""
    msg_lower = message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            return intent
    return "faq"
```

#### 2.2.2 聊天接口

```python
@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: Session = Depends(get_db)):
    # 1. 获取或创建会话
    conversation_id = request.conversation_id or create_conversation()

    # 2. 意图识别
    intent = classify_intent(request.message)

    # 3. 向量检索（从知识库查找相关内容）
    docs = await vector_store.search(request.message, top_k=2)

    # 4. 构建上下文
    context = "\n\n".join([d["content"][:500] for d in docs])
    context_prompt = f"\n\n知识库内容：\n{context}"

    # 5. 调用 LLM 生成回复
    messages = history + [{"role": "user", "content": request.message + context_prompt}]
    response_text = await llm_service.generate(messages, system=SYSTEM_PROMPT)

    # 6. 如果需要创建工单
    if intent == "create_ticket":
        jira_service.create_issue(project_key="SUBV", summary=..., description=...)

    return ChatResponse(response=response_text, conversation_id=conversation_id, intent=intent)
```

**面试考点**:
- FastAPI 依赖注入 (Depends)
- 异步编程 (async/await)
- 中间件模式
- RESTful API 设计

### 2.3 LLM 服务 (`llm.py`)

**文件**: `backend/app/services/llm.py`

```python
class LLMService:
    def __init__(self):
        self.base_url = os.getenv("ANTHROPIC_BASE_URL")
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        self.model = "claude-3-5-sonnet-20241022"
        self.max_tokens = 1024

    async def generate(self, messages: List[dict], system: str = None) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "anthropic-version": "2023-06-01"
        }
        payload = {"model": self.model, "messages": messages, "max_tokens": self.max_tokens}
        if system:
            payload["system"] = system

        async with httpx.AsyncClient() as client:
            response = await client.post(f"{self.base_url}/v1/messages", headers=headers, json=payload)
            data = response.json()
            # 解析 content 中的 text 块
            for block in data.get("content", []):
                if block.get("type") == "text":
                    return block.get("text", "")
```

**面试考点**:
- httpx 异步 HTTP 客户端
- API 认证方式 (Bearer Token)
- LLM 调用模式

### 2.4 向量存储服务 (`vector_store.py`)

**文件**: `backend/app/services/vector_store.py`

```python
class VectorStore:
    def __init__(self):
        self.client = QdrantClient(
            host=os.getenv("QDRANT_HOST"),
            port=int(os.getenv("QDRANT_PORT"))
        )
        self.collection_name = "it_support_docs"

    async def add_documents(self, documents: List[dict]):
        """批量添加文档到向量数据库"""
        points = []
        for i, doc in enumerate(documents):
            embedding = await embedding_service.get_embedding(doc["content"])
            points.append(PointStruct(
                id=i,
                vector=embedding,
                payload={"content": doc["content"], "source": doc["source"]}
            ))
        self.client.upsert(collection_name=self.collection_name, points=points)

    async def search(self, query: str, top_k: int = 5) -> List[dict]:
        """向量相似度检索"""
        query_embedding = await embedding_service.get_embedding(query)
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=top_k
        )
        return [{"content": hit.payload["content"],
                 "source": hit.payload["source"],
                 "score": hit.score} for hit in results.points]
```

**面试考点**:
- 向量数据库原理
- 余弦相似度 (Cosine Similarity)
- ANN (Approximate Nearest Neighbor) 算法
- HNSW 索引

### 2.5 Jira 服务 (`jira.py`)

**文件**: `backend/app/services/jira.py`

```python
class JiraService:
    def create_issue(self, project_key: str, summary: str, description: str,
                     issue_type: str = "Task", priority: str = "Medium") -> dict:
        """创建 Jira 工单"""
        headers = {
            "Authorization": self._get_auth_header(),
            "Content-Type": "application/json"
        }
        payload = {
            "fields": {
                "project": {"key": project_key},
                "summary": summary,
                "description": {"type": "doc", "version": 1,
                               "content": [{"type": "paragraph",
                                            "content": [{"type": "text", "text": description}]}]},
                "issuetype": {"name": issue_type},
                "priority": {"name": priority}
            }
        }
        response = httpx.post(f"{self.jira_url}/rest/api/3/issue",
                              headers=headers, json=payload)
        return response.json()

    def get_issue(self, issue_key: str) -> dict:
        """获取工单详情"""
        response = httpx.get(f"{self.jira_url}/rest/api/3/issue/{issue_key}",
                           headers=self._get_auth_header())
        return response.json()

    def get_issues_by_keys(self, issue_keys: List[str]) -> List[dict]:
        """批量获取工单（用于同步）"""
        issues = []
        for key in issue_keys:
            try:
                issue = self.get_issue(key)
                issues.append({
                    "key": issue["key"],
                    "status": issue["fields"]["status"]["name"],
                    "priority": issue["fields"]["priority"]["name"]
                })
            except:
                continue  # 工单不存在则跳过
        return issues
```

**面试考点**:
- RESTful API 调用
- Basic Auth vs Bearer Token
- 错误处理与异常捕获

---

## 3. 前端核心组件

### 3.1 API 客户端 (`client.ts`)

**文件**: `frontend/src/api/client.ts`

```typescript
class ApiClient {
  constructor(private baseUrl: string) {}

  async get<T>(path: string): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      headers: { "Content-Type": "application/json" }
    });
    if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
    return response.json();
  }

  async post<T>(path: string, data: any): Promise<T> {
    const response = await fetch(`${this.baseUrl}${path}`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(data)
    });
    return response.json();
  }
}

export const chatApi = {
  sendMessage: (data: { message: string; conversation_id?: number }) =>
    api.post<ChatResponse>("/chat", data)
};
```

### 3.2 聊天组件 (`Chat.tsx`)

**文件**: `frontend/src/components/Chat.tsx`

```typescript
const Chat: React.FC = () => {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isLoading, setIsLoading] = useState(false);

  const handleSend = async () => {
    setIsLoading(true);
    try {
      const response = await chatApi.sendMessage({ message: input });
      setMessages(prev => [...prev,
        { role: "user", content: input },
        { role: "assistant", content: response.response }
      ]);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col h-full">
      <div className="flex-1 overflow-y-auto">
        {messages.map((msg, i) => (
          <div key={i} className={msg.role === "user" ? "bg-blue-500" : "bg-gray-100"}>
            {msg.content}
          </div>
        ))}
      </div>
      <div className="flex gap-2">
        <input value={input} onChange={e => setInput(e.target.value)} />
        <button onClick={handleSend} disabled={isLoading}>发送</button>
      </div>
    </div>
  );
};
```

---

## 4. 数据库设计

### 4.1 SQLAlchemy 模型

**文件**: `backend/app/models/database.py`

```python
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String)
    email = Column(String, unique=True, index=True)
    role = Column(String, default="user")

class Conversation(Base):
    __tablename__ = "conversations"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    status = Column(String, default="active")  # active/closed
    created_at = Column(DateTime, default=datetime.utcnow)

class Message(Base):
    __tablename__ = "messages"
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String)  # user/assistant
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

class Ticket(Base):
    __tablename__ = "tickets"
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String)
    description = Column(Text)
    category = Column(String)  # incident/service_request/create_ticket
    priority = Column(String)   # Low/Medium/High/Critical
    status = Column(String, default="open")  # open/in_progress/resolved/closed
    jira_id = Column(String, nullable=True)  # Jira 工单号
    created_at = Column(DateTime, default=datetime.utcnow)
```

### 4.2 ER 关系图

```
User (1) ──────< Conversation (1) ──────< Message (N)
  │                                        │
  │                                        │
  └────< Ticket (N)                       │
                                              │
                                              │
              Jira Issue (通过 jira_id 关联)
```

**面试考点**:
- 一对多关系 (One-to-Many)
- 外键约束 (Foreign Key)
- 索引作用 (Index)
- SQLAlchemy ORM 用法

---

## 5. 向量数据库与RAG

### 5.1 RAG 流程

```
用户问题 ──▶ Embedding API ──▶ Qdrant 检索 ──▶ 获取相关文档
                                      │
                                      ▼
                              构建 Context Prompt
                                      │
                                      ▼
                              LLM 生成回复 + 参考文档
```

### 5.2 Embedding 服务

**文件**: `backend/app/services/embedding.py`

```python
class EmbeddingService:
    def __init__(self):
        self.api_url = "https://dashscope.aliyuncs.com/compatible-mode/v1/embeddings"
        self.model = "text-embedding-v3"
        self.dimension = 1024  # text-embedding-v3 输出 1024 维

    async def get_embedding(self, text: str) -> List[float]:
        response = httpx.post(self.api_url, json={
            "model": self.model,
            "input": text
        }, headers={"Authorization": f"Bearer {QWEN_API_KEY}"})

        data = response.json()
        return data["data"][0]["embedding"]
```

### 5.3 参考文档过滤

```python
def format_references(docs: List[dict], min_score: float = 0.7) -> str:
    """过滤高相关度文档，排除 seed_data"""
    filtered = [d for d in docs
                if d.get('score', 0) >= min_score
                and '/seed_data/' not in d.get('source', '')]

    if not filtered:
        return "\n\n**参考文档：**暂无相关文档"

    lines = ["\n\n**参考文档：**"]
    for i, doc in enumerate(filtered, 1):
        lines.append(f"{i}. {doc['source']}")
    return "\n".join(lines)
```

**面试考点**:
- RAG (Retrieval-Augmented Generation) 原理
- 向量嵌入 (Embedding) 概念
- 余弦相似度计算
- Top-K 检索
- Context Window 限制

---

## 6. Jira 集成

### 6.1 同步机制

```python
@router.post("/tickets/sync")
async def sync_tickets_with_jira(db: Session = Depends(get_db)):
    """同步本地工单与 Jira 状态"""
    local_tickets = db.query(Ticket).filter(Ticket.jira_id.isnot(None)).all()

    # 批量获取 Jira 工单状态
    jira_keys = [t.jira_id for t in local_tickets]
    jira_issues = jira_service.get_issues_by_keys(jira_keys)
    jira_map = {issue["key"]: issue for issue in jira_issues}

    for ticket in local_tickets:
        if ticket.jira_id in jira_map:
            # 工单存在，同步状态
            ticket.status = status_map[jira_map[ticket.jira_id]["status"]]
        else:
            # 工单在 Jira 被删除，标记为 closed
            ticket.status = "closed"

    db.commit()
    return {"success": True, "synced": len(local_tickets)}
```

### 6.2 状态映射

| Jira 状态 | 本地状态 |
|-----------|---------|
| 打开/To Do | open |
| 进行中/In Progress | in_progress |
| 完成/Done | resolved |
| 关闭/Closed | closed |

---

## 7. 面试考点与题目

### 7.1 FastAPI 考点

**Q1: FastAPI 如何实现异步处理？**

```python
@router.post("/chat")
async def chat(request: ChatRequest):  # async def
    result = await some_async_operation()  # await 异步调用
    return result
```

**Q2: FastAPI 的依赖注入如何使用？**

```python
from fastapi import Depends

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/items")
async def read_items(db: Session = Depends(get_db)):  # 通过 Depends 注入
    return db.query(Item).all()
```

---

### 7.2 向量数据库考点

**Q3: 向量数据库的ANN算法有哪些？**

答：HNSW (Hierarchical Navigable Small World)、IVF、PQ 等。Qdrant 使用 HNSW。

**Q4: 如何选择合适的 top_k 值？**

答：需要权衡召回率和准确率。top_k 越大，召回越多但可能引入噪声；越小越精准但可能遗漏。通常设置为 3-5。

**Q5: 向量检索的分数 (score) 代表什么？**

答：通常是余弦相似度，范围 -1 到 1（或 0 到 1，取决于实现）。分数越高表示向量越相似。

---

### 7.3 RAG 考点

**Q6: RAG 相比直接调用 LLM 的优势？**

答：
1. **知识时效性** - 可更新知识库，无需重新训练
2. **减少幻觉** - 基于真实文档回答
3. **可溯源** - 提供参考文档链接
4. **成本更低** - 无需 Fine-tuning

**Q7: RAG 的局限性有哪些？**

答：
1. 依赖检索质量
2. Context Length 限制
3. 多跳推理困难
4. 跨文档理解有限

---

### 7.4 数据库考点

**Q8: 为什么要给 email 字段加索引？**

答：索引可以加速查询。email 作为查询条件（登录、查找用户），加索引可将查询从 O(n) 降到 O(log n)。

**Q9: SQLAlchemy 中 session 和 engine 的区别？**

答：
- Engine：数据库连接池，管理底层连接
- Session：ORM 操作接口，提供事务管理

---

### 7.5 系统设计考点

**Q10: 如何设计一个高可用的 AI Agent 系统？**

答：
1. **无状态服务** - 后端实例可水平扩展
2. **多级缓存** - Redis 缓存热点数据
3. **熔断机制** - LLM 调用失败时降级
4. **重试机制** - 临时故障自动重试
5. **监控告警** - 关键指标实时监控

**Q11: 如何保证工单不丢失？**

答：
1. 本地数据库先写入
2. Jira 创建成功后更新本地 jira_id
3. 定期同步检查 Jira 状态
4. 失败重试机制

**Q12: 如何优化 LLM 调用延迟？**

答：
1. 减少 Context 长度（限制检索文档数）
2. 使用更快的模型
3. 添加流式输出（改善用户体验）
4. 缓存常见问题答案
5. 并行处理（向量检索和 LLM 调用）

---

### 7.6 代码实现题

**Q13: 实现一个简单的意图识别函数**

```python
def classify_intent(message: str) -> str:
    INTENT_KEYWORDS = {
        "faq": ["如何", "怎么", "什么"],
        "incident": ["无法", "坏了", "报错"],
        "service_request": ["申请", "需要", "开通"],
        "ticket": ["提交工单", "创建工单"],
    }

    msg_lower = message.lower()
    for intent, keywords in INTENT_KEYWORDS.items():
        if any(kw in msg_lower for kw in keywords):
            return intent
    return "faq"

# 测试
print(classify_intent("我的电脑坏了"))  # incident
print(classify_intent("如何重置密码"))  # faq
print(classify_intent("帮我提交工单"))  # ticket
```

**Q14: 实现向量相似度计算**

```python
import math

def cosine_similarity(vec1: list, vec2: list) -> float:
    dot_product = sum(a * b for a, b in zip(vec1, vec2))
    mag1 = math.sqrt(sum(a * a for a in vec1))
    mag2 = math.sqrt(sum(b * b for b in vec2))
    return dot_product / (mag1 * mag2) if mag1 and mag2 else 0

# 测试
v1 = [0.1, 0.2, 0.3]
v2 = [0.1, 0.2, 0.3]
print(f"相似度: {cosine_similarity(v1, v2):.4f}")  # 1.0000
```

---

## 附录：常见问题

### Q: Docker 网络中如何让容器互通？
A: 使用服务名作为主机名，如 `postgres`、`qdrant`

### Q: 为什么向量维度要匹配？
A: 向量数据库按维度创建索引，维度不匹配会导致存储和检索失败

### Q: 如何处理 LLM API 失败？
A: 添加 try-except 捕获异常，返回友好提示，并记录日志

### Q: 为什么参考文档要过滤 seed_data？
A: seed_data 是测试数据，不应作为正式参考来源

---

*文档版本: 1.0*
*最后更新: 2026-03-25*
