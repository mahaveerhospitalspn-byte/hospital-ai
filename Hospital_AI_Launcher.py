import subprocess
import webbrowser
import time
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
os.chdir(BASE_DIR)

subprocess.Popen([
    "python", "-m", "streamlit", "run",
    os.path.join(BASE_DIR, "app.py"),
    "--server.address", "0.0.0.0"
])

time.sleep(4)
webbrowser.open("http://localhost:8501")
