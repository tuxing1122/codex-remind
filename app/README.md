# Android LSPosed 模块

通过LSPosed框架hook ColorOS系统，实现Claude Code状态通知。

## 功能

- ✅ Hook系统通知服务
- ✅ 接收Windows端推送的任务状态
- ✅ 在流体云界面显示实时进度
- ✅ 无需独立App界面

## 编译

### 前置要求

- Android Studio Arctic Fox+
- JDK 17
- Gradle 8.2+

### 构建步骤

```bash
# 克隆仓库
cd remind

# 编译APK
./gradlew assembleRelease

# 输出位置
# app/build/outputs/apk/release/app-release.apk
```

## 安装与配置

### 1. 准备工作

确保手机已安装：
- ✅ LSPosed框架
- ✅ Magisk或KernelSU

### 2. 安装模块

```bash
adb install app/build/outputs/apk/release/app-release.apk
```

或直接在手机上安装APK文件。

### 3. 激活模块

1. 打开LSPosed管理器
2. 找到"Claude Notify"模块
3. 勾选以下作用域：
   - ✅ 系统框架 (android)
   - ✅ 系统界面 (com.android.systemui)
   - ✅ ColorOS服务 (com.coloros.bootreg)
4. 重启系统服务或重启手机

### 4. 配置服务器地址

编辑模块配置（需要在代码中修改）：

[WebSocketManager.kt:20](app/src/main/java/com/claude/notify/WebSocketManager.kt#L20)

```kotlin
private var serverUrl = "ws://YOUR_SERVER_IP:8765"
```

将 `YOUR_SERVER_IP` 替换为中继服务器地址。

## 验证

### 检查日志

```bash
# 查看Xposed日志
adb logcat | grep ClaudeNotify

# 应该看到类似输出
ClaudeNotify: Initializing WebSocket Manager
ClaudeNotify: WebSocket connected
ClaudeNotify: Task started - xxx
```

### 测试通知

从Windows端触发任务后，手机应显示通知。

## 故障排除

### 模块未激活

**症状**：LSPosed中模块未生效

**解决**：
1. 确认已勾选作用域
2. 重启系统服务
3. 检查LSPosed框架是否正常

### 无法连接WebSocket

**症状**：日志显示连接失败

**解决**：
1. 检查服务器地址配置
2. 确认服务器正在运行
3. 检查防火墙设置
4. 确认手机和服务器网络可达

### 通知不显示

**症状**：已连接但无通知

**解决**：
1. 检查通知权限
2. 查看系统日志
3. 确认消息格式正确

## 高级配置

### 自定义通知样式

修改 [FluidCloudInjector.kt](app/src/main/java/com/claude/notify/FluidCloudInjector.kt) 中的通知构建逻辑。

### 调整重连策略

修改 [WebSocketManager.kt](app/src/main/java/com/claude/notify/WebSocketManager.kt) 中的重连间隔。

## 开发调试

### 启用调试日志

在 [XposedEntry.kt](app/src/main/java/com/claude/notify/XposedEntry.kt) 中添加更多日志输出。

### 使用LSPosed调试

LSPosed提供实时日志查看功能，可在管理器中查看模块日志。

## 兼容性

### 测试设备

- OPPO/OnePlus with ColorOS 16

### 理论支持

- Android 11+ (API 30+)
- 其他基于AOSP的ROM

## 注意事项

⚠️ **警告**
- 此模块需要root权限
- 修改系统行为可能影响稳定性
- 仅供学习研究使用

## 许可证

MIT License
