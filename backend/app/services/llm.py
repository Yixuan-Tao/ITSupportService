"""
LLM 服务模块

提供大语言模型调用功能：
- 使用 Anthropic API（通过 MiniMax 代理）
- 支持 Claude 3.5 Sonnet 等模型
"""

import os
import json
from typing import List, Optional
import httpx


class LLMService:
    def __init__(self):
        self.base_url = os.getenv("ANTHROPIC_BASE_URL", "https://api.minimaxi.com/anthropic")
        self.api_key = os.getenv("ANTHROPIC_API_KEY", "")
        self.model = os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
        self.max_tokens = 1024

    async def generate(
        self,
        messages: List[dict],
        system: Optional[str] = None
    ) -> str:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": "2023-06-01"
        }

        payload = {
            "model": self.model,
            "max_tokens": self.max_tokens,
            "messages": messages
        }

        if system:
            payload["system"] = system

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/v1/messages",
                headers=headers,
                json=payload,
                timeout=60.0
            )

            if response.status_code != 200:
                raise Exception(f"LLM API error: {response.status_code} - {response.text}")

            data = response.json()

            # MiniMax API 返回格式：content 是数组，包含 thinking 和 text 块
            content = data.get("content", [])
            if isinstance(content, list):
                for block in content:
                    # 找到 text 类型的块
                    if block.get("type") == "text":
                        return block.get("text", "")
                    # 跳过 thinking 类型的块
                    elif block.get("type") == "thinking":
                        continue
                # 如果没有 text 块，尝试返回第一个非 thinking 块
                for block in content:
                    if block.get("type") != "thinking":
                        return str(block)
            return str(content)


llm_service = LLMService()
