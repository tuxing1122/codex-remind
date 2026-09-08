# 快速启动指南

## 3分钟快速测试

### 1. 启动服务器（选择一个）

**Windows:**
```bash
cd tools
python relay_server.py
```

**Linux/Mac:**
```bash
cd tools
./start_server.sh
```

### 2. 获取服务器IP

**Windows:**
```bash
ipconfig
# 查找 IPv4 地址，如 192.168.1.100
```

**Linux/Mac:**
```bash
ifconfig
# 或
ip addr
```

### 3. 修改配置

**Android模块配置：**

编辑 [app/src/main/java/com/claude/notify/WebSocketManager.kt:20](app/src/main/java/com/claude/notify/WebSocketManager.kt#L20)

```kotlin
private var serverUrl = "ws://192.168.1.100:8765"  // 改成你的IP
```

**Windows客户端配置：**

编辑 [windows/config.json](windows/config.json)

```json
{
  "websocket_server": "ws://192.168.1.100:8765"  // 改成你的IP
}
```

### 4. 编译Android模块

```bash
# Windows
gradlew.bat assembleRelease

# Linux/Mac
./gradlew assembleRelease
```

输出：`app/build/outputs/apk/release/app-release.apk`

### 5. 安装并激活

1. 在手机上安装APK
2. 打开LSPosed管理器
3. 激活"Claude Notify"模块
4. 勾选作用域：android, com.android.systemui
5. 重启系统服务

### 6. 测试

**启动Windows监控：**
```bash
cd windows
python monitor.py
# 或双击 start.bat
```

**发送测试消息：**
```bash
cd tools
python test_client.py
```

手机应该收到通知！ 🎉

## 检查清单

启动前确保：

- [ ] Python 3.10+ 已安装
- [ ] 手机已root并安装LSPosed
- [ ] 手机和电脑在同一网络
- [ ] 防火墙允许8765端口
- [ ] 服务器地址配置正确

## 常见问题

**Q: 连接不上服务器？**  
A: 检查IP地址、防火墙、网络连通性

**Q: 没有收到通知？**  
A: 查看 `adb logcat | grep ClaudeNotify` 日志

**Q: LSPosed模块未激活？**  
A: 确保勾选了正确的作用域并重启

## 完整文档

详细部署指南：[DEPLOY.md](DEPLOY.md)

## 获取帮助

1. 检查日志文件
2. 运行测试脚本
3. 查看协议文档
