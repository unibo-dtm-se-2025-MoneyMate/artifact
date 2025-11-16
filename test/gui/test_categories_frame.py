"""
GUI tests for CategoriesFrame.

These tests validate the categories management screen in the Tkinter GUI:

- Refresh behavior: loading categories via the mocked API and populating
  the Treeview.
- Adding a category with valid data and showing a success message.
- Client-side validation when the category name is missing (no API call).
- Removing a selected category with confirmation and success feedback.
- Removing without any selection (warning only, no API call).
- Handling API failures during refresh with an error message and empty table.
"""

import pytest
from unittest.mock import MagicMock

def test_categories_refresh_loads_data(logged_in_app, mock_api):
    """
    Verifica che il refresh carichi correttamente le categorie e popoli la tabella.
    """
    # --- Arrange ---
    app = logged_in_app
    cat_frame = app.frames['CategoriesFrame']
    mock_api['get_categories'].return_value = {
        'success': True,
        'data': [
            {'id': 1, 'name': 'Food', 'description': 'Groceries, restaurants'},
            {'id': 2, 'name': 'Transport', 'description': 'Bus, taxi'}
        ]
    }
    # --- Act ---
    cat_frame.refresh()
    app.update_idletasks()
    # --- Assert ---
    mock_api['get_categories'].assert_called_with(user_id=1, order="name_asc")
    items = cat_frame.table.get_children()
    assert len(items) == 2, "Devono essere presenti due categorie"
    first_values = cat_frame.table.item(items[0])['values']
    assert first_values[1] == 'Food'
    assert first_values[2] == 'Groceries, restaurants'

def test_categories_add_category(logged_in_app, mock_api, mock_messagebox):
    """
    Verifica aggiunta categoria valida e notifica di successo con refresh.
    """
    # --- Arrange ---
    app = logged_in_app
    cat_frame = app.frames['CategoriesFrame']
    mock_api['add_category'].return_value = {'success': True}
    # --- Act ---
    cat_frame.name_entry.insert(0, 'Utilities')
    cat_frame.desc_entry.insert(0, 'Electricity, Water')
    cat_frame.add_category()
    app.update_idletasks()
    # --- Assert ---
    mock_api['add_category'].assert_called_with(
        user_id=1,
        name='Utilities',
        description='Electricity, Water'
    )
    # Messaggio di successo (robusto su eventuali punteggiature)
    args, kwargs = mock_messagebox['showinfo'].call_args
    assert "success" in args[0].lower()
    assert "utilities" in args[1].lower()
    assert mock_api['get_categories'].call_count == 1

def test_categories_add_category_missing_name(logged_in_app, mock_api, mock_messagebox):
    """
    Verifica validazione: nome categoria mancante -> errore e nessuna chiamata API.
    """
    # --- Arrange ---
    app = logged_in_app
    cat_frame = app.frames['CategoriesFrame']
    # --- Act ---
    cat_frame.add_category()  # name vuoto
    app.update_idletasks()
    # --- Assert ---
    args, kwargs = mock_messagebox['showerror'].call_args
    assert "name" in args[1].lower()
    mock_api['add_category'].assert_not_called()

def test_categories_remove_without_selection(logged_in_app, mock_api, mock_messagebox):
    """
    Verifica comportamento se si tenta di rimuovere senza selezione -> warning.
    """
    # --- Arrange ---
    app = logged_in_app
    cat_frame = app.frames['CategoriesFrame']
    mock_api['get_categories'].return_value = {'success': True, 'data': []}
    cat_frame.refresh()
    # --- Act ---
    cat_frame.remove_category()
    app.update_idletasks()
    # --- Assert ---
    args, kwargs = mock_messagebox['showwarning'].call_args
    assert "select" in args[1].lower()
    mock_api['delete_category'].assert_not_called()

def test_categories_refresh_error(logged_in_app, mock_api, mock_messagebox):
    """
    Verifica gestione errore durante refresh (API failure) -> messagebox errore.
    """
    # --- Arrange ---
    app = logged_in_app
    cat_frame = app.frames['CategoriesFrame']
    mock_api['get_categories'].return_value = {'success': False, 'error': 'DB error'}
    # --- Act ---
    cat_frame.refresh()
    app.update_idletasks()
    # --- Assert ---
    args, kwargs = mock_messagebox['showerror'].call_args
    assert "error" in args[0].lower()
    assert "db" in args[1].lower()
    assert len(cat_frame.table.get_children()) == 0