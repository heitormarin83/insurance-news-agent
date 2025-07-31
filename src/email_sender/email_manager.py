"""
Email Manager - Versão com envio real de e-mails
"""

import os
import yaml
import smtplib
from email.message import EmailMessage
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger("email_manager")


class EmailManager:
    def __init__(self, config_path: str = "config/email_config.yaml"):
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.authenticated = False
        self.logger = logger

        self.smtp_configured = bool(
            os.getenv('GMAIL_EMAIL') and 
            os.getenv('GMAIL_APP_PASSWORD')
        )

        if self.smtp_configured:
            self.logger.info("Email Manager inicializado (SMTP configurado)")
        else:
            self.logger.warning("Email Manager inicializado (SMTP não configurado)")

    def _load_config(self) -> Dict[str, Any]:
        try:
            if not self.config_path.exists():
                logger.info(f"Arquivo de configuração não encontrado: {self.config_path}")
                return self._get_default_config()

            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)

            logger.info("Configuração de e-mail carregada")
            return config
        except Exception as e:
            logger.warning(f"Erro ao carregar configuração: {e}")
            return self._get_default_config()

    def _get_default_config(self) -> Dict[str, Any]:
        return {
            'recipients': {
                'daily_report': [],
                'alerts': [],
                'errors': []
            },
            'templates': {
                'max_top_articles': 10,
                'include_article_summaries': True,
                'include_detailed_stats': True
            },
            'sending': {
                'immediate_open_insurance_alerts': True,
                'alert_relevance_threshold': 0.7
            }
        }

    def authenticate(self) -> bool:
        if not self.smtp_configured:
            self.logger.info("SMTP não configurado - pulando autenticação")
            return False

        try:
            email = os.getenv('GMAIL_EMAIL')
            password = os.getenv('GMAIL_APP_PASSWORD')

            if email and password and '@' in email and len(password) > 10:
                self.authenticated = True
                self.logger.info("✅ Credenciais SMTP válidas")
                return True
            else:
                self.logger.warning("❌ Credenciais SMTP inválidas")
                return False
        except Exception as e:
            self.logger.error(f"❌ Erro na autenticação: {e}")
            return False

    def send_daily_report(self, report_html: str) -> bool:
        if not self.smtp_configured:
            self.logger.info("📧 E-mail não configurado - relatório salvo apenas localmente")
            return True

        try:
            recipients = self.config.get('recipients', {}).get('daily_report', [])
            if not recipients:
                self.logger.warning("Nenhum destinatário configurado")
                return True

            email = os.getenv('GMAIL_EMAIL')
            password = os.getenv('GMAIL_APP_PASSWORD')

            msg = EmailMessage()
            msg['Subject'] = '📊 Relatório Diário - Notícias de Seguros'
            msg['From'] = email
            msg['To'] = ", ".join(recipients)
            msg.set_content("Seu cliente de e-mail não suporta HTML.")
            msg.add_alternative(report_html, subtype='html')

            with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
                smtp.starttls()
                smtp.login(email, password)
                smtp.send_message(msg)

            self.logger.info(f"✅ E-mail enviado com sucesso para {len(recipients)} destinatário(s)")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar e-mail: {e}")
            return False


