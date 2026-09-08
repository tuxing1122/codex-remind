# ColorOS 流体云协议分析文档

## 概述

本文档记录ColorOS 16流体云的实现原理，用于指导LSPosed模块开发。

## 系统架构

### 流体云组件

ColorOS的流体云功能涉及以下系统组件：

1. **SystemUI** (`com.android.systemui`)
   - 负责通知显示
   - 管理通知面板UI

2. **OPLUS Framework** (`com.oplus.*`)
   - ColorOS特有的系统服务
   - 可能包含流体云核心逻辑

3. **通知服务** (`NotificationManagerService`)
   - Android标准通知系统
   - ColorOS可能对其进行了扩展

## Hook点分析

### 方案1: 标准通知系统

通过Android标准NotificationManager显示通知：

```kotlin
// Hook点
com.android.server.notification.NotificationManagerService
  - enqueueNotificationInternal()
  - postNotificationInternal()
```

**优点**：
- API稳定，兼容性好
- 不依赖ColorOS特定实现

**缺点**：
- 无法完全模拟流体云效果
- 可能需要通知权限

### 方案2: Hook SystemUI

直接注入SystemUI的通知显示流程：

```kotlin
// 可能的Hook点
com.android.systemui.statusbar.notification.NotificationWakeUpCoordinator
com.android.systemui.statusbar.NotificationShadeWindowController
```

**优点**：
- 可以更精确控制显示效果
- 更接近流体云原生体验

**缺点**：
- 实现复杂度高
- ColorOS版本间可能有差异

### 方案3: OPLUS专有API

如果存在OPLUS的流体云专有API：

```kotlin
// 需要逆向分析的类
com.oplus.fluidcloud.*
com.coloros.notification.*
```

**优点**：
- 完美模拟流体云效果

**缺点**：
- 需要逆向工程
- 高度依赖ColorOS版本

## 逆向分析步骤

### 1. 提取系统应用

```bash
adb shell pm path com.android.systemui
adb pull /system/priv-app/SystemUI/SystemUI.apk
```

### 2. 反编译分析

使用工具：
- jadx-gui
- apktool
- JEB Decompiler

### 3. 关键字搜索

搜索关键词：
- "fluid"
- "cloud"
- "notification"
- "oplus"

## 当前实现方案

目前采用**方案1（标准通知系统）**，因为：

1. ✅ 稳定可靠
2. ✅ 无需深度逆向
3. ✅ 快速验证可行性

后续可根据需要升级到方案2或方案3。

## 测试要点

### 测试设备
- 设备型号：需要用户提供
- ColorOS版本：16.0.10.501
- Android版本：通常为Android 15

### 测试场景
1. 通知正常显示
2. 通知点击响应
3. 通知持久化
4. 通知样式和动画

## 参考资料

- [LSPosed文档](https://github.com/LSPosed/LSPosed)
- [Xposed API](https://api.xposed.info/)
- [Android Notification Guide](https://developer.android.com/develop/ui/views/notifications)
