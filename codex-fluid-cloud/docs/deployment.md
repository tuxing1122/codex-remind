# 部署与真机验证

本文档面向开发机和自有测试设备。解锁 Bootloader、Root、修改 SystemUI 作用域可能触发清除
数据、降低设备安全性或导致系统界面崩溃。开始前应备份数据，并准备可用的 Recovery、ADB
或其他模块禁用手段。

## 1. 建议构建环境

- Windows 10/11 x64
- JDK 17
- 项目自带的 Gradle Wrapper；AGP、Gradle 与 JDK 版本按仓库锁定值使用
- Android SDK Platform 36、对应 Build Tools 和 Platform Tools
- VS Code 可选安装 Java/Gradle 扩展，但构建以终端中的 `gradlew.bat` 结果为准

LSPosed API 只能作为 `compileOnly` 依赖，不能打包进 APK。发布前应确认依赖仓库可复现，
并锁定依赖校验值。模块必须声明正确的 Xposed 入口和作用域，且不添加 Launcher Activity。

预期构建命令（以最终工程目录和 Wrapper 为准）：

```powershell
cd .\codex-fluid-cloud\android
.\gradlew.bat :app:assembleDebug
```

## 2. 设备准备

1. 记录机型、Android 版本、ColorOS 版本、完整 build fingerprint、SystemUI APK 版本和安全补丁日期。
2. 确认设备已解锁并取得 Root；确认所用 LSPosed 明确支持当前 Android 16 构建。
3. 准备 Root shell、ADB 或 Recovery 下的模块禁用路径，防止 SystemUI 崩溃循环时无法操作。
4. 安装模块 APK，并通过 ADB 授予通知权限（模块没有 Activity，不能弹出运行时权限对话框）：

   ```powershell
   adb install -r .\android\app\build\outputs\apk\debug\app-debug.apk
   adb shell pm grant com.codex.fluidcloud android.permission.POST_NOTIFICATIONS
   ```

5. 在 LSPosed 中启用模块，作用域仅选择 `System UI`（`com.android.systemui`）。
6. 重启设备；开发阶段若只重启 SystemUI，应预期屏幕短暂黑屏和系统界面重新加载。

没有启动图标是预期行为。模块需要 APK 和 LSPosed，不等于普通“免安装”程序。

## 3. 密钥与网络配置

1. 生成每台手机独立的高熵随机密钥，不使用仓库示例值。
2. 把密钥写入被 Git 忽略的 `windows/config.local.json`；Android 构建会自动读取同一值。
   也可用 `-PbridgeToken=<密钥>` 覆盖。构建和 watcher 都拒绝短于 32 字符或仓库示例值的 token。
3. 手机与 Windows 连接同一可信 Wi-Fi，关闭 AP isolation/客户端隔离，确认双方地址没有频繁变化。
4. 允许 Windows 向手机 TCP `24680` 发起出站连接；不要配置公网映射。

当前 TCP 只认证、不加密，局域网抓包仍可能看到 token 和状态文本。只在可信 Wi-Fi 使用，
不要转发公网端口；也可使用 `adb forward tcp:24680 tcp:24680` 后把 `phone_host` 设为
`127.0.0.1`，通过 ADB 通道测试。

可先用 `Test-NetConnection` 验证网络可达性：

```powershell
Test-NetConnection -ComputerName <手机局域网IP> -Port 24680
```

端口不可达时先检查 SystemUI/LSPosed 日志、手机监听状态、Wi-Fi 客户端隔离和防火墙，不要先
修改流体云 Hook。

## 4. 分层验收

### A. 进程与 TCP

- LSPosed 日志显示模块只加载到 `com.android.systemui`。
- 接收线程成功监听预期地址和端口；SystemUI 主线程没有网络 I/O。
- 正确密钥得到 `ok` 应答；错误密钥和超长 JSON 被拒绝。
- 重复 `event_id` 不产生重复通知，乱序 `sequence` 不覆盖新状态。
- SystemUI 重启后监听器只启动一个实例。
- 认证后的事件通过 `STATUS_BAR` 权限保护的显式广播交给模块 UID，广播中不包含 token。

### B. 普通持续通知

依次发送 `started`、多个 `progress` 和 `completed`：

- 同一任务始终只保留一条通知并原位更新；并行任务使用不同通知，不互相覆盖。
- 运行中通知不可被普通滑动误清除，完成后转为非 ongoing 并按策略清理。
- `failed`、`cancelled` 的文本和图标与成功状态可区分。
- 锁屏内容遵循用户的隐私设置，不显示完整命令或敏感输出。

这一步通过后，才能继续判断 promoted ongoing 或 ColorOS 适配问题。

### C. Android 16 promoted ongoing

- 确认系统版本为 API 36，通知满足 promoted ongoing 的公开 API 和系统条件。
- 检查模块确实发出提升请求，并记录系统接受/拒绝结果（若 API 可查询）。
- 在系统“应用 > Codex Fluid Cloud > 实时通知/Live Updates”中确认开关已开启；不同 ColorOS
  构建的菜单名称可能不同。
- 在锁屏、通知栏及系统支持的突出表面观察展示；关闭相关用户设置后应优雅退回普通通知。
- 省电模式、锁屏、Wi-Fi 断开和 SystemUI 重启后不应出现崩溃或无限重试。

### D. ColorOS 16 流体云

- ColorOS 16 使用 Android 16 Live Updates 标准映射流体云；工程不注入私有 Oplus 字段。
- 用同一组事件对照普通通知、promoted ongoing 和流体云展示，记录目标固件的实际生命周期。
- 验证进行中、完成、失败、取消、超时和连续任务，不只验证一条静态演示数据。
- 检查流体云点击行为；无手机 UI 时不要注册无效或越权的跳转目标。
- 重启、切换主题、横竖屏、锁屏和多任务下确认 SystemUI 稳定。

若只有普通通知而没有流体云，说明 Live Updates 资格、权限、用户开关或 OEM 策略未通过，
不是 TCP 失败。必须在 `ColorOS 16.0.10.501` 真机上验收后再确认该版本的最终展示。

## 5. Codex Desktop 接入验收

先用固定测试事件打通手机，再接入 Codex Desktop。采集器至少应准确产生：

- 用户任务开始：`started`
- 命令开始或阶段切换：`command_started`
- 可节流的进度更新：`progress`
- 正常完成：`completed`
- 命令或任务失败：`failed`
- 用户中止：`cancelled`

Windows 用 0.5 秒轮询并合并离线队列。未 ACK 的事件写入磁盘 spool，重启后恢复；同一任务的
终态会替换旧进度并优先发送。手机若 30 分钟未收到更新，会自动清除运行中通知。

## 6. 日志采集

开发阶段可使用以下只读命令观察日志，实际标签以实现为准：

```powershell
adb logcat -s LSPosed CodexFluidCloud AndroidRuntime
adb shell getprop ro.build.fingerprint
adb shell dumpsys notification
```

提交日志前删除 IP、密钥、提示词、命令内容和个人通知。OEM 反射失败只需要类名、方法签名、
异常类型和固件指纹，不需要上传完整用户数据。

## 7. 回滚

1. 模块工作但展示异常：先在 LSPosed 中取消 `System UI` 作用域并重启。
2. SystemUI 可启动但反复报错：禁用模块，保留日志后重启设备。
3. 出现 SystemUI 崩溃循环：使用 ADB、Root shell 或 Recovery 的预先准备路径禁用 LSPosed 模块。
4. 恢复后先验证 TCP 和普通通知，再检查系统 Live Updates/流体云设置。

卸载 APK 前先在 LSPosed 中禁用模块。不要在没有回滚通道的日用主设备上首次验证新的
SystemUI Hook。
