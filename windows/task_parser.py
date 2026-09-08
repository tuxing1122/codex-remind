"""
任务解析模块
解析Claude任务状态和输出
"""

import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class TaskParser:
    """任务解析器"""

    def __init__(self):
        self.task_cache = {}

    def parse_task(self, task_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        解析任务数据

        Args:
            task_data: 任务JSON数据

        Returns:
            标准化的任务对象
        """
        try:
            task = {
                'id': task_data.get('id', 'unknown'),
                'name': task_data.get('name', 'Unnamed Task'),
                'status': task_data.get('status', 'unknown'),
                'description': task_data.get('description', ''),
                'progress': task_data.get('progress', 0),
                'result': task_data.get('result'),
                'error': task_data.get('error'),
                'timestamp': task_data.get('timestamp')
            }

            # 缓存任务
            self.task_cache[task['id']] = task

            return task

        except Exception as e:
            logger.error(f"解析任务数据失败: {e}")
            return {
                'id': 'error',
                'name': 'Parse Error',
                'status': 'failed',
                'error': str(e)
            }

    def parse_output(self, output: str) -> Dict[str, Any]:
        """
        解析命令输出

        Args:
            output: 命令输出文本

        Returns:
            解析后的输出信息
        """
        lines = output.strip().split('\n')

        return {
            'raw': output,
            'lines': lines,
            'line_count': len(lines),
            'preview': lines[-5:] if len(lines) > 5 else lines
        }

    def extract_progress(self, output: str) -> int:
        """
        从输出中提取进度

        Args:
            output: 输出文本

        Returns:
            进度百分比 (0-100)
        """
        # 简单的进度提取逻辑
        # 可以根据实际输出格式进行调整

        import re

        # 匹配 "50%" 或 "Progress: 50"
        patterns = [
            r'(\d+)%',
            r'[Pp]rogress:\s*(\d+)',
            r'\[(\d+)/\d+\]'
        ]

        for pattern in patterns:
            match = re.search(pattern, output)
            if match:
                try:
                    progress = int(match.group(1))
                    return min(100, max(0, progress))
                except ValueError:
                    pass

        return 0
