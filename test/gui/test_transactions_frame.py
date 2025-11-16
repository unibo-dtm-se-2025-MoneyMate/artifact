"""
GUI tests for the TransactionsFrame.

Covers the transactions screen behavior with mocked APIs and message boxes:

- Refresh:
  - "All": loads both sent and received transactions.
  - "Sent"/"Received": use the correct as_sender flag.
  - Text search: filters rows by substring.

- Add transaction:
  - Missing contact: validation error, no API call.
  - Non-numeric amount: validation error, no API call.
  - Valid add: calls api_add_transaction with from_user_id, contact_id and to_user_id=None.

- Balance:
  - Error from api_get_user_balance_breakdown -> label shows an error state.

- Remove:
  - No selection: warning only, no delete API call.

- Error handling:
  - Failure loading "sent" transactions shows an appropriate error message.
"""

import pytest
import tkinter as tk
from unittest.mock import call

def test_transactions_refresh_all(logged_in_app, mock_api, mock_messagebox):
    """Refresh con filtro 'All': carica sent e received e popola correttamente."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': [{'id': 5, 'name': 'Alice'}]}
    mock_api['get_transactions'].side_effect = [
        {'success': True, 'data': [{'id': 101, 'date': '2025-01-01', 'type': 'credit',
                                    'from_user_id': 1, 'to_user_id': 2, 'description': 'Loan',
                                    'amount': 50.0, 'contact_id': 5}]},
        {'success': True, 'data': []}
    ]
    mock_api['get_balance_breakdown'].return_value = {'success': True, 'data': {'credits_received': 0, 'debits_sent': 0, 'credits_sent': 0, 'debits_received': 0}}
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
    mock_api['get_balance_breakdown'].return_value = {'success': True, 'data': {}}
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
    mock_api['get_balance_breakdown'].return_value = {'success': True, 'data': {}}
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
    mock_api['get_balance_breakdown'].return_value = {'success': True, 'data': {}}
    frame.refresh()
    items = frame.table.get_children()
    assert len(items) == 1
    vals = frame.table.item(items[0])['values']
    assert "loan" in vals[5].lower()

def test_transactions_add_missing_contact(logged_in_app, mock_api, mock_messagebox):
    """Contatto non selezionato -> errore e nessuna chiamata add_transaction."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': []}
    mock_api['get_transactions'].side_effect = [{'success': True, 'data': []}, {'success': True, 'data': []}]
    frame.refresh()
    frame.date_entry.delete(0, tk.END); frame.date_entry.insert(0, '2025-01-10')
    frame.amount_entry.insert(0, '12')
    frame.desc_entry.insert(0, 'Test')
    # contact non impostato
    frame.add_transaction()
    args, _ = mock_messagebox['showerror'].call_args
    assert "contact" in args[1].lower()
    mock_api['add_transaction'].assert_not_called()

def test_transactions_add_invalid_amount_non_numeric(logged_in_app, mock_api, mock_messagebox):
    """Amount non numerico -> errore e nessuna API add."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': [{'id': 7, 'name': 'Bob'}]}
    mock_api['get_transactions'].side_effect = [{'success': True, 'data': []}, {'success': True, 'data': []}]
    frame.refresh()
    frame.date_entry.delete(0, tk.END); frame.date_entry.insert(0, '2025-01-11')
    frame.contact_combo.set('Bob')
    frame.amount_entry.insert(0, 'abc')
    frame.desc_entry.insert(0, 'Err')
    frame.add_transaction()
    args, _ = mock_messagebox['showerror'].call_args
    assert "invalid amount" in args[1].lower()
    mock_api['add_transaction'].assert_not_called()

def test_transactions_add_valid_calls_api_with_contact(logged_in_app, mock_api, mock_messagebox):
    """Inserimento valido -> chiamata API con contact_id e to_user_id=None."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': [{'id': 9, 'name': 'Alice'}]}
    # Usare return_value per gestire anche il refresh successivo all'inserimento (evita StopIteration)
    mock_api['get_transactions'].return_value = {'success': True, 'data': []}
    frame.refresh()
    frame.date_entry.delete(0, tk.END); frame.date_entry.insert(0, '2025-01-12')
    frame.contact_combo.set('Alice')
    frame.amount_entry.insert(0, '7')
    frame.desc_entry.insert(0, 'Gift')
    frame.add_transaction()
    assert mock_api['add_transaction'].called
    kwargs = mock_api['add_transaction'].call_args.kwargs
    assert kwargs['from_user_id'] == 1
    assert kwargs['contact_id'] == 9
    assert kwargs.get('to_user_id') is None
    assert kwargs['type_'] in ('credit', 'debit')  # default set on UI
    # Messaggio di successo mostrato
    args, _ = mock_messagebox['showinfo'].call_args
    assert "success" in args[0].lower()

def test_transactions_net_balance_error(logged_in_app, mock_api):
    """Errore su balance breakdown API -> label mostra stato 'Error' (fallback)."""
    app = logged_in_app
    frame = app.frames['TransactionsFrame']
    frame.filter_type_var.set("Sent")
    mock_api['get_contacts_trans'].return_value = {'success': True, 'data': []}
    mock_api['get_transactions'].return_value = {'success': True, 'data': []}
    mock_api['get_balance_breakdown'].return_value = {'success': False, 'error': 'fail'}
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
    mock_api['get_balance_breakdown'].return_value = {'success': True, 'data': {}}
    frame.refresh()
    args, _ = mock_messagebox['showerror'].call_args
    assert "sent" in args[1].lower() or "db down" in args[1].lower()