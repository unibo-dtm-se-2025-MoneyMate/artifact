import logging

# Best practice: non configurare handler globali a import-time.
# Aggiungi un NullHandler al logger di package per evitare "No handler found".
logging.getLogger("MoneyMate").addHandler(logging.NullHandler())