"""
Tailscale 服务 - 管理 Tailscale 网络连接和节点发现
"""
import httpx
import logging
from typing import Optional
from dataclasses import dataclass
from enum import Enum

from src.core.config import settings

logger = logging.getLogger(__name__)


class NodeStatus(Enum):
    ONLINE = "online"
    OFFLINE = "offline"
    UNKNOWN = "unknown"


@dataclass
class TailscaleNode:
    """Tailscale 网络节点"""
    node_id: str
    name: str
    hostname: str
    ip_address: str
    status: NodeStatus
    last_seen: Optional[str] = None


class TailscaleService:
    """Tailscale 网络服务"""
    
    def __init__(self):
        self.enabled = settings.tailscale_enabled
        self.authkey = settings.tailscale_authkey
        self.hostname = settings.tailscale_hostname
        self.proxy_url = settings.tailscale_proxy_url
        self._client: Optional[httpx.AsyncClient] = None
        
    async def get_client(self) -> httpx.AsyncClient:
        """获取 HTTP 客户端（懒加载）"""
        if self._client is None:
            self._client = httpx.AsyncClient(timeout=30.0)
        return self._client
    
    async def close(self):
        """关闭客户端"""
        if self._client:
            await self._client.aclose()
            self._client = None
    
    async def get_node_ip(self, hostname: str) -> Optional[str]:
        """
        根据 hostname 获取节点的 Tailscale IP 地址
        
        Args:
            hostname: 节点主机名
            
        Returns:
            节点的 Tailscale IP 地址，如果未找到返回 None
        """
        if not self.enabled:
            logger.warning("Tailscale is not enabled")
            return None
        
        try:
            # 优先使用配置的 proxy URL
            if self.proxy_url:
                base_url = self.proxy_url.rstrip("/")
            else:
                # 默认使用本地 Tailscale API
                base_url = "http://localhost:8080"
            
            client = await self.get_client()
            
            # 获取节点列表
            response = await client.get(f"{base_url}/api/v1/node")
            
            if response.status_code == 200:
                data = response.json()
                nodes = data.get("Nodes", [])
                
                for node in nodes:
                    if node.get("Hostname") == hostname:
                        return node.get("TailscaleIPs", [None])[0]
            
            logger.warning(f"Node {hostname} not found in Tailscale network")
            return None
            
        except Exception as e:
            logger.error(f"Failed to get node IP for {hostname}: {e}")
            return None
    
    async def get_all_nodes(self) -> list[TailscaleNode]:
        """
        获取所有 Tailscale 节点
        
        Returns:
            节点列表
        """
        if not self.enabled:
            return []
        
        try:
            if self.proxy_url:
                base_url = self.proxy_url.rstrip("/")
            else:
                base_url = "http://localhost:8080"
            
            client = await self.get_client()
            response = await client.get(f"{base_url}/api/v1/nodes")
            
            if response.status_code == 200:
                data = response.json()
                nodes = []
                
                for node_data in data.get("Nodes", []):
                    node = TailscaleNode(
                        node_id=node_data.get("ID", ""),
                        name=node_data.get("Name", ""),
                        hostname=node_data.get("Hostname", ""),
                        ip_address=node_data.get("TailscaleIPs", [""])[0] or "",
                        status=NodeStatus.ONLINE if node_data.get("Online") else NodeStatus.OFFLINE,
                        last_seen=node_data.get("LastSeen"),
                    )
                    nodes.append(node)
                
                return nodes
            
            return []
            
        except Exception as e:
            logger.error(f"Failed to get Tailscale nodes: {e}")
            return []
    
    async def check_node_connectivity(self, hostname: str, port: int = 18789) -> bool:
        """
        检查节点连通性
        
        Args:
            hostname: 节点主机名或 IP
            port: 端口号
            
        Returns:
            是否可达
        """
        try:
            # 如果传入的是主机名，尝试解析为 IP
            ip = hostname
            if not self._is_ip(hostname) and self.enabled:
                resolved_ip = await self.get_node_ip(hostname)
                if resolved_ip:
                    ip = resolved_ip
            
            client = await self.get_client()
            response = await client.get(
                f"http://{ip}:{port}/health",
                timeout=5.0
            )
            
            return response.status_code == 200
            
        except Exception as e:
            logger.error(f"Node {hostname}:{port} is not reachable: {e}")
            return False
    
    def _is_ip(self, value: str) -> bool:
        """检查是否为 IP 地址"""
        parts = value.split(".")
        if len(parts) != 4:
            return False
        return all(part.isdigit() and 0 <= int(part) <= 255 for part in parts)
    
    async def get_openclaw_url(self, instance_hostname: str, default_url: str) -> str:
        """
        获取 OpenClaw 实例的完整 URL
        
        如果 Tailscale 已启用，会尝试解析为 Tailscale IP
        
        Args:
            instance_hostname: OpenClaw 实例的主机名
            default_url: 默认 URL
            
        Returns:
            完整的 URL
        """
        if not self.enabled:
            return default_url
        
        # 如果 default_url 已经是完整 URL，直接返回
        if default_url.startswith("http"):
            return default_url
        
        # 尝试解析 Tailscale IP
        tailscale_ip = await self.get_node_ip(instance_hostname)
        
        if tailscale_ip:
            # 假设默认端口 18789
            return f"http://{tailscale_ip}:18789"
        
        # 如果无法解析，返回原始 URL
        return default_url


# 全局实例
tailscale_service = TailscaleService()
