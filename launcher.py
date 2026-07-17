import os
import socket
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import IO

import webview

from src.database.db import get_app_data_dir


APP_NAME = "FinanceTracker"
APP_HOST = "127.0.0.1"


def get_bundle_dir() -> Path:
    """
    Cartella dei file inclusi da PyInstaller.

    In modalità --onefile corrisponde alla cartella temporanea _MEI...
    In sviluppo corrisponde alla root del progetto.
    """
    if getattr(sys, "frozen", False):
        return Path(sys._MEIPASS)

    return Path(__file__).resolve().parent


def get_log_path() -> Path:
    log_dir = get_app_data_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    return log_dir / "launcher.log"


def get_webview_gui() -> str | None:
    """Backend nativo della finestra desktop per piattaforma."""
    if sys.platform == "win32":
        return "edgechromium"

    # Linux → GTK/WebKit, macOS → Cocoa (scelta automatica).
    return None


def find_free_port() -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((APP_HOST, 0))
        return int(sock.getsockname()[1])


def configure_environment(port: int) -> dict[str, str]:
    """
    Restituisce un ambiente pulito e forza tutte le impostazioni
    importanti, ignorando eventuali configurazioni Streamlit globali.
    """
    environment = os.environ.copy()

    environment["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"

    environment["STREAMLIT_SERVER_ADDRESS"] = APP_HOST
    environment["STREAMLIT_SERVER_PORT"] = str(port)
    environment["STREAMLIT_SERVER_HEADLESS"] = "true"
    environment["STREAMLIT_SERVER_FILE_WATCHER_TYPE"] = "none"

    environment["STREAMLIT_BROWSER_SERVER_ADDRESS"] = APP_HOST
    environment["STREAMLIT_BROWSER_SERVER_PORT"] = str(port)
    environment["STREAMLIT_BROWSER_GATHER_USAGE_STATS"] = "false"

    environment["STREAMLIT_SERVER_ENABLE_CORS"] = "false"
    environment["STREAMLIT_SERVER_ENABLE_XSRF_PROTECTION"] = "false"

    environment["STREAMLIT_CLIENT_TOOLBAR_MODE"] = "minimal"

    # Evita l'apertura di Chrome o Edge come browser esterno.
    environment["BROWSER"] = "none"

    return environment


def run_streamlit_cli(port: int) -> None:
    """
    Esegue l'equivalente di:

        streamlit run app.py --server.port=...

    utilizzando l'entry point CLI incluso nel pacchetto.
    """
    environment = configure_environment(port)
    os.environ.update(environment)

    app_path = get_bundle_dir() / "app.py"

    if not app_path.exists():
        raise FileNotFoundError(
            f"app.py non trovato nel pacchetto: {app_path}"
        )

    # Import successivo alla configurazione dell'ambiente.
    from streamlit.web.cli import main as streamlit_main

    sys.argv = [
        "streamlit",
        "run",
        str(app_path),
        "--global.developmentMode=false",
        f"--server.address={APP_HOST}",
        f"--server.port={port}",
        "--server.headless=true",
        "--server.fileWatcherType=none",
        "--server.enableCORS=false",
        "--server.enableXsrfProtection=false",
        f"--browser.serverAddress={APP_HOST}",
        f"--browser.serverPort={port}",
        "--browser.gatherUsageStats=false",
        "--client.toolbarMode=minimal",
    ]

    streamlit_main()


def get_worker_command(port: int) -> list[str]:
    if getattr(sys, "frozen", False):
        # L'EXE rilancia se stesso in modalità server.
        return [
            sys.executable,
            "--streamlit-worker",
            str(port),
        ]

    # Durante lo sviluppo rilancia launcher.py con Python.
    return [
        sys.executable,
        str(Path(__file__).resolve()),
        "--streamlit-worker",
        str(port),
    ]


def start_worker(
    port: int,
) -> tuple[subprocess.Popen, IO[str]]:
    log_file = get_log_path().open(
        "w",
        encoding="utf-8",
        buffering=1,
    )

    creation_flags = 0

    if sys.platform == "win32":
        creation_flags = subprocess.CREATE_NO_WINDOW

    process = subprocess.Popen(
        get_worker_command(port),
        cwd=str(get_bundle_dir()),
        stdout=log_file,
        stderr=subprocess.STDOUT,
        env=configure_environment(port),
        creationflags=creation_flags,
    )

    return process, log_file


def wait_until_ready(
    process: subprocess.Popen,
    app_url: str,
    timeout: float = 90.0,
) -> None:
    health_url = f"{app_url}/_stcore/health"
    deadline = time.time() + timeout

    while time.time() < deadline:
        if process.poll() is not None:
            raise RuntimeError(
                "Il server Streamlit si è chiuso durante l'avvio. "
                f"Controlla il log: {get_log_path()}"
            )

        try:
            with urllib.request.urlopen(
                health_url,
                timeout=2,
            ) as response:
                if response.status == 200:
                    return

        except (
            urllib.error.URLError,
            TimeoutError,
            ConnectionError,
        ):
            time.sleep(0.3)

    raise RuntimeError(
        "FinanceTracker non è riuscito ad avviare il server "
        f"entro {int(timeout)} secondi. "
        f"Controlla il log: {get_log_path()}"
    )


def stop_worker(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return

    process.terminate()

    try:
        process.wait(timeout=5)
    except subprocess.TimeoutExpired:
        process.kill()


def main() -> None:
    port = find_free_port()
    app_url = f"http://{APP_HOST}:{port}"

    worker, log_file = start_worker(port)

    try:
        wait_until_ready(worker, app_url)

        webview.create_window(
            title=APP_NAME,
            url=app_url,
            width=1400,
            height=900,
            min_size=(1050, 700),
            resizable=True,
        )

        # pywebview carica il server locale in una finestra desktop.
        webview.start(
            gui=get_webview_gui(),
            debug=False,
        )

    finally:
        stop_worker(worker)
        log_file.close()


if __name__ == "__main__":
    if "--streamlit-worker" in sys.argv:
        worker_argument_index = (
            sys.argv.index("--streamlit-worker") + 1
        )
        worker_port = int(sys.argv[worker_argument_index])

        run_streamlit_cli(worker_port)
    else:
        main()