import socket
import sys
import threading
import time
import webbrowser
from pathlib import Path

HOST = "127.0.0.1"
PORT = 8710
URL = f"http://{HOST}:{PORT}"

# Make sure the data folders exist (portability to new PCs)
for folder in ["data", "backups"]:
    Path(folder).mkdir(exist_ok=True)


def server_running() -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.4)
        return s.connect_ex((HOST, PORT)) == 0


def open_browser_when_ready() -> None:
    """Open the browser only once the server actually accepts connections.

    Opened any earlier, the browser lands on "site can't be reached" and does
    not retry by itself — the user would have to keep hitting reload until the
    startup (data folder on the network, lock, migrations) is through; the
    start backup then keeps running in the background.
    Uvicorn binds the port only after the startup is complete, so a successful
    connection means the app is ready to answer."""
    while not server_running():
        time.sleep(0.05)
    webbrowser.open(URL)


if __name__ == "__main__":
    if server_running():
        # Server already running (e.g. second double-click) — just open the browser.
        webbrowser.open(URL)
        sys.exit(0)

    import uvicorn

    threading.Thread(target=open_browser_when_ready, daemon=True).start()
    uvicorn.run("app.main:app", host=HOST, port=PORT)
