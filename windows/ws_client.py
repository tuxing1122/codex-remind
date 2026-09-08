"""
WebSocket客户端模块
负责与中继服务器通信
"""

import asyncio
import json
import logging
import websockets
from typing import Optional

logger = logging.getLogger(__name__)


class WebSocketClient:
    """WebSocket客户端"""

    def __init__(self, server_url: str):
        self.server_url = server_url
        self.websocket: Optional[websockets.WebSocketClientProtocol] = None
        self.connected = False
        self.reconnect_interval = 5

    async def connect(self):
        """连接到WebSocket服务器"""
        while not self.connected:
            try:
                logger.info(f"正在连接WebSocket服务器: {self.server_url}")
                self.websocket = await websockets.connect(
                    self.server_url,
                    ping_interval=20,
                    ping_timeout=10
                )
                self.connected = True
                logger.info("✅ WebSocket已连接")

                # 发送握手消息
                await self.send_message({
                    'type': 'handshake',
                    'client': 'windows',
                    'timestamp': int(asyncio.get_event_loop().time() * 1000)
                })

                # 启动接收任务
                asyncio.create_task(self._receive_messages())

            except Exception as e:
                logger.error(f"WebSocket连接失败: {e}")
                logger.info(f"将在 {self.reconnect_interval} 秒后重试...")
                await asyncio.sleep(self.reconnect_interval)

    async def _receive_messages(self):
        """接收服务器消息"""
        try:
            async for message in self.websocket:
                await self._handle_message(message)
        except websockets.exceptions.ConnectionClosed:
            logger.warning("WebSocket连接已关闭")
            self.connected = False
            await self.connect()
        except Exception as e:
            logger.error(f"接收消息出错: {e}")
            self.connected = False

    async def _handle_message(self, message: str):
        """处理接收到的消息"""
        try:
            data = json.loads(message)
            logger.debug(f"收到消息: {data}")

            # 处理服务器消息（如配置更新、控制命令等）
            if data.get('type') == 'ping':
                await self.send_message({'type': 'pong'})
            elif data.get('type') == 'config_update':
                logger.info("收到配置更新")

        except json.JSONDecodeError as e:
            logger.error(f"消息解析失败: {e}")

    async def send_message(self, data: dict):
        """发送消息到服务器"""
        if not self.connected or not self.websocket:
            logger.warning("WebSocket未连接，消息未发送")
            return

        try:
            message = json.dumps(data, ensure_ascii=False)
            await self.websocket.send(message)
            logger.debug(f"已发送: {data.get('type', 'unknown')}")

        except Exception as e:
            logger.error(f"发送消息失败: {e}")
            self.connected = False

    async def close(self):
        """关闭连接"""
        if self.websocket:
            await self.websocket.close()
            logger.info("WebSocket连接已关闭")
