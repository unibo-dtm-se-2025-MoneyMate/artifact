# test/gui/test_categories_frame.py
import pytest
from unittest.mock import MagicMock

def test_categories_refresh_loads_data(logged_in_app, mock_api):
    """
    Test that calling 'refresh' on the CategoriesFrame loads data
    from the API into the Treeview table.
    """
    # --- Arrange ---
    app = logged_in_app
    cat_frame = app.frames['CategoriesFrame']
    
    # Set mock category data
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
    # 1. Check that the correct API was called
    mock_api['get_categories'].assert_called_with(user_id=1, order="name_asc")
    
    # 2. Check that the table was populated
    table_items = cat_frame.table.get_children()
    assert len(table_items) == 2
    
    # 3. Check the content of the first row
    first_row_values = cat_frame.table.item(table_items[0])['values']
    assert first_row_values[0] == 1
    assert first_row_values[1] == 'Food'
    assert first_row_values[2] == 'Groceries, restaurants'

def test_categories_add_category(logged_in_app, mock_api, mock_messagebox):
    """
    Test that filling the form and clicking 'Add' calls the API
    and shows a success message.
    """
    # --- Arrange ---
    app = logged_in_app
    cat_frame = app.frames['CategoriesFrame']
    mock_api['add_category'].return_value = {'success': True}
    
    # --- Act ---
    # Simulate filling the form
    cat_frame.name_entry.insert(0, 'Utilities')
    cat_frame.desc_entry.insert(0, 'Electricity, Water')
    
    # Simulate button click
    cat_frame.add_category()
    app.update_idletasks()
    
    # --- Assert ---
    # 1. Check that the add_category API was called correctly
    mock_api['add_category'].assert_called_with(
        user_id=1,
        name='Utilities',
        description='Electricity, Water'
    )
    
    # 2. Check that a success message was shown
    mock_messagebox['showinfo'].assert_called_with(
        "Success", "Category 'Utilities' added."
    )
    
    # 3. Check that refresh was called (which calls get_categories again)
    # FIX: The refresh is called *after* the add, so the *first* call
    # is the one triggered by the add.
    assert mock_api['get_categories'].call_count == 1

def test_categories_remove_category(logged_in_app, mock_api, mock_messagebox):
    """
    Test that selecting a category and clicking 'Remove' calls the
    delete API after confirmation.
    """
    # --- Arrange ---
    app = logged_in_app
    cat_frame = app.frames['CategoriesFrame']
    
    # 1. Populate the table
    mock_api['get_categories'].return_value = {
        'success': True,
        'data': [{'id': 1, 'name': 'Food', 'description': 'Groceries'}]
    }
    cat_frame.refresh()
    app.update_idletasks()
    
    # 2. Mock the delete API
    mock_api['delete_category'].return_value = {'success': True, 'data': {'deleted': 1}}
    
    # 3. Mock the confirmation dialog
    mock_messagebox['askyesno'].return_value = True
    
    # --- Act ---
    # 4. Select the first item
    table_item = cat_frame.table.get_children()[0]
    cat_frame.table.selection_set(table_item)
    
    # 5. Simulate button click
    cat_frame.remove_category()
    app.update_idletasks()
    
    # --- Assert ---
    # 6. Check confirmation
    mock_messagebox['askyesno'].assert_called_with(
        "Confirm Removal", 
        "Are you sure you want to remove category 'Food' (ID: 1)?\n\n(This will not affect existing expenses.)"
    )
    
    # 7. Check that delete API was called
    mock_api['delete_category'].assert_called_with(category_id=1, user_id=1)
    
    # 8. Check success message
    mock_messagebox['showinfo'].assert_called_with("Success", "Category removed.")