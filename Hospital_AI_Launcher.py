<<<<<<< HEAD
import subprocess
import webbrowser
import time
import os

APP_DIR = r"C:\Users\admin\Desktop\Hospital_AI"

os.chdir(APP_DIR)

subprocess.Popen(["python", "-m", "streamlit", "run", "app.py"])

time.sleep(4)

webbrowser.open("http://localhost:8501")
=======
import subprocess
import webbrowser
import time
import os

APP_DIR = r"C:\Users\admin\Desktop\Hospital_AI"

os.chdir(APP_DIR)

subprocess.Popen(["python", "-m", "streamlit", "run", "app.py"])

time.sleep(4)

webbrowser.open("http://localhost:8501")
>>>>>>> d67240b6b301f5efd6ea7b3a00d8b3b998948d69
