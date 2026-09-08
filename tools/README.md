# 工具和服务

本目录包含中继服务器和共享工具。

## relay_server.py

WebSocket中继服务器，负责在Windows和Android之间转发消息。

### 运行

```bash
python relay_server.py
```

服务器将在 `0.0.0.0:8765` 监听连接。

### 要求

- Python 3.10+
- websockets

```bash
pip install websockets
```

## 部署建议

### 本地网络

如果Windows电脑和Android手机在同一局域网：

1. 在Windows电脑运行中继服务器
2. 获取Windows电脑的局域网IP（如 192.168.1.100）
3. 配置Android模块连接到该IP

### 云服务器

如果需要跨网络访问：

1. 将 `relay_server.py` 部署到云服务器
2. 配置防火墙开放端口 8765
3. Windows和Android都连接到服务器的公网IP

推荐使用：
- 阿里云ECS
- 腾讯云CVM
- AWS EC2

### Docker部署

```dockerfile
FROM python:3.11-slim

WORKDIR /app
RUN pip install websockets

COPY relay_server.py .

EXPOSE 8765

CMD ["python", "relay_server.py"]
```

```bash
docker build -t claude-relay .
docker run -d -p 8765:8765 claude-relay
```
