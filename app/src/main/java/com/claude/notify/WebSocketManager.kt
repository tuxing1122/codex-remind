package com.claude.notify

import android.os.Handler
import android.os.Looper
import de.robv.android.xposed.XposedBridge
import kotlinx.coroutines.*
import okhttp3.*
import java.util.concurrent.TimeUnit

/**
 * WebSocket管理器
 * 负责与Windows端通信，接收Claude执行状态
 */
object WebSocketManager {

    private var webSocket: WebSocket? = null
    private val client = OkHttpClient.Builder()
        .connectTimeout(10, TimeUnit.SECONDS)
        .readTimeout(0, TimeUnit.MINUTES) // WebSocket不超时
        .build()

    private val scope = CoroutineScope(Dispatchers.IO + SupervisorJob())
    private val mainHandler = Handler(Looper.getMainLooper())

    // WebSocket服务器地址（可通过配置文件修改）
    private var serverUrl = "ws://192.168.1.100:8765"

    fun init(classLoader: ClassLoader) {
        XposedBridge.log("ClaudeNotify: Initializing WebSocket Manager")

        // 延迟启动，避免过早连接
        scope.launch {
            delay(5000) // 等待5秒
            connect()
        }
    }

    private fun connect() {
        try {
            val request = Request.Builder()
                .url(serverUrl)
                .build()

            webSocket = client.newWebSocket(request, object : WebSocketListener() {

                override fun onOpen(webSocket: WebSocket, response: Response) {
                    XposedBridge.log("ClaudeNotify: WebSocket connected")
                    // 发送握手消息
                    webSocket.send("""{"type":"handshake","client":"android"}""")
                }

                override fun onMessage(webSocket: WebSocket, text: String) {
                    XposedBridge.log("ClaudeNotify: Received message: $text")
                    handleMessage(text)
                }

                override fun onFailure(webSocket: WebSocket, t: Throwable, response: Response?) {
                    XposedBridge.log("ClaudeNotify: WebSocket error: ${t.message}")
                    // 重连
                    scope.launch {
                        delay(5000)
                        connect()
                    }
                }

                override fun onClosing(webSocket: WebSocket, code: Int, reason: String) {
                    XposedBridge.log("ClaudeNotify: WebSocket closing: $reason")
                }

                override fun onClosed(webSocket: WebSocket, code: Int, reason: String) {
                    XposedBridge.log("ClaudeNotify: WebSocket closed: $reason")
                    // 重连
                    scope.launch {
                        delay(5000)
                        connect()
                    }
                }
            })

        } catch (e: Exception) {
            XposedBridge.log("ClaudeNotify: Error connecting WebSocket: ${e.message}")
        }
    }

    /**
     * 处理接收到的消息
     */
    private fun handleMessage(json: String) {
        try {
            val message = MessageParser.parse(json)

            when (message.type) {
                "task_start" -> {
                    FluidCloudInjector.showTaskStart(
                        message.data["task"] as? String ?: "Unknown Task"
                    )
                }
                "task_progress" -> {
                    val progress = (message.data["progress"] as? Double)?.toInt() ?: 0
                    val description = message.data["description"] as? String ?: ""
                    FluidCloudInjector.showTaskProgress(progress, description)
                }
                "task_complete" -> {
                    val result = message.data["result"] as? String ?: "Completed"
                    FluidCloudInjector.showTaskComplete(result)
                }
                "command_output" -> {
                    val output = message.data["output"] as? String ?: ""
                    FluidCloudInjector.showCommandOutput(output)
                }
            }

        } catch (e: Exception) {
            XposedBridge.log("ClaudeNotify: Error handling message: ${e.message}")
        }
    }

    fun disconnect() {
        webSocket?.close(1000, "App closing")
        client.dispatcher.executorService.shutdown()
    }
}
