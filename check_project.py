#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
项目完整性检查脚本
验证所有必要文件是否存在
"""

import os
import sys
from pathlib import Path

# Windows下修复编码
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

def check_file(path, description):
    """检查文件是否存在"""
    if os.path.exists(path):
        print(f"[OK] {description}: {path}")
        return True
    else:
        print(f"[FAIL] {description}: {path} [缺失]")
        return False

def main():
    print("=" * 60)
    print("Claude Code Notification System - Project Check")
    print("=" * 60)
    print()

    base_dir = Path(__file__).parent
    os.chdir(base_dir)

    all_ok = True

    # Android模块
    print("[Android Module]")
    print("-" * 60)
    android_files = [
        ("app/build.gradle", "Android构建配置"),
        ("app/src/main/AndroidManifest.xml", "Android清单文件"),
        ("app/src/main/assets/xposed_init", "Xposed入口配置"),
        ("app/src/main/java/com/claude/notify/XposedEntry.kt", "Xposed入口类"),
        ("app/src/main/java/com/claude/notify/WebSocketManager.kt", "WebSocket管理器"),
        ("app/src/main/java/com/claude/notify/FluidCloudInjector.kt", "通知注入器"),
        ("app/src/main/java/com/claude/notify/MessageParser.kt", "消息解析器"),
        ("app/proguard-rules.pro", "混淆规则"),
    ]
    for path, desc in android_files:
        all_ok &= check_file(path, desc)
    print()

    # Windows客户端
    print("[Windows Client]")
    print("-" * 60)
    windows_files = [
        ("windows/monitor.py", "主程序"),
        ("windows/file_watcher.py", "文件监控"),
        ("windows/task_parser.py", "任务解析"),
        ("windows/ws_client.py", "WebSocket客户端"),
        ("windows/config.json", "配置文件"),
        ("windows/requirements.txt", "Python依赖"),
        ("windows/start.bat", "启动脚本"),
    ]
    for path, desc in windows_files:
        all_ok &= check_file(path, desc)
    print()

    # 服务器和工具
    print("[Server & Tools]")
    print("-" * 60)
    tools_files = [
        ("tools/relay_server.py", "中继服务器"),
        ("tools/test_client.py", "测试工具"),
        ("tools/start_server.sh", "启动脚本"),
        ("tools/PROTOCOL.md", "协议文档"),
    ]
    for path, desc in tools_files:
        all_ok &= check_file(path, desc)
    print()

    # 文档
    print("[Documentation]")
    print("-" * 60)
    doc_files = [
        ("README.md", "项目说明"),
        ("QUICKSTART.md", "快速开始"),
        ("DEPLOY.md", "部署指南"),
        ("CONTRIBUTING.md", "开发指南"),
        ("FAQ.md", "常见问题"),
        ("CHANGELOG.md", "版本历史"),
        ("PROJECT_SUMMARY.md", "项目总结"),
        ("WINDOWS_PROTOCOL.md", "协议分析"),
        ("LICENSE", "许可证"),
    ]
    for path, desc in doc_files:
        all_ok &= check_file(path, desc)
    print()

    # 构建配置
    print("[Build Configuration]")
    print("-" * 60)
    config_files = [
        ("build.gradle", "根构建配置"),
        ("settings.gradle", "Gradle设置"),
        ("gradle.properties", "Gradle属性"),
        ("gradlew", "Gradle包装器(Unix)"),
        ("gradlew.bat", "Gradle包装器(Windows)"),
        (".gitignore", "Git忽略规则"),
    ]
    for path, desc in config_files:
        all_ok &= check_file(path, desc)
    print()

    # 统计信息
    print("=" * 60)
    print("[Statistics]")
    print("-" * 60)

    # 统计代码文件
    kt_files = list(Path('.').rglob('*.kt'))
    py_files = list(Path('.').rglob('*.py'))
    md_files = list(Path('.').rglob('*.md'))

    print(f"Kotlin文件: {len(kt_files)} 个")
    print(f"Python文件: {len(py_files)} 个")
    print(f"Markdown文档: {len(md_files)} 个")
    print()

    # 最终结果
    print("=" * 60)
    if all_ok:
        print("[SUCCESS] All core files are complete!")
        print()
        print("Next steps:")
        print("1. Read QUICKSTART.md for quick start")
        print("2. Or check DEPLOY.md for full deployment")
        return 0
    else:
        print("[ERROR] Missing files detected. Please check project integrity.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
