"""
Low-level authentication and session management utilities.

This module implements a standalone auth subsystem for SQLite-backed apps,
including:

- User account schema (users, sessions, login_attempts) and initializer.
- Secure password hashing and verification using PBKDF2 (configurable via env).
- Session token generation and verification (only hashes stored in DB).
- Login attempt auditing with lockout after repeated failures.
- Basic account operations such as registration, logout, and password change.

It does not depend on the higher-level MoneyMate manager classes and can be
used as an independent authentication layer for SQLite databases.
"""

import os
import sqlite3
import time
import secrets
import hmac
import hashlib
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

import logging

logger = logging.getLogger("MoneyMate")
if not logging.getLogger().handlers:
    logging.basicConfig(level=logging.INFO)

# Configurazione da ENV (override in produzione)
PASSWORD_MIN_LEN = int(os.getenv("MONEYMATE_PASSWORD_MIN_LEN", "10"))
PWD_PEPPER = os.getenv("MONEYMATE_PWD_PEPPER", "")  # opzionale, non salvare mai in DB
PBKDF2_ITERATIONS = int(os.getenv("MONEYMATE_PBKDF2_ITERS", "310000"))

SESSION_TTL_MIN = int(os.getenv("MONEYMATE_SESSION_TTL_MIN", "120"))  # 2h
MAX_FAILED_ATTEMPTS = int(os.getenv("MONEYMATE_MAX_FAILED_ATTEMPTS", "5"))
LOCKOUT_SECONDS = int(os.getenv("MONEYMATE_LOCKOUT_SECONDS", "900"))  # 15 min

# Formato password (simile a Django):
# pbkdf2_sha256$<iterations>$<salt-hex>$<hash-hex>


@dataclass
class AuthResult:
    ok: bool
    user_id: Optional[int] = None
    token: Optional[str] = None
    reason: Optional[str] = None


def _now_utc() -> datetime:
    return datetime.now(timezone.utc)


def _epoch() -> int:
    return int(time.time())


def init_auth_schema(conn: sqlite3.Connection) -> None:
    """
    Crea, se mancante, le tabelle users, sessions e login_attempts.
    """
    cur = conn.cursor()
    cur.execute("""
    CREATE TABLE IF NOT EXISTS users (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        email TEXT UNIQUE NOT NULL,
        password_hash TEXT NOT NULL,
        is_active INTEGER NOT NULL DEFAULT 1,
        failed_attempts INTEGER NOT NULL DEFAULT 0,
        locked_until INTEGER,  -- epoch seconds UTC
        created_at TEXT NOT NULL,
        updated_at TEXT NOT NULL
    )
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS sessions (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER NOT NULL,
        token_sha256 TEXT NOT NULL,      -- hash del token (non il token in chiaro)
        expires_at INTEGER NOT NULL,     -- epoch seconds UTC
        created_at TEXT NOT NULL,
        FOREIGN KEY (user_id) REFERENCES users(id) ON DELETE CASCADE
    )
    """)
    cur.execute("""
    CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_token ON sessions(token_sha256)
    """)
    cur.execute("""
    CREATE TABLE IF NOT EXISTS login_attempts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_ref TEXT,        -- username o email tentata
        success INTEGER NOT NULL,
        reason TEXT,
        ts INTEGER NOT NULL   -- epoch seconds UTC
    )
    """)
    conn.commit()


def _password_ok(password: str) -> Tuple[bool, Optional[str]]:
    if len(password) < PASSWORD_MIN_LEN:
        return False, f"Password troppo corta: minimo {PASSWORD_MIN_LEN} caratteri"
    # Puoi aggiungere altri vincoli qui (maiuscole, numeri, simboli, ecc.)
    return True, None


def _pbkdf2(password: str, salt: bytes, iterations: int) -> bytes:
    to_hash = (password + PWD_PEPPER).encode("utf-8")
    return hashlib.pbkdf2_hmac("sha256", to_hash, salt, iterations)


def _make_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    dk = _pbkdf2(password, salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${salt.hex()}${dk.hex()}"


def _check_password(password: str, encoded: str) -> bool:
    try:
        algo, iters_s, salt_hex, hash_hex = encoded.split("$", 3)
        if algo != "pbkdf2_sha256":
            return False
        iterations = int(iters_s)
        salt = bytes.fromhex(salt_hex)
        expected = bytes.fromhex(hash_hex)
        dk = _pbkdf2(password, salt, iterations)
        return hmac.compare_digest(dk, expected)
    except Exception:
        return False


def _hash_token_for_storage(token: str) -> str:
    # Memorizziamo solo l'hash (hex) del token di sessione
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _get_user_by_ref(conn: sqlite3.Connection, user_ref: str) -> Optional[sqlite3.Row]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE username = ? OR email = ?", (user_ref, user_ref))
    return cur.fetchone()


def _audit_attempt(conn: sqlite3.Connection, user_ref: str, success: bool, reason: Optional[str]):
    cur = conn.cursor()
    cur.execute("""
        INSERT INTO login_attempts (user_ref, success, reason, ts) VALUES (?, ?, ?, ?)
    """, (user_ref, 1 if success else 0, reason, _epoch()))
    conn.commit()


def register_user(conn: sqlite3.Connection, username: str, email: str, password: str) -> Tuple[bool, Optional[int], Optional[str]]:
    ok, reason = _password_ok(password)
    if not ok:
        return False, None, reason

    cur = conn.cursor()
    cur.execute("SELECT 1 FROM users WHERE username = ? OR email = ?", (username, email))
    if cur.fetchone():
        return False, None, "Username o email già in uso"

    pwd_hash = _make_password(password)
    ts = _now_utc().isoformat()
    try:
        cur.execute("""
            INSERT INTO users (username, email, password_hash, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?)
        """, (username, email, pwd_hash, ts, ts))
        conn.commit()
        user_id = cur.lastrowid
        logger.info("Creato utente id=%s username=%s", user_id, username)
        return True, user_id, None
    except sqlite3.IntegrityError:
        return False, None, "Violazione di integrità (duplicato?)"


def authenticate(conn: sqlite3.Connection, user_ref: str, password: str) -> AuthResult:
    user = _get_user_by_ref(conn, user_ref)
    if not user:
        _audit_attempt(conn, user_ref, False, "Utente inesistente")
        return AuthResult(False, reason="Credenziali errate")

    if not user["is_active"]:
        _audit_attempt(conn, user_ref, False, "Utente disattivato")
        return AuthResult(False, reason="Utente disattivato")

    now_epoch = _epoch()
    if user["locked_until"] and now_epoch < int(user["locked_until"]):
        seconds = int(user["locked_until"]) - now_epoch
        _audit_attempt(conn, user_ref, False, f"Account lock per {seconds}s")
        return AuthResult(False, reason=f"Account bloccato. Riprova tra {seconds} secondi")

    if not _check_password(password, user["password_hash"]):
        failed = int(user["failed_attempts"]) + 1
        locked_until = None
        if failed >= MAX_FAILED_ATTEMPTS:
            locked_until = now_epoch + LOCKOUT_SECONDS
            logger.warning("Lock account username=%s per %ss (tentativi=%s)", user["username"], LOCKOUT_SECONDS, failed)

        cur = conn.cursor()
        cur.execute("""
            UPDATE users SET failed_attempts = ?, locked_until = ?, updated_at = ?
            WHERE id = ?
        """, (failed, locked_until, _now_utc().isoformat(), user["id"]))
        conn.commit()
        _audit_attempt(conn, user_ref, False, "Password errata")
        return AuthResult(False, reason="Credenziali errate")

    # Successo: reset tentativi e crea sessione
    cur = conn.cursor()
    cur.execute("""
        UPDATE users SET failed_attempts = 0, locked_until = NULL, updated_at = ?
        WHERE id = ?
    """, (_now_utc().isoformat(), user["id"]))
    conn.commit()

    # Genera token di sessione
    token = secrets.token_urlsafe(32)
    token_sha = _hash_token_for_storage(token)
    expires_at = now_epoch + (SESSION_TTL_MIN * 60)
    cur.execute("""
        INSERT INTO sessions (user_id, token_sha256, expires_at, created_at)
        VALUES (?, ?, ?, ?)
    """, (int(user["id"]), token_sha, expires_at, _now_utc().isoformat()))
    conn.commit()

    _audit_attempt(conn, user_ref, True, None)
    return AuthResult(True, user_id=int(user["id"]), token=token)


def verify_session(conn: sqlite3.Connection, token: str) -> Tuple[bool, Optional[sqlite3.Row], Optional[str]]:
    if not token:
        return False, None, "Token mancante"
    token_sha = _hash_token_for_storage(token)
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("""
        SELECT s.user_id, s.expires_at, u.username, u.email, u.is_active
        FROM sessions s
        JOIN users u ON u.id = s.user_id
        WHERE s.token_sha256 = ?
    """, (token_sha,))
    row = cur.fetchone()
    if not row:
        return False, None, "Sessione non trovata"

    if _epoch() >= int(row["expires_at"]):
        # sessione scaduta → delete best effort
        try:
            cur.execute("DELETE FROM sessions WHERE token_sha256 = ?", (token_sha,))
            conn.commit()
        except Exception:
            pass
        return False, None, "Sessione scaduta"

    if not int(row["is_active"]):
        return False, None, "Utente disattivato"

    return True, row, None


def logout(conn: sqlite3.Connection, token: str) -> None:
    if not token:
        return
    token_sha = _hash_token_for_storage(token)
    cur = conn.cursor()
    cur.execute("DELETE FROM sessions WHERE token_sha256 = ?", (token_sha,))
    conn.commit()


def change_password(conn: sqlite3.Connection, user_id: int, old_password: str, new_password: str) -> Tuple[bool, Optional[str]]:
    conn.row_factory = sqlite3.Row
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user = cur.fetchone()
    if not user:
        return False, "Utente non trovato"

    if not _check_password(old_password, user["password_hash"]):
        return False, "Vecchia password errata"

    ok, reason = _password_ok(new_password)
    if not ok:
        return False, reason

    new_hash = _make_password(new_password)
    cur.execute("""
        UPDATE users SET password_hash = ?, updated_at = ?
        WHERE id = ?
    """, (new_hash, _now_utc().isoformat(), user_id))
    conn.commit()
    return True, None


def deactivate_user(conn: sqlite3.Connection, user_id: int) -> None:
    cur = conn.cursor()
    cur.execute("UPDATE users SET is_active = 0, updated_at = ? WHERE id = ?", (_now_utc().isoformat(), user_id))
    conn.commit()