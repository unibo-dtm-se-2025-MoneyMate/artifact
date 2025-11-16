"""
Shared pytest fixtures and monkeypatch helpers for GUI tests.

This conftest module:

- Safely instantiates MoneyMateGUI by patching data_layer.api.set_db_path
  before the GUI import, avoiding side-effect DB creation.
- Provides an `app` fixture that skips cleanly when Tk/Tcl is unavailable.
- Exposes `mock_api` to patch all API calls used by GUI frames with MagicMocks.
- Exposes `mock_messagebox` to mock tkinter.messagebox dialogs.
- Provides `logged_in_app` to put the GUI into a logged-in state for frame tests.
"""

import pytest
from unittest.mock import MagicMock
import importlib


def _patch(monkeypatch, dotted_path):
    """
    Crea e applica un MagicMock sull'attributo indicato.
    """
    module_path, attr_name = dotted_path.rsplit('.', 1)
    module = __import__(module_path, fromlist=[attr_name])
    mock = MagicMock()
    # raising=True: fallisce subito se l'attributo non esiste (fail-fast utile in sviluppo)
    monkeypatch.setattr(module, attr_name, mock, raising=True)
    return mock


@pytest.fixture
def app(monkeypatch):
    """
    Istanzia MoneyMateGUI in modo sicuro:
    - Patch set_db_path a no-op prima di importare la GUI (evita side-effect su file).
    - Import lazy di tkinter e MoneyMateGUI.
    - Skip pulito se Tk/Tcl manca.
    """
    # Patch preventivo di set_db_path
    try:
        api_module = importlib.import_module('MoneyMate.data_layer.api')
        monkeypatch.setattr(api_module, 'set_db_path', lambda *a, **kw: None, raising=True)
    except Exception as e:
        pytest.skip(f"Impossibile patchare set_db_path prima dell'import GUI: {e}")
        return

    # Import lazy di tkinter
    try:
        import tkinter as tk  # noqa: F401
    except Exception as e:
        pytest.skip(f"GUI non disponibile (import tkinter fallito): {e}")
        return

    # Import lazy della GUI
    try:
        gui_app_module = importlib.import_module('MoneyMate.gui.app')
        MoneyMateGUI = getattr(gui_app_module, 'MoneyMateGUI')
    except Exception as e:
        pytest.skip(f"GUI non disponibile (import MoneyMateGUI fallito): {e}")
        return

    # Istanziazione con gestione TclError
    try:
        app_instance = MoneyMateGUI()
    except Exception as e:
        pytest.skip(f"Tk/Tcl non disponibile: {e}")
        return

    yield app_instance

    try:
        app_instance.destroy()
    except Exception:
        pass


@pytest.fixture
def mock_api(monkeypatch):
    """
    Mock di tutte le API usate dai frame GUI.
    Patch SOLO ciò che è effettivamente importato in ciascun modulo.
    """
    mocks = {
        # MoneyMate.gui.app
        'logout': _patch(monkeypatch, 'MoneyMate.gui.app.api_logout_user'),

        # MoneyMate.gui.login_frame
        'login': _patch(monkeypatch, 'MoneyMate.gui.login_frame.api_login_user'),

        # MoneyMate.gui.register_frame
        'register': _patch(monkeypatch, 'MoneyMate.gui.register_frame.api_register_user'),

        # MoneyMate.gui.expenses_frame
        'add_expense': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_add_expense'),
        'get_expenses': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_get_expenses'),
        'delete_expense': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_delete_expense'),
        'update_expense': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_update_expense'),
        'get_categories_exp': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_get_categories'),
        'search_expenses': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_search_expenses'),
        'clear_expenses': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_clear_expenses'),

        # MoneyMate.gui.contacts_frame
        'add_contact': _patch(monkeypatch, 'MoneyMate.gui.contacts_frame.api_add_contact'),
        'get_contacts': _patch(monkeypatch, 'MoneyMate.gui.contacts_frame.api_get_contacts'),
        'delete_contact': _patch(monkeypatch, 'MoneyMate.gui.contacts_frame.api_delete_contact'),

        # MoneyMate.gui.categories_frame
        'add_category': _patch(monkeypatch, 'MoneyMate.gui.categories_frame.api_add_category'),
        'get_categories': _patch(monkeypatch, 'MoneyMate.gui.categories_frame.api_get_categories'),
        'delete_category': _patch(monkeypatch, 'MoneyMate.gui.categories_frame.api_delete_category'),

        # MoneyMate.gui.transactions_frame
        'add_transaction': _patch(monkeypatch, 'MoneyMate.gui.transactions_frame.api_add_transaction'),
        'get_transactions': _patch(monkeypatch, 'MoneyMate.gui.transactions_frame.api_get_transactions'),
        'delete_transaction': _patch(monkeypatch, 'MoneyMate.gui.transactions_frame.api_delete_transaction'),
        'get_contacts_trans': _patch(monkeypatch, 'MoneyMate.gui.transactions_frame.api_get_contacts'),
        'get_balance_breakdown': _patch(monkeypatch, 'MoneyMate.gui.transactions_frame.api_get_user_balance_breakdown'),

        # MoneyMate.gui.charts_frame
        'get_expenses_charts': _patch(monkeypatch, 'MoneyMate.gui.charts_frame.api_get_expenses'),
        'get_balance_breakdown_charts': _patch(monkeypatch, 'MoneyMate.gui.charts_frame.api_get_user_balance_breakdown'),
        'get_categories_charts': _patch(monkeypatch, 'MoneyMate.gui.charts_frame.api_get_categories'),
    }

    # Valori di default
    for name in [
        'get_expenses', 'get_categories_exp', 'search_expenses',
        'get_contacts', 'get_categories', 'get_transactions',
        'get_contacts_trans', 'get_expenses_charts', 'get_categories_charts'
    ]:
        mocks[name].return_value = {'success': True, 'data': []}

    # Login deve avere user_id
    mocks['login'].return_value = {
        'success': True,
        'data': {'user_id': 1, 'username': 'testuser'}
    }

    # Breakdown/bilanci
    mocks['get_balance_breakdown'].return_value = {'success': True, 'data': {}}
    mocks['get_balance_breakdown_charts'].return_value = {'success': True, 'data': {}}

    # Operazioni semplici -> success
    for name in [
        'logout', 'register', 'add_expense', 'delete_expense', 'update_expense',
        'add_contact', 'delete_contact', 'add_category', 'delete_category',
        'add_transaction', 'delete_transaction', 'clear_expenses'
    ]:
        mocks[name].return_value = {'success': True}

    # Fallback generico
    for mock in mocks.values():
        if not mock.return_value:
            mock.return_value = {'success': True, 'data': []}

    return mocks


@pytest.fixture
def mock_messagebox(monkeypatch):
    """
    Mock di tkinter.messagebox usato nei frame GUI.
    """
    try:
        from tkinter import messagebox
    except Exception as e:
        pytest.skip(f"GUI non disponibile (import messagebox fallito): {e}")
        return

    mocks = {
        'showerror': MagicMock(),
        'showinfo': MagicMock(),
        'showwarning': MagicMock(),
        'askyesno': MagicMock(),
    }
    monkeypatch.setattr(messagebox, 'showerror', mocks['showerror'])
    monkeypatch.setattr(messagebox, 'showinfo', mocks['showinfo'])
    monkeypatch.setattr(messagebox, 'showwarning', mocks['showwarning'])
    monkeypatch.setattr(messagebox, 'askyesno', mocks['askyesno'])
    return mocks


@pytest.fixture
def logged_in_app(app, mock_api):
    """
    Porta l'app nello stato 'logged-in' per i test dei frame.
    """
    app.on_login_success(user_id=1, username='testuser')
    try:
        app.update_idletasks()
    except Exception:
        pass
    return app