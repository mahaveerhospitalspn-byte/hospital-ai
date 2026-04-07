
import subprocess
import webbrowser
import time
import sys
import os

# ✅ PyInstaller-safe base path
if getattr(sys, 'frozen', False):
    BASE_DIR = sys._MEIPASS
else:
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app_path = os.path.join(BASE_DIR, "app.py")

# ✅ Bind Streamlit to network (CRITICAL FIX)
subprocess.Popen([
    "python",
    "-m",
    "streamlit",
    "run",
    app_path,
    "--server.address",
    "0.0.0.0"
])

time.sleep(4)

# ✅ Open locally
webbrowser.open("http://localhost:8501")
