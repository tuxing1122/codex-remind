"""
文件监控模块
使用 watchdog 监控目录变化
"""

import logging
import time
from pathlib import Path
from watchdog.observers import Observer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
import asyncio
from typing import Callable

logger = logging.getLogger(__name__)


class ClaudeFileHandler(FileSystemEventHandler):
    """Claude文件事件处理器"""

    def __init__(self, callback: Callable):
        self.callback = callback
        self.loop = None

    def set_loop(self, loop):
        """设置事件循环"""
        self.loop = loop

    def on_modified(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle_event('modified', event.src_path)

    def on_created(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle_event('created', event.src_path)

    def on_deleted(self, event: FileSystemEvent):
        if not event.is_directory:
            self._handle_event('deleted', event.src_path)

    def _handle_event(self, event_type: str, file_path: str):
        """处理事件"""
        if self.loop and self.callback:
            asyncio.run_coroutine_threadsafe(
                self.callback(event_type, file_path),
                self.loop
            )


class FileWatcher:
    """文件监控器"""

    def __init__(self, watch_path: str, callback: Callable):
        self.watch_path = Path(watch_path)
        self.callback = callback
        self.observer = None
        self.handler = ClaudeFileHandler(callback)

        # 确保监控路径存在
        if not self.watch_path.exists():
            logger.warning(f"监控路径不存在，尝试创建: {self.watch_path}")
            self.watch_path.mkdir(parents=True, exist_ok=True)

    def start(self):
        """启动文件监控"""
        try:
            # 设置事件循环
            self.handler.set_loop(asyncio.get_event_loop())

            self.observer = Observer()
            self.observer.schedule(
                self.handler,
                str(self.watch_path),
                recursive=True
            )
            self.observer.start()
            logger.info(f"文件监控已启动: {self.watch_path}")

        except Exception as e:
            logger.error(f"启动文件监控失败: {e}")
            raise

    def stop(self):
        """停止文件监控"""
        if self.observer:
            self.observer.stop()
            self.observer.join()
            logger.info("文件监控已停止")
