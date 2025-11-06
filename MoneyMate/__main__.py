"""
MoneyMate package entry point.

This allows the application to be run as a module from the 'artifact' 
directory using:
python -m MoneyMate
"""

import sys
import os

# Ensure the 'MoneyMate' package itself is in the path 
# (this helps fix some import issues)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from gui.app import run_gui
except ImportError as e:
    print("ImportError: Could not import the GUI application.")
    print("Please ensure you are running this from the 'artifact' directory using: python -m MoneyMate")
    print(f"Error details: {e}")
    sys.exit(1)


if __name__ == "__main__":
    run_gui()