"""
GUI tests for LoginFrame.

These tests cover the login screen behavior:

- Successful login: calls api_login_user and triggers the controller's
  on_login_success callback with the returned user_id.
- Failed login: shows an error message and leaves app.user_id unchanged.
- Missing username/password: client-side validation prevents API calls and
  shows a descriptive error.
"""

import pytest
from unittest.mock import MagicMock

def test_login_success(app, mock_api):
    """Login con credenziali corrette -> callback on_login_success chiamata."""
    app.on_login_success = MagicMock()
    mock_api['login'].return_value = {'success': True, 'data': {'user_id': 123, 'role': 'user'}}
    frame = app.frames['LoginFrame']
    frame.login_user_entry.insert(0, 'testuser')
    frame.login_pass_entry.insert(0, 'password123')
    app.update_idletasks()
    frame.attempt_login()
    mock_api['login'].assert_called_with('testuser', 'password123')
    app.on_login_success.assert_called_with(123, 'testuser')

def test_login_failure(app, mock_api, mock_messagebox):
    """Login con password errata -> errore e user_id invariato."""
    app.on_login_success = MagicMock()
    mock_api['login'].return_value = {'success': False, 'error': 'Invalid credentials'}
    frame = app.frames['LoginFrame']
    frame.login_user_entry.insert(0, 'testuser')
    frame.login_pass_entry.insert(0, 'wrongpass')
    frame.attempt_login()
    mock_api['login'].assert_called_with('testuser', 'wrongpass')
    args, _ = mock_messagebox['showerror'].call_args
    assert "login" in args[0].lower()
    assert "invalid" in args[1].lower()
    assert app.user_id is None

def test_login_missing_fields(app, mock_api, mock_messagebox):
    """Login con campi vuoti -> validazione lato GUI."""
    frame = app.frames['LoginFrame']
    frame.attempt_login()
    args, _ = mock_messagebox['showerror'].call_args
    assert "username" in args[1].lower()
    mock_api['login'].assert_not_called()