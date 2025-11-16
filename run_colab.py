# run_colab.py

import os
import subprocess
import shutil
from pyngrok import ngrok
from dotenv import load_dotenv


def install_chromium_if_needed():
    if shutil.which("chromium-browser") is None:
        print("🔧 Installing Chromium browser...")
        subprocess.run(["apt-get", "update"], check=True)
        subprocess.run(["apt-get", "install", "-y", "chromium-browser"], check=True)
    else:
        print("✔ Chromium already installed")

def setup_ngrok(token):
    print("🔐 Setting up ngrok...")
    ngrok.set_auth_token(token)
    return ngrok.connect(addr="8501", proto="http")

def kill_streamlit():
    print("🛑 Killing any existing Streamlit instances (if any)...")
    subprocess.run(["pkill", "streamlit"], stderr=subprocess.DEVNULL)

def start_streamlit():
    print("🚀 Starting Streamlit app in background...")
    cmd = "nohup streamlit run main.py >/dev/null 2>&1 &"
    subprocess.Popen(cmd, shell=True)

def main():
    load_dotenv()
    token = os.getenv("NGROK_AUTH_TOKEN")

    root_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(root_dir)

    install_chromium_if_needed()
    kill_streamlit()
    start_streamlit()

    # Start tunnel
    tunnel = setup_ngrok(token)
    print(f"🎉 Your Streamlit app is live at: {tunnel.public_url}")

if __name__ == "__main__":
    main()
