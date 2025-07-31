
"""
Email Manager com yagmail para envio real de e-mails
"""

import os
import yaml
import yagmail
from typing import List, Dict, Any
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

        # Verifica se as credenciais de e-mail estão configuradas
        self.smtp_configured = bool(
            os.getenv('EMAIL_USER') and 
            os.getenv('EMAIL_APP_PASSWORD')
        )

        if self.smtp_configured:
            self.logger.info("Email Manager inicializado (yagmail configurado)")
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

    def send_daily_report(self, report_html: str) -> bool:
        if not self.smtp_configured:
            self.logger.info("📧 E-mail não configurado - relatório salvo apenas localmente")
            return True

        try:
            recipients = self.config.get('recipients', {}).get('daily_report', [])
            if not recipients:
                self.logger.warning("Nenhum destinatário configurado")
                return True

            sender_email = os.getenv("EMAIL_USER")
            app_password = os.getenv("EMAIL_APP_PASSWORD")

            yag = yagmail.SMTP(user=sender_email, password=app_password)
            yag.send(
                to=recipients,
                subject='📊 Relatório Diário - Notícias de Seguros',
                contents=[report_html]
            )

            self.logger.info(f"✅ E-mail enviado com sucesso para {len(recipients)} destinatário(s)")
            return True
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar e-mail com yagmail: {e}")
            return False


