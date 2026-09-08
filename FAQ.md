# 常见问题解答 (FAQ)

## 安装和配置

### Q1: 需要什么前置条件？

**Android手机：**
- ✅ 已root（Magisk或KernelSU）
- ✅ 安装LSPosed框架
- ✅ ColorOS 16或其他Android 11+系统

**Windows电脑：**
- ✅ Python 3.10或更高版本
- ✅ 网络连接

**服务器：**
- ✅ 可选：云服务器或本地电脑
- ✅ Python 3.10+
- ✅ 开放8765端口

### Q2: 必须使用ColorOS吗？

不是必须的。项目设计为通用的Android通知系统，理论上支持所有Android 11+的ROM。ColorOS的流体云功能是额外的优化目标。

### Q3: 可以不用云服务器吗？

可以。如果Windows和手机在同一局域网（WiFi），可以直接在Windows上运行中继服务器。

## 连接问题

### Q4: WebSocket连接失败怎么办？

**检查步骤：**

1. **确认服务器运行**
   ```bash
   # 查看服务器日志
   python relay_server.py
   ```

2. **测试网络连通性**
   ```bash
   # Windows PowerShell
   Test-NetConnection -ComputerName SERVER_IP -Port 8765
   
   # 或使用telnet
   telnet SERVER_IP 8765
   ```

3. **检查防火墙**
   ```bash
   # Windows防火墙
   # 控制面板 → Windows Defender防火墙 → 高级设置 → 入站规则
   # 添加8765端口规则
   
   # Linux
   sudo ufw allow 8765
   ```

4. **确认IP地址正确**
   - Android模块中的配置
   - Windows客户端中的配置
   - 必须使用实际IP，不能用localhost

### Q5: 显示"连接成功"但收不到通知？

**排查方法：**

1. **查看Android日志**
   ```bash
   adb logcat | grep ClaudeNotify
   ```
   
2. **检查消息是否发送**
   ```bash
   # 运行测试脚本
   cd tools
   python test_client.py
   ```

3. **确认通知权限**
   - 设置 → 应用 → 权限管理
   - 检查通知权限是否开启

## LSPosed相关

### Q6: LSPosed模块未激活？

**解决步骤：**

1. 打开LSPosed管理器
2. 找到"Claude Notify"模块
3. 确保勾选了启用
4. 作用域必须包含：
   - ✅ 系统框架 (android)
   - ✅ 系统界面 (com.android.systemui)
5. 点击"重新启动作用域"
6. 或完全重启手机

### Q7: 如何查看Xposed日志？

**方法1：LSPosed管理器**
- 打开LSPosed → 日志 → 查看详细日志

**方法2：ADB命令**
```bash
adb logcat -s ClaudeNotify:* Xposed:*
```

**方法3：保存到文件**
```bash
adb logcat -s ClaudeNotify:* > claude.log
```

### Q8: 模块安装后没有图标？

这是正常的。LSPosed模块不需要用户界面，它在后台工作。所有配置通过修改代码完成。

## 监控问题

### Q9: Windows端没有检测到Claude Code的活动？

**检查项：**

1. **监控路径是否正确**
   ```json
   // config.json
   {
     "monitor_path": "C:\\Users\\YOUR_NAME\\.claude"
   }
   ```

2. **Claude Code是否在运行任务**
   - 执行一些命令测试
   - 查看 `.claude` 目录是否有新文件

3. **文件监控是否工作**
   ```bash
   # 查看日志
   python monitor.py
   # 应该显示"文件监控已启动"
   ```

### Q10: 如何自定义监控的内容？

编辑 [monitor.py](windows/monitor.py)，修改 `on_file_change` 方法：

```python
async def on_file_change(self, event_type: str, file_path: str):
    # 添加自定义过滤
    if 'ignore_this' in file_path:
        return
    
    # 添加自定义处理
    # ...
```

## 通知相关

### Q11: 通知样式如何自定义？

编辑 [FluidCloudInjector.kt](app/src/main/java/com/claude/notify/FluidCloudInjector.kt)：

```kotlin
private fun buildNotification(...): Notification {
    builder.apply {
        // 修改颜色
        setColor(Color.parseColor("#YOUR_COLOR"))
        
        // 修改图标
        setSmallIcon(R.drawable.your_icon)
        
        // 添加动作按钮
        addAction(...)
    }
}
```

### Q12: 可以添加声音和震动吗？

可以。在构建通知时添加：

```kotlin
builder.apply {
    setSound(RingtoneManager.getDefaultUri(RingtoneManager.TYPE_NOTIFICATION))
    setVibrate(longArrayOf(0, 500, 200, 500))
}
```

### Q13: 如何让通知持久显示？

```kotlin
builder.apply {
    setOngoing(true)  // 不可滑动清除
    setAutoCancel(false)  // 点击不自动消失
}
```

## 性能和稳定性

### Q14: 会不会很耗电？

影响不大。主要功耗来自：
- WebSocket长连接（很小）
- 文件监控（Windows端）

建议：
- 使用WiFi而非移动网络
- 不用时关闭Windows监控

### Q15: 会影响系统稳定性吗？

LSPosed模块理论上不会影响系统稳定性，因为：
- 使用标准Android API
- 错误处理完善
- 不修改系统文件

但建议：
- 在测试机上先试用
- 定期查看日志
- 遇到问题及时禁用

### Q16: 消息延迟多久？

正常情况下：
- 本地网络：< 100ms
- 公网服务器：100-500ms

影响因素：
- 网络质量
- 服务器性能
- 文件监控频率

## 开发相关

### Q17: 如何添加新的消息类型？

1. 在 [tools/PROTOCOL.md](tools/PROTOCOL.md) 定义协议
2. Windows端发送 [monitor.py](windows/monitor.py)
3. Android端接收 [WebSocketManager.kt](app/src/main/java/com/claude/notify/WebSocketManager.kt)
4. 显示通知 [FluidCloudInjector.kt](app/src/main/java/com/claude/notify/FluidCloudInjector.kt)

### Q18: 如何调试Android模块？

```bash
# 实时查看日志
adb logcat -s ClaudeNotify:V

# 安装调试版本
./gradlew installDebug

# 使用Android Studio的调试器（需要root）
```

### Q19: 源码在哪里修改服务器地址？

**Android端：**
[app/src/main/java/com/claude/notify/WebSocketManager.kt:20](app/src/main/java/com/claude/notify/WebSocketManager.kt#L20)

```kotlin
private var serverUrl = "ws://YOUR_IP:8765"
```

**Windows端：**
[windows/config.json](windows/config.json)

```json
{
  "websocket_server": "ws://YOUR_IP:8765"
}
```

## 安全和隐私

### Q20: 数据安全吗？

当前版本使用未加密的WebSocket (ws://)，建议：

**生产环境：**
- 使用WSS (WebSocket Secure)
- 添加token认证
- 使用VPN

**开发测试：**
- 局域网使用可接受
- 不传输敏感数据

### Q21: 会收集用户数据吗？

不会。所有数据：
- 仅在你的设备间传输
- 不上传到任何第三方服务器
- 源代码完全开放

## 故障排除

### Q22: 完全不工作，如何系统排查？

**第一步：检查服务器**
```bash
cd tools
python relay_server.py
# 应该显示"服务器已启动"
```

**第二步：测试服务器**
```bash
python test_client.py
# 应该显示"连接成功"
```

**第三步：检查Windows客户端**
```bash
cd windows
python monitor.py
# 应该显示"WebSocket已连接"
```

**第四步：检查Android**
```bash
adb logcat | grep ClaudeNotify
# 应该看到"WebSocket connected"
```

**第五步：端到端测试**
- 运行test_client.py
- 查看手机是否收到通知

### Q23: 遇到错误如何报告？

提供以下信息：

1. **环境信息**
   - Android版本和ROM
   - Windows版本
   - Python版本

2. **日志**
   ```bash
   # Android
   adb logcat -s ClaudeNotify:* > android.log
   
   # Windows
   python monitor.py 2>&1 | tee windows.log
   
   # 服务器
   python relay_server.py 2>&1 | tee server.log
   ```

3. **错误描述**
   - 期望行为
   - 实际行为
   - 复现步骤

---

## 更多问题？

- 查看 [README.md](README.md)
- 阅读 [DEPLOY.md](DEPLOY.md)
- 查看 [CONTRIBUTING.md](CONTRIBUTING.md)
- 提交Issue到GitHub
