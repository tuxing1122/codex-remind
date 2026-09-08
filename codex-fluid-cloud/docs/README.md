# Codex Fluid Cloud 文档

本项目的目标是把 Windows 上 Codex Desktop 的任务状态，经同一 Wi-Fi 下的 TCP
连接发送到 Android 16 / ColorOS 16 手机，并由一个**无启动界面**的 LSPosed 模块在
`com.android.systemui` 进程中接收和呈现：

```text
Codex Desktop
    -> Windows 状态采集器
    -> TCP/JSONL（同一 Wi-Fi）
    -> LSPosed 模块（SystemUI 作用域，无手机端 UI）
    -> 模块 UID 的受权限保护通知 Receiver
    -> Android 16 promoted ongoing notification
    -> ColorOS 16 流体云（标准 Live Updates 映射）
```

## 交付边界

工程按三层能力设计，每层都可以独立验收：

1. **基础层**：手机收到任务事件并显示一条可更新的持续通知；任务完成后替换为完成或失败通知。
2. **Android 16 层**：在系统允许时请求 promoted ongoing 展示。该请求由系统最终裁决，不保证一定晋升。
3. **ColorOS 层**：ColorOS 16 已接入 Android 16 Live Updates 标准。模块不猜测私有 extras；是否显示为流体云由指定固件的系统策略和用户开关决定，仍需真机验收。

因此，“能显示普通持续通知”不能证明“已接入流体云”；反过来，OEM 适配失效也不应影响
TCP 接收和普通通知兜底。

## 前置条件

- 手机已解锁 Bootloader，并已取得可用的 Root 权限。
- 已安装与 Android 16 / 当前 ColorOS 固件兼容的 LSPosed。
- 模块 APK 已安装，并在 LSPosed 中仅启用 `System UI`（`com.android.systemui`）作用域。
- Windows 与手机位于同一可信 Wi-Fi，网络允许 Windows 访问手机监听端口。
- Windows 端有一个状态采集器。Codex Desktop 的内部事件接口并非本项目可假定的稳定公共 API；具体版本若没有生命周期回调，需要通过受支持的日志、通知或命令包装器接入。

“无手机端 App”在这里表示没有 Launcher Activity、没有常驻用户界面和单独的前台应用流程；
LSPosed 模块本身仍然以 APK 形式安装，token 通过被 Git 忽略的本地配置或构建参数写入 APK，
通知运行时权限通过 ADB/Root 授予。

## 安全约束

- 监听器仅服务局域网，不应映射到公网，也不应使用路由器端口转发。
- 每台设备使用独立随机密钥；不要把示例密钥用于实际环境。
- 当前 TCP 只认证、不加密，状态文本和 token 可能被同网段抓包；只使用可信 LAN 或 ADB 转发。
- 限制单条消息大小、连接空闲时间和并发数，并校验任务 ID、序号和时间戳。
- 日志不得记录完整密钥、用户提示词、命令输出或其他敏感内容。
- SystemUI 是关键系统进程。所有网络和解析工作必须离开主线程，Hook 失败必须快速降级，不能让异常逃逸到宿主进程。

## 文档索引

- [架构说明](architecture.md)：组件职责、状态模型、TCP 协议和 Android/OEM 适配边界。
- [部署与验证](deployment.md)：构建、安装、LSPosed 启用、网络配置、分层验收和回滚。

当前工程已完成本机构建和自动化测试，不代表已在目标机型和指定固件上完成流体云真机验收。
