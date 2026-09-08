"""
Claude Code 执行状态监控器
监控 .claude 目录变化并推送执行状态
"""

import asyncio
import json
import logging
import os
import sys
from pathlib import Path
from datetime import datetime

from file_watcher import FileWatcher
from task_parser import TaskParser
from ws_client import WebSocketClient

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('monitor.log', encoding='utf-8')
    ]
)

logger = logging.getLogger(__name__)


class ClaudeMonitor:
    """Claude Code监控器主类"""

    def __init__(self, config_path: str = "config.json"):
        self.config = self._load_config(config_path)
        self.ws_client = None
        self.file_watcher = None
        self.task_parser = TaskParser()
        self.current_task = None

    def _load_config(self, config_path: str) -> dict:
        """加载配置文件"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"配置已加载: {config_path}")
                return config
        except FileNotFoundError:
            logger.error(f"配置文件不存在: {config_path}")
            sys.exit(1)
        except json.JSONDecodeError as e:
            logger.error(f"配置文件格式错误: {e}")
            sys.exit(1)

    async def start(self):
        """启动监控服务"""
        logger.info("=" * 50)
        logger.info("Claude Code Monitor 启动中...")
        logger.info("=" * 50)

        # 连接WebSocket服务器
        self.ws_client = WebSocketClient(self.config['websocket_server'])
        await self.ws_client.connect()

        # 启动文件监控
        self.file_watcher = FileWatcher(
            self.config['monitor_path'],
            self.on_file_change
        )
        self.file_watcher.start()

        logger.info(f"监控路径: {self.config['monitor_path']}")
        logger.info(f"WebSocket: {self.config['websocket_server']}")
        logger.info("监控已启动，等待任务...")

        # 保持运行
        try:
            while True:
                await asyncio.sleep(1)
        except KeyboardInterrupt:
            logger.info("收到退出信号，正在关闭...")
            await self.stop()

    async def on_file_change(self, event_type: str, file_path: str):
        """文件变化回调"""
        try:
            logger.debug(f"文件变化: {event_type} - {file_path}")

            # 解析任务状态
            path = Path(file_path)

            # 检测任务文件
            if path.name.endswith('.task.json'):
                await self._handle_task_file(path)

            # 检测输出文件
            elif path.name.endswith('.output') or path.name.endswith('.log'):
                await self._handle_output_file(path)

            # 检测会话文件
            elif 'sessions' in path.parts:
                await self._handle_session_file(path)

        except Exception as e:
            logger.error(f"处理文件变化时出错: {e}", exc_info=True)

    async def _handle_task_file(self, path: Path):
        """处理任务文件"""
        try:
            with open(path, 'r', encoding='utf-8') as f:
                task_data = json.load(f)

            task = self.task_parser.parse_task(task_data)

            if task['status'] == 'running' and self.current_task != task['id']:
                # 新任务开始
                self.current_task = task['id']
                await self.ws_client.send_message({
                    'type': 'task_start',
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'data': {
                        'task': task['name'],
                        'description': task.get('description', '')
                    }
                })
                logger.info(f"📌 任务开始: {task['name']}")

            elif task['status'] == 'completed':
                # 任务完成
                await self.ws_client.send_message({
                    'type': 'task_complete',
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'data': {
                        'result': task.get('result', '任务已完成')
                    }
                })
                logger.info(f"✅ 任务完成: {task['name']}")
                self.current_task = None

            elif task['status'] == 'failed':
                # 任务失败
                await self.ws_client.send_message({
                    'type': 'task_complete',
                    'timestamp': int(datetime.now().timestamp() * 1000),
                    'data': {
                        'result': f"❌ 失败: {task.get('error', 'Unknown error')}"
                    }
                })
                logger.warning(f"❌ 任务失败: {task['name']}")
                self.current_task = None

        except Exception as e:
            logger.error(f"处理任务文件出错: {e}")

    async def _handle_output_file(self, path: Path):
        """处理输出文件"""
        try:
            # 读取最后几行输出
            with open(path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
                if lines:
                    # 取最后5行
                    recent_output = ''.join(lines[-5:]).strip()
                    if recent_output:
                        await self.ws_client.send_message({
                            'type': 'command_output',
                            'timestamp': int(datetime.now().timestamp() * 1000),
                            'data': {
                                'output': recent_output
                            }
                        })
                        logger.debug(f"📟 命令输出: {recent_output[:50]}...")
        except Exception as e:
            logger.error(f"处理输出文件出错: {e}")

    async def _handle_session_file(self, path: Path):
        """处理会话文件"""
        try:
            # 检测活跃会话
            if path.name == 'active':
                with open(path, 'r', encoding='utf-8') as f:
                    session_id = f.read().strip()
                    logger.info(f"🔄 活跃会话: {session_id}")
        except Exception as e:
            logger.error(f"处理会话文件出错: {e}")

    async def stop(self):
        """停止监控服务"""
        if self.file_watcher:
            self.file_watcher.stop()
        if self.ws_client:
            await self.ws_client.close()
        logger.info("监控服务已停止")


async def main():
    """主函数"""
    monitor = ClaudeMonitor()
    await monitor.start()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n程序已退出")
