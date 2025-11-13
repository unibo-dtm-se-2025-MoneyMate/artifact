import pytest
from unittest.mock import MagicMock

# Copertura login/registrazione:
# - Login successo
# - Login fallito (credenziali errate)
# - Login campi mancanti
# - Registrazione success
# - Registrazione password troppo corta
# - Registrazione errore API
#
# Notazione messaggi: substring case-insensitive.

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
    # Messaggio errore robusto
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

def test_registration_success(app, mock_api, mock_messagebox):
    """Registrazione utente valida -> success message e pulizia form."""
    frame = app.frames['LoginFrame']
    mock_api['register'].return_value = {'success': True}
    frame.reg_user_entry.insert(0, 'newuser')
    frame.reg_pass_entry.insert(0, 'abcdef')
    frame.attempt_registration()
    mock_api['register'].assert_called_with('newuser', 'abcdef')
    args, _ = mock_messagebox['showinfo'].call_args
    assert "registered" in args[1].lower()

def test_registration_password_short(app, mock_api, mock_messagebox):
    """Password troppo corta -> errore e nessuna chiamata API."""
    frame = app.frames['LoginFrame']
    frame.reg_user_entry.insert(0, 'usr')
    frame.reg_pass_entry.insert(0, '123')
    frame.attempt_registration()
    args, _ = mock_messagebox['showerror'].call_args
    assert "password" in args[1].lower()
    assert "6" in args[1]  # riferimento lunghezza minima
    mock_api['register'].assert_not_called()

def test_registration_error_api(app, mock_api, mock_messagebox):
    """Errore lato API registrazione (es. user già esistente)."""
    frame = app.frames['LoginFrame']
    mock_api['register'].return_value = {'success': False, 'error': 'User exists'}
    frame.reg_user_entry.insert(0, 'dup')
    frame.reg_pass_entry.insert(0, '123456')
    frame.attempt_registration()
    mock_api['register'].assert_called_with('dup', '123456')
    args, _ = mock_messagebox['showerror'].call_args
    assert "registration" in args[0].lower()
    assert "exists" in args[1].lower()