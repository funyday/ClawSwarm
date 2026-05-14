"""飞书消息解析服务。"""

from typing import Optional
from dataclasses import dataclass
import re


@dataclass
class FeishuMention:
    """飞书 @ 信息"""
    name: str
    id: str  # Bot 的 open_id 或 user_id
    type: str  # bot / user


@dataclass
class FeishuMessage:
    """飞书消息解析结果"""
    message_id: str
    chat_id: str
    sender_id: str
    sender_name: Optional[str]
    content: str  # 原始文本内容（去除 @ 部分）
    mentions: list[FeishuMention]
    message_type: str  # text / card / image 等
    
    @property
    def mentioned_bot_names(self) -> list[str]:
        """获取被 @ 的 Bot 名称"""
        return [m.name for m in self.mentions if m.type == "bot"]
    
    @property
    def has_bot_mention(self) -> bool:
        """是否有 @ Bot"""
        return any(m.type == "bot" for m in self.mentions)


class FeishuMessageParser:
    """飞书消息解析器"""
    
    # Bot mention 格式: <at user_id="ou_xxx" user_name="BotName"></at>
    BOT_MENTION_PATTERN = re.compile(r'<at user_id="([^"]+)" user_name="([^"]+)"></at>')
    # 用户 mention 格式类似
    USER_MENTION_PATTERN = re.compile(r'<at user_id="([^"]+)" user_name="([^"]+)"></at>')
    
    @staticmethod
    def parse_mentions(content: str) -> list[FeishuMention]:
        """解析消息中的 @ 信息"""
        mentions = []
        
        # 匹配所有 <at> 标签
        for match in FeishuMessageParser.BOT_MENTION_PATTERN.finditer(content):
            user_id = match.group(1)
            user_name = match.group(2)
            # 注意：这里需要额外信息判断是 Bot 还是 User
            # 暂时根据 user_id 前缀判断：ou_ 通常是用户，ob_ 是 Bot
            mention_type = "bot" if user_id.startswith("ob_") else "user"
            mentions.append(FeishuMention(
                name=user_name,
                id=user_id,
                type=mention_type,
            ))
        
        return mentions
    
    @staticmethod
    def extract_text_content(content: str) -> str:
        """提取纯文本内容，去除 @ 标签"""
        # 去除 <at> 标签但保留空格
        text = re.sub(r'<at[^>]*></at>', ' ', content)
        # 清理多余空格
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    @classmethod
    def parse(cls, payload: dict) -> Optional[FeishuMessage]:
        """
        解析飞书 Webhook 事件 payload
        
        payload 结构:
        {
            "schema": "2.0",
            "header": {...},
            "event": {...}
        }
        """
        try:
            event = payload.get("event", {})
            header = payload.get("header", {})
            
            # 提取消息基本信息
            message_id = event.get("message_id", "")
            chat_id = event.get("chat_id", "")
            msg_type = event.get("message_type", "text")
            
            # 提取发送者信息
            sender = event.get("sender", {})
            sender_id = sender.get("sender_id", {}).get("open_id", "")
            sender_name = sender.get("sender_name", "")
            
            # 提取消息内容
            content_str = event.get("content", "{}")
            if isinstance(content_str, str):
                import json
                content_data = json.loads(content_str)
            else:
                content_data = content_str
            
            text_content = ""
            if msg_type == "text":
                text_content = content_data.get("text", "")
            elif msg_type == "post":
                # 富文本消息，提取所有文本
                text_content = cls._extract_post_text(content_data)
            
            # 解析 @ 信息
            mentions = cls.parse_mentions(text_content)
            
            # 提取纯文本
            clean_text = cls.extract_text_content(text_content)
            
            return FeishuMessage(
                message_id=message_id,
                chat_id=chat_id,
                sender_id=sender_id,
                sender_name=sender_name,
                content=clean_text,
                mentions=mentions,
                message_type=msg_type,
            )
            
        except Exception as e:
            print(f"Failed to parse feishu message: {e}")
            return None
    
    @staticmethod
    def _extract_post_text(content: dict) -> str:
        """从富文本消息中提取文本"""
        texts = []
        try:
            post_content = content.get("post", {})
            zh_cn = post_content.get("zh_cn", {})
            content_list = zh_cn.get("content", [])
            
            for section in content_list:
                for item in section:
                    if item.get("tag") == "text":
                        texts.append(item.get("text", ""))
                    elif item.get("tag") == "at":
                        user_name = item.get("user_name", "")
                        if user_name:
                            texts.append(f"@{user_name}")
            
            return " ".join(texts)
        except Exception:
            return ""
