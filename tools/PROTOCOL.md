# 通信协议定义

## 消息格式

所有消息均为JSON格式：

```json
{
  "type": "message_type",
  "timestamp": 1234567890000,
  "data": {
    "key": "value"
  }
}
```

## 消息类型

### 1. 握手 (handshake)

**客户端 → 服务器**

```json
{
  "type": "handshake",
  "client": "windows" | "android",
  "timestamp": 1234567890000
}
```

**服务器 → 客户端**

```json
{
  "type": "handshake_ack",
  "status": "connected"
}
```

### 2. 任务开始 (task_start)

**Windows → Android**

```json
{
  "type": "task_start",
  "timestamp": 1234567890000,
  "data": {
    "task": "任务名称",
    "description": "任务描述"
  }
}
```

### 3. 任务进度 (task_progress)

**Windows → Android**

```json
{
  "type": "task_progress",
  "timestamp": 1234567890000,
  "data": {
    "progress": 50,
    "description": "正在执行步骤X..."
  }
}
```

### 4. 任务完成 (task_complete)

**Windows → Android**

```json
{
  "type": "task_complete",
  "timestamp": 1234567890000,
  "data": {
    "result": "任务完成/失败信息"
  }
}
```

### 5. 命令输出 (command_output)

**Windows → Android**

```json
{
  "type": "command_output",
  "timestamp": 1234567890000,
  "data": {
    "output": "命令输出文本"
  }
}
```

### 6. 心跳 (ping/pong)

**客户端 → 服务器**

```json
{
  "type": "ping"
}
```

**服务器 → 客户端**

```json
{
  "type": "pong"
}
```

## 状态码

- `connected`: 已连接
- `disconnected`: 已断开
- `error`: 错误
