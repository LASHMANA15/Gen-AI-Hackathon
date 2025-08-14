import os
import subprocess
import webbrowser
import time

def run_app():
    # Start Streamlit app
    subprocess.Popen(["streamlit", "run", "app.py"])
    time.sleep(2)  # Give it time to start
    webbrowser.open("http://localhost:8501")

if __name__ == "__main__":
    run_app()
