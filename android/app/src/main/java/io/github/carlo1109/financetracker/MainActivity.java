package io.github.carlo1109.financetracker;

import android.app.Activity;
import android.app.KeyguardManager;
import android.content.ActivityNotFoundException;
import android.content.ClipData;
import android.content.ContentResolver;
import android.content.ContentValues;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.pm.ApplicationInfo;
import android.graphics.Color;
import android.hardware.biometrics.BiometricManager;
import android.hardware.biometrics.BiometricPrompt;
import android.net.Uri;
import android.os.Build;
import android.os.Bundle;
import android.os.CancellationSignal;
import android.os.Environment;
import android.os.SystemClock;
import android.provider.DocumentsContract;
import android.provider.MediaStore;
import android.util.Base64;
import android.util.Log;
import android.util.TypedValue;
import android.view.Gravity;
import android.view.View;
import android.view.ViewGroup;
import android.view.WindowInsets;
import android.view.WindowManager;
import android.webkit.ConsoleMessage;
import android.webkit.JavascriptInterface;
import android.webkit.RenderProcessGoneDetail;
import android.webkit.ServiceWorkerClient;
import android.webkit.ServiceWorkerController;
import android.webkit.ValueCallback;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebResourceResponse;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.Button;
import android.widget.FrameLayout;
import android.widget.ImageView;
import android.widget.LinearLayout;
import android.widget.TextView;
import android.widget.Toast;

import org.json.JSONException;
import org.json.JSONObject;

import java.io.ByteArrayInputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.util.HashMap;
import java.util.Locale;
import java.util.Map;

/**
 * Involucro nativo di FinanceTracker.
 *
 * L'interfaccia è l'app Streamlit originale, eseguita dentro la WebView
 * con stlite (Streamlit + Python/Pyodide in WebAssembly). Tutti i file
 * stanno nell'APK (assets/web) e vengono serviti da qui sotto l'indirizzo
 * https://appassets.androidplatform.net/ : nessun accesso a internet.
 *
 * Dati: una copia interna (IndexedDB della WebView) per la velocità e,
 * se l'utente l'ha scelta, la cartella sul telefono (FolderStorage), dove
 * la pagina copia database e categorie dopo ogni modifica.
 *
 * Blocco: se attivo, l'app chiede impronta/volto/PIN del telefono
 * all'avvio e quando torna in primo piano dopo un po'.
 */
public class MainActivity extends Activity {

    private static final String TAG = "FinanceTracker";
    private static final String HOST = "appassets.androidplatform.net";
    private static final String START_URL = "https://" + HOST + "/";
    private static final String ASSET_ROOT = "web/";
    private static final String BACKUP_PREFIX = "FinanceTracker_Backup_";

    private static final int FILE_CHOOSER_REQUEST = 4101;
    private static final int FOLDER_PICKER_REQUEST = 4102;

    private static final String PREFS = "ft_prefs";
    private static final String KEY_LOCK = "lock_enabled";
    private static final long RELOCK_AFTER_MS = 30_000;

    private static final int AUTH_UNLOCK = 0;
    private static final int AUTH_ENABLE = 1;
    private static final int AUTH_DISABLE = 2;

    private static final Map<String, String> MIME_TYPES = new HashMap<>();

    static {
        MIME_TYPES.put("html", "text/html");
        MIME_TYPES.put("js", "text/javascript");
        MIME_TYPES.put("mjs", "text/javascript");
        MIME_TYPES.put("css", "text/css");
        MIME_TYPES.put("json", "application/json");
        MIME_TYPES.put("wasm", "application/wasm");
        MIME_TYPES.put("whl", "application/zip");
        MIME_TYPES.put("zip", "application/zip");
        MIME_TYPES.put("tar", "application/x-tar");
        MIME_TYPES.put("png", "image/png");
        MIME_TYPES.put("jpg", "image/jpeg");
        MIME_TYPES.put("svg", "image/svg+xml");
        MIME_TYPES.put("ico", "image/x-icon");
        MIME_TYPES.put("woff2", "font/woff2");
        MIME_TYPES.put("woff", "font/woff");
        MIME_TYPES.put("ttf", "font/ttf");
        MIME_TYPES.put("py", "text/plain");
        MIME_TYPES.put("toml", "text/plain");
        MIME_TYPES.put("txt", "text/plain");
    }

    private FrameLayout root;
    private WebView webView;
    private View lockOverlay;
    private ValueCallback<Uri[]> pendingFileCallback;
    private FolderStorage storage;
    private SharedPreferences prefs;

    private boolean locked;
    private boolean authInProgress;
    private boolean skipRelockOnce;
    private long pausedAt;

    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);

        boolean debuggable = (getApplicationInfo().flags & ApplicationInfo.FLAG_DEBUGGABLE) != 0;
        WebView.setWebContentsDebuggingEnabled(debuggable);

        storage = new FolderStorage(this);
        prefs = getSharedPreferences(PREFS, MODE_PRIVATE);

        root = new FrameLayout(this);
        root.setBackgroundColor(Color.parseColor("#0B1220"));
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            // Da Android 11 gestiamo noi gli spazi di barre e tastiera
            // (su Android 15 è comunque obbligatorio: edge-to-edge).
            getWindow().setDecorFitsSystemWindows(false);
            applySystemBarInsets(root);
        }
        setContentView(root);

        ServiceWorkerController.getInstance().setServiceWorkerClient(new ServiceWorkerClient() {
            @Override
            public WebResourceResponse shouldInterceptRequest(WebResourceRequest request) {
                return serveAsset(request.getUrl());
            }
        });

        createWebView();
        lockOverlay = buildLockOverlay();
        root.addView(lockOverlay, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));

        if (isLockEnabled()) {
            setSecureWindow(true);
            lock();
        }

        webView.loadUrl(START_URL);
    }

    // ------------------------------------------------------------------ WebView

    private void createWebView() {
        webView = new WebView(this);
        webView.setBackgroundColor(Color.parseColor("#0B1220"));
        webView.setOverScrollMode(View.OVER_SCROLL_NEVER);

        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setDatabaseEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setSupportMultipleWindows(false);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setMediaPlaybackRequiresUserGesture(true);
        settings.setBuiltInZoomControls(false);
        settings.setDisplayZoomControls(false);
        settings.setSupportZoom(false);
        settings.setTextZoom(100);
        settings.setCacheMode(WebSettings.LOAD_DEFAULT);
        settings.setOffscreenPreRaster(true);

        webView.addJavascriptInterface(new Bridge(), "FTAndroid");
        webView.setWebViewClient(new AppWebViewClient());
        webView.setWebChromeClient(new AppChromeClient());

        // Indice 0: la WebView resta sotto la schermata di blocco.
        root.addView(webView, 0, new FrameLayout.LayoutParams(
                ViewGroup.LayoutParams.MATCH_PARENT,
                ViewGroup.LayoutParams.MATCH_PARENT));
    }

    /** Se Android chiude il motore della WebView (poca memoria), lo ricreiamo. */
    private void recreateWebView() {
        if (webView != null) {
            root.removeView(webView);
            webView.destroy();
        }
        createWebView();
        webView.loadUrl(START_URL);
    }

    private void callJs(String function, JSONObject payload) {
        String script = "window." + function + " && window." + function + "(" + payload + ")";
        runOnUiThread(() -> {
            if (webView != null) {
                webView.evaluateJavascript(script, null);
            }
        });
    }

    private class AppWebViewClient extends WebViewClient {
        @Override
        public WebResourceResponse shouldInterceptRequest(WebView view, WebResourceRequest request) {
            return serveAsset(request.getUrl());
        }

        @Override
        public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
            Uri uri = request.getUrl();
            if (HOST.equals(uri.getHost())) {
                return false;
            }
            // Link esterni (es. help): si aprono nel browser del telefono.
            String scheme = uri.getScheme();
            if ("http".equals(scheme) || "https".equals(scheme) || "mailto".equals(scheme)) {
                try {
                    startActivity(new Intent(Intent.ACTION_VIEW, uri));
                } catch (ActivityNotFoundException ignored) {
                    // Nessuna app per aprire il link.
                }
            }
            return true;
        }

        @Override
        public boolean onRenderProcessGone(WebView view, RenderProcessGoneDetail detail) {
            Log.w(TAG, "Processo WebView terminato, riavvio dell'interfaccia");
            recreateWebView();
            return true;
        }
    }

    private class AppChromeClient extends WebChromeClient {
        @Override
        public boolean onShowFileChooser(WebView view,
                                         ValueCallback<Uri[]> callback,
                                         FileChooserParams params) {
            if (pendingFileCallback != null) {
                pendingFileCallback.onReceiveValue(null);
            }
            pendingFileCallback = callback;

            // */* perché i CSV/XLSX delle banche arrivano con tipi MIME molto vari.
            Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT);
            intent.addCategory(Intent.CATEGORY_OPENABLE);
            intent.setType("*/*");
            if (params.getMode() == FileChooserParams.MODE_OPEN_MULTIPLE) {
                intent.putExtra(Intent.EXTRA_ALLOW_MULTIPLE, true);
            }

            if (startForResult(intent, FILE_CHOOSER_REQUEST)) {
                return true;
            }
            pendingFileCallback = null;
            callback.onReceiveValue(null);
            return false;
        }

        @Override
        public boolean onConsoleMessage(ConsoleMessage message) {
            if (message.messageLevel() == ConsoleMessage.MessageLevel.ERROR) {
                Log.e(TAG, message.message() + " (" + message.sourceId() + ":" + message.lineNumber() + ")");
            }
            return true;
        }
    }

    private boolean startForResult(Intent intent, int requestCode) {
        try {
            startActivityForResult(intent, requestCode);
            return true;
        } catch (ActivityNotFoundException e) {
            return false;
        }
    }

    @Override
    protected void onActivityResult(int requestCode, int resultCode, Intent data) {
        // Rientro da un selettore aperto dall'app: non è un "ritorno" da bloccare.
        skipRelockOnce = true;

        if (requestCode == FILE_CHOOSER_REQUEST) {
            deliverChosenFiles(resultCode, data);
        } else if (requestCode == FOLDER_PICKER_REQUEST) {
            deliverChosenFolder(resultCode, data);
        } else {
            super.onActivityResult(requestCode, resultCode, data);
        }
    }

    private void deliverChosenFiles(int resultCode, Intent data) {
        if (pendingFileCallback == null) {
            return;
        }
        Uri[] result = null;
        if (resultCode == RESULT_OK && data != null) {
            ClipData clip = data.getClipData();
            if (clip != null && clip.getItemCount() > 0) {
                result = new Uri[clip.getItemCount()];
                for (int i = 0; i < clip.getItemCount(); i++) {
                    result[i] = clip.getItemAt(i).getUri();
                }
            } else if (data.getData() != null) {
                result = new Uri[]{data.getData()};
            }
        }
        pendingFileCallback.onReceiveValue(result);
        pendingFileCallback = null;
    }

    private void deliverChosenFolder(int resultCode, Intent data) {
        JSONObject result = new JSONObject();
        try {
            if (resultCode == RESULT_OK && data != null && data.getData() != null) {
                storage.setTree(data.getData());
                result.put("ok", true);
                result.put("label", storage.label());
                result.put("hasData", storage.exists("finance_tracker.db"));
            } else {
                result.put("ok", false);
                result.put("cancelled", true);
            }
        } catch (RuntimeException | JSONException e) {
            Log.e(TAG, "Scelta cartella non riuscita", e);
            putQuietly(result, "ok", false);
            putQuietly(result, "error", "Non riesco a usare questa cartella: " + e.getMessage());
        }
        callJs("__ftFolderPicked", result);
    }

    // ------------------------------------------------------------------ assets

    /** Serve i file da assets/web per l'indirizzo interno dell'app. */
    private WebResourceResponse serveAsset(Uri uri) {
        if (uri == null) {
            return null;
        }
        if (!HOST.equals(uri.getHost())) {
            // App offline: nessuna richiesta di rete verso l'esterno
            // (es. i controlli di stlite verso "stlite.invalid").
            String scheme = uri.getScheme();
            if ("http".equals(scheme) || "https".equals(scheme)) {
                return notFound(new HashMap<>());
            }
            return null;
        }

        String path = uri.getPath();
        if (path == null || path.isEmpty() || "/".equals(path)) {
            path = "/index.html";
        }
        path = path.substring(1);

        Map<String, String> headers = new HashMap<>();
        headers.put("Access-Control-Allow-Origin", "*");
        headers.put("Cache-Control", "no-cache");

        if (path.contains("..")) {
            return notFound(headers);
        }

        InputStream stream = openAsset(path);

        // Pagine dell'app (/movimenti, /impostazioni, ...): stessa index.html.
        if (stream == null && extensionOf(path).isEmpty()) {
            path = "index.html";
            stream = openAsset(path);
        }
        if (stream == null) {
            return notFound(headers);
        }

        String mime = mimeTypeOf(path);
        String encoding = mime.startsWith("text/") || mime.equals("application/json") ? "utf-8" : null;
        return new WebResourceResponse(mime, encoding, 200, "OK", headers, stream);
    }

    private InputStream openAsset(String path) {
        try {
            return getAssets().open(ASSET_ROOT + path);
        } catch (IOException e) {
            return null;
        }
    }

    private static WebResourceResponse notFound(Map<String, String> headers) {
        return new WebResourceResponse("text/plain", "utf-8", 404, "Not Found", headers,
                new ByteArrayInputStream(new byte[0]));
    }

    private static String extensionOf(String path) {
        int slash = path.lastIndexOf('/');
        int dot = path.lastIndexOf('.');
        return dot > slash ? path.substring(dot + 1).toLowerCase(Locale.ROOT) : "";
    }

    private static String mimeTypeOf(String path) {
        String mime = MIME_TYPES.get(extensionOf(path));
        return mime != null ? mime : "application/octet-stream";
    }

    // ------------------------------------------------------------------ ponte JS

    /** Metodi chiamati dalla pagina come window.FTAndroid.* (sempre stringhe/JSON). */
    public class Bridge {

        // --- download (Excel, backup) ---

        @JavascriptInterface
        public void saveFile(String fileName, String mimeType, String base64) {
            String name = sanitizeFileName(fileName);
            try {
                byte[] bytes = Base64.decode(base64, Base64.DEFAULT);
                String savedAs = saveToDownloads(name, mimeType, bytes);
                String message = "Salvato in Download: " + savedAs;

                // I backup finiscono anche nella cartella dei dati, come sul PC.
                if (name.startsWith(BACKUP_PREFIX) && storage.isConfigured()) {
                    storage.write("backups/" + name, bytes);
                    message += " e nella cartella dei dati";
                }
                showToast(message);
            } catch (Exception e) {
                Log.e(TAG, "Salvataggio non riuscito", e);
                showToast("Salvataggio non riuscito: " + e.getMessage());
            }
        }

        @JavascriptInterface
        public void toast(String message) {
            showToast(message);
        }

        @JavascriptInterface
        public void appReady() {
            Log.i(TAG, "Interfaccia pronta");
        }

        // --- cartella dei dati ---

        @JavascriptInterface
        public String storageState() {
            JSONObject state = new JSONObject();
            boolean configured = storage.isConfigured();
            putQuietly(state, "configured", configured);
            putQuietly(state, "prompted", storage.wasPrompted());
            putQuietly(state, "label", configured ? storage.label() : "");
            return state.toString();
        }

        @JavascriptInterface
        public void pickFolder() {
            runOnUiThread(() -> {
                Intent intent = new Intent(Intent.ACTION_OPEN_DOCUMENT_TREE);
                intent.addFlags(FolderStorage.GRANT_FLAGS
                        | Intent.FLAG_GRANT_PERSISTABLE_URI_PERMISSION
                        | Intent.FLAG_GRANT_PREFIX_URI_PERMISSION);
                intent.putExtra(DocumentsContract.EXTRA_INITIAL_URI, DocumentsContract.buildDocumentUri(
                        "com.android.externalstorage.documents", "primary:Documents"));
                if (!startForResult(intent, FOLDER_PICKER_REQUEST)) {
                    JSONObject result = new JSONObject();
                    putQuietly(result, "ok", false);
                    putQuietly(result, "error", "Su questo telefono non c'è un selettore di cartelle.");
                    callJs("__ftFolderPicked", result);
                }
            });
        }

        @JavascriptInterface
        public void skipFolderPrompt() {
            storage.markPrompted();
        }

        @JavascriptInterface
        public String folderRead(String relativePath) {
            JSONObject result = new JSONObject();
            try {
                byte[] data = storage.read(relativePath);
                putQuietly(result, "ok", true);
                if (data == null) {
                    putQuietly(result, "missing", true);
                } else {
                    FolderStorage.FileInfo info = storage.info(relativePath);
                    putQuietly(result, "data", Base64.encodeToString(data, Base64.NO_WRAP));
                    putQuietly(result, "size", info != null ? info.size : data.length);
                    putQuietly(result, "modified", info != null ? info.modified : 0);
                }
            } catch (IOException | RuntimeException e) {
                putQuietly(result, "ok", false);
                putQuietly(result, "error", String.valueOf(e.getMessage()));
            }
            return result.toString();
        }

        @JavascriptInterface
        public String folderInfo(String relativePath) {
            JSONObject result = new JSONObject();
            try {
                FolderStorage.FileInfo info = storage.info(relativePath);
                putQuietly(result, "ok", true);
                putQuietly(result, "exists", info != null);
                if (info != null) {
                    putQuietly(result, "size", info.size);
                    putQuietly(result, "modified", info.modified);
                }
            } catch (IOException | RuntimeException e) {
                putQuietly(result, "ok", false);
                putQuietly(result, "error", String.valueOf(e.getMessage()));
            }
            return result.toString();
        }

        @JavascriptInterface
        public String folderWrite(String relativePath, String base64) {
            JSONObject result = new JSONObject();
            try {
                storage.write(relativePath, Base64.decode(base64, Base64.DEFAULT));
                FolderStorage.FileInfo info = storage.info(relativePath);
                putQuietly(result, "ok", true);
                putQuietly(result, "size", info != null ? info.size : -1);
                putQuietly(result, "modified", info != null ? info.modified : 0);
            } catch (IOException | RuntimeException e) {
                Log.e(TAG, "Scrittura nella cartella non riuscita", e);
                putQuietly(result, "ok", false);
                putQuietly(result, "error", String.valueOf(e.getMessage()));
            }
            return result.toString();
        }

        // --- blocco con impronta / PIN ---

        @JavascriptInterface
        public String lockState() {
            JSONObject state = new JSONObject();
            putQuietly(state, "available", isDeviceSecure());
            putQuietly(state, "enabled", isLockEnabled());
            return state.toString();
        }

        @JavascriptInterface
        public void setLockEnabled(boolean enabled) {
            runOnUiThread(() -> {
                if (!isDeviceSecure()) {
                    JSONObject result = new JSONObject();
                    putQuietly(result, "ok", false);
                    putQuietly(result, "enabled", isLockEnabled());
                    putQuietly(result, "error",
                            "Imposta prima un blocco schermo (PIN, sequenza o impronta) nelle impostazioni del telefono.");
                    callJs("__ftLockChanged", result);
                    return;
                }
                authenticate(enabled ? AUTH_ENABLE : AUTH_DISABLE);
            });
        }
    }

    private static void putQuietly(JSONObject object, String key, Object value) {
        try {
            object.put(key, value);
        } catch (JSONException ignored) {
            // Le chiavi sono fisse: non succede.
        }
    }

    // ------------------------------------------------------------------ download

    private String saveToDownloads(String name, String mimeType, byte[] bytes) throws IOException {
        ContentResolver resolver = getContentResolver();
        ContentValues values = new ContentValues();
        values.put(MediaStore.Downloads.DISPLAY_NAME, name);
        values.put(MediaStore.Downloads.MIME_TYPE,
                mimeType == null || mimeType.isEmpty() ? "application/octet-stream" : mimeType);
        values.put(MediaStore.Downloads.RELATIVE_PATH, Environment.DIRECTORY_DOWNLOADS);
        values.put(MediaStore.Downloads.IS_PENDING, 1);

        Uri item = resolver.insert(MediaStore.Downloads.EXTERNAL_CONTENT_URI, values);
        if (item == null) {
            throw new IOException("impossibile creare il file in Download");
        }

        try (OutputStream out = resolver.openOutputStream(item)) {
            if (out == null) {
                throw new IOException("impossibile scrivere il file");
            }
            out.write(bytes);
        } catch (IOException e) {
            resolver.delete(item, null, null);
            throw e;
        }

        ContentValues done = new ContentValues();
        done.put(MediaStore.Downloads.IS_PENDING, 0);
        resolver.update(item, done, null, null);

        // Android può rinominare il file se esiste già (es. "file (1).xlsx").
        String finalName = name;
        try (android.database.Cursor cursor = resolver.query(item,
                new String[]{MediaStore.Downloads.DISPLAY_NAME}, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                finalName = cursor.getString(0);
            }
        }
        return finalName;
    }

    private static String sanitizeFileName(String name) {
        String cleaned = name == null ? "" : name.replaceAll("[\\\\/:*?\"<>|\\x00-\\x1f]", "_").trim();
        return cleaned.isEmpty() ? "FinanceTracker_download" : cleaned;
    }

    private void showToast(String message) {
        runOnUiThread(() -> Toast.makeText(this, message, Toast.LENGTH_LONG).show());
    }

    // ------------------------------------------------------------------ blocco

    private boolean isLockEnabled() {
        return prefs.getBoolean(KEY_LOCK, false);
    }

    private boolean isDeviceSecure() {
        KeyguardManager keyguard = getSystemService(KeyguardManager.class);
        return keyguard != null && keyguard.isDeviceSecure();
    }

    /** Con il blocco attivo: niente screenshot e anteprima nascosta tra le app recenti. */
    private void setSecureWindow(boolean secure) {
        if (secure) {
            getWindow().addFlags(WindowManager.LayoutParams.FLAG_SECURE);
        } else {
            getWindow().clearFlags(WindowManager.LayoutParams.FLAG_SECURE);
        }
    }

    private void lock() {
        locked = true;
        lockOverlay.setVisibility(View.VISIBLE);
    }

    private void unlock() {
        locked = false;
        lockOverlay.setVisibility(View.GONE);
    }

    private void authenticate(int purpose) {
        if (authInProgress) {
            return;
        }
        authInProgress = true;

        String subtitle = purpose == AUTH_UNLOCK
                ? "Usa impronta, volto o PIN del telefono"
                : purpose == AUTH_ENABLE
                ? "Conferma per attivare il blocco dell'app"
                : "Conferma per disattivare il blocco dell'app";

        BiometricPrompt.Builder builder = new BiometricPrompt.Builder(this)
                .setTitle("FinanceTracker")
                .setSubtitle(subtitle);
        if (Build.VERSION.SDK_INT >= Build.VERSION_CODES.R) {
            builder.setAllowedAuthenticators(
                    BiometricManager.Authenticators.BIOMETRIC_WEAK
                            | BiometricManager.Authenticators.DEVICE_CREDENTIAL);
        } else {
            builder.setDeviceCredentialAllowed(true);
        }

        try {
            builder.build().authenticate(new CancellationSignal(), getMainExecutor(),
                    new BiometricPrompt.AuthenticationCallback() {
                        @Override
                        public void onAuthenticationSucceeded(BiometricPrompt.AuthenticationResult result) {
                            authInProgress = false;
                            handleAuthSuccess(purpose);
                        }

                        @Override
                        public void onAuthenticationError(int errorCode, CharSequence message) {
                            authInProgress = false;
                            handleAuthFailure(purpose, String.valueOf(message));
                        }
                    });
        } catch (RuntimeException e) {
            authInProgress = false;
            Log.e(TAG, "Autenticazione non disponibile", e);
            handleAuthFailure(purpose, "Autenticazione non disponibile su questo telefono.");
        }
    }

    private void handleAuthSuccess(int purpose) {
        if (purpose == AUTH_UNLOCK) {
            unlock();
            return;
        }
        boolean enable = purpose == AUTH_ENABLE;
        prefs.edit().putBoolean(KEY_LOCK, enable).apply();
        setSecureWindow(enable);

        JSONObject result = new JSONObject();
        putQuietly(result, "ok", true);
        putQuietly(result, "enabled", enable);
        callJs("__ftLockChanged", result);
        showToast(enable ? "Blocco attivato" : "Blocco disattivato");
    }

    private void handleAuthFailure(int purpose, String message) {
        if (purpose == AUTH_UNLOCK) {
            // La schermata di blocco resta: si riprova con "Sblocca".
            return;
        }
        JSONObject result = new JSONObject();
        putQuietly(result, "ok", false);
        putQuietly(result, "enabled", isLockEnabled());
        putQuietly(result, "error", message);
        callJs("__ftLockChanged", result);
    }

    private View buildLockOverlay() {
        LinearLayout overlay = new LinearLayout(this);
        overlay.setOrientation(LinearLayout.VERTICAL);
        overlay.setGravity(Gravity.CENTER);
        overlay.setBackgroundColor(Color.parseColor("#0B1220"));
        overlay.setClickable(true); // blocca i tocchi verso l'app sotto
        overlay.setVisibility(View.GONE);

        ImageView logo = new ImageView(this);
        logo.setImageResource(R.mipmap.ic_launcher);
        int logoSize = dp(88);
        LinearLayout.LayoutParams logoParams = new LinearLayout.LayoutParams(logoSize, logoSize);
        logoParams.bottomMargin = dp(20);
        overlay.addView(logo, logoParams);

        TextView title = new TextView(this);
        title.setText("FinanceTracker è bloccata");
        title.setTextColor(Color.parseColor("#EEF3FF"));
        title.setTextSize(TypedValue.COMPLEX_UNIT_SP, 20);
        title.setGravity(Gravity.CENTER);
        overlay.addView(title);

        Button unlockButton = new Button(this);
        unlockButton.setText("Sblocca");
        unlockButton.setAllCaps(false);
        unlockButton.setOnClickListener(v -> authenticate(AUTH_UNLOCK));
        LinearLayout.LayoutParams buttonParams = new LinearLayout.LayoutParams(
                ViewGroup.LayoutParams.WRAP_CONTENT, ViewGroup.LayoutParams.WRAP_CONTENT);
        buttonParams.topMargin = dp(24);
        overlay.addView(unlockButton, buttonParams);

        return overlay;
    }

    private int dp(int value) {
        return Math.round(value * getResources().getDisplayMetrics().density);
    }

    // ------------------------------------------------------------------ sistema

    /** Il contenuto resta fuori da barra di stato, barra di navigazione e tastiera (Android 11+). */
    private static void applySystemBarInsets(View view) {
        view.setOnApplyWindowInsetsListener((v, insets) -> {
            android.graphics.Insets bars = insets.getInsets(
                    WindowInsets.Type.systemBars()
                            | WindowInsets.Type.displayCutout()
                            | WindowInsets.Type.ime());
            v.setPadding(bars.left, bars.top, bars.right, bars.bottom);
            return WindowInsets.CONSUMED;
        });
    }

    @Override
    public void onBackPressed() {
        if (!locked && webView != null && webView.canGoBack()) {
            webView.goBack();
        } else {
            // Come le app native: torna alla home senza chiudere Python,
            // così riaprendo l'app è subito pronta.
            moveTaskToBack(true);
        }
    }

    @Override
    protected void onResume() {
        super.onResume();
        if (webView != null) {
            webView.onResume();
        }

        if (isLockEnabled()) {
            boolean away = pausedAt > 0 && SystemClock.elapsedRealtime() - pausedAt > RELOCK_AFTER_MS;
            if (!locked && away && !skipRelockOnce) {
                lock();
            }
            if (locked) {
                authenticate(AUTH_UNLOCK);
            }
        }
        skipRelockOnce = false;
    }

    @Override
    protected void onPause() {
        pausedAt = SystemClock.elapsedRealtime();
        if (webView != null) {
            webView.onPause();
        }
        super.onPause();
    }

    @Override
    protected void onDestroy() {
        if (webView != null) {
            root.removeView(webView);
            webView.destroy();
            webView = null;
        }
        super.onDestroy();
    }
}
