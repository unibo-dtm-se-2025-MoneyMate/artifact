"""
GUI tests for ContactsFrame.

These tests cover the contacts management UI, ensuring:

- Refresh loads and displays contacts from the mocked API.
- Adding a valid contact triggers the API and shows a success message.
- Empty-name validation prevents add_contact API calls and shows an error.
- Client-side search filters the table by substring (case-insensitive).
- Removing a selected contact with confirmation calls the delete API.
- Removing without a selection results in a warning, no delete API call.
"""

import pytest
from unittest.mock import MagicMock

def test_contacts_refresh_loads_data(logged_in_app, mock_api):
    """Refresh popola tabella con lista contatti."""
    # --- Arrange ---
    app = logged_in_app
    frame = app.frames['ContactsFrame']
    mock_api['get_contacts'].return_value = {
        'success': True,
        'data': [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}]
    }
    # --- Act ---
    frame.refresh()
    app.update_idletasks()
    # --- Assert ---
    mock_api['get_contacts'].assert_called_with(user_id=1, order="name_asc")
    assert len(frame.table.get_children()) == 2

def test_contacts_add_contact(logged_in_app, mock_api, mock_messagebox):
    """Aggiunta contatto valida -> success e refresh."""
    app = logged_in_app
    frame = app.frames['ContactsFrame']
    mock_api['add_contact'].return_value = {'success': True}
    frame.name_entry.insert(0, 'Charlie')
    frame.add_contact()
    mock_api['add_contact'].assert_called_with(name='Charlie', user_id=1)
    args, _ = mock_messagebox['showinfo'].call_args
    assert "charlie" in args[1].lower()
    assert mock_api['get_contacts'].call_count == 1

def test_contacts_add_contact_empty_name(logged_in_app, mock_api, mock_messagebox):
    """Validazione nome vuoto -> errore e nessuna chiamata add_contact."""
    app = logged_in_app
    frame = app.frames['ContactsFrame']
    frame.add_contact()
    args, _ = mock_messagebox['showerror'].call_args
    assert "name" in args[1].lower()
    mock_api['add_contact'].assert_not_called()

def test_contacts_filter_search(logged_in_app, mock_api):
    """Filtro search per substring nel nome (case-insensitive)."""
    app = logged_in_app
    frame = app.frames['ContactsFrame']
    mock_api['get_contacts'].return_value = {
        'success': True,
        'data': [{'id': 1, 'name': 'Alice'}, {'id': 2, 'name': 'Bob'}, {'id': 3, 'name': 'Carlo'}]
    }
    frame.search_entry.insert(0, 'bo')
    frame.refresh()
    items = frame.table.get_children()
    assert len(items) == 1
    vals = frame.table.item(items[0])['values']
    assert vals[1].lower() == 'bob'

def test_contacts_remove_contact(logged_in_app, mock_api, mock_messagebox):
    """Rimozione contatto con selezione e conferma -> success."""
    app = logged_in_app
    frame = app.frames['ContactsFrame']
    mock_api['get_contacts'].return_value = {'success': True, 'data': [{'id': 10, 'name': 'Test'}]}
    frame.refresh()
    mock_api['delete_contact'].return_value = {'success': True, 'data': {'deleted': 1}}
    mock_messagebox['askyesno'].return_value = True
    iid = frame.table.get_children()[0]
    frame.table.selection_set(iid)
    frame.remove_contact()
    mock_api['delete_contact'].assert_called_with(contact_id=10, user_id=1)
    args, _ = mock_messagebox['showinfo'].call_args
    assert "removed" in args[1].lower()

def test_contacts_remove_without_selection(logged_in_app, mock_api, mock_messagebox):
    """Rimozione senza selezione -> warning, nessuna API di delete."""
    app = logged_in_app
    frame = app.frames['ContactsFrame']
    mock_api['get_contacts'].return_value = {'success': True, 'data': []}
    frame.refresh()
    frame.remove_contact()
    args, _ = mock_messagebox['showwarning'].call_args
    assert "select" in args[1].lower()
    mock_api['delete_contact'].assert_not_called()