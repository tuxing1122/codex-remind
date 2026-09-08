# 开发指南

## 项目结构

```
remind/
├── app/                          # Android LSPosed模块
│   ├── src/main/
│   │   ├── java/com/claude/notify/
│   │   │   ├── XposedEntry.kt          # Xposed入口
│   │   │   ├── WebSocketManager.kt     # WebSocket客户端
│   │   │   ├── FluidCloudInjector.kt   # 通知注入
│   │   │   ├── MessageParser.kt        # 消息解析
│   │   ├── AndroidManifest.xml
│   │   ├── res/                        # 资源文件
│   │   └── assets/xposed_init          # Xposed配置
│   ├── build.gradle
│   └── proguard-rules.pro
│
├── windows/                      # Windows监控客户端
│   ├── monitor.py                # 主程序
│   ├── file_watcher.py          # 文件监控
│   ├── task_parser.py           # 任务解析
│   ├── ws_client.py             # WebSocket客户端
│   ├── config.json              # 配置文件
│   ├── requirements.txt         # Python依赖
│   └── start.bat                # 启动脚本
│
├── tools/                        # 通信服务
│   ├── relay_server.py          # WebSocket中继服务器
│   ├── test_client.py           # 测试工具
│   ├── PROTOCOL.md              # 通信协议文档
│   └── start_server.sh          # 启动脚本
│
├── build.gradle                  # 根构建配置
├── settings.gradle              # Gradle设置
├── gradle.properties            # Gradle属性
├── README.md                    # 项目说明
├── QUICKSTART.md               # 快速开始
├── DEPLOY.md                   # 部署指南
├── WINDOWS_PROTOCOL.md         # ColorOS协议分析
└── LICENSE                      # 许可证
```

## 开发环境搭建

### Android模块开发

**要求：**
- Android Studio Arctic Fox+
- JDK 17
- Android SDK 30+

**配置：**
1. 打开 Android Studio
2. Open Project → 选择 `remind` 目录
3. 等待 Gradle 同步
4. 连接已root的测试设备

**调试：**
```bash
# 查看Xposed日志
adb logcat -s ClaudeNotify:* Xposed:*

# 安装调试版本
./gradlew installDebug

# 构建发布版本
./gradlew assembleRelease
```

### Windows客户端开发

**要求：**
- Python 3.10+
- pip

**配置：**
```bash
cd windows
pip install -r requirements.txt
```

**调试：**
```bash
# 启用调试日志
# 编辑 monitor.py，设置 level=logging.DEBUG
python monitor.py
```

### 服务器开发

**要求：**
- Python 3.10+
- websockets库

**运行：**
```bash
cd tools
python relay_server.py
```

## 代码规范

### Kotlin代码

- 使用4空格缩进
- 遵循 Kotlin 官方编码规范
- 类名：PascalCase
- 函数/变量：camelCase
- 常量：UPPER_SNAKE_CASE

```kotlin
class MyClass {
    companion object {
        private const val MAX_RETRIES = 3
    }
    
    private var myVariable = 0
    
    fun myFunction() {
        // ...
    }
}
```

### Python代码

- 遵循 PEP 8
- 使用4空格缩进
- 类型提示（Python 3.10+）

```python
def my_function(param: str) -> dict:
    """函数说明"""
    return {"result": param}
```

## 通信协议

详见 [tools/PROTOCOL.md](tools/PROTOCOL.md)

## Hook点说明

### Android系统Hook

**SystemServer进程：**
```kotlin
// 在系统启动时初始化
hookSystemServer(lpparam: LoadPackageParam)
```

**SystemUI进程：**
```kotlin
// Hook通知管理器
NotificationManagerService.enqueueNotificationInternal()
```

**ColorOS服务：**
```kotlin
// 尝试Hook流体云API（需要逆向分析）
com.oplus.fluidcloud.*
```

## 扩展开发

### 添加新的消息类型

1. **定义协议** (tools/PROTOCOL.md)
2. **Windows端发送** (windows/monitor.py)
3. **Android端处理** (app/.../WebSocketManager.kt)
4. **显示通知** (app/.../FluidCloudInjector.kt)

### 自定义通知样式

编辑 [FluidCloudInjector.kt:100](app/src/main/java/com/claude/notify/FluidCloudInjector.kt#L100)：

```kotlin
private fun buildNotification(...): Notification {
    builder.apply {
        // 自定义样式
        setColor(Color.parseColor("#FF6B35"))
        setLights(Color.BLUE, 500, 500)
        // ...
    }
}
```

### 添加新的监控源

编辑 [monitor.py](windows/monitor.py)：

```python
async def on_file_change(self, event_type: str, file_path: str):
    # 添加新的文件类型处理
    if path.name.endswith('.your_extension'):
        await self._handle_your_file(path)
```

## 测试

### 单元测试

```bash
# Android
./gradlew test

# Python
cd windows
pytest
```

### 集成测试

```bash
# 启动完整系统
cd tools && python relay_server.py &
cd windows && python monitor.py &

# 运行测试脚本
python tools/test_client.py
```

## 性能优化

### Android端

- 使用协程避免阻塞
- 限制日志输出
- 复用WebSocket连接

### Windows端

- 使用异步IO
- 批量处理文件事件
- 缓存解析结果

### 服务器端

- 使用连接池
- 实现消息队列
- 添加速率限制

## 常见问题

### Q: 如何逆向ColorOS流体云？

A: 参考 [WINDOWS_PROTOCOL.md](WINDOWS_PROTOCOL.md)

### Q: 如何调试Xposed模块？

A: 使用 LSPosed 的日志功能和 `XposedBridge.log()`

### Q: 如何处理网络断线？

A: 已实现自动重连，参见 WebSocketManager 和 ws_client.py

## 贡献指南

1. Fork项目
2. 创建特性分支
3. 提交更改
4. 推送到分支
5. 创建Pull Request

## 安全注意事项

⚠️ **重要提醒**

- 不要在代码中硬编码敏感信息
- 使用环境变量或配置文件
- 生产环境使用WSS (WebSocket Secure)
- 添加认证和授权机制

## 发布流程

1. 更新版本号
2. 编译发布版本
3. 签名APK
4. 创建Release Tag
5. 上传artifacts

```bash
# 签名APK
jarsigner -verbose -sigalg SHA256withRSA \
  -digestalg SHA-256 \
  -keystore my-release-key.jks \
  app-release.apk my-key-alias
```

## 资源链接

- [LSPosed文档](https://github.com/LSPosed/LSPosed)
- [Xposed API参考](https://api.xposed.info/)
- [WebSocket协议](https://datatracker.ietf.org/doc/html/rfc6455)
- [Android开发文档](https://developer.android.com/)
