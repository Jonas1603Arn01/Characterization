"""Characterization als eigenes Programm: dieselbe App wie run.py, aber in
einem eigenen Fenster (pywebview/WebView2) statt im Browser und ohne das
schwarze Serverfenster.

Der Server läuft in einem Hintergrund-Thread. Schließt man das Fenster (oder
klickt „Quit“), fährt er regulär herunter — wie Strg+C bei run.py: der
Lifespan sichert die Datenbank und gibt die Sperre im Datenordner frei.

Fenster: Windows WebView2 (edgechromium), macOS WebKit (cocoa).

Aus dem Quellordner (zum Ausprobieren, braucht requirements-build.txt):

    .venv-build\\Scripts\\python.exe desktop.py

Gepackt wird er mit PyInstaller (Characterization.spec, tools/build.py).
Dieselbe exe startet mit --dialog den Auswahl-Dialog (app/dialogs.py), weil
es im gepackten Programm kein „python -m“ gibt. --server-only startet nur
den Server ohne Fenster (Rauchtest der Builds, tools/smoke_test.py).
"""
import os
import socket
import sys
import threading
import time
import webbrowser

HOST = "127.0.0.1"
# Anderer Port nur zum Ausprobieren neben der laufenden echten App
# (zusammen mit CHARACTERIZATION_HOME, siehe app/config.py)
PORT = int(os.environ.get("CHARACTERIZATION_PORT") or 8710)
URL = f"http://{HOST}:{PORT}"
TITLE = "Characterization"
# pywebview-Backend je System
GUI = "cocoa" if sys.platform == "darwin" else "edgechromium"

LOADING_HTML = """<!doctype html><html><body style="margin:0;height:100vh;
display:flex;align-items:center;justify-content:center;font:15px 'Segoe UI',
sans-serif;color:#555;background:#f6f7fb">{text}</body></html>"""


def server_running() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((HOST, PORT)) == 0


def redirect_output(home) -> None:
    """Ohne Konsole sind stdout/stderr None — uvicorn und jede Fehlermeldung
    liefen dann ins Leere bzw. stürzten ab. Stattdessen: app.log im
    Datenordner des Programms (bei jedem Start neu). Gepackt immer — auch
    unter macOS, wo die Ausgabe sonst unsichtbar verpufft."""
    if not getattr(sys, "frozen", False) and sys.stdout and sys.stderr:
        return
    home.mkdir(parents=True, exist_ok=True)
    log = open(home / "app.log", "w", encoding="utf-8", buffering=1)
    sys.stdout = sys.stderr = log


def unblock_net_dlls() -> None:
    """Entpackt man die ZIP aus einem Browser-Download, trägt jede Datei die
    Download-Markierung (Zone.Identifier). .NET lädt so markierte
    Bibliotheken nicht — pythonnet und damit das Fenster scheitern dann
    („Failed to resolve Python.Runtime.Loader.Initialize“). Die Markierung
    der eigenen .NET-DLLs wird deshalb vor dem Laden entfernt, wie
    „Zulassen“ in den Dateieigenschaften."""
    if not getattr(sys, "frozen", False) or sys.platform != "win32":
        return
    from pathlib import Path
    base = Path(sys._MEIPASS)
    for sub in ("pythonnet", "clr_loader", "webview"):
        for dll in (base / sub).rglob("*.dll"):
            try:
                os.remove(f"{dll}:Zone.Identifier")
            except OSError:
                pass  # nicht markiert (oder kein Schreibrecht)


def version(base) -> str:
    try:
        return (base / "VERSION").read_text(encoding="utf-8").strip()
    except OSError:
        return ""


def serve_only() -> None:
    """Nur der Server, im Vordergrund, bis „Quit“ (POST /api/shutdown)."""
    import uvicorn

    from app import api
    from app.main import app

    server = uvicorn.Server(uvicorn.Config(app, host=HOST, port=PORT))
    api.on_quit = lambda: setattr(server, "should_exit", True)
    server.run()


def main() -> None:
    if len(sys.argv) > 1 and sys.argv[1] == "--dialog":
        from app import dialog_worker
        sys.argv = [sys.argv[0], *sys.argv[2:]]
        dialog_worker.main()
        return

    from app import config
    redirect_output(config.HOME_DIR)
    config.HOME_DIR.mkdir(parents=True, exist_ok=True)

    if len(sys.argv) > 1 and sys.argv[1] == "--server-only":
        serve_only()
        return

    unblock_net_dlls()
    import webview
    v = version(config.BASE_DIR)
    title = f"{TITLE} {v}".strip()

    if server_running():
        # Läuft schon (zweiter Doppelklick, oder run.py): nur ein Fenster
        # dazu — dessen Schließen beendet den laufenden Server nicht.
        webview.create_window(title, URL, width=1400, height=900, min_size=(900, 600))
        try:
            webview.start(gui=GUI, private_mode=False,
                          storage_path=str(config.HOME_DIR / "webview"))
        except Exception as e:  # kein Fenster möglich: wie run.py im Browser
            print(f"No program window ({e}); opening the browser", file=sys.stderr)
            webbrowser.open(URL)
        return

    import uvicorn

    from app import api
    from app.main import app

    server = uvicorn.Server(uvicorn.Config(app, host=HOST, port=PORT))
    # Server im Hintergrund-Thread: uvicorn installiert dort keine
    # Signal-Handler, das Beenden läuft über should_exit
    thread = threading.Thread(target=server.run, name="uvicorn")
    thread.start()

    window = webview.create_window(
        title, html=LOADING_HTML.format(text="Starting …"),
        width=1400, height=900, min_size=(900, 600),
    )

    def quit_app() -> None:
        # „Quit“ in der App: das Backup ist schon gemacht (api.shutdown)
        window.destroy()

    api.on_quit = quit_app

    def load_when_ready() -> None:
        # Der Port ist erst offen, wenn Sperre und Migrationen durch sind
        while not server.started:
            if not thread.is_alive():
                window.load_html(LOADING_HTML.format(
                    text=f"The app could not start — see {config.HOME_DIR / 'app.log'}"))
                return
            time.sleep(0.05)
        window.load_url(URL)

    try:
        webview.start(load_when_ready, gui=GUI, private_mode=False,
                      storage_path=str(config.HOME_DIR / "webview"))
    except Exception as e:  # kein Fenster möglich (z. B. WebView2 fehlt): Browser
        print(f"No program window ({e}); falling back to the browser", file=sys.stderr)
        api.on_quit = lambda: setattr(server, "should_exit", True)
        while thread.is_alive() and not server.started:
            time.sleep(0.05)
        webbrowser.open(URL)
        thread.join()
        return

    # Fenster zu: Server regulär beenden (Backup + Sperre freigeben im Lifespan)
    server.should_exit = True
    thread.join()


if __name__ == "__main__":
    main()
