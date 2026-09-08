package com.codex.fluidcloud;

import android.content.ComponentName;
import android.content.Context;
import android.content.Intent;

import org.json.JSONObject;

import java.io.BufferedInputStream;
import java.io.BufferedWriter;
import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.OutputStreamWriter;
import java.net.InetAddress;
import java.net.ServerSocket;
import java.net.Socket;
import java.nio.charset.StandardCharsets;
import java.security.MessageDigest;
import java.util.concurrent.ArrayBlockingQueue;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.RejectedExecutionException;
import java.util.concurrent.ThreadPoolExecutor;
import java.util.concurrent.TimeUnit;

import de.robv.android.xposed.XposedBridge;

/** Authenticated newline-delimited JSON server for the Windows bridge. */
final class BridgeServer {
    static final int PORT = 24680;
    private static final int MAX_EVENT_BYTES = 16 * 1024;
    private static final int READ_TIMEOUT_MS = 30_000;
    private static final int CLIENT_THREADS = 2;
    private static final int MAX_PENDING_CLIENTS = 8;

    private final EventDeduplicator deduplicator = new EventDeduplicator();
    private final Context context;
    private final ExecutorService clients = new ThreadPoolExecutor(
            CLIENT_THREADS,
            CLIENT_THREADS,
            0L,
            TimeUnit.MILLISECONDS,
            new ArrayBlockingQueue<>(MAX_PENDING_CLIENTS),
            runnable -> {
                Thread thread = new Thread(runnable, "codex-fluid-client");
                thread.setDaemon(true);
                return thread;
            },
            new ThreadPoolExecutor.AbortPolicy());

    BridgeServer(Context context) {
        this.context = context;
    }

    void start() {
        Thread listener = new Thread(this::listen, "codex-fluid-listener");
        listener.setDaemon(true);
        listener.start();
    }

    private void listen() {
        try (ServerSocket server = new ServerSocket(
                PORT, 8, InetAddress.getByName("0.0.0.0"))) {
            XposedBridge.log("CodexFluidCloud: listening on TCP " + PORT);
            while (!server.isClosed()) {
                Socket socket = server.accept();
                try {
                    clients.execute(() -> handle(socket));
                } catch (RejectedExecutionException rejected) {
                    closeQuietly(socket);
                }
            }
        } catch (Throwable error) {
            XposedBridge.log("CodexFluidCloud: bridge stopped: " + error);
        }
    }

    private void handle(Socket socket) {
        try (Socket owned = socket;
             BufferedInputStream input = new BufferedInputStream(owned.getInputStream());
             BufferedWriter output = new BufferedWriter(new OutputStreamWriter(
                     owned.getOutputStream(), StandardCharsets.UTF_8))) {
            owned.setSoTimeout(READ_TIMEOUT_MS);
            String line;
            while ((line = readLine(input)) != null) {
                process(line, output);
            }
        } catch (IOException ignored) {
            // Clients normally close immediately after the acknowledgement.
        } catch (Throwable error) {
            XposedBridge.log("CodexFluidCloud: client error: " + error);
        }
    }

    private void process(String line, BufferedWriter output) throws IOException {
        try {
            JSONObject event = new JSONObject(line);
            if (!tokenMatches(event.optString("token", ""))) {
                reply(output, "{\"ok\":false,\"error\":\"unauthorized\"}");
                return;
            }
            if (!deduplicator.accept(event)) {
                reply(output, "{\"ok\":true,\"duplicate\":true}");
                return;
            }
            forward(event);
            reply(output, "{\"ok\":true}");
        } catch (Throwable invalid) {
            reply(output, "{\"ok\":false,\"error\":\"invalid_event\"}");
        }
    }

    private static boolean tokenMatches(String supplied) {
        return MessageDigest.isEqual(
                supplied.getBytes(StandardCharsets.UTF_8),
                BuildConfig.BRIDGE_TOKEN.getBytes(StandardCharsets.UTF_8));
    }

    private void forward(JSONObject event) {
        event.remove("token");
        Intent intent = new Intent(BridgeContract.ACTION_SHOW_EVENT)
                .setComponent(new ComponentName(
                        BridgeContract.MODULE_PACKAGE,
                        BridgeContract.RECEIVER_CLASS))
                .addFlags(Intent.FLAG_INCLUDE_STOPPED_PACKAGES)
                .putExtra(BridgeContract.EXTRA_EVENT_JSON, event.toString());
        context.sendBroadcast(intent);
    }

    private static String readLine(BufferedInputStream input) throws IOException {
        ByteArrayOutputStream buffer = new ByteArrayOutputStream(512);
        while (true) {
            int value = input.read();
            if (value == -1) {
                return buffer.size() == 0 ? null : buffer.toString(StandardCharsets.UTF_8.name());
            }
            if (value == '\n') {
                byte[] bytes = buffer.toByteArray();
                int length = bytes.length;
                if (length > 0 && bytes[length - 1] == '\r') {
                    length--;
                }
                return new String(bytes, 0, length, StandardCharsets.UTF_8);
            }
            if (buffer.size() >= MAX_EVENT_BYTES) {
                throw new IOException("event exceeds " + MAX_EVENT_BYTES + " bytes");
            }
            buffer.write(value);
        }
    }

    private static void reply(BufferedWriter output, String json) throws IOException {
        output.write(json);
        output.write('\n');
        output.flush();
    }

    private static void closeQuietly(Socket socket) {
        try {
            socket.close();
        } catch (IOException ignored) {
            // The peer may already have closed the rejected connection.
        }
    }
}
