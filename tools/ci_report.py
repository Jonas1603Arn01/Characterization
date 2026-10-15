"""Show a test failure on GitHub as an annotation of the run.

Workflow logs are only visible to signed-in users; annotations (the error
messages attached to a run) are public. tools/smoke_test.py and
tools/update_test.py report their failure and the program's logs through
this, so a failed build can be diagnosed from the run page or the API.
"""
import os
import traceback


def report(title: str, logs: dict[str, str]) -> None:
    """Call from an except block: the exception plus the given logs."""
    if not os.environ.get("GITHUB_ACTIONS"):
        return
    parts = [traceback.format_exc()]
    for name, text in logs.items():
        parts.append(f"----- {name} -----\n{text[-5000:]}")
    message = "\n".join(parts)[-12000:]
    # workflow command escaping (multi-line annotation)
    message = message.replace("%", "%25").replace("\r", "%0D").replace("\n", "%0A")
    print(f"::error title={title}::{message}", flush=True)
