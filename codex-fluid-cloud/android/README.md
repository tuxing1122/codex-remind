# Codex Fluid Cloud Android 模块

这是一个独立的 LSPosed Android 模块，没有 Launcher Activity 或启动界面。LSPosed 只把它
加载到 `com.android.systemui`；模块 Hook `SystemUIApplication.onCreate`，并在手机 TCP
`24680` 端口启动 JSONL 监听器。

事件通过认证后，System UI 会向模块进程发送受权限保护的显式广播，再由模块自身 UID 发布
通知。共享 token 会在发送广播前删除。

## 构建

需要 JDK 17 和 Android SDK 36。未指定 `-PbridgeToken` 时，Gradle 会自动读取
`../windows/config.local.json` 中的 token：

```powershell
.\gradlew.bat :app:assembleDebug
```

构建会拒绝短于 32 字符或仓库示例值的 token。若不用本地配置，可通过
`-PbridgeToken=<至少32字符的随机值>` 显式传入。Debug APK 已签名；Release 构建需另行
配置签名。

## 安装

安装 APK，在 LSPosed 中启用模块并确认唯一作用域是 `System UI`
（`com.android.systemui`），授予通知权限，然后重启手机：

```powershell
adb install -r .\app\build\outputs\apk\debug\app-debug.apk
adb shell pm grant com.codex.fluidcloud android.permission.POST_NOTIFICATIONS
```

模块没有 Activity，无法自行弹出运行时权限对话框，因此通知权限通过 ADB 授予。导出的
Receiver 需要签名级 `android.permission.STATUS_BAR` 权限，普通应用无法向它注入事件。

## 协议

Windows 连接手机局域网地址的 TCP `24680` 端口，每行发送一个 UTF-8 JSON 对象，并读取
一行 ACK。单条事件上限为 16 KiB。

```json
{"token":"至少32字符的共享随机值","event_id":"8e9418d2","task_id":"task-1","sequence":2,"type":"progress","title":"Codex","message":"Running tests","progress":{"current":2,"total":5}}
```

模块会拒绝错误 token，按 `event_id` 去重，并忽略同一 `task_id` 中重复或倒退的
`sequence`。终态类型包括 `completed`、`failed`、`error`、`cancelled`、`done` 和
`success`。发送相同 `task_id` 的 `clear` 可删除对应通知。不同任务使用独立通知 ID，
并行根任务不会互相覆盖。

## Live Updates 与流体云

Android 16 上的运行中事件使用 `Notification.ProgressStyle`，通过
`android.requestPromotedOngoing` 请求推广，并提供简短状态文本。模块不会手工写入系统结果位
`FLAG_PROMOTED_ONGOING`，也不使用未经证实的 Oplus 私有 extras。

ColorOS 16 会把合格的 Android Live Updates 映射到流体云。若系统策略拒绝推广，同一事件
仍会显示为普通进度通知。通知采用锁屏隐私模式；运行中通知 30 分钟无更新后过期，终态通知
10 分钟后过期。

监听器会绑定手机全部网络接口。TCP 内容经过 token 认证但没有加密，只能用于可信局域网或
ADB 转发，不要在路由器上转发或向公网暴露 `24680` 端口。
