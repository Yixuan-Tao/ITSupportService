"""
IT Support AI Agent - FastAPI 应用入口

该模块是整个后端服务的入口点，负责：
- 初始化 FastAPI 应用
- 配置 CORS 中间件
- 注册路由
- 启动时初始化数据库
"""

import sys
from pathlib import Path

# 将 app 目录添加到 Python 路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.models.database import init_db
from app.routers import chat

# 创建 FastAPI 应用实例，设置 API 标题
app = FastAPI(title="IT Support AI Agent")

# 配置 CORS 中间件，允许前端跨域访问
# allow_origins: 允许访问的源（前端地址）
# allow_credentials: 允许携带凭证
# allow_methods/headers: 允许所有方法和请求头
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://frontend:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 应用启动时的事件处理函数
# 确保数据库表已创建
@app.on_event("startup")
async def startup_event():
    init_db()

# 注册聊天相关路由，使用 /api 前缀
app.include_router(chat.router, prefix="/api")

# 健康检查接口
# 用于 Kubernetes/负载均衡器探测服务状态
@app.get("/health")
async def health_check():
    return {"status": "healthy"}

# 根路径接口
@app.get("/")
async def root():
    return {"message": "IT Support AI Agent API"}
