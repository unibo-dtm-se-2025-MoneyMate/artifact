# test/gui/test_contacts_frame.py
import pytest
from unittest.mock import MagicMock

def test_contacts_refresh_loads_data(logged_in_app, mock_api):
    """
    Test that calling 'refresh' on the ContactsFrame loads data
    from the API into the Treeview table.
    """
    # --- Arrange ---
    app = logged_in_app
    contacts_frame = app.frames['ContactsFrame']
    
    # Set mock contact data
    mock_api['get_contacts'].return_value = {
        'success': True,
        'data': [
            {'id': 1, 'name': 'Alice'},
            {'id': 2, 'name': 'Bob'}
        ]
    }
    
    # --- Act ---
    contacts_frame.refresh()
    app.update_idletasks()
    
    # --- Assert ---
    # 1. Check that the correct API was called
    mock_api['get_contacts'].assert_called_with(user_id=1, order="name_asc")
    
    # 2. Check that the table was populated
    table_items = contacts_frame.table.get_children()
    assert len(table_items) == 2
    
    # 3. Check the content of the second row
    second_row_values = contacts_frame.table.item(table_items[1])['values']
    assert second_row_values[0] == 2      # ID
    assert second_row_values[1] == 'Bob'  # Name

def test_contacts_add_contact(logged_in_app, mock_api, mock_messagebox):
    """
    Test that filling the form and clicking 'Add' calls the API
    and shows a success message.
    """
    # --- Arrange ---
    app = logged_in_app
    contacts_frame = app.frames['ContactsFrame']
    mock_api['add_contact'].return_value = {'success': True}
    
    # --- Act ---
    # Simulate filling the form
    contacts_frame.name_entry.insert(0, 'Charlie')
    
    # Simulate button click
    contacts_frame.add_contact()
    app.update_idletasks()
    
    # --- Assert ---
    # 1. Check that the add_contact API was called correctly
    mock_api['add_contact'].assert_called_with(name='Charlie', user_id=1)
    
    # 2. Check that a success message was shown
    mock_messagebox['showinfo'].assert_called_with(
        "Success", "Contact 'Charlie' added."
    )
    
    # 3. Check that refresh was called (which calls get_contacts again)
    # This assertion is now 1, because refresh() is only called *after* the add.
    assert mock_api['get_contacts'].call_count == 1

def test_contacts_remove_contact(logged_in_app, mock_api, mock_messagebox):
    """
    Test that selecting a contact and clicking 'Remove' calls the
    delete API after confirmation.
    """
    # --- Arrange ---
    app = logged_in_app
    contacts_frame = app.frames['ContactsFrame']
    
    # 1. Populate the table first
    mock_api['get_contacts'].return_value = {
        'success': True,
        'data': [{'id': 1, 'name': 'Alice'}]
    }
    contacts_frame.refresh()
    app.update_idletasks()
    
    # 2. Mock the delete API
    mock_api['delete_contact'].return_value = {'success': True, 'data': {'deleted': 1}}
    
    # 3. Mock the confirmation dialog to return 'Yes'
    mock_messagebox['askyesno'].return_value = True
    
    # --- Act ---
    # 4. Select the first item in the table
    table_item = contacts_frame.table.get_children()[0]
    contacts_frame.table.selection_set(table_item)
    
    # 5. Simulate button click
    contacts_frame.remove_contact()
    app.update_idletasks()
    
    # --- Assert ---
    # 6. Check that confirmation was requested
    mock_messagebox['askyesno'].assert_called_with(
        "Confirm Removal", "Are you sure you want to remove contact 'Alice' (ID: 1)?"
    )
    
    # 7. Check that the delete API was called
    mock_api['delete_contact'].assert_called_with(contact_id=1, user_id=1)
    
    # 8. Check that a success message was shown
    mock_messagebox['showinfo'].assert_called_with("Success", "Contact removed.")