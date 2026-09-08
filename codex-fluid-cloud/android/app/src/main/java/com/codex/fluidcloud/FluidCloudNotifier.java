package com.codex.fluidcloud;

import android.annotation.SuppressLint;
import android.app.Notification;
import android.app.NotificationChannel;
import android.app.NotificationManager;
import android.content.Context;
import android.graphics.Color;
import android.os.Build;
import android.util.Log;

import org.json.JSONObject;

import java.util.Locale;

/** Maps bridge events to Android 16 live updates with a normal notification fallback. */
final class FluidCloudNotifier {
    private static final String LOG_TAG = "CodexFluidCloud";
    private static final String CHANNEL_ID = "codex_fluid_progress";
    private static final String NOTIFICATION_TAG = "codex-fluid-cloud";
    private static final int DEFAULT_NOTIFICATION_ID = 24680;
    private static final int TASK_NOTIFICATION_ID_PREFIX = 0x40000000;
    private static final int TASK_NOTIFICATION_ID_MASK = 0x3fffffff;
    private static final long RUNNING_TIMEOUT_MS = 30 * 60 * 1000L;
    private static final long COMPLETION_TIMEOUT_MS = 10 * 60 * 1000L;
    // Android 16's public SDK exposes the result flag but not this request key.
    private static final String EXTRA_REQUEST_PROMOTED_ONGOING =
            "android.requestPromotedOngoing";

    private final Context context;
    private final NotificationManager manager;

    FluidCloudNotifier(Context context) {
        this.context = context;
        this.manager = context.getSystemService(NotificationManager.class);
        createChannel();
    }

    void show(JSONObject event) {
        if (manager == null) {
            return;
        }
        String type = event.optString("type", "progress").toLowerCase(Locale.ROOT);
        String taskId = normalizeTaskId(event.optString("task_id", ""));
        String notificationTag = notificationTagForTask(taskId);
        int notificationId = notificationIdForTask(taskId);
        if ("clear".equals(type)) {
            manager.cancel(notificationTag, notificationId);
            return;
        }

        boolean terminal = event.optBoolean("terminal", false) || isTerminalType(type);
        boolean failed = "failed".equals(type) || "error".equals(type);
        EventProgress progress = readProgress(event);
        Notification notification;
        try {
            notification = build(event, type, terminal, failed, progress, true);
        } catch (Throwable promotedError) {
            Log.w(LOG_TAG, "Promoted notification fallback", promotedError);
            notification = build(event, type, terminal, failed, progress, false);
        }
        manager.notify(notificationTag, notificationId, notification);
    }

    private Notification build(
            JSONObject event,
            String type,
            boolean terminal,
            boolean failed,
            EventProgress progress,
            boolean allowPromoted) {
        String title = clip(event.optString("title", "Codex"), 80);
        String fallbackMessage = terminal ? "Task completed" : "Working";
        String message = clip(event.optString("message", fallbackMessage), 240);

        Notification.Builder builder = new Notification.Builder(context, CHANNEL_ID)
                .setSmallIcon(android.R.drawable.ic_dialog_info)
                .setContentTitle(title)
                .setContentText(message)
                .setCategory(failed ? Notification.CATEGORY_ERROR : Notification.CATEGORY_PROGRESS)
                .setVisibility(Notification.VISIBILITY_PRIVATE)
                .setColor(failed ? Color.rgb(211, 47, 47) : Color.rgb(25, 118, 210))
                .setOngoing(!terminal)
                .setOnlyAlertOnce(!terminal)
                .setShowWhen(false);

        if (terminal) {
            builder.setStyle(new Notification.BigTextStyle().bigText(message));
            builder.setProgress(0, 0, false);
            builder.setTimeoutAfter(COMPLETION_TIMEOUT_MS);
        } else if (allowPromoted && Build.VERSION.SDK_INT >= 36) {
            builder.setTimeoutAfter(RUNNING_TIMEOUT_MS);
            applyAndroid16Progress(builder, progress);
        } else if (progress.percent >= 0) {
            builder.setTimeoutAfter(RUNNING_TIMEOUT_MS);
            builder.setProgress(100, progress.percent, false);
        } else {
            builder.setTimeoutAfter(RUNNING_TIMEOUT_MS);
            builder.setProgress(100, 0, true);
        }

        return builder.build();
    }

    @SuppressLint("NewApi")
    private static void applyAndroid16Progress(
            Notification.Builder builder, EventProgress progress) {
        Notification.ProgressStyle style = new Notification.ProgressStyle();
        if (progress.percent >= 0) {
            style.setProgress(progress.percent);
            builder.setShortCriticalText(progress.percent + "%");
        } else {
            style.setProgressIndeterminate(true);
            builder.setShortCriticalText("Codex");
        }
        builder.getExtras().putBoolean(EXTRA_REQUEST_PROMOTED_ONGOING, true);
        builder.setStyle(style);
    }

    private void createChannel() {
        if (manager == null) {
            return;
        }
        NotificationChannel channel = new NotificationChannel(
                CHANNEL_ID, "Codex task progress", NotificationManager.IMPORTANCE_DEFAULT);
        channel.setDescription("Live progress and completion updates from Windows Codex");
        channel.setShowBadge(false);
        manager.createNotificationChannel(channel);
    }

    private static boolean isTerminalType(String type) {
        return "complete".equals(type)
                || "completed".equals(type)
                || "done".equals(type)
                || "success".equals(type)
                || "failed".equals(type)
                || "error".equals(type)
                || "cancelled".equals(type);
    }

    private static EventProgress readProgress(JSONObject event) {
        int direct = event.optInt("percent", -1);
        if (direct >= 0) {
            return new EventProgress(clamp(direct));
        }
        JSONObject nested = event.optJSONObject("progress");
        if (nested == null) {
            return new EventProgress(-1);
        }
        double current = nested.optDouble("current", -1.0);
        double total = nested.optDouble("total", -1.0);
        if (current < 0.0 || total <= 0.0) {
            return new EventProgress(-1);
        }
        return new EventProgress(clamp((int) Math.round(current * 100.0 / total)));
    }

    private static int clamp(int value) {
        return Math.max(0, Math.min(100, value));
    }

    static int notificationIdForTask(String taskId) {
        String normalized = normalizeTaskId(taskId);
        if (normalized.isEmpty()) {
            return DEFAULT_NOTIFICATION_ID;
        }
        return TASK_NOTIFICATION_ID_PREFIX
                | (normalized.hashCode() & TASK_NOTIFICATION_ID_MASK);
    }

    static String notificationTagForTask(String taskId) {
        String normalized = normalizeTaskId(taskId);
        return normalized.isEmpty() ? NOTIFICATION_TAG : NOTIFICATION_TAG + ":" + normalized;
    }

    private static String normalizeTaskId(String taskId) {
        return taskId == null ? "" : taskId.trim();
    }

    private static String clip(String value, int maxLength) {
        if (value == null) {
            return "";
        }
        return value.length() <= maxLength
                ? value
                : value.substring(0, maxLength - 3) + "...";
    }

    private static final class EventProgress {
        final int percent;

        EventProgress(int percent) {
            this.percent = percent;
        }
    }
}
