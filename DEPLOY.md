# 完整部署指南

本指南将帮助你从零开始部署整个系统。

## 系统架构

```
┌─────────────┐         WebSocket         ┌─────────────┐
│   Windows   │ ◄───────────────────────► │   服务器    │
│  监控客户端  │                           │  中继服务器  │
└─────────────┘                           └─────────────┘
                                                ▲
                                                │ WebSocket
                                                ▼
                                          ┌─────────────┐
                                          │   Android   │
                                          │ LSPosed模块 │
                                          └─────────────┘
```

## 第一步：部署中继服务器

### 选项A：本地网络（推荐测试）

如果Windows和Android在同一WiFi：

```bash
# 在Windows上运行
cd tools
python relay_server.py
```

记录Windows的局域网IP（如 192.168.1.100）。

### 选项B：云服务器（推荐生产）

1. **购买服务器**
   - 推荐：阿里云、腾讯云、AWS
   - 配置：1核1G即可
   - 系统：Ubuntu 22.04

2. **安装依赖**
   ```bash
   ssh user@your-server
   sudo apt update
   sudo apt install python3 python3-pip -y
   pip3 install websockets
   ```

3. **上传服务器**
   ```bash
   scp tools/relay_server.py user@your-server:~/
   ```

4. **运行服务**
   ```bash
   # 测试运行
   python3 relay_server.py
   
   # 或使用nohup后台运行
   nohup python3 relay_server.py > relay.log 2>&1 &
   ```

5. **配置防火墙**
   ```bash
   # 开放8765端口
   sudo ufw allow 8765
   ```

### 选项C：Docker部署

```bash
cd tools

# 构建镜像
docker build -t claude-relay -f- . <<EOF
FROM python:3.11-slim
RUN pip install websockets
COPY relay_server.py /app/
WORKDIR /app
EXPOSE 8765
CMD ["python", "relay_server.py"]
EOF

# 运行容器
docker run -d -p 8765:8765 --name relay --restart always claude-relay
```

## 第二步：配置Windows监控端

1. **安装Python依赖**
   ```bash
   cd windows
   pip install -r requirements.txt
   ```

2. **修改配置文件**
   
   编辑 [windows/config.json](windows/config.json):
   
   ```json
   {
     "websocket_server": "ws://YOUR_SERVER_IP:8765",
     "monitor_path": "C:\\Users\\YOUR_USERNAME\\.claude",
     "poll_interval": 1
   }
   ```
   
   替换：
   - `YOUR_SERVER_IP`: 服务器IP地址
   - `YOUR_USERNAME`: 你的Windows用户名

3. **测试运行**
   ```bash
   python monitor.py
   ```
   
   应该看到：
   ```
   ✅ WebSocket已连接
   监控已启动，等待任务...
   ```

4. **设置开机自启（可选）**
   
   创建启动脚本 `start_monitor.bat`:
   ```batch
   @echo off
   cd /d C:\Users\gmy15\Documents\ChatGPT\remind\windows
   python monitor.py
   pause
   ```
   
   将快捷方式放入启动文件夹：
   ```
   Win+R → shell:startup
   ```

## 第三步：编译Android模块

### 方法A：Android Studio（推荐）

1. **打开项目**
   - 启动Android Studio
   - Open → 选择 `remind` 目录

2. **等待Gradle同步完成**

3. **编译APK**
   - Build → Build Bundle(s) / APK(s) → Build APK(s)
   - 输出位置：`app/build/outputs/apk/release/app-release.apk`

### 方法B：命令行

```bash
# Windows
cd remind
gradlew.bat assembleRelease

# Linux/Mac
./gradlew assembleRelease
```

## 第四步：安装Android模块

### 前置条件检查

✅ 手机已root  
✅ 已安装Magisk或KernelSU  
✅ 已安装LSPosed框架

### 安装步骤

1. **传输APK到手机**
   ```bash
   adb push app/build/outputs/apk/release/app-release.apk /sdcard/
   ```
   或通过其他方式传输

2. **安装APK**
   ```bash
   adb install app/build/outputs/apk/release/app-release.apk
   ```
   或在手机上直接安装

3. **激活LSPosed模块**
   - 打开LSPosed管理器
   - 模块 → 找到"Claude Notify"
   - 勾选启用
   - 作用域选择：
     * ✅ 系统框架 (android)
     * ✅ 系统界面 (com.android.systemui)
     * ✅ ColorOS服务 (如果有)
   - 点击"重新启动作用域"

4. **配置服务器地址**
   
   ⚠️ **重要**：需要修改代码中的服务器地址
   
   编辑 [app/src/main/java/com/claude/notify/WebSocketManager.kt:20](app/src/main/java/com/claude/notify/WebSocketManager.kt#L20):
   
   ```kotlin
   private var serverUrl = "ws://YOUR_SERVER_IP:8765"
   ```
   
   然后重新编译安装。

## 第五步：测试系统

### 1. 检查服务器状态

服务器应显示：
```
WebSocket中继服务器启动中...
✅ 服务器已启动，等待连接...
```

### 2. 启动Windows监控

```bash
cd windows
python monitor.py
```

应该看到：
```
✅ WebSocket已连接
监控已启动，等待任务...
```

### 3. 检查Android日志

```bash
adb logcat | grep ClaudeNotify
```

应该看到：
```
ClaudeNotify: Initializing WebSocket Manager
ClaudeNotify: WebSocket connected
```

### 4. 触发测试任务

在Claude Code中执行任何命令，例如：
```bash
echo "Hello from Claude"
```

手机应该收到通知！

## 故障排除

### Windows端无法连接

**检查项**：
- [ ] 服务器是否运行
- [ ] 配置文件中的IP地址是否正确
- [ ] 防火墙是否阻止连接
- [ ] 网络是否可达

**测试连接**：
```bash
# Windows PowerShell
Test-NetConnection -ComputerName YOUR_SERVER_IP -Port 8765
```

### Android端无法连接

**检查项**：
- [ ] LSPosed模块是否激活
- [ ] 作用域是否正确选择
- [ ] 系统服务是否重启
- [ ] 代码中的服务器地址是否修改

**查看日志**：
```bash
adb logcat -s ClaudeNotify:*
```

### 没有收到通知

**检查项**：
- [ ] 通知权限是否开启
- [ ] Windows监控是否检测到文件变化
- [ ] 消息是否成功发送（查看服务器日志）
- [ ] Android端是否成功接收（查看logcat）

## 性能优化

### 减少延迟

1. **使用本地网络**：Windows和Android在同一WiFi
2. **优化监控间隔**：调整 `config.json` 中的 `poll_interval`
3. **使用有线网络**：服务器端使用有线连接

### 降低资源消耗

1. **调整日志级别**：生产环境使用 INFO 或 WARNING
2. **限制监控范围**：只监控必要的目录
3. **批量发送**：合并短时间内的多条消息

## 安全建议

⚠️ **生产环境注意事项**

1. **使用HTTPS/WSS**
   ```python
   # 配置SSL证书
   ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
   ssl_context.load_cert_chain('cert.pem', 'key.pem')
   ```

2. **添加认证**
   - 在握手消息中加入token
   - 服务器端验证token

3. **限制访问**
   - 使用防火墙限制IP
   - 配置VPN连接

## 下一步

- [ ] 根据实际ColorOS版本优化通知样式
- [ ] 添加消息持久化
- [ ] 实现双向控制（手机控制Windows）
- [ ] 添加Web管理界面

## 获取帮助

- 查看日志文件
- 检查 [WINDOWS_PROTOCOL.md](WINDOWS_PROTOCOL.md)
- 阅读 [tools/PROTOCOL.md](tools/PROTOCOL.md)
