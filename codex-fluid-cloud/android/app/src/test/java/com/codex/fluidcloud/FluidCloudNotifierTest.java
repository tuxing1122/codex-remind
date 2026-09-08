package com.codex.fluidcloud;

import static org.junit.Assert.assertEquals;
import static org.junit.Assert.assertNotEquals;
import static org.junit.Assert.assertTrue;

import org.junit.Test;

public final class FluidCloudNotifierTest {
    @Test
    public void notificationIdIsStableForTask() {
        int first = FluidCloudNotifier.notificationIdForTask("root-task-42");
        int second = FluidCloudNotifier.notificationIdForTask("root-task-42");

        assertEquals(first, second);
        assertTrue(first > 0);
    }

    @Test
    public void notificationIdSeparatesTypicalTaskIds() {
        int first = FluidCloudNotifier.notificationIdForTask("root-task-1");
        int second = FluidCloudNotifier.notificationIdForTask("root-task-2");

        assertNotEquals(first, second);
    }

    @Test
    public void notificationTagSeparatesHashCollisions() {
        assertEquals(
                FluidCloudNotifier.notificationIdForTask("Aa"),
                FluidCloudNotifier.notificationIdForTask("BB"));
        assertNotEquals(
                FluidCloudNotifier.notificationTagForTask("Aa"),
                FluidCloudNotifier.notificationTagForTask("BB"));
    }

    @Test
    public void notificationIdNormalizesWhitespace() {
        assertEquals(
                FluidCloudNotifier.notificationIdForTask("root-task-42"),
                FluidCloudNotifier.notificationIdForTask("  root-task-42  "));
    }

    @Test
    public void notificationIdFallsBackWhenTaskIsMissing() {
        assertEquals(24680, FluidCloudNotifier.notificationIdForTask(null));
        assertEquals(24680, FluidCloudNotifier.notificationIdForTask("   "));
    }
}
