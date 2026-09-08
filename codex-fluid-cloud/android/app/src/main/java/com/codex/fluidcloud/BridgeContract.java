package com.codex.fluidcloud;

/** Explicit System UI-to-module broadcast contract. */
final class BridgeContract {
    static final String MODULE_PACKAGE = "com.codex.fluidcloud";
    static final String RECEIVER_CLASS = MODULE_PACKAGE + ".NotificationEventReceiver";
    static final String ACTION_SHOW_EVENT = MODULE_PACKAGE + ".action.SHOW_EVENT";
    static final String EXTRA_EVENT_JSON = "event_json";

    private BridgeContract() {
    }
}
