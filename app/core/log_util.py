import logging


def log_exception():
    """Loga exceções com traceback completo para depuração."""
    logging.exception("Ocorreu uma exceção não tratada")
