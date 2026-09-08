#!/usr/bin/env python3
"""
WebSocket中继服务器
在Windows客户端和Android手机之间转发消息
"""

import asyncio
import json
import logging
import sys
from datetime import datetime
from typing import Set
import websockets
from websockets.server import WebSocketServerProtocol

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger(__name__)


class RelayServer:
    """WebSocket中继服务器"""

    def __init__(self, host: str = "0.0.0.0", port: int = 8765):
        self.host = host
        self.port = port
        self.windows_clients: Set[WebSocketServerProtocol] = set()
        self.android_clients: Set[WebSocketServerProtocol] = set()

    async def handler(self, websocket: WebSocketServerProtocol, path: str):
        """处理WebSocket连接"""
        client_type = None

        try:
            logger.info(f"新连接来自: {websocket.remote_address}")

            async for message in websocket:
                try:
                    data = json.loads(message)
                    msg_type = data.get('type')

                    # 处理握手消息
                    if msg_type == 'handshake':
                        client_type = data.get('client')
                        if client_type == 'windows':
                            self.windows_clients.add(websocket)
                            logger.info(f"✅ Windows客户端已连接 (总计: {len(self.windows_clients)})")
                        elif client_type == 'android':
                            self.android_clients.add(websocket)
                            logger.info(f"✅ Android客户端已连接 (总计: {len(self.android_clients)})")

                        # 发送确认
                        await websocket.send(json.dumps({
                            'type': 'handshake_ack',
                            'status': 'connected'
                        }))

                    # 转发消息
                    elif msg_type in ['task_start', 'task_progress', 'task_complete', 'command_output']:
                        # 从Windows转发到Android
                        if websocket in self.windows_clients:
                            await self._broadcast_to_android(message)
                            logger.info(f"📤 转发消息: {msg_type}")

                    # 处理ping
                    elif msg_type == 'ping':
                        await websocket.send(json.dumps({'type': 'pong'}))

                except json.JSONDecodeError:
                    logger.error(f"消息解析失败: {message}")
                except Exception as e:
                    logger.error(f"处理消息出错: {e}")

        except websockets.exceptions.ConnectionClosed:
            logger.info(f"连接关闭: {websocket.remote_address}")
        finally:
            # 清理连接
            if websocket in self.windows_clients:
                self.windows_clients.remove(websocket)
                logger.info(f"Windows客户端断开 (剩余: {len(self.windows_clients)})")
            if websocket in self.android_clients:
                self.android_clients.remove(websocket)
                logger.info(f"Android客户端断开 (剩余: {len(self.android_clients)})")

    async def _broadcast_to_android(self, message: str):
        """广播消息到所有Android客户端"""
        if not self.android_clients:
            logger.warning("没有Android客户端在线")
            return

        disconnected = set()

        for client in self.android_clients:
            try:
                await client.send(message)
            except Exception as e:
                logger.error(f"发送到Android客户端失败: {e}")
                disconnected.add(client)

        # 清理断开的连接
        self.android_clients -= disconnected

    async def _broadcast_to_windows(self, message: str):
        """广播消息到所有Windows客户端"""
        if not self.windows_clients:
            return

        disconnected = set()

        for client in self.windows_clients:
            try:
                await client.send(message)
            except Exception as e:
                logger.error(f"发送到Windows客户端失败: {e}")
                disconnected.add(client)

        # 清理断开的连接
        self.windows_clients -= disconnected

    async def start(self):
        """启动服务器"""
        logger.info("=" * 50)
        logger.info("WebSocket中继服务器启动中...")
        logger.info(f"监听地址: {self.host}:{self.port}")
        logger.info("=" * 50)

        async with websockets.serve(self.handler, self.host, self.port):
            logger.info("✅ 服务器已启动，等待连接...")
            await asyncio.Future()  # 永久运行

    def get_status(self) -> dict:
        """获取服务器状态"""
        return {
            'windows_clients': len(self.windows_clients),
            'android_clients': len(self.android_clients),
            'total_clients': len(self.windows_clients) + len(self.android_clients)
        }


async def main():
    """主函数"""
    server = RelayServer(host="0.0.0.0", port=8765)

    try:
        await server.start()
    except KeyboardInterrupt:
        logger.info("\n服务器正在关闭...")
    except Exception as e:
        logger.error(f"服务器错误: {e}", exc_info=True)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已退出")
