import sys, os
from core import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.streamlit_app import create_interface


def main():
    model = config.ACTIVE_MODEL
    api = config.ACTIVE_API_KEY
    create_interface(model, api)


if __name__ == "__main__":
    main()
