"""Startet die App mit einer Wegwerf-Datenbank in einem Temp-Ordner —
zum Ausprobieren/Testen, ohne die echte data/app.db anzufassen.

    .venv\Scripts\python.exe tools\test_server.py
"""
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import uvicorn

from app import db

if __name__ == "__main__":
    tmp = Path(tempfile.mkdtemp(prefix="charak-test-")) / "app.db"
    print(f"Test-DB: {tmp}")
    db.init_db(tmp)
    from app.main import app

    uvicorn.run(app, host="127.0.0.1", port=8711)
