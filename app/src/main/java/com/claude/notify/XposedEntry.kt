package com.claude.notify

import de.robv.android.xposed.IXposedHookLoadPackage
import de.robv.android.xposed.XC_MethodHook
import de.robv.android.xposed.XposedBridge
import de.robv.android.xposed.XposedHelpers
import de.robv.android.xposed.callbacks.XC_LoadPackage

/**
 * Xposed模块入口
 * 监听系统进程并Hook流体云相关功能
 */
class XposedEntry : IXposedHookLoadPackage {

    override fun handleLoadPackage(lpparam: XC_LoadPackage.LoadPackageParam) {
        when (lpparam.packageName) {
            "android" -> {
                hookSystemServer(lpparam)
            }
            "com.android.systemui" -> {
                hookSystemUI(lpparam)
            }
            "com.coloros.bootreg" -> {
                hookColorOSBootreg(lpparam)
            }
        }
    }

    /**
     * Hook System Server进程
     */
    private fun hookSystemServer(lpparam: XC_LoadPackage.LoadPackageParam) {
        try {
            XposedBridge.log("ClaudeNotify: Hooking System Server")

            // 启动WebSocket服务
            WebSocketManager.init(lpparam.classLoader)

        } catch (e: Exception) {
            XposedBridge.log("ClaudeNotify: Error hooking SystemServer - ${e.message}")
        }
    }

    /**
     * Hook SystemUI进程（通知栏）
     */
    private fun hookSystemUI(lpparam: XC_LoadPackage.LoadPackageParam) {
        try {
            XposedBridge.log("ClaudeNotify: Hooking SystemUI")

            // Hook通知管理器
            hookNotificationManager(lpparam)

        } catch (e: Exception) {
            XposedBridge.log("ClaudeNotify: Error hooking SystemUI - ${e.message}")
        }
    }

    /**
     * Hook ColorOS特有服务
     */
    private fun hookColorOSBootreg(lpparam: XC_LoadPackage.LoadPackageParam) {
        try {
            XposedBridge.log("ClaudeNotify: Hooking ColorOS Bootreg")

            // Hook流体云相关功能
            hookFluidCloud(lpparam)

        } catch (e: Exception) {
            XposedBridge.log("ClaudeNotify: Error hooking ColorOS - ${e.message}")
        }
    }

    /**
     * Hook通知管理器，用于显示Claude执行状态
     */
    private fun hookNotificationManager(lpparam: XC_LoadPackage.LoadPackageParam) {
        try {
            val notificationManagerClass = XposedHelpers.findClass(
                "com.android.server.notification.NotificationManagerService",
                lpparam.classLoader
            )

            XposedHelpers.findAndHookMethod(
                notificationManagerClass,
                "enqueueNotificationInternal",
                String::class.java,
                String::class.java,
                Int::class.java,
                Int::class.java,
                String::class.java,
                Int::class.java,
                android.app.Notification::class.java,
                Int::class.java,
                object : XC_MethodHook() {
                    override fun beforeHookedMethod(param: MethodHookParam) {
                        // 可以在这里修改或注入通知
                        val pkg = param.args[0] as? String
                        if (pkg == "com.claude.notify") {
                            XposedBridge.log("ClaudeNotify: Notification from our module")
                        }
                    }
                }
            )
        } catch (e: Exception) {
            XposedBridge.log("ClaudeNotify: Error hooking NotificationManager - ${e.message}")
        }
    }

    /**
     * Hook ColorOS流体云功能
     */
    private fun hookFluidCloud(lpparam: XC_LoadPackage.LoadPackageParam) {
        try {
            // 尝试找到流体云相关类
            // 注意：实际类名需要通过逆向ColorOS系统确定
            val fluidCloudClasses = listOf(
                "com.oplus.fluidcloud.FluidCloudService",
                "com.oplus.fluidcloud.NotificationManager",
                "com.coloros.fluidspace.FluidSpaceManager"
            )

            for (className in fluidCloudClasses) {
                try {
                    val clazz = XposedHelpers.findClass(className, lpparam.classLoader)
                    XposedBridge.log("ClaudeNotify: Found FluidCloud class: $className")

                    // Hook所有方法以便调试和注入
                    XposedBridge.hookAllMethods(clazz, "show", object : XC_MethodHook() {
                        override fun beforeHookedMethod(param: MethodHookParam) {
                            XposedBridge.log("ClaudeNotify: FluidCloud show() called")
                        }
                    })

                } catch (e: ClassNotFoundException) {
                    // 该类不存在，继续尝试下一个
                }
            }

            // 注册消息接收器
            FluidCloudInjector.init(lpparam.classLoader)

        } catch (e: Exception) {
            XposedBridge.log("ClaudeNotify: Error hooking FluidCloud - ${e.message}")
        }
    }
}
