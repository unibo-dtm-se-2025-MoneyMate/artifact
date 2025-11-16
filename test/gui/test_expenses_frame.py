"""
GUI tests for ExpensesFrame.

This suite verifies the expenses management screen behavior with mocked APIs:

- Refreshing populates the table from api_get_expenses and category choices.
- Adding a valid expense validates inputs, calls api_add_expense, and shows
  a success message.
- Validation of missing fields, invalid date format, and invalid amount.
- Updating an existing selected expense calls api_update_expense with
  the correct parameters.
- Removing without selection triggers a warning only.
- Refresh with a search term uses api_search_expenses instead of get_expenses.
- Handling API errors on refresh shows an error message and avoids populating rows.
"""

import pytest
import tkinter as tk

def test_expenses_refresh_loads_data(logged_in_app, mock_api):
    """Refresh carica spese e popola tabella correttamente."""
    mock_api['get_expenses'].return_value = {
        'success': True,
        'data': [
            {'id': 1, 'date': '2025-01-01', 'title': 'Caffè', 'price': 1.50, 'category': 'Food'},
            {'id': 2, 'date': '2025-01-02', 'title': 'Bus', 'price': 2.00, 'category': 'Transport'}
        ]
    }
    mock_api['get_categories_exp'].return_value = {'success': True, 'data': [{'id': 1, 'name': 'Food'}]}
    app = logged_in_app
    frame = app.frames['ExpensesFrame']
    frame.refresh()
    # Verifica robusta: user_id=1 nei kwargs
    assert mock_api['get_expenses'].called
    _, kwargs = mock_api['get_expenses'].call_args
    assert kwargs['user_id'] == 1
    assert len(frame.table.get_children()) == 2

def test_expenses_add_valid(logged_in_app, mock_api, mock_messagebox):
    """Aggiunta spesa valida -> success e refresh."""
    app = logged_in_app
    frame = app.frames['ExpensesFrame']
    mock_api['get_categories_exp'].return_value = {'success': True, 'data': [{'id': 2, 'name': 'Transport'}]}
    mock_api['add_expense'].return_value = {'success': True}
    frame.refresh()
    frame.date_entry.delete(0, tk.END)
    frame.date_entry.insert(0, '2025-01-03')
    frame.amount_entry.insert(0, '15.00')
    frame.category_combo.set('Transport')
    frame.desc_entry.insert(0, 'Taxi')
    frame.add_expense()
    mock_api['add_expense'].assert_called_with(
        title='Taxi', price=15.0, date='2025-01-03',
        category='Transport', user_id=1, category_id=2
    )
    args, _ = mock_messagebox['showinfo'].call_args
    assert "success" in args[0].lower()
    assert "expense" in args[1].lower()

def test_expenses_add_missing_fields(logged_in_app, mock_api, mock_messagebox):
    """Validazione: campi mancanti -> errore e nessuna API add."""
    app = logged_in_app
    frame = app.frames['ExpensesFrame']
    frame.add_expense()
    args, _ = mock_messagebox['showerror'].call_args
    assert "required" in args[1].lower()
    mock_api['add_expense'].assert_not_called()

def test_expenses_add_invalid_date(logged_in_app, mock_api, mock_messagebox):
    """Data in formato errato -> errore e nessuna API add."""
    app = logged_in_app
    frame = app.frames['ExpensesFrame']
    mock_api['get_categories_exp'].return_value = {'success': True, 'data': [{'id': 1, 'name': 'Food'}]}
    frame.refresh()
    frame.date_entry.delete(0, tk.END)
    frame.date_entry.insert(0, '2025/01/03')  # formato errato
    frame.amount_entry.insert(0, '10')
    frame.category_combo.set('Food')
    frame.desc_entry.insert(0, 'Spesa')
    frame.add_expense()
    args, _ = mock_messagebox['showerror'].call_args
    assert "date" in args[1].lower()
    mock_api['add_expense'].assert_not_called()

def test_expenses_add_invalid_amount(logged_in_app, mock_api, mock_messagebox):
    """Importo non positivo -> errore e nessuna API add."""
    app = logged_in_app
    frame = app.frames['ExpensesFrame']
    mock_api['get_categories_exp'].return_value = {'success': True, 'data': [{'id': 1, 'name': 'Food'}]}
    frame.refresh()
    frame.date_entry.delete(0, tk.END)
    frame.date_entry.insert(0, '2025-01-03')
    frame.amount_entry.insert(0, '-5')
    frame.category_combo.set('Food')
    frame.desc_entry.insert(0, 'Spesa')
    frame.add_expense()
    args, _ = mock_messagebox['showerror'].call_args
    assert "amount" in args[1].lower()
    mock_api['add_expense'].assert_not_called()

def test_expenses_update_existing(logged_in_app, mock_api, mock_messagebox):
    """Update su spesa selezionata -> modifica corretta con chiamata API."""
    app = logged_in_app
    frame = app.frames['ExpensesFrame']
    mock_api['get_categories_exp'].return_value = {'success': True, 'data': [{'id': 1, 'name': 'Food'}]}
    mock_api['get_expenses'].return_value = {'success': True, 'data': [
        {'id': 99, 'date': '2025-01-01', 'title': 'Pane', 'price': 2.0, 'category': 'Food', 'category_id': 1}
    ]}
    frame.refresh()
    iid = frame.table.get_children()[0]
    frame.table.selection_set(iid)
    frame.on_row_select()
    mock_api['update_expense'].return_value = {'success': True}
    frame.amount_entry.delete(0, tk.END)
    frame.amount_entry.insert(0, '3.50')
    frame.update_expense()
    mock_api['update_expense'].assert_called_with(
        expense_id=99, user_id=1, title='Pane', price=3.5,
        date='2025-01-01', category='Food', category_id=1
    )
    args, _ = mock_messagebox['showinfo'].call_args
    assert "updated" in args[1].lower()

def test_expenses_remove_without_selection(logged_in_app, mock_api, mock_messagebox):
    """Remove senza selezione -> warning."""
    app = logged_in_app
    frame = app.frames['ExpensesFrame']
    frame.remove_expense()
    args, _ = mock_messagebox['showwarning'].call_args
    assert "select" in args[1].lower()
    mock_api['delete_expense'].assert_not_called()

def test_expenses_refresh_search_term(logged_in_app, mock_api):
    """Refresh con search term -> utilizza API search_expenses e popola tabella."""
    app = logged_in_app
    frame = app.frames['ExpensesFrame']
    mock_api['get_categories_exp'].return_value = {'success': True, 'data': []}
    mock_api['search_expenses'].return_value = {'success': True, 'data': [
        {'id': 5, 'date': '2025-01-10', 'title': 'Latte', 'price': 1.2, 'category': 'Food'}
    ]}
    frame.search_entry.insert(0, 'Latte')
    frame.refresh()
    mock_api['search_expenses'].assert_called_with(query='Latte', user_id=1)
    assert len(frame.table.get_children()) == 1

def test_expenses_refresh_error(logged_in_app, mock_api, mock_messagebox):
    """Gestione errore API durante refresh -> messagebox errore, nessuna riga."""
    app = logged_in_app
    frame = app.frames['ExpensesFrame']
    mock_api['get_expenses'].return_value = {'success': False, 'error': 'DB fail'}
    frame.refresh()
    args, _ = mock_messagebox['showerror'].call_args
    assert "error" in args[0].lower()
    assert "db" in args[1].lower()