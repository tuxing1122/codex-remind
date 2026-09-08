package com.codex.fluidcloud;

import android.app.Application;
import android.content.Context;

import java.util.concurrent.atomic.AtomicBoolean;

import de.robv.android.xposed.IXposedHookLoadPackage;
import de.robv.android.xposed.XC_MethodHook;
import de.robv.android.xposed.XposedBridge;
import de.robv.android.xposed.XposedHelpers;
import de.robv.android.xposed.callbacks.XC_LoadPackage;

/** LSPosed entry point. The module is intentionally scoped only to SystemUI. */
public final class FluidCloudHook implements IXposedHookLoadPackage {
    private static final String SYSTEM_UI = "com.android.systemui";
    private static final AtomicBoolean STARTED = new AtomicBoolean();

    @Override
    public void handleLoadPackage(XC_LoadPackage.LoadPackageParam loadPackageParam) {
        if (!SYSTEM_UI.equals(loadPackageParam.packageName)
                || !SYSTEM_UI.equals(loadPackageParam.processName)) {
            return;
        }

        try {
            XposedHelpers.findAndHookMethod(
                    "com.android.systemui.SystemUIApplication",
                    loadPackageParam.classLoader,
                    "onCreate",
                    new XC_MethodHook() {
                        @Override
                        protected void afterHookedMethod(MethodHookParam param) {
                            if (!STARTED.compareAndSet(false, true)) {
                                return;
                            }
                            Context context = ((Application) param.thisObject).getApplicationContext();
                            new BridgeServer(context).start();
                        }
                    });
            XposedBridge.log("CodexFluidCloud: SystemUIApplication hook installed");
        } catch (Throwable error) {
            XposedBridge.log("CodexFluidCloud: unable to hook SystemUIApplication.onCreate: " + error);
        }
    }
}
