# test/gui/test_expenses_frame.py
import pytest
import tkinter as tk
def test_expenses_refresh_loads_data(logged_in_app, mock_api):
    """
    Test that calling 'refresh' on the ExpensesFrame loads data
    from the API into the Treeview table.
    """
    # --- Arrange ---
    mock_api['get_expenses'].return_value = {
        'success': True,
        'data': [
            {'id': 1, 'date': '2025-01-01', 'title': 'Caffè', 'price': 1.50, 'category': 'Food'},
            {'id': 2, 'date': '2025-01-02', 'title': 'Bus', 'price': 2.00, 'category': 'Transport'}
        ]
    }
    app = logged_in_app
    exp_frame = app.frames['ExpensesFrame']

    # Configure the 'add_expense' mock
    mock_api['add_expense'].return_value = {'success': True, 'data': None}

    # --- INSERISCI QUESTO BLOCCO ---
    # Fornisci dati per il category dropdown
    mock_api['get_categories_exp'].return_value = {
        'success': True,
        'data': [
            {'id': 1, 'name': 'Food'},
            {'id': 2, 'name': 'Transport'} # Questo ID corrisponde all'asserzione del test
        ]
    }
    # --------------------------------

    # Refresh to populate category combobox
    
    exp_frame.refresh()
    
    # Process any pending tkinter events
    app.update_idletasks()
    
    # --- Assert ---
    # 1. Check that the correct API was called
    mock_api['get_expenses'].assert_called_with(user_id=1)
    
    # 2. Check that the table was populated
    table_items = exp_frame.table.get_children()
    assert len(table_items) == 2
    
    # 3. Check the content of the first row
    first_row_values = exp_frame.table.item(table_items[0])['values']
    assert first_row_values[0] == 1
    assert first_row_values[2] == 'Caffè'  # Corrisponde a exp.get("name")
    assert first_row_values[3] == 'Food'
    assert first_row_values[4] == '1.50'

def test_expenses_add_expense(logged_in_app, mock_api, mock_messagebox):
    """
    Test that filling the form and clicking 'Add' calls the API
    and shows a success message.
    """
    # --- Arrange ---
    app = logged_in_app
    exp_frame = app.frames['ExpensesFrame']
    
    # Configure the 'add_expense' mock
    mock_api['add_expense'].return_value = {'success': True, 'data': None}
    mock_api['get_categories_exp'].return_value = {
        'success': True,
        'data': [
            {'id': 1, 'name': 'Food'},
            {'id': 2, 'name': 'Transport'} # Questo corrisponde all'ID 2 nell'asserzione
        ]
    }
    # Refresh to populate category combobox
    exp_frame.refresh()
    app.update_idletasks()
    
    # --- Act ---
    # Simulate filling the form
    exp_frame.date_entry.delete(0, tk.END) # <-- ADD THIS
    exp_frame.date_entry.insert(0, '2025-01-03')
    
    exp_frame.amount_entry.delete(0, tk.END) # <-- ADD THIS
    exp_frame.amount_entry.insert(0, '15.00')
    
    exp_frame.category_combo.set('Transport')
    
    exp_frame.desc_entry.delete(0, tk.END) # <-- ADD THIS
    exp_frame.desc_entry.insert(0, 'Taxi')
    
    # Simulate button click
    exp_frame.add_expense()
    app.update_idletasks()
    
    # --- Assert ---
    # 1. Check that the add_expense API was called with the correct data
    mock_api['add_expense'].assert_called_with(
        title='Taxi',
        price=15.0,
        date='2025-01-03',
        category='Transport',
        user_id=1,
        category_id=2  # 'Transport' was mapped to id 2 by our mock
    )
    
    # 2. Check that a success message was shown
    mock_messagebox['showinfo'].assert_called_with(
        "Success", "Expense added successfully."
    )
    
    # 3. Check that the 'get_expenses' API was called again (by refresh)
    assert mock_api['get_expenses'].call_count == 2