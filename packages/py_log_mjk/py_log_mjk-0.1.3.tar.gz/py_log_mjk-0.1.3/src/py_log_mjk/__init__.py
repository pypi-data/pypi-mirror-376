# src/py_log_mjk/__init__.py

"""
Py Log MJK: Um pacote completo para logging profissional em Python.
"""
# Expõe a função principal diretamente no pacote.
# Assim, o usuário pode fazer 'from py_log_mjk import get_logger'
# em vez de 'from py_log_mjk.config_logging import get_logger'.
from py_log_mjk.setup import get_logger

__version__ = "0.1.0" # Versão inicial da sua biblioteca