"""
Email Manager - Gerencia o envio de e-mails
VERSÃO FINAL - Correção de path absoluto para Railway
"""

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formataddr
import yaml
from pathlib import Path
from datetime import datetime
from typing import List
import os

from .email_template import EmailTemplate
from src.utils.logger import get_logger

logger = get_logger("email_manager")


class EmailManager:
    def __init__(self):
        self.config = self._load_config()
        self.sender_name = self.config.get('gmail', {}).get('sender_name', 'Insurance News Agent')
        self.recipients = self.config.get('recipients', {})
        self.smtp_server = 'smtp.gmail.com'
        self.smtp_port = 587
        self.smtp_user = None
        self.smtp_password = None
        self._authenticated = False

    def _load_config(self) -> dict:
        base_dir = Path(os.getcwd())
        config_path = base_dir / "config" / "email_config.yaml"

        logger.info(f"🔠 Caminho absoluto final do config: {config_path.resolve()}")

        if not config_path.exists():
            logger.error(f"❌ Arquivo de configuração não encontrado: {config_path}")
            return {}

        with open(config_path, 'r', encoding='utf-8') as f:
            config = yaml.safe_load(f)

        logger.info("🔠 Configuração de e-mail carregada")
        logger.info(f"🔠 Conteúdo carregado da configuração: {config}")
        return config

    def authenticate(self) -> bool:
        if self._authenticated:
            return True

        self.smtp_user = "seu_email@gmail.com"
        self.smtp_password = "sua_senha_de_aplicativo"

        if self.smtp_user and self.smtp_password:
            self._authenticated = True
            return True
        return False

    def validate_configuration(self) -> dict:
        issues = []

        logger.info(f"🔠 SELF.recipients atual: {self.recipients}")
        logger.info(f"🔠 SELF.recipients[daily_report]: {self.recipients.get('daily_report')}")

        if not self.recipients.get('daily_report'):
            issues.append("Nenhum destinatário configurado para relatório diário")

        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'recipients_count': len(self.recipients.get('daily_report', []))
        }

    def send_daily_report(self, report) -> bool:
        try:
            subject = f"📈 Insurance News Report - {report.date.strftime('%d/%m/%Y')}"
            html_content = EmailTemplate.build_daily_report(report)

            return self._send_email(
                recipients=self.recipients.get('daily_report', []),
                subject=subject,
                html=html_content
            )
        except Exception as e:
            logger.error(f"Erro ao enviar relatório diário: {e}")
            return False

    def send_open_insurance_alert(self, articles: List) -> bool:
        try:
            subject = f"🚨 Alerta: Novidades Open Insurance - {datetime.now().strftime('%d/%m/%Y')}"
            html_content = EmailTemplate.build_open_insurance_alert(articles)

            return self._send_email(
                recipients=self.recipients.get('alerts', []),
                subject=subject,
                html=html_content
            )
        except Exception as e:
            logger.error(f"Erro ao enviar alerta Open Insurance: {e}")
            return False

    def send_error_notification(self, error_info: dict) -> bool:
        try:
            subject = "❌ Erro no Insurance News Agent"
            html = f"<h2>Erro detectado</h2><p>{error_info.get('error')}</p><pre>{error_info.get('details')}</pre>"

            return self._send_email(
                recipients=self.recipients.get('errors', []),
                subject=subject,
                html=html
            )
        except Exception as e:
            logger.error(f"Erro ao enviar notificação de erro: {e}")
            return False

    def send_test_email(self, email: str) -> bool:
        try:
            subject = "✅ Teste de envio de e-mail"
            html = "<p>Este é um e-mail de teste do Insurance News Agent</p>"
            return self._send_email(
                recipients=[email],
                subject=subject,
                html=html
            )
        except Exception as e:
            logger.error(f"Erro ao enviar e-mail de teste: {e}")
            return False

    def _send_email(self, recipients: List[str], subject: str, html: str) -> bool:
        try:
            msg = MIMEMultipart()
            msg['From'] = formataddr((self.sender_name, self.smtp_user))
            msg['To'] = ', '.join(recipients)
            msg['Subject'] = subject

            msg.attach(MIMEText(html, 'html'))

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_user, self.smtp_password)
                server.sendmail(self.smtp_user, recipients, msg.as_string())

            logger.info(f"E-mail enviado para: {recipients}")
            return True
        except Exception as e:
            logger.error(f"Falha ao enviar e-mail: {e}")
            return False
