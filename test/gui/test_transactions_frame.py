import pytest
import tkinter as tk
from unittest.mock import call

# Copertura estesa:
# - Refresh all (sent+received)
# - Filtri sent / received
# - Ricerca testo
# - Add transaction: dialog annullato / user id non numerico / self user id
# - Net balance errore
# - Remove senza selezione
# - Errore caricamento sent
#
# Uso substring per messaggi.

def test_transactions_refresh_all(logged_in_app, mock_api, mock_messagebox):
    """Refresh con filtro 'All': carica chiamate sent e received e popola correttamente."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': [{'id': 5, 'name': 'Alice'}]}
    mock_api['get_transactions'].side_effect = [
        {'success': True, 'data': [{'id': 101, 'date': '2025-01-01', 'type': 'credit',
                                    'from_user_id': 1, 'to_user_id': 2, 'description': 'Loan',
                                    'amount': 50.0, 'contact_id': 5}]},
        {'success': True, 'data': []}
    ]
    mock_api['get_user_net_balance'].return_value = {'success': True, 'data': {'net_balance': -50.0}}
    frame.refresh()
    mock_api['get_contacts_trans'].assert_called_with(1, order="name_asc")
    mock_api['get_transactions'].assert_has_calls([
        call(user_id=1, as_sender=True, order="date_desc"),
        call(user_id=1, as_sender=False, order="date_desc")
    ])
    assert len(frame.table.get_children()) == 1

def test_transactions_filter_sent_only(logged_in_app, mock_api):
    """Filtro 'Sent' -> solo chiamata as_sender True, una riga in tabella."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    frame.filter_type_var.set("Sent")
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': []}
    mock_api['get_transactions'].return_value = {'success': True, 'data': [
        {'id': 11, 'date': '2025-01-05', 'type': 'debit', 'from_user_id': 1,
         'to_user_id': 2, 'description': 'Test', 'amount': 10.0}
    ]}
    mock_api['get_user_net_balance'].return_value = {'success': True, 'data': {'net_balance': 0.0}}
    frame.refresh()
    mock_api['get_transactions'].assert_called_once()
    assert len(frame.table.get_children()) == 1

def test_transactions_filter_received_only(logged_in_app, mock_api):
    """Filtro 'Received' -> as_sender False."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    frame.filter_type_var.set("Received")
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': []}
    mock_api['get_transactions'].return_value = {'success': True, 'data': [
        {'id': 12, 'date': '2025-01-06', 'type': 'credit', 'from_user_id': 2,
         'to_user_id': 1, 'description': 'Pay', 'amount': 20.0}
    ]}
    mock_api['get_user_net_balance'].return_value = {'success': True, 'data': {'net_balance': 0.0}}
    frame.refresh()
    mock_api['get_transactions'].assert_called_once()
    assert len(frame.table.get_children()) == 1

def test_transactions_search_filter(logged_in_app, mock_api):
    """Ricerca testo (loan) filtra correttamente le transazioni caricate."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    frame.filter_type_var.set("All")
    frame.search_entry.insert(0, "loan")
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': []}
    mock_api['get_transactions'].side_effect = [
        {'success': True, 'data': [
            {'id': 200, 'date': '2025-02-01', 'type': 'credit', 'from_user_id': 1,
             'to_user_id': 9, 'description': 'Loan', 'amount': 30.0}
        ]},
        {'success': True, 'data': []}
    ]
    mock_api['get_user_net_balance'].return_value = {'success': True, 'data': {'net_balance': 0.0}}
    frame.refresh()
    items = frame.table.get_children()
    assert len(items) == 1
    vals = frame.table.item(items[0])['values']
    assert "loan" in vals[5].lower()

def test_transactions_add_cancel_dialog(logged_in_app, mock_api, mock_messagebox, mock_simpledialog):
    """Dialog annullato (None) -> nessuna API add_transaction."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': [{'id': 5, 'name': 'Alice'}]}
    mock_api['get_transactions'].side_effect = [{'success': True, 'data': []}, {'success': True, 'data': []}]
    frame.refresh()
    frame.date_entry.delete(0, tk.END); frame.date_entry.insert(0, '2025-01-10')
    frame.contact_combo.set('Alice')
    frame.amount_entry.insert(0, '12')
    frame.desc_entry.insert(0, 'Test')
    mock_simpledialog.return_value = None
    frame.add_transaction()
    mock_api['add_transaction'].assert_not_called()

def test_transactions_add_invalid_user_id(logged_in_app, mock_api, mock_messagebox, mock_simpledialog):
    """User ID non numerico nel dialog -> errore e nessuna API add."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': [{'id': 7, 'name': 'Bob'}]}
    mock_api['get_transactions'].side_effect = [{'success': True, 'data': []}, {'success': True, 'data': []}]
    frame.refresh()
    frame.date_entry.delete(0, tk.END); frame.date_entry.insert(0, '2025-01-11')
    frame.contact_combo.set('Bob')
    frame.amount_entry.insert(0, '5')
    frame.desc_entry.insert(0, 'Err')
    mock_simpledialog.return_value = 'abc'
    frame.add_transaction()
    args, _ = mock_messagebox['showerror'].call_args
    assert "user id" in args[1].lower()
    mock_api['add_transaction'].assert_not_called()

def test_transactions_add_self_user_id(logged_in_app, mock_api, mock_messagebox, mock_simpledialog):
    """User ID uguale al proprio -> errore auto-destinatario."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': [{'id': 9, 'name': 'Alice'}]}
    mock_api['get_transactions'].side_effect = [{'success': True, 'data': []}, {'success': True, 'data': []}]
    frame.refresh()
    frame.date_entry.delete(0, tk.END); frame.date_entry.insert(0, '2025-01-12')
    frame.contact_combo.set('Alice')
    frame.amount_entry.insert(0, '7')
    frame.desc_entry.insert(0, 'Self')
    mock_simpledialog.return_value = '1'
    frame.add_transaction()
    args, _ = mock_messagebox['showerror'].call_args
    assert "yourself" in args[1].lower() or "your self" in args[1].lower()
    mock_api['add_transaction'].assert_not_called()

def test_transactions_net_balance_error(logged_in_app, mock_api):
    """Errore su net balance API -> label mostra stato 'Error' (fallback)."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    frame.filter_type_var.set("Sent")
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': []}
    mock_api['get_transactions'].return_value = {'success': True, 'data': []}
    mock_api['get_user_net_balance'].return_value = {'success': False, 'error': 'fail'}
    frame.refresh()
    assert "error" in frame.balance_label.cget("text").lower()

def test_transactions_remove_without_selection(logged_in_app, mock_api, mock_messagebox):
    """Remove senza selezione -> warning e nessuna delete API."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    frame.remove_transaction()
    args, _ = mock_messagebox['showwarning'].call_args
    assert "select" in args[1].lower()
    mock_api['delete_transaction'].assert_not_called()

def test_transactions_error_loading_sent(logged_in_app, mock_api, mock_messagebox):
    """Errore caricamento transazioni sent -> messagebox error (sent branch)."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    frame.filter_type_var.set("Sent")
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': []}
    mock_api['get_transactions'].return_value = {'success': False, 'error': 'DB down'}
    mock_api['get_user_net_balance'].return_value = {'success': True, 'data': {'net_balance': 0}}
    frame.refresh()
    args, _ = mock_messagebox['showerror'].call_args
    assert "sent" in args[1].lower() or "db down" in args[1].lower()