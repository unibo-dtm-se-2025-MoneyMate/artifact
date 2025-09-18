# Package marker. Evita log a import-time.
import logging
logging.getLogger(__name__).addHandler(logging.NullHandler())
# logging.getLogger("MoneyMate").debug("MoneyMate loaded")
