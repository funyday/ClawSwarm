"""飞书消息发送服务。"""

import httpx
from typing import Optional
import json

from src.models.feishu_bot import FeishuBot


class FeishuMessageSender:
    """飞书消息发送器"""
    
    BASE_URL = "https://open.feishu.cn/open-apis"
    
    # 缓存的 token
    _token_cache: dict[str, tuple[str, float]] = {}
    _token_cache_duration = 7000  # 2 小时（飞书 token 有效期 2 小时）
    
    def __init__(self, bot: FeishuBot):
        self.bot = bot
    
    async def _get_tenant_access_token(self) -> Optional[str]:
        """
        获取 tenant_access_token
        
        使用缓存机制，避免频繁请求
        """
        cache_key = self.bot.app_id
        
        # 检查缓存
        if cache_key in self._token_cache:
            token, expires_at = self._token_cache[cache_key]
            if expires_at > 0:
                return token
        
        # 请求新 token
        url = f"{self.BASE_URL}/auth/v3/tenant_access_token/internal"
        data = {
            "app_id": self.bot.app_id,
            "app_secret": self.bot.app_secret,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, json=data, timeout=30.0)
            result = response.json()
            
            if result.get("code") != 0:
                print(f"Failed to get tenant token: {result}")
                return None
            
            token = result.get("tenant_access_token")
            # 缓存 token
            self._token_cache[cache_key] = (token, self._token_cache_duration)
            
            return token
    
    async def send_text(self, receive_id: str, text: str) -> dict:
        """
        发送文本消息
        
        Args:
            receive_id: 接收者 ID（群 ID 或用户 open_id）
            text: 消息内容
            
        Returns:
            API 响应
        """
        content = json.dumps({"text": text})
        return await self._send_message(receive_id, "text", content)
    
    async def send_card(self, receive_id: str, card_content: dict) -> dict:
        """
        发送卡片消息
        
        Args:
            receive_id: 接收者 ID
            card_content: 卡片内容（JSON）
            
        Returns:
            API 响应
        """
        content = json.dumps(card_content)
        return await self._send_message(receive_id, "interactive", content)
    
    async def _send_message(
        self,
        receive_id: str,
        msg_type: str,
        content: str,
    ) -> dict:
        """
        发送消息的底层实现
        """
        token = await self._get_tenant_access_token()
        if not token:
            return {"code": 1, "msg": "Failed to get access token"}
        
        url = f"{self.BASE_URL}/im/v1/messages?receive_id_type=chat_id"
        headers = {
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        }
        
        payload = {
            "receive_id": receive_id,
            "msg_type": msg_type,
            "content": content,
        }
        
        async with httpx.AsyncClient() as client:
            response = await client.post(url, headers=headers, json=payload, timeout=30.0)
            return response.json()
    
    async def build_response_card(
        self,
        agent_name: str,
        response_text: str,
        message_id: str = "",
    ) -> dict:
        """
        构建响应卡片
        
        Args:
            agent_name: Agent 名称
            response_text: 响应内容
            message_id: 关联的消息 ID
            
        Returns:
            卡片 JSON
        """
        return {
            "schema": "2.0",
            "config": {
                "wide_screen_mode": True,
            },
            "elements": [
                {
                    "tag": "markdown",
                    "content": f"**[{agent_name}]**\n\n{response_text}",
                },
                {
                    "tag": "hr",
                },
                {
                    "tag": "note",
                    "elements": [
                        {
                            "tag": "plain_text",
                            "content": f"消息 ID: {message_id}" if message_id else "ClawSwarm 自动回复",
                        },
                    ],
                },
            ],
        }
    
    async def send_agent_response(
        self,
        chat_id: str,
        agent_name: str,
        response_text: str,
        use_card: bool = True,
    ) -> dict:
        """
        发送 Agent 响应到飞书群
        
        Args:
            chat_id: 飞书群 ID
            agent_name: Agent 名称
            response_text: 响应内容
            use_card: 是否使用卡片格式
            
        Returns:
            API 响应
        """
        if use_card:
            card = await self.build_response_card(agent_name, response_text)
            return await self.send_card(chat_id, card)
        else:
            formatted_text = f"**[{agent_name}]**\n\n{response_text}"
            return await self.send_text(chat_id, formatted_text)
