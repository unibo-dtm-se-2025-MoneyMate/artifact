import sqlite3
from typing import Dict, Any, Optional
from datetime import datetime

DB_PATH = "moneymate.db"

def dict_response(success: bool, error: Optional[str] = None, data: Any = None) -> Dict[str, Any]:
    """to enable a standardized response format for all API calls."""
    return {"success": success, "error": error, "data": data}