"""
Email Sender Package
VERSÃO CORRIGIDA - Remove importação do gmail_sender que não existe
"""

from .email_manager import EmailManager
from .email_template import EmailTemplate

# Remove a importação problemática do gmail_sender
# from .gmail_sender import GmailSender  # ← REMOVIDO

__all__ = [
    'EmailManager',
    'EmailTemplate'
]
