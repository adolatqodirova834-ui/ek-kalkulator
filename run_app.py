"""Launcher: start the Streamlit server on a free port and open the browser.

Used by the double-click scripts (Ishga_tushirish.bat / .command / .sh).
"""

import socket
import subprocess
import sys
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def free_port(preferred: int = 8501) -> int:
    for port in (preferred, 0):
        with socket.socket() as s:
            try:
                s.bind(("127.0.0.1", port))
                return s.getsockname()[1]
            except OSError:
                continue
    raise RuntimeError("Bo'sh port topilmadi.")


def wait_until_up(port: int, proc: subprocess.Popen, timeout: float = 60.0) -> bool:
    end = time.time() + timeout
    while time.time() < end and proc.poll() is None:
        with socket.socket() as s:
            s.settimeout(0.5)
            if s.connect_ex(("127.0.0.1", port)) == 0:
                return True
        time.sleep(0.3)
    return False


def main() -> int:
    port = free_port()
    url = f"http://localhost:{port}"
    # headless: skips Streamlit's first-run e-mail prompt; we open the browser ourselves
    proc = subprocess.Popen(
        [sys.executable, "-m", "streamlit", "run", str(ROOT / "app.py"),
         "--server.headless", "true", "--server.port", str(port), "--server.address", "127.0.0.1",
         "--browser.gatherUsageStats", "false"],
        cwd=ROOT,
    )
    try:
        if not wait_until_up(port, proc):
            print("XATO: ilova ishga tushmadi. Yuqoridagi xabarlarni tekshiring.")
            proc.terminate()
            return 1
        print(f"\nEK kalkulyatori ishlayapti: {url}")
        print("To'xtatish uchun shu oynani yoping yoki Ctrl+C bosing.\n")
        if "--no-browser" not in sys.argv:
            webbrowser.open(url)
        return proc.wait()
    except KeyboardInterrupt:
        proc.terminate()
        return 0


if __name__ == "__main__":
    sys.exit(main())
