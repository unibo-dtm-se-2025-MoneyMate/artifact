# test/gui/conftest.py
#
# !!! NON USARE matplotlib.use('Agg') !!!
# Causa un conflitto diretto con FigureCanvasTkAgg
# usato in charts_frame.py e genera TclError.
#
# import matplotlib
# matplotlib.use('Agg')
#
# Versione SENZA uso della fixture 'mocker' (pytest-mock non richiesto).
# Si utilizza 'monkeypatch' + unittest.mock.MagicMock per mantenere i test
# semplici, isolati e deterministici. Se Tk/Tcl non è disponibile viene
# effettuato uno skip pulito dei test GUI (fail-fast).
#
# Principi SE rispettati:
# - Isolamento (fixture per ogni test)
# - Determinismo (mock con valori fissati)
# - Chiarezza (commenti e pattern Arrange–Act–Assert usato nei test)
# - Fail-fast per ambiente non idoneo (skip se Tk assente)

import pytest
import tkinter as tk
from unittest.mock import MagicMock

from MoneyMate.gui.app import MoneyMateGUI


def _patch(monkeypatch, dotted_path):
    """
    Utility interna per creare e applicare un MagicMock sostituendo l'attributo indicato.
    Ritorna il mock creato.
    """
    module_path, attr_name = dotted_path.rsplit('.', 1)
    module = __import__(module_path, fromlist=[attr_name])
    mock = MagicMock()
    monkeypatch.setattr(module, attr_name, mock)
    return mock


@pytest.fixture
def app(monkeypatch):
    """
    Fixture per creare e distruggere un'istanza di MoneyMateGUI per ogni test.
    Effettua patch di 'set_db_path' (se esiste) per prevenire la creazione di file.
    Se Tk/Tcl non è disponibile --> skip pulito dei test GUI.
    """
    try:
        from MoneyMate.gui import app as app_module
        if hasattr(app_module, 'set_db_path'):
            monkeypatch.setattr(app_module, 'set_db_path', lambda *a, **kw: None)
    except ImportError:
        pass

    try:
        app_instance = MoneyMateGUI()
    except tk.TclError:
        pytest.skip("Tk/Tcl non disponibile: installa Python da python.org per eseguire i test GUI.")
        return

    yield app_instance

    try:
        app_instance.destroy()
    except tk.TclError:
        pass


@pytest.fixture
def mock_api(monkeypatch):
    """
    Simula tutte le funzioni api_... importate e usate dai frame della GUI.
    Restituisce un dizionario di mock che i test possono configurare.
    """
    mocks = {
        # MoneyMate.gui.app
        'logout': _patch(monkeypatch, 'MoneyMate.gui.app.api_logout_user'),

        # MoneyMate.gui.login_frame
        'register': _patch(monkeypatch, 'MoneyMate.gui.login_frame.api_register_user'),
        'login': _patch(monkeypatch, 'MoneyMate.gui.login_frame.api_login_user'),

        # MoneyMate.gui.expenses_frame
        'add_expense': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_add_expense'),
        'get_expenses': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_get_expenses'),
        'delete_expense': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_delete_expense'),
        'update_expense': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_update_expense'),
        'get_categories_exp': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_get_categories'),
        'search_expenses': _patch(monkeypatch, 'MoneyMate.gui.expenses_frame.api_search_expenses'),

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
        'get_contact_balance': _patch(monkeypatch, 'MoneyMate.gui.transactions_frame.api_get_contact_balance'),
        'get_user_net_balance': _patch(monkeypatch, 'MoneyMate.gui.transactions_frame.api_get_user_net_balance'),

        # MoneyMate.gui.charts_frame
        'get_expenses_charts': _patch(monkeypatch, 'MoneyMate.gui.charts_frame.api_get_expenses'),
        'get_balance_breakdown_charts': _patch(monkeypatch, 'MoneyMate.gui.charts_frame.api_get_user_balance_breakdown'),
        'get_categories_charts': _patch(monkeypatch, 'MoneyMate.gui.charts_frame.api_get_categories'),
    }

    # Mock che restituiscono liste
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

    # Bilanci / breakdown
    mocks['get_contact_balance'].return_value = {'success': True, 'data': {'balance': 0.0}}
    mocks['get_user_net_balance'].return_value = {'success': True, 'data': {'net_balance': 0.0}}
    mocks['get_balance_breakdown_charts'].return_value = {'success': True, 'data': {}}

    # Operazioni semplici
    for name in [
        'logout', 'register', 'add_expense', 'delete_expense', 'update_expense',
        'add_contact', 'delete_contact', 'add_category', 'delete_category',
        'add_transaction', 'delete_transaction'
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
    Simula tutte le funzioni di tkinter.messagebox.
    Best practice: mockare anche showwarning, usato nei casi di 'nessuna selezione'.
    """
    from tkinter import messagebox
    mocks = {
        'showerror': MagicMock(),
        'showinfo': MagicMock(),
        'showwarning': MagicMock(),   # <- AGGIUNTO per i test di warning
        'askyesno': MagicMock(),
    }
    monkeypatch.setattr(messagebox, 'showerror', mocks['showerror'])
    monkeypatch.setattr(messagebox, 'showinfo', mocks['showinfo'])
    monkeypatch.setattr(messagebox, 'showwarning', mocks['showwarning'])  # <- AGGIUNTO
    monkeypatch.setattr(messagebox, 'askyesno', mocks['askyesno'])
    return mocks


@pytest.fixture
def mock_simpledialog(monkeypatch):
    """
    Simula tkinter.simpledialog.askstring.
    """
    from tkinter import simpledialog
    mock = MagicMock()
    monkeypatch.setattr(simpledialog, 'askstring', mock)
    return mock


@pytest.fixture
def logged_in_app(app, mock_api):
    """
    Fixture di aiuto per mettere l'app nello stato 'logged-in'.
    Esegue il login dell'utente e gestisce la transizione.
    """
    app.on_login_success(user_id=1, username='testuser')
    app.update_idletasks()  # Processa gli eventi di login (MOLTO IMPORTANTE)
    return app