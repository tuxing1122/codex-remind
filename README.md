# Claude Code Real-time Notification System

<div align="center">

![Platform](https://img.shields.io/badge/platform-Android%20%7C%20Windows-blue)
![Android](https://img.shields.io/badge/Android-11%2B-green)
![Python](https://img.shields.io/badge/Python-3.10%2B-yellow)
![License](https://img.shields.io/badge/license-MIT-orange)

Push Windows Claude Code execution status to Android phone notifications in real-time.

[English](README.md) | [中文](README_CN.md)

</div>

## ✨ Features

- 🚀 Real-time monitoring of Claude Code task execution
- 📱 No standalone app required on phone
- 🔌 Based on LSPosed module
- 🌐 WebSocket communication
- 📊 Real-time task progress and command output display
- 🎯 Supports ColorOS Fluid Cloud

## 🏗️ Architecture

```
Windows Client ←→ WebSocket Server ←→ Android Module
  (Monitor)          (Relay)            (Notify)
```

## 🚀 Quick Start

### Prerequisites

- ✅ Android phone (rooted + LSPosed)
- ✅ Windows PC (Python 3.10+)
- ✅ Same network or cloud server

### 3-Minute Deployment

```bash
# 1. Start relay server
cd tools && python relay_server.py

# 2. Start Windows monitor
cd windows && python monitor.py

# 3. Install Android module
./gradlew assembleRelease
# Install APK and activate in LSPosed

# 4. Test
python tools/test_client.py
```

See [Quick Start Guide](QUICKSTART.md) for details.

## 📚 Documentation

| Document | Description |
|----------|-------------|
| [QUICKSTART.md](QUICKSTART.md) | 3-minute quick start |
| [DEPLOY.md](DEPLOY.md) | Complete deployment guide |
| [FAQ.md](FAQ.md) | Frequently asked questions |
| [CONTRIBUTING.md](CONTRIBUTING.md) | Developer guide |
| [PROJECT_SUMMARY.md](PROJECT_SUMMARY.md) | Project summary |

## 🛠️ Tech Stack

- **Android**: Kotlin + LSPosed + OkHttp
- **Windows**: Python + websockets + watchdog
- **Server**: Python + websockets

## 📝 License

MIT License

## ⚠️ Disclaimer

For educational purposes only. Requires root access. Use at your own risk.

---

Made with ❤️ for Claude Code users
