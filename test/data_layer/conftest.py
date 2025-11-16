# test/conftest.py
import sys
import os

# Calcola la root del progetto (cartella che contiene MoneyMate e test)
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

# Inserisce la root in sys.path così che "import MoneyMate" funzioni sempre
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)
