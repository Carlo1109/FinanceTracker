package io.github.carlo1109.financetracker;

import android.content.ContentProvider;
import android.content.ContentValues;
import android.content.Context;
import android.database.Cursor;
import android.database.MatrixCursor;
import android.net.Uri;
import android.os.ParcelFileDescriptor;
import android.provider.OpenableColumns;

import java.io.File;
import java.io.FileNotFoundException;
import java.util.Locale;

/**
 * Condivide con altre app (es. "Salva su Drive") i file preparati dall'app.
 *
 * I file stanno nella cache privata (cache/shared) e sono solo in lettura:
 * l'app che li riceve ottiene il permesso per quel singolo file, per il
 * tempo della condivisione. Nessuna dipendenza esterna (al posto di
 * androidx FileProvider).
 */
public final class ShareProvider extends ContentProvider {

    private static final String AUTHORITY_SUFFIX = ".share";

    static File sharedDir(Context context) {
        File dir = new File(context.getCacheDir(), "shared");
        //noinspection ResultOfMethodCallIgnored
        dir.mkdirs();
        return dir;
    }

    static Uri uriFor(Context context, String fileName) {
        return new Uri.Builder()
                .scheme("content")
                .authority(context.getPackageName() + AUTHORITY_SUFFIX)
                .appendPath(fileName)
                .build();
    }

    static String mimeFor(String name) {
        String lower = name.toLowerCase(Locale.ROOT);
        if (lower.endsWith(".zip")) return "application/zip";
        if (lower.endsWith(".xlsx")) return "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet";
        if (lower.endsWith(".json")) return "application/json";
        return "application/octet-stream";
    }

    private File fileFor(Uri uri) throws FileNotFoundException {
        String name = uri.getLastPathSegment();
        if (name == null || name.isEmpty() || name.contains("/") || name.startsWith(".")) {
            throw new FileNotFoundException("percorso non valido");
        }
        File file = new File(sharedDir(getContext()), name);
        if (!file.isFile()) {
            throw new FileNotFoundException(name);
        }
        return file;
    }

    @Override
    public boolean onCreate() {
        return true;
    }

    @Override
    public String getType(Uri uri) {
        String name = uri.getLastPathSegment();
        return name == null ? "application/octet-stream" : mimeFor(name);
    }

    @Override
    public ParcelFileDescriptor openFile(Uri uri, String mode) throws FileNotFoundException {
        if (mode == null || !mode.startsWith("r") || mode.contains("w")) {
            throw new SecurityException("solo lettura");
        }
        return ParcelFileDescriptor.open(fileFor(uri), ParcelFileDescriptor.MODE_READ_ONLY);
    }

    @Override
    public Cursor query(Uri uri, String[] projection, String selection, String[] selectionArgs, String sortOrder) {
        File file;
        try {
            file = fileFor(uri);
        } catch (FileNotFoundException e) {
            return null;
        }
        String[] columns = projection != null
                ? projection
                : new String[]{OpenableColumns.DISPLAY_NAME, OpenableColumns.SIZE};
        Object[] values = new Object[columns.length];
        int used = 0;
        String[] kept = new String[columns.length];
        for (String column : columns) {
            if (OpenableColumns.DISPLAY_NAME.equals(column)) {
                kept[used] = column;
                values[used++] = file.getName();
            } else if (OpenableColumns.SIZE.equals(column)) {
                kept[used] = column;
                values[used++] = file.length();
            }
        }
        String[] finalColumns = new String[used];
        Object[] finalValues = new Object[used];
        System.arraycopy(kept, 0, finalColumns, 0, used);
        System.arraycopy(values, 0, finalValues, 0, used);
        MatrixCursor cursor = new MatrixCursor(finalColumns, 1);
        cursor.addRow(finalValues);
        return cursor;
    }

    @Override
    public Uri insert(Uri uri, ContentValues values) {
        throw new UnsupportedOperationException("solo lettura");
    }

    @Override
    public int delete(Uri uri, String selection, String[] selectionArgs) {
        throw new UnsupportedOperationException("solo lettura");
    }

    @Override
    public int update(Uri uri, ContentValues values, String selection, String[] selectionArgs) {
        throw new UnsupportedOperationException("solo lettura");
    }
}
