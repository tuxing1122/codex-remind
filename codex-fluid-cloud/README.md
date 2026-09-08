# Codex Fluid Cloud

这个独立项目把 Windows Codex Desktop 的任务状态实时发送到 ColorOS 16 手机。
手机端没有启动界面，由 LSPosed 把模块加载到 `com.android.systemui`；运行中任务优先使用
Android 16 Live Updates，并保留普通进度通知作为回退。ColorOS 16 已接入这套公开规范，
因此工程不依赖猜测的 Oplus 私有字段。

```text
Codex Desktop session JSONL
  -> Windows watcher
  -> TCP 24680 / JSONL / shared token
  -> LSPosed module in SystemUI -> permission-protected module receiver
  -> Android 16 live update
  -> ColorOS 16 Fluid Cloud
```

## 当前目录

- `android/`: 无 Launcher Activity 的 LSPosed 模块。
- `windows/`: 监听 `%USERPROFILE%\.codex\sessions` 的零依赖 Python watcher。
- `docs/`: 架构、部署与真机分层验证说明。
- `.vscode/`: 已配置 JDK 17、Android SDK、Gradle、Python 和构建任务。

## 构建 Android 模块

`windows/config.local.json` 已保存一枚本机专用随机 token，普通构建会自动读取它。
也可用 `-PbridgeToken` 显式覆盖：

```powershell
cd .\android
.\gradlew.bat :app:assembleDebug -PbridgeToken=replace-with-a-long-random-token
```

APK 输出到 `android/app/build/outputs/apk/debug/app-debug.apk`。安装后在 LSPosed 中启用模块，
作用域只选 `System UI`，授予模块通知权限，随后重启手机：

```powershell
adb install -r .\android\app\build\outputs\apk\debug\app-debug.apk
adb shell pm grant com.codex.fluidcloud android.permission.POST_NOTIFICATIONS
```

模块监听手机 TCP `24680`。当前协议未加密，只能用于可信局域网或 ADB 转发，不能映射到公网。

## 启动 Windows watcher

编辑被 Git 忽略的 `windows/config.local.json`：

1. 把 `phone_host` 改为手机的局域网 IP。
2. 保持 `token` 与构建 APK 时使用的值一致。

然后启动：

```powershell
cd .\windows
.\start-watcher.ps1
```

安装手机模块后，可先执行 `python .\send_test_event.py`，确认手机依次显示开始、50% 和完成。

watcher 默认只读取启动后新增的 Codex 会话事件，不回放历史任务。它不会发送对话、推理、
命令参数、stdout/stderr、路径、文件名、文件内容或 diff；命令状态只包含可执行文件名。
未收到手机 ACK 的事件会写入本地 spool，并在 watcher 重启后恢复；终态优先发送。

## 验证

```powershell
cd .\windows
python -m unittest discover -s tests -v

Test-NetConnection -ComputerName <手机IP> -Port 24680
adb logcat -s LSPosed CodexFluidCloud AndroidRuntime
```

当前实现严格按 Android 16 Live Updates 条件构建通知：`ProgressStyle`、ongoing、推广请求、
短状态文本和模块自身通知权限。公开资料表明 ColorOS 16 会把合格的 Live Updates 接入流体云；
指定固件 `ColorOS 16.0.10.501` 的最终展示仍受系统开关和 OEM 策略控制，需要连接目标手机
完成最后的真机验收。详见 `docs/deployment.md`。
