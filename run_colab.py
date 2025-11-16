# run_colab.py

import os
import subprocess
from pyngrok import ngrok


def install_chromium():
    print("Installing Chromium browser...")
    subprocess.run(["apt-get", "update"], check=True)
    subprocess.run(["apt-get", "install", "-y", "chromium-browser"], check=True)


def setup_ngrok(token):
    print("Setting up ngrok...")
    ngrok.set_auth_token(token)
    return ngrok.connect(addr="8501", proto="http")


def kill_streamlit():
    print("Killing any existing Streamlit instances...")
    subprocess.run(["pkill", "streamlit"], stderr=subprocess.DEVNULL)


def start_streamlit():
    print("Starting Streamlit...")
    env = os.environ.copy()
    cmd = "streamlit run main.py"
    subprocess.Popen(cmd, shell=True, env=env)


def main():
    token = "34zKZUKvecXFl5BMojaUUKy6329_2Xttf9KCVPN2mDXaEDD64"
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    install_chromium()
    kill_streamlit()
    start_streamlit()
    tunnel = setup_ngrok(token)

    print(f"🚀 Streamlit app is live at: {tunnel.public_url}")


if __name__ == "__main__":
    main()
