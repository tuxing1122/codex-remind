# Codex Desktop 状态监听器

这个 Windows 监听器会跟踪 `%USERPROFILE%\.codex\sessions` 下的 Codex Desktop 会话
JSONL 文件，并通过 TCP `24680` 端口把任务状态发送到手机端 LSPosed 模块。程序只使用
Python 标准库，不需要安装 pip 依赖。

## 配置与启动

1. 使用 Python 3.10 或更高版本。
2. 编辑被 Git 忽略的 `config.local.json`，把 `phone_host` 改成手机局域网 IP。
3. 保持其中至少 32 字符的 `token` 与构建 LSPosed 模块时的 token 完全一致。仓库示例值会被拒绝。
4. 在开始 Codex 任务前运行 `start-watcher.ps1` 或 `start-watcher.bat`。

默认情况下，监听器从启动时已有文件的末尾开始，只处理后续新增事件，不回放旧任务。启动后
新建的会话文件会从头读取。只有调试时才使用 `--replay-existing`。

默认忽略独立子代理的会话文件，避免它们的终态覆盖根任务；根会话中的
`SubAgentActivity` 进度仍会转发。

只验证解析、不连接手机：

```powershell
.\start-watcher.ps1 -WatcherArguments '--dry-run'
```

只扫描一次并退出：

```powershell
.\start-watcher.ps1 -WatcherArguments '--once', '--dry-run', '--replay-existing'
```

运行测试：

```powershell
python -m unittest discover -s tests -v
```

手机模块安装完成后，发送开始、50% 和完成三阶段测试事件：

```powershell
python .\send_test_event.py
```

## 解析的事件

- `event_msg`：`task_started`、`task_complete` 和 `turn_aborted`。
- `event_msg.item_completed`：`CommandExecution`、`FileChange` 和 `SubAgentActivity`。
- `response_item`：`function_call` 和 `custom_tool_call` 工具启动事件。

隐私边界是刻意限制的：不会转发对话、推理、命令参数、stdout/stderr、路径、文件名、文件
内容、diff、完整工具参数或工具结果。命令状态只包含可执行文件名。

监听器会添加 `token`、`event_id`、`session_id`、`task_id`、`phase`，以及手机端兼容字段
`type`、`title`、`message` 和 `percent`。手机应返回 `{"ok":true}`。

未收到 ACK 的事件会原子保存到 `spool_path`，监听器重启后继续发送。终态会替换同一任务的
旧进度并优先发送。队列满时，终态可淘汰旧进度；新进度只有能替换同一任务的旧进度时才会
保留。

TCP 负载经过认证但没有加密。只在可信局域网使用；也可执行
`adb forward tcp:24680 tcp:24680` 并把 `phone_host` 改成 `127.0.0.1`，通过 ADB 通道测试。
不要通过路由器暴露 `24680` 端口。
