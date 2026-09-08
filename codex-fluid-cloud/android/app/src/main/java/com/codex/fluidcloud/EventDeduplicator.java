package com.codex.fluidcloud;

import org.json.JSONObject;

import java.util.LinkedHashMap;
import java.util.Map;

/** Bounds replay memory while rejecting duplicate IDs and stale task sequences. */
final class EventDeduplicator {
    private static final int MAX_EVENT_IDS = 512;
    private static final int MAX_TASKS = 128;

    private final Map<String, Boolean> eventIds = new LinkedHashMap<String, Boolean>(
            MAX_EVENT_IDS + 1, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<String, Boolean> eldest) {
            return size() > MAX_EVENT_IDS;
        }
    };
    private final Map<String, Long> taskSequences = new LinkedHashMap<String, Long>(
            MAX_TASKS + 1, 0.75f, true) {
        @Override
        protected boolean removeEldestEntry(Map.Entry<String, Long> eldest) {
            return size() > MAX_TASKS;
        }
    };

    synchronized boolean accept(JSONObject event) {
        String eventId = event.optString("event_id", "").trim();
        if (!eventId.isEmpty() && eventIds.containsKey(eventId)) {
            return false;
        }

        String taskId = event.optString("task_id", "").trim();
        long sequence = event.optLong("sequence", -1L);
        if (!taskId.isEmpty() && sequence >= 0L) {
            Long previous = taskSequences.get(taskId);
            if (previous != null && sequence <= previous) {
                return false;
            }
            taskSequences.put(taskId, sequence);
        }
        if (!eventId.isEmpty()) {
            eventIds.put(eventId, Boolean.TRUE);
        }
        return true;
    }
}
