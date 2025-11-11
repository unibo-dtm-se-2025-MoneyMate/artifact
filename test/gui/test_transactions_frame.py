# test/gui/test_transactions_frame.py
import pytest
import tkinter as tk
from unittest.mock import MagicMock, call

def test_transactions_refresh_loads_data(logged_in_app, mock_api):
    """
    Test that refreshing the TransactionsFrame loads both contacts
    and transactions, and populates the table correctly.
    """
    # --- Arrange ---
    app = logged_in_app
    trans_frame = app.frames['TransactionsFrame']
    
    # 1. Mock contacts (for the dropdown)
    mock_api['get_contacts_trans'].return_value = {
        'success': True,
        'data': [{'id': 5, 'name': 'Alice'}]
    }
    
    # 2. Mock transactions (for the table)
    # The default "All" filter calls get_transactions TWICE.
    # We must mock both calls.
    mock_sent = {
        'success': True,
        'data': [
            {
                'id': 101, 'date': '2025-01-01', 'type': 'credit',
                'from_user_id': 1, 'to_user_id': 2, 
                'description': 'Loan', 'amount': 50.0, 'contact_id': 5
            }
        ]
    }
    mock_received = {'success': True, 'data': []}
    mock_api['get_transactions'].side_effect = [mock_sent, mock_received]
    
    # 3. Mock net balance
    mock_api['get_user_net_balance'].return_value = {'success': True, 'data': {'net_balance': -50.0}}
    
    # --- Act ---
    trans_frame.refresh()
    app.update_idletasks()
    
    # --- Assert ---
    # 1. Check that APIs were called
    mock_api['get_contacts_trans'].assert_called_with(1, order="name_asc")
    mock_api['get_user_net_balance'].assert_called_with(1)
    
    # 2. Check that get_transactions was called twice
    mock_api['get_transactions'].assert_has_calls([
        call(user_id=1, as_sender=True, order="date_desc"),
        call(user_id=1, as_sender=False, order="date_desc")
    ])

    # 3. Check combobox
    assert 'Alice' in trans_frame.contact_combo['values']
    
    # 4. Check table (should only have the one 'sent' item)
    table_items = trans_frame.table.get_children()
    assert len(table_items) == 1
    
    # 5. Check row content
    row_values = trans_frame.table.item(table_items[0])['values']
    assert row_values[0] == 101       # ID
    assert row_values[3] == 'Sent'    # Direction
    assert row_values[4] == 'Alice'   # Counterparty (resolved from contact_id)
    assert row_values[6] == '50.00'   # Amount

def test_transactions_add_transaction(logged_in_app, mock_api, mock_messagebox, mock_simpledialog):
    """
    Test that adding a transaction mocks the simpledialog and calls
    the correct API.
    """
    # --- Arrange ---
    app = logged_in_app
    trans_frame = app.frames['TransactionsFrame']
    
    # 1. Refresh to load contacts
    mock_api['get_contacts_trans'].return_value = {
        'success': True,
        'data': [{'id': 5, 'name': 'Alice'}]
    }
    # Set up the get_transactions mock for the refresh call
    mock_api['get_transactions'].side_effect = [
        {'success': True, 'data': []}, # 1. Sent (for setup refresh)
        {'success': True, 'data': []}, # 2. Received (for setup refresh)
        {'success': True, 'data': []}, # 3. Sent (for refresh after add)
        {'success': True, 'data': []}  # 4. Received (for refresh after add)
    ]
    trans_frame.refresh()
    app.update_idletasks()

    # 2. Mock the simpledialog to return a user ID
    mock_simpledialog.return_value = '2' 
    
    # 3. Mock the add_transaction API
    mock_api['add_transaction'].return_value = {'success': True}

    # --- Act ---
    # 4. Simulate filling the form
    trans_frame.date_entry.delete(0, tk.END) # <-- ADD THIS
    trans_frame.date_entry.insert(0, '2025-01-05')
    
    trans_frame.contact_combo.set('Alice')
    trans_frame.type_combo.set('credit')
    
    trans_frame.amount_entry.delete(0, tk.END) # <-- ADD THIS
    trans_frame.amount_entry.insert(0, '25.0')
    
    trans_frame.desc_entry.delete(0, tk.END) # <-- ADD THIS
    trans_frame.desc_entry.insert(0, 'Payment')
    
    # 5. Simulate button click
    trans_frame.add_transaction()
    app.update_idletasks()
    
    # --- Assert ---
    # 6. Check that the dialog was shown
    mock_simpledialog.assert_called()
    
    # 7. Check that the API was called with correct data
    mock_api['add_transaction'].assert_called_with(
        from_user_id=1,
        to_user_id=2,  # From the mocked simpledialog
        type_='credit',
        amount=25.0,
        date='2025-01-05',
        description='Payment',
        contact_id=5   # Mapped from 'Alice'
    )
    
    # 8. Check success message
    mock_messagebox['showinfo'].assert_called_with("Success", "Transaction added.")

def test_transactions_remove_sent_transaction(logged_in_app, mock_api, mock_messagebox):
    """
    Test that removing a 'Sent' transaction works.
    """
    # --- Arrange ---
    app = logged_in_app
    trans_frame = app.frames['TransactionsFrame']
    
    # 1. Populate the table with a 'Sent' transaction
    mock_api['get_transactions'].side_effect = [
        {
            'success': True,
            'data': [
                {
                    'id': 101, 'date': '2025-01-01', 'type': 'credit',
                    'from_user_id': 1, 'to_user_id': 2, 
                    'description': 'Loan', 'amount': 50.0, 'contact_id': 5
                }
            ]
        },
        {'success': True, 'data': []} # Received call
    ]
    trans_frame.refresh()
    app.update_idletasks()
    
    # 2. Mock delete API and confirmation
    mock_api['delete_transaction'].return_value = {'success': True, 'data': {'deleted': 1}}
    mock_messagebox['askyesno'].return_value = True
    
    # 3. Reset the get_transactions mock for the refresh *after* delete
    mock_api['get_transactions'].side_effect = [
        {'success': True, 'data': []}, # Sent
        {'success': True, 'data': []}  # Received
    ]

    # --- Act ---
    # 4. Select the item
    table_item = trans_frame.table.get_children()[0]
    trans_frame.table.selection_set(table_item)
    
    # 5. Click remove
    trans_frame.remove_transaction()
    app.update_idletasks()
    
    # --- Assert ---
    # 6. Check confirmation and API call
    mock_messagebox['askyesno'].assert_called()
    mock_api['delete_transaction'].assert_called_with(transaction_id=101, user_id=1)
    mock_messagebox['showinfo'].assert_called_with("Success", "Transaction removed.")

def test_transactions_cannot_remove_received(logged_in_app, mock_api, mock_messagebox):
    """
    Test that attempting to remove a 'Received' transaction shows an error.
    """
    # --- Arrange ---
    app = logged_in_app
    trans_frame = app.frames['TransactionsFrame']
    
    # 1. Load a 'Received' transaction (by setting 'as_sender=False')
    trans_frame.filter_type_var.set("Received")
    mock_api['get_transactions'].return_value = {
        'success': True,
        'data': [
            {
                'id': 102, 'date': '2025-01-02', 'type': 'credit',
                'from_user_id': 2, 'to_user_id': 1, 
                'description': 'Payment', 'amount': 10.0, 'contact_id': None
            }
        ]
    }
    trans_frame.refresh()
    app.update_idletasks()
    
    # --- Act ---
    # 2. Select the item
    table_item = trans_frame.table.get_children()[0]
    trans_frame.table.selection_set(table_item)
    
    # 3. Click remove
    trans_frame.remove_transaction()
    app.update_idletasks()
    
    # --- Assert ---
    # 4. Check that an error is shown and the API is NOT called
    mock_messagebox['showerror'].assert_called_with(
        "Error", "You can only remove transactions you have sent."
    )
    mock_api['delete_transaction'].assert_not_called()