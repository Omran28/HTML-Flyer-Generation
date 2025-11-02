import sys, os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from ui.streamlit_app import create_interface


def main():
    create_interface()


if __name__ == "__main__":
    main()
