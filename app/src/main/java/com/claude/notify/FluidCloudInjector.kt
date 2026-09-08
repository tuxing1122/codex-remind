package com.claude.notify

import android.app.Notification
import android.app.NotificationChannel
import android.app.NotificationManager
import android.content.Context
import android.os.Build
import de.robv.android.xposed.XposedBridge
import de.robv.android.xposed.XposedHelpers

/**
 * 流体云注入器
 * 负责在ColorOS流体云中显示Claude执行状态
 */
object FluidCloudInjector {

    private var systemContext: Context? = null
    private var notificationManager: NotificationManager? = null
    private const val CHANNEL_ID = "claude_notify_channel"
    private const val NOTIFICATION_ID = 10086

    fun init(classLoader: ClassLoader) {
        try {
            // 获取系统Context
            val activityThreadClass = XposedHelpers.findClass(
                "android.app.ActivityThread",
                classLoader
            )

            val currentActivityThread = XposedHelpers.callStaticMethod(
                activityThreadClass,
                "currentActivityThread"
            )

            systemContext = XposedHelpers.callMethod(
                currentActivityThread,
                "getSystemContext"
            ) as? Context

            systemContext?.let { ctx ->
                notificationManager = ctx.getSystemService(Context.NOTIFICATION_SERVICE) as NotificationManager
                createNotificationChannel(ctx)
                XposedBridge.log("ClaudeNotify: FluidCloudInjector initialized")
            }

        } catch (e: Exception) {
            XposedBridge.log("ClaudeNotify: Error initializing FluidCloudInjector: ${e.message}")
        }
    }

    /**
     * 创建通知渠道
     */
    private fun createNotificationChannel(context: Context) {
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            val channel = NotificationChannel(
                CHANNEL_ID,
                "Claude Code 执行状态",
                NotificationManager.IMPORTANCE_HIGH
            ).apply {
                description = "实时显示Claude Code任务执行状态"
                enableLights(true)
                enableVibration(true)
            }
            notificationManager?.createNotificationChannel(channel)
        }
    }

    /**
     * 显示任务开始
     */
    fun showTaskStart(taskName: String) {
        try {
            val notification = buildNotification(
                title = "Claude Code 执行中",
                content = taskName,
                ongoing = true,
                progress = 0
            )
            notificationManager?.notify(NOTIFICATION_ID, notification)
            XposedBridge.log("ClaudeNotify: Task started - $taskName")
        } catch (e: Exception) {
            XposedBridge.log("ClaudeNotify: Error showing task start: ${e.message}")
        }
    }

    /**
     * 显示任务进度
     */
    fun showTaskProgress(progress: Int, description: String) {
        try {
            val notification = buildNotification(
                title = "Claude Code 执行中 ($progress%)",
                content = description,
                ongoing = true,
                progress = progress
            )
            notificationManager?.notify(NOTIFICATION_ID, notification)
            XposedBridge.log("ClaudeNotify: Progress - $progress% - $description")
        } catch (e: Exception) {
            XposedBridge.log("ClaudeNotify: Error showing progress: ${e.message}")
        }
    }

    /**
     * 显示任务完成
     */
    fun showTaskComplete(result: String) {
        try {
            val notification = buildNotification(
                title = "✅ Claude Code 执行完成",
                content = result,
                ongoing = false,
                progress = 100
            )
            notificationManager?.notify(NOTIFICATION_ID, notification)
            XposedBridge.log("ClaudeNotify: Task completed - $result")
        } catch (e: Exception) {
            XposedBridge.log("ClaudeNotify: Error showing completion: ${e.message}")
        }
    }

    /**
     * 显示命令输出
     */
    fun showCommandOutput(output: String) {
        try {
            val shortOutput = if (output.length > 100) {
                output.substring(0, 100) + "..."
            } else {
                output
            }

            val notification = buildNotification(
                title = "📟 命令输出",
                content = shortOutput,
                ongoing = false
            )
            notificationManager?.notify(NOTIFICATION_ID + 1, notification)
            XposedBridge.log("ClaudeNotify: Command output - $shortOutput")
        } catch (e: Exception) {
            XposedBridge.log("ClaudeNotify: Error showing command output: ${e.message}")
        }
    }

    /**
     * 构建通知
     */
    private fun buildNotification(
        title: String,
        content: String,
        ongoing: Boolean = false,
        progress: Int? = null
    ): Notification {
        val context = systemContext ?: throw IllegalStateException("System context not available")

        val builder = if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.O) {
            Notification.Builder(context, CHANNEL_ID)
        } else {
            @Suppress("DEPRECATION")
            Notification.Builder(context)
        }

        builder.apply {
            setContentTitle(title)
            setContentText(content)
            setSmallIcon(android.R.drawable.ic_dialog_info)
            setOngoing(ongoing)
            setAutoCancel(!ongoing)

            // 添加进度条
            progress?.let {
                setProgress(100, it, false)
            }

            // 设置样式为大文本
            if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.N) {
                setStyle(Notification.BigTextStyle().bigText(content))
            }
        }

        return if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.JELLY_BEAN) {
            builder.build()
        } else {
            @Suppress("DEPRECATION")
            builder.notification
        }
    }
}
