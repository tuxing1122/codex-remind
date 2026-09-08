package com.claude.notify

import com.google.gson.Gson
import com.google.gson.JsonObject

/**
 * 消息数据结构
 */
data class ClaudeMessage(
    val type: String,
    val timestamp: Long,
    val data: Map<String, Any>
)

/**
 * 消息解析器
 */
object MessageParser {

    private val gson = Gson()

    fun parse(json: String): ClaudeMessage {
        val jsonObject = gson.fromJson(json, JsonObject::class.java)

        val type = jsonObject.get("type")?.asString ?: "unknown"
        val timestamp = jsonObject.get("timestamp")?.asLong ?: System.currentTimeMillis()

        val dataObject = jsonObject.getAsJsonObject("data")
        val data = mutableMapOf<String, Any>()

        dataObject?.entrySet()?.forEach { entry ->
            val value = entry.value
            data[entry.key] = when {
                value.isJsonPrimitive -> {
                    val primitive = value.asJsonPrimitive
                    when {
                        primitive.isString -> primitive.asString
                        primitive.isNumber -> primitive.asDouble
                        primitive.isBoolean -> primitive.asBoolean
                        else -> value.toString()
                    }
                }
                else -> value.toString()
            }
        }

        return ClaudeMessage(type, timestamp, data)
    }
}
