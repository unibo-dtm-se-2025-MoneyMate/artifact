# test/gui/test_login_frame.py
import pytest
from unittest.mock import MagicMock

def test_login_success(app, mock_api, mocker):
    """
    Test that a successful login calls the API, updates the app state,
    and calls the controller's on_login_success method.
    """
    # --- Arrange ---
    # 1. Mock the app's 'on_login_success' to check if it gets called
    app.on_login_success = MagicMock()
    
    # 2. Set the return value for the mocked login API
    mock_api['login'].return_value = {
        'success': True,
        'data': {'user_id': 123, 'role': 'user'}
    }
    
    # 3. Get the login frame
    login_frame = app.frames['LoginFrame']
    
    # --- Act ---
    # 4. Simulate user typing into the entry fields
    login_frame.login_user_entry.insert(0, 'testuser')
    login_frame.login_pass_entry.insert(0, 'password123')
    
    # --- ADD THIS LINE ---
    app.update_idletasks() # Force tkinter to process the widget .insert() events
    
    # 5. Simulate the user clicking the login button
    login_frame.attempt_login()
    
    # --- Assert ---
    # 6. Check that the API was called with the correct credentials
    mock_api['login'].assert_called_with('testuser', 'password123')
    
    # 7. Check that the app's on_login_success method was called
    app.on_login_success.assert_called_with(123, 'testuser')

def test_login_failure(app, mock_api, mock_messagebox):
    """
    Test that a failed login calls the API, shows an error message,
    and does NOT update the app state.
    """
    # --- Arrange ---
    # 1. Mock the app's 'on_login_success' to ensure it's NOT called
    app.on_login_success = MagicMock()
    
    # 2. Set the return value for a failed login
    mock_api['login'].return_value = {
        'success': False,
        'error': 'Invalid credentials'
    }
    
    # 3. Get the login frame
    login_frame = app.frames['LoginFrame']
    
    # --- Act ---
    # 4. Simulate user typing
    login_frame.login_user_entry.insert(0, 'testuser')
    login_frame.login_pass_entry.insert(0, 'wrongpass')
    
    # --- ADD THIS LINE ---
    app.update_idletasks() # Force tkinter to process the widget .insert() events
    
    # 5. Simulate button click
    login_frame.attempt_login()
    
    # --- Assert ---
    # 6. Check that the API was called
    mock_api['login'].assert_called_with('testuser', 'wrongpass')
    
    # 7. Check that the app state was NOT changed
    assert app.user_id is None
    app.on_login_success.assert_not_called()
    
    # 8. Check that an error message was shown
    mock_messagebox['showerror'].assert_called_with(
        'Login Error', 'Invalid credentials'
    )