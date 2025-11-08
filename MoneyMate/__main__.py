"""
MoneyMate package entry point.

This file allows the application to be run as a module 
from the 'artifact' directory using:
python -m MoneyMate
"""

try:
    # Use a relative import to start the app
    from .gui.app import run_gui
except ImportError as e:
    print("ImportError: Could not import the GUI application.")
    print("Please ensure you are running this from the 'artifact' directory using: python -m MoneyMate")
    print(f"Error details: {e}")
    import sys
    sys.exit(1)


if __name__ == "__main__":
    run_gui()