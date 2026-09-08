#!/usr/bin/env python3
"""
快速测试脚本
发送测试消息到服务器
"""

import asyncio
import json
import websockets

async def test():
    uri = "ws://localhost:8765"

    print(f"正在连接到 {uri}...")

    try:
        async with websockets.connect(uri) as websocket:
            print("✅ 连接成功")

            # 发送握手
            await websocket.send(json.dumps({
                'type': 'handshake',
                'client': 'windows'
            }))
            print("📤 已发送握手")

            # 接收响应
            response = await websocket.recv()
            print(f"📥 收到响应: {response}")

            # 发送测试任务
            print("\n发送测试消息...")

            # 任务开始
            await websocket.send(json.dumps({
                'type': 'task_start',
                'timestamp': 1234567890000,
                'data': {
                    'task': '测试任务',
                    'description': '这是一个测试任务'
                }
            }))
            print("📤 任务开始")
            await asyncio.sleep(2)

            # 任务进度
            for progress in [25, 50, 75]:
                await websocket.send(json.dumps({
                    'type': 'task_progress',
                    'timestamp': 1234567890000,
                    'data': {
                        'progress': progress,
                        'description': f'执行中... {progress}%'
                    }
                }))
                print(f"📤 进度: {progress}%")
                await asyncio.sleep(1)

            # 命令输出
            await websocket.send(json.dumps({
                'type': 'command_output',
                'timestamp': 1234567890000,
                'data': {
                    'output': 'Hello from test script!\nThis is a test output.'
                }
            }))
            print("📤 命令输出")
            await asyncio.sleep(1)

            # 任务完成
            await websocket.send(json.dumps({
                'type': 'task_complete',
                'timestamp': 1234567890000,
                'data': {
                    'result': '✅ 测试任务完成'
                }
            }))
            print("📤 任务完成")

            print("\n✅ 测试完成！检查手机是否收到通知。")

    except Exception as e:
        print(f"❌ 错误: {e}")

if __name__ == "__main__":
    asyncio.run(test())
