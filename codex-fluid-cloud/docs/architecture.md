# 架构说明

## 1. 设计目标

系统只传递“任务展示所需的最小状态”，不远程控制 Codex，也不在手机上执行 Windows
命令。手机没有可交互的模块界面；当 SystemUI 重启时，接收器可以自动恢复，并由后续事件
重建当前通知。

## 2. 组件与职责

### Windows 状态采集器

- 从 Codex Desktop 的可用事件源获取任务开始、命令执行、进度、完成、失败和取消状态。
- 把不同来源归一化为稳定的任务事件，不把 Codex 内部对象直接暴露给手机。
- 维护 `task_id` 和单调递增的 `sequence`；断线事件原子写入磁盘并在重启后恢复。
- 终态会替换同一任务的旧进度并优先发送，避免手机永久停留在“执行中”。
- 不发送提示词、参数、输出、路径、文件名、diff 或文件内容；命令状态只保留可执行文件名。

Codex Desktop 若没有稳定、受支持的事件接口，采集适配器是版本相关组件。第一版可用显式
命令包装器或手工事件完成端到端验证，之后再替换采集器，不改变 TCP 协议。

### TCP 传输层

- 手机作为 TCP 服务端，Windows 主动连接，避免 Windows 防火墙开放入站端口。
- 一条 UTF-8 JSON 对象占一行（JSONL），每条事件收到一次 JSON 应答。
- 建议默认端口 `24680`；端口必须可配置且只在可信局域网使用。
- 单条消息不超过 16 KiB，空闲连接 30 秒后关闭；客户端并发队列有固定上限。
- 当前使用至少 32 字符的随机共享 token。TCP 内容未加密，只允许可信局域网或 ADB 转发；
  后续若跨越不可信网络，应改为 TLS，而不是仅依赖 token。

示例事件：

```json
{
  "version": 1,
  "event_id": "2ee669b8-36b9-4f51-8097-1b91286d47c3",
  "task_id": "bbef91f4-6bd2-46d6-a83f-f7721b73c623",
  "sequence": 7,
  "type": "progress",
  "title": "Codex",
  "message": "正在运行测试",
  "progress": { "current": 42, "total": 100 },
  "timestamp": "2026-09-08T03:04:05.123Z",
  "token": "至少32字符的共享随机值"
}
```

建议事件类型为 `started`、`command_started`、`progress`、`completed`、`failed` 和
`cancelled`。手机端按 `event_id` 去重，并拒绝同一任务中小于或等于已处理 `sequence` 的事件。
应答只返回处理结果，不回显事件内容：

```json
{"ok":true,"accepted_sequence":7}
```

### LSPosed SystemUI 模块

- 入口只处理 `com.android.systemui`，并在 SystemUI 完成初始化后启动单例接收器。
- Socket 接收、JSON 解析、认证和去重全部在独立线程执行。
- 认证后删除 token，通过显式广播把最小事件交给模块 APK 的 Receiver。
- Receiver 由签名级 `android.permission.STATUS_BAR` 保护，并在模块自身 UID 下发布通知，
  因而模块 Manifest 的通知权限确实生效；普通应用不能伪造广播。
- SystemUI 被系统杀死或重启时允许服务重新绑定。端口占用、权限或 SELinux 拒绝时只记录简短诊断并停止重试风暴。
- Hook 和网络边界捕获异常，不使用 OEM 反射或未知私有字段。

## 3. 状态机

```text
IDLE -> RUNNING -> COMPLETED
               -> FAILED
               -> CANCELLED
```

`started` 和 `command_started` 创建或更新 `RUNNING`；`progress` 更新展示。Windows spool 会让
终态覆盖同一任务的未发送进度。终态通知 10 分钟后清理；运行中通知若 30 分钟没有更新也会
自动过期，不会永久停留。

## 4. 展示适配器

### 公共通知兜底

每个 `task_id` 派生稳定的通知 ID 和 tag。同一任务原位更新，并行根任务互不覆盖。任务运行时
使用 ongoing/progress 语义；完成、失败或取消后取消 ongoing 并设置自动清理时间。通知实际由
模块 Receiver 发布，不借用 SystemUI 的包身份。

### Android 16 promoted ongoing

Android 16 公共 API 支持应用请求把符合条件的 ongoing 通知提升为更显眼的系统表面。实现应：

- 使用 Android 16（API 36）SDK 编译，设置 `ProgressStyle` 和标准
  `android.requestPromotedOngoing` 请求字段。
- 保持通知确实为 ongoing，并提供简短、实时、可理解的状态文本和有效进度。
- 不手工设置系统结果位 `FLAG_PROMOTED_ONGOING`，也不 colorize 候选通知。
- 请求被系统或用户设置拒绝时继续显示普通通知。
- 不伪造通话、导航、媒体播放等与任务无关的类别来获取更高优先级。

promoted ongoing 是“请求”，不是显示承诺；系统策略、电量策略、用户设置和 OEM 改造均可能
改变最终效果。

### ColorOS 16 流体云

ColorOS 16 已公开接入 Android 16 Live Updates 规范，合格的标准实时更新可映射到流体云。
因此本工程只生成符合公开资格条件的通知，不添加无法验证的 `oplus.*` extras，也不 Hook
ColorOS 私有类。最终晋升仍由目标 ROM、用户的实时通知开关和系统策略决定；指定
`ColorOS 16.0.10.501` 需要用真机确认视觉结果。

## 5. 配置方式

端口和协议版本固定在当前构建中。高熵 token 来自被 Git 忽略的
`windows/config.local.json` 或 `-PbridgeToken`，构建会拒绝短 token 和示例值，并把 token
写入该设备的 APK。Windows 使用同一 token。模块无设置 Activity；更换 token 后需要重建并
重装 APK。

## 6. 失败隔离与可观测性

- 日志统一使用 `CodexFluidCloud` 标签，只记录阶段和错误，不记录事件正文或 token。
- 不在 SystemUI 主线程执行 DNS、Socket、文件 I/O、JSON 解析或重试等待。
- TCP 工作线程和待处理连接均有上限；超长、错误认证、重复或乱序事件不会更新通知。
