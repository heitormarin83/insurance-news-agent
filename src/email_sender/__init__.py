"""
Pacote de envio de e-mails do Insurance News Agent
Expondo as interfaces públicas: EmailManager e EmailTemplate
"""

from .email_manager import EmailManager
from .email_template import EmailTemplate

__all__ = [
    'EmailManager',
    'EmailTemplate'
]
