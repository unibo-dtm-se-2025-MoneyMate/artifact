import logging
from MoneyMate.data_layer.manager import DatabaseManager, dict_response

# Evita "No handler found" se l'app non configura logging
logging.getLogger("MoneyMate").addHandler(logging.NullHandler())

__all__ = ["DatabaseManager", "dict_response"]