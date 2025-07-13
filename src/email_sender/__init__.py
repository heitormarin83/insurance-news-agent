"""
Módulo de envio de e-mails para o sistema de notícias de seguros
"""

from .gmail_sender import GmailSender
from .email_template import EmailTemplate

__all__ = ['GmailSender', 'EmailTemplate']

