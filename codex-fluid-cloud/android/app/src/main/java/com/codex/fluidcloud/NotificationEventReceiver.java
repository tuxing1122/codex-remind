package com.codex.fluidcloud;

import android.content.BroadcastReceiver;
import android.content.Context;
import android.content.Intent;
import android.util.Log;

import org.json.JSONObject;

/** Publishes an authenticated bridge event from the module application's UID. */
public final class NotificationEventReceiver extends BroadcastReceiver {
    private static final String LOG_TAG = "CodexFluidCloud";

    @Override
    public void onReceive(Context context, Intent intent) {
        if (intent == null || !BridgeContract.ACTION_SHOW_EVENT.equals(intent.getAction())) {
            return;
        }
        String eventJson = intent.getStringExtra(BridgeContract.EXTRA_EVENT_JSON);
        if (eventJson == null || eventJson.isEmpty()) {
            return;
        }
        try {
            JSONObject event = new JSONObject(eventJson);
            new FluidCloudNotifier(context.getApplicationContext()).show(event);
        } catch (Throwable invalid) {
            Log.w(LOG_TAG, "Ignored invalid notification event", invalid);
        }
    }
}
