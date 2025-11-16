# run_colab.py

import os
import subprocess
import shutil
import time
import socket
from pyngrok import ngrok
from dotenv import load_dotenv


def install_chromium_if_needed():
    if shutil.which("chromium-browser") is None:
        print("🔧 Installing Chromium browser...")
        subprocess.run(["apt-get", "update"], check=True)
        subprocess.run(["apt-get", "install", "-y", "chromium-browser"], check=True)
    else:
        print("✔ Chromium already installed")


def kill_streamlit():
    print("🛑 Killing any existing Streamlit instances (if any)...")
    subprocess.run(["pkill", "streamlit"], stderr=subprocess.DEVNULL)


def start_streamlit():
    print("🚀 Starting Streamlit app in background...")
    cmd = "nohup streamlit run main.py >/dev/null 2>&1 &"
    subprocess.Popen(cmd, shell=True)


def wait_for_streamlit(port=8501, timeout=20):
    """Wait until Streamlit is listening on the port."""
    print("⏳ Waiting for Streamlit to start...")
    start_time = time.time()
    while True:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            try:
                s.connect(("localhost", port))
                print("✔ Streamlit is up!")
                return
            except ConnectionRefusedError:
                if time.time() - start_time > timeout:
                    raise TimeoutError("Streamlit did not start in time")
                time.sleep(0.5)


def setup_ngrok(token):
    print("🔐 Setting up ngrok...")
    ngrok.set_auth_token(token)
    tunnel = ngrok.connect(addr="8501", proto="http")
    return tunnel


def main():
    # Load environment variables from .env
    load_dotenv()
    token = os.getenv("NGROK_AUTH_TOKEN")
    if not token:
        raise ValueError("NGROK_AUTH_TOKEN not found in .env")

    # Ensure we are in the project directory
    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)

    # Install Chromium if needed
    install_chromium_if_needed()

    # Kill old Streamlit processes
    kill_streamlit()

    # Start Streamlit and wait until it's ready
    start_streamlit()
    wait_for_streamlit()

    # Start ngrok tunnel
    tunnel = setup_ngrok(token)
    print(f"🎉 Your Streamlit app is live at: {tunnel.public_url}")


if __name__ == "__main__":
    main()
