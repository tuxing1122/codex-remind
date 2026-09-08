# Claude Code 实时通知系统

<div align="center">

![Platform](https://img.shields.io/badge/platform-Android%20%7C%20Windows-blue)
![Android](https://img.shields.io/badge/Android-11%2B-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)
![License](https://img.shields.io/badge/license-MIT-orange)

将Windows端Claude Code的执行状态实时推送到手机的ColorOS流体云

[English](README.md) | [中文](README_CN.md)

</div>

## ✨ 特性

- 🚀 实时监控Claude Code任务执行
- 📱 手机端无需独立App
- 🔌 基于LSPosed模块
- 🌐 WebSocket通信
- 📊 任务进度、命令输出实时显示
- 🎯 支持ColorOS流体云

## 📸 效果演示

当Windows端Claude Code执行任务时，手机会收到实时通知：

```
┌─────────────────────────────┐
│ 📱 Claude Code 执行中       │
│                             │
│ 正在编译项目...             │
│ ████████░░░░░░░░ 50%       │
└─────────────────────────────┘
```

## 🏗️ 架构

```
Windows客户端 ←→ WebSocket服务器 ←→ Android模块
  (监控)           (中继)          (通知)
```

## 🚀 快速开始

### 前置要求

- ✅ Android手机（已root + LSPosed）
- ✅ Windows电脑（Python 3.10+）
- ✅ 同一网络或云服务器

### 3分钟部署

```bash
# 1. 启动服务器
cd tools && python relay_server.py

# 2. 启动Windows监控
cd windows && python monitor.py

# 3. 安装Android模块
./gradlew assembleRelease
# 安装APK并在LSPosed激活

# 4. 测试
python tools/test_client.py
```

详见 [快速开始指南](QUICKSTART.md)

## 📚 文档

| 文档 | 说明 |
|------|------|
| [QUICKSTART.md](QUICKSTART.md) | 3分钟快速开始 |
| [DEPLOY.md](DEPLOY.md) | 完整部署指南 |
| [FAQ.md](FAQ.md) | 常见问题解答 |
| [CONTRIBUTING.md](CONTRIBUTING.md) | 开发者指南 |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | 项目总结 |

## 🛠️ 技术栈

- **Android**: Kotlin + LSPosed + OkHttp
- **Windows**: Python + websockets + watchdog
- **Server**: Python + websockets

## 📝 许可证

MIT License

## ⚠️ 免责声明

仅供学习研究，需root权限，使用风险自负。

---

Made with ❤️ for Claude Code users
