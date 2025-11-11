# test/gui/conftest.py
#
# !!! NON USARE matplotlib.use('Agg') !!!
# Causa un conflitto diretto con FigureCanvasTkAgg
# usato in charts_frame.py e genera TclError.
#
# import matplotlib
# matplotlib.use('Agg') 

import pytest
import tkinter as tk
from unittest.mock import MagicMock, patch

from MoneyMate.gui.app import MoneyMateGUI

@pytest.fixture
def app(mocker):
    """
    Fixture per creare e distruggere un'istanza di MoneyMateGUI per ogni test.
    Effettua anche il patch di 'set_db_path' per prevenire la creazione di file.
    """
    # Patch di set_db_path per non fare nulla
    mocker.patch('MoneyMate.gui.app.set_db_path')
    
    # Crea l'istanza dell'app
    app_instance = MoneyMateGUI()
    
    # Fornisce l'app al test
    yield app_instance
    
    # Teardown: distrugge la finestra dell'app dopo il test
    try:
        app_instance.destroy()
    except tk.TclError:
        pass # La finestra potrebbe essere già distrutta

@pytest.fixture
def mock_api(mocker):
    """
    Simula tutte le funzioni api_... importate e usate dai frame della GUI.
    Restituisce un dizionario di mock che i test possono configurare.
    """
    mocks = {
        # MoneyMate.gui.app
        'logout': mocker.patch('MoneyMate.gui.app.api_logout_user'),
        
        # MoneyMate.gui.login_frame
        'register': mocker.patch('MoneyMate.gui.login_frame.api_register_user'),
        'login': mocker.patch('MoneyMate.gui.login_frame.api_login_user'),
        
        # MoneyMate.gui.expenses_frame
        'add_expense': mocker.patch('MoneyMate.gui.expenses_frame.api_add_expense'),
        'get_expenses': mocker.patch('MoneyMate.gui.expenses_frame.api_get_expenses'),
        'delete_expense': mocker.patch('MoneyMate.gui.expenses_frame.api_delete_expense'),
        'update_expense': mocker.patch('MoneyMate.gui.expenses_frame.api_update_expense'),
        'get_categories_exp': mocker.patch('MoneyMate.gui.expenses_frame.api_get_categories'),
        'search_expenses': mocker.patch('MoneyMate.gui.expenses_frame.api_search_expenses'),
        
        # MoneyMate.gui.contacts_frame
        'add_contact': mocker.patch('MoneyMate.gui.contacts_frame.api_add_contact'),
        'get_contacts': mocker.patch('MoneyMate.gui.contacts_frame.api_get_contacts'),
        'delete_contact': mocker.patch('MoneyMate.gui.contacts_frame.api_delete_contact'),
        
        # MoneyMate.gui.categories_frame
        'add_category': mocker.patch('MoneyMate.gui.categories_frame.api_add_category'),
        'get_categories': mocker.patch('MoneyMate.gui.categories_frame.api_get_categories'),
        'delete_category': mocker.patch('MoneyMate.gui.categories_frame.api_delete_category'),
        
        # MoneyMate.gui.transactions_frame
        'add_transaction': mocker.patch('MoneyMate.gui.transactions_frame.api_add_transaction'),
        'get_transactions': mocker.patch('MoneyMate.gui.transactions_frame.api_get_transactions'),
        'delete_transaction': mocker.patch('MoneyMate.gui.transactions_frame.api_delete_transaction'),
        'get_contacts_trans': mocker.patch('MoneyMate.gui.transactions_frame.api_get_contacts'),
        'get_contact_balance': mocker.patch('MoneyMate.gui.transactions_frame.api_get_contact_balance'),
        'get_user_net_balance': mocker.patch('MoneyMate.gui.transactions_frame.api_get_user_net_balance'),
        
        # MoneyMate.gui.charts_frame
        'get_expenses_charts': mocker.patch('MoneyMate.gui.charts_frame.api_get_expenses'),
        'get_balance_breakdown_charts': mocker.patch('MoneyMate.gui.charts_frame.api_get_user_balance_breakdown'),
        'get_categories_charts': mocker.patch('MoneyMate.gui.charts_frame.api_get_categories'),
    }
    
    # --- FIX CORRETTO ---
    # Imposta valori di ritorno 'success' specifici basati sul tipo di dati atteso

    # --- Mock che restituiscono una LISTA ---
    list_mocks = [
        'get_expenses', 'get_categories_exp', 'search_expenses',
        'get_contacts', 'get_categories', 'get_transactions',
        'get_contacts_trans', 'get_expenses_charts', 'get_categories_charts'
    ]
    for name in list_mocks:
        if name in mocks:
            mocks[name].return_value = {'success': True, 'data': []}

    # --- Mock che restituiscono un DIZIONARIO (o un singolo item) ---
    
    # FIX 1: Il Login DEVE restituire un user_id
    mocks['login'].return_value = {
        'success': True, 
        'data': {'user_id': 1, 'username': 'testuser'}
    }
    
    # I bilanci sono dizionari
    mocks['get_contact_balance'].return_value = {'success': True, 'data': {'balance': 0.0}}
    mocks['get_user_net_balance'].return_value = {'success': True, 'data': {'net_balance': 0.0}}
    
    # FIX 2: Il breakdown (per i grafici) DEVE essere un dict, non una list
    mocks['get_balance_breakdown_charts'].return_value = {'success': True, 'data': {}} 

    # --- Mock per semplici ADD/DELETE/UPDATE/REGISTER/LOGOUT ---
    simple_success_mocks = [
        'logout', 'register', 'add_expense', 'delete_expense', 'update_expense',
        'add_contact', 'delete_contact', 'add_category', 'delete_category',
        'add_transaction', 'delete_transaction'
    ]
    for name in simple_success_mocks:
        if name in mocks:
            mocks[name].return_value = {'success': True} # 'data' spesso non è necessario

    # Fallback per qualsiasi mock dimenticato
    for mock in mocks.values():
        if not mock.return_value: # Se non già impostato
            mock.return_value = {'success': True, 'data': []}
            
    return mocks

@pytest.fixture
def mock_messagebox(mocker):
    """Simula tutte le funzioni di tkinter.messagebox."""
    return {
        'showerror': mocker.patch('tkinter.messagebox.showerror'),
        'showinfo': mocker.patch('tkinter.messagebox.showinfo'),
        'askyesno': mocker.patch('tkinter.messagebox.askyesno'),
    }

@pytest.fixture
def mock_simpledialog(mocker):
    """Simula tkinter.simpledialog.askstring."""
    return mocker.patch('tkinter.simpledialog.askstring')

@pytest.fixture
def logged_in_app(app, mock_api):
    """
    Fixture di aiuto per mettere l'app nello stato 'logged-in'.
    Esegue il login dell'utente e gestisce la transizione.
    """
    # Esegue il login
    app.on_login_success(user_id=1, username='testuser')
    app.update_idletasks() # Processa gli eventi di login (MOLTO IMPORTANTE)
    return app