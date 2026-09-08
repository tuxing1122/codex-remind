# Windows 监控客户端

监控Claude Code的执行状态并通过WebSocket推送到手机。

## 功能

- 监控Claude Code任务执行
- 捕获命令输出
- 实时推送状态到手机

## 安装

```bash
pip install -r requirements.txt
```

## 配置

编辑 `config.json`:

```json
{
  "websocket_server": "ws://your-server:8765",
  "monitor_path": "C:\\Users\\YourUser\\.claude",
  "poll_interval": 1
}
```

## 运行

```bash
python monitor.py
```

## 架构

```
monitor.py          # 主程序入口
├── file_watcher.py # 文件监控
├── task_parser.py  # 任务解析
└── ws_client.py    # WebSocket客户端
```
