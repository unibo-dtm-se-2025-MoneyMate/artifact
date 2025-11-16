"""
GUI tests for RegisterFrame.

This module validates the registration screen behavior:

- Successful registration: calls api_register_user, shows a success message,
  and clears the password field.
- Too-short password: client-side validation prevents API calls and shows
  a length-related error.
- API error (e.g., duplicate user): propagates an error message via messagebox.
"""

import pytest

def test_registration_success(app, mock_api, mock_messagebox):
    """Registrazione utente valida -> success message e pulizia form."""
    frame = app.frames['RegisterFrame']
    mock_api['register'].return_value = {'success': True}
    frame.reg_user_entry.insert(0, 'newuser')
    frame.reg_pass_entry.insert(0, 'abcdef')
    frame.attempt_registration()
    mock_api['register'].assert_called_with('newuser', 'abcdef')
    args, _ = mock_messagebox['showinfo'].call_args
    assert "registered" in args[1].lower()
    # password field cleared
    assert frame.reg_pass_entry.get() == ""

def test_registration_password_short(app, mock_api, mock_messagebox):
    """Password troppo corta -> errore e nessuna chiamata API."""
    frame = app.frames['RegisterFrame']
    frame.reg_user_entry.insert(0, 'usr')
    frame.reg_pass_entry.insert(0, '123')
    frame.attempt_registration()
    args, _ = mock_messagebox['showerror'].call_args
    assert "password" in args[1].lower()
    assert "6" in args[1]  # riferimento lunghezza minima
    mock_api['register'].assert_not_called()

def test_registration_error_api(app, mock_api, mock_messagebox):
    """Errore lato API registrazione (es. user già esistente)."""
    frame = app.frames['RegisterFrame']
    mock_api['register'].return_value = {'success': False, 'error': 'User exists'}
    frame.reg_user_entry.insert(0, 'dup')
    frame.reg_pass_entry.insert(0, '123456')
    frame.attempt_registration()
    mock_api['register'].assert_called_with('dup', '123456')
    args, _ = mock_messagebox['showerror'].call_args
    assert "registration" in args[0].lower()
    assert "exists" in args[1].lower()