package io.github.carlo1109.financetracker;

import android.content.ContentResolver;
import android.content.Context;
import android.content.Intent;
import android.content.SharedPreferences;
import android.content.UriPermission;
import android.database.Cursor;
import android.net.Uri;
import android.provider.DocumentsContract;
import android.provider.DocumentsContract.Document;

import java.io.ByteArrayOutputStream;
import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;

/**
 * Cartella dei dati scelta dall'utente (Storage Access Framework).
 *
 * L'utente sceglie una cartella con il selettore di Android; l'app ne
 * conserva il permesso e ci legge/scrive finance_tracker.db,
 * categories.json e backups/. Nessun permesso "accesso a tutti i file".
 *
 * I percorsi sono relativi alla cartella, es. "finance_tracker.db"
 * oppure "backups/FinanceTracker_Backup_....zip".
 */
final class FolderStorage {

    static final int GRANT_FLAGS =
            Intent.FLAG_GRANT_READ_URI_PERMISSION | Intent.FLAG_GRANT_WRITE_URI_PERMISSION;

    private static final String PREFS = "ft_storage";
    private static final String KEY_TREE = "tree_uri";
    private static final String KEY_PROMPTED = "prompted";

    /** Informazioni su un file della cartella. */
    static final class FileInfo {
        final long size;
        final long modified;

        FileInfo(long size, long modified) {
            this.size = size;
            this.modified = modified;
        }
    }

    private final Context context;
    private final SharedPreferences prefs;

    FolderStorage(Context context) {
        this.context = context.getApplicationContext();
        this.prefs = this.context.getSharedPreferences(PREFS, Context.MODE_PRIVATE);
    }

    // ------------------------------------------------------------------ stato

    Uri tree() {
        String value = prefs.getString(KEY_TREE, null);
        return value == null ? null : Uri.parse(value);
    }

    /** True se c'è una cartella scelta e Android ci dà ancora il permesso. */
    boolean isConfigured() {
        Uri tree = tree();
        if (tree == null) {
            return false;
        }
        for (UriPermission permission : resolver().getPersistedUriPermissions()) {
            if (permission.getUri().equals(tree)
                    && permission.isReadPermission()
                    && permission.isWritePermission()) {
                return true;
            }
        }
        return false;
    }

    boolean wasPrompted() {
        return prefs.getBoolean(KEY_PROMPTED, false);
    }

    void markPrompted() {
        prefs.edit().putBoolean(KEY_PROMPTED, true).apply();
    }

    /** Salva la cartella scelta e ne conserva il permesso anche dopo il riavvio. */
    void setTree(Uri tree) {
        resolver().takePersistableUriPermission(tree, GRANT_FLAGS);

        Uri previous = tree();
        if (previous != null && !previous.equals(tree)) {
            try {
                resolver().releasePersistableUriPermission(previous, GRANT_FLAGS);
            } catch (SecurityException ignored) {
                // Permesso già revocato.
            }
        }
        prefs.edit().putString(KEY_TREE, tree.toString()).putBoolean(KEY_PROMPTED, true).apply();
    }

    /** Nome leggibile della cartella, es. "Telefono › Documents/FinanceTracker". */
    String label() {
        Uri tree = tree();
        if (tree == null) {
            return "";
        }
        String treeId = DocumentsContract.getTreeDocumentId(tree);
        int colon = treeId.indexOf(':');
        if ("com.android.externalstorage.documents".equals(tree.getAuthority()) && colon >= 0) {
            String volume = treeId.substring(0, colon);
            String path = treeId.substring(colon + 1);
            String prefix = "primary".equals(volume) ? "Telefono" : "Scheda SD";
            return path.isEmpty() ? prefix : prefix + " › " + path;
        }
        String name = queryString(rootDocument(tree), Document.COLUMN_DISPLAY_NAME);
        return name != null ? name : treeId;
    }

    // ------------------------------------------------------------------ file

    byte[] read(String relativePath) throws IOException {
        Uri file = resolve(relativePath, false);
        if (file == null) {
            return null;
        }
        try (InputStream in = resolver().openInputStream(file)) {
            if (in == null) {
                throw new IOException("impossibile aprire " + relativePath);
            }
            ByteArrayOutputStream out = new ByteArrayOutputStream();
            byte[] buffer = new byte[64 * 1024];
            int read;
            while ((read = in.read(buffer)) != -1) {
                out.write(buffer, 0, read);
            }
            return out.toByteArray();
        }
    }

    FileInfo info(String relativePath) throws IOException {
        Uri file = resolve(relativePath, false);
        if (file == null) {
            return null;
        }
        try (Cursor cursor = resolver().query(file,
                new String[]{Document.COLUMN_SIZE, Document.COLUMN_LAST_MODIFIED},
                null, null, null)) {
            if (cursor == null || !cursor.moveToFirst()) {
                return null;
            }
            return new FileInfo(cursor.getLong(0), cursor.getLong(1));
        }
    }

    boolean exists(String relativePath) {
        try {
            return resolve(relativePath, false) != null;
        } catch (IOException e) {
            return false;
        }
    }

    void write(String relativePath, byte[] data) throws IOException {
        Uri file = resolve(relativePath, true);
        // "wt" = scrivi da capo (tronca il file esistente).
        try (OutputStream out = resolver().openOutputStream(file, "wt")) {
            if (out == null) {
                throw new IOException("impossibile scrivere " + relativePath);
            }
            out.write(data);
        }
    }

    // ------------------------------------------------------------------ interni

    private ContentResolver resolver() {
        return context.getContentResolver();
    }

    private static Uri rootDocument(Uri tree) {
        return DocumentsContract.buildDocumentUriUsingTree(tree, DocumentsContract.getTreeDocumentId(tree));
    }

    /** Trova (o crea, se create=true) il file indicato, cartelle intermedie incluse. */
    private Uri resolve(String relativePath, boolean create) throws IOException {
        Uri tree = tree();
        if (tree == null) {
            throw new IOException("nessuna cartella scelta");
        }
        String[] parts = relativePath.split("/");
        String parentId = DocumentsContract.getTreeDocumentId(tree);

        for (int i = 0; i < parts.length; i++) {
            String name = parts[i];
            if (name.isEmpty() || ".".equals(name) || "..".equals(name)) {
                throw new IOException("percorso non valido: " + relativePath);
            }
            boolean isLast = i == parts.length - 1;
            String childId = findChild(tree, parentId, name);

            if (childId == null) {
                if (!create) {
                    return null;
                }
                Uri parentUri = DocumentsContract.buildDocumentUriUsingTree(tree, parentId);
                String mime = isLast ? mimeFor(name) : Document.MIME_TYPE_DIR;
                Uri created = DocumentsContract.createDocument(resolver(), parentUri, mime, name);
                if (created == null) {
                    throw new IOException("impossibile creare " + name);
                }
                childId = DocumentsContract.getDocumentId(created);
            }
            parentId = childId;
        }
        return DocumentsContract.buildDocumentUriUsingTree(tree, parentId);
    }

    private String findChild(Uri tree, String parentId, String name) {
        Uri children = DocumentsContract.buildChildDocumentsUriUsingTree(tree, parentId);
        try (Cursor cursor = resolver().query(children,
                new String[]{Document.COLUMN_DOCUMENT_ID, Document.COLUMN_DISPLAY_NAME},
                null, null, null)) {
            if (cursor == null) {
                return null;
            }
            while (cursor.moveToNext()) {
                if (name.equals(cursor.getString(1))) {
                    return cursor.getString(0);
                }
            }
        }
        return null;
    }

    private String queryString(Uri uri, String column) {
        try (Cursor cursor = resolver().query(uri, new String[]{column}, null, null, null)) {
            if (cursor != null && cursor.moveToFirst()) {
                return cursor.getString(0);
            }
        } catch (RuntimeException ignored) {
            // Provider che non supporta la query.
        }
        return null;
    }

    private static String mimeFor(String name) {
        String lower = name.toLowerCase(java.util.Locale.ROOT);
        if (lower.endsWith(".json")) return "application/json";
        if (lower.endsWith(".zip")) return "application/zip";
        if (lower.endsWith(".xlsx")) return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
        // .db e altro: binario generico (evita che il provider aggiunga estensioni).
        return "application/octet-stream";
    }
}
