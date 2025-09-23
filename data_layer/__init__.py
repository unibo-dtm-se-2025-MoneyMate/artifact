"""
Compatibility shim: expose DatabaseManager at top-level 'data_layer' for tests.

The implementation lives under MoneyMate.data_layer.manager.
"""
from MoneyMate.data_layer.manager import DatabaseManager

__all__ = ["DatabaseManager"]