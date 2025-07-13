#!/usr/bin/env python3
"""
Script para configurar e-mails via variáveis de ambiente no GitHub Actions
"""

import os
import yaml
from pathlib import Path


def setup_email_config():
    """Configura arquivo de e-mail baseado em variáveis de ambiente"""
    
    # Obtém destinatários das variáveis de ambiente
    daily_recipients = os.getenv('EMAIL_RECIPIENTS_DAILY', '').split(',')
    alert_recipients = os.getenv('EMAIL_RECIPIENTS_ALERTS', '').split(',')
    error_recipients = os.getenv('EMAIL_RECIPIENTS_ERRORS', '').split(',')
    
    # Remove strings vazias
    daily_recipients = [email.strip() for email in daily_recipients if email.strip()]
    alert_recipients = [email.strip() for email in alert_recipients if email.strip()]
    error_recipients = [email.strip() for email in error_recipients if email.strip()]
    
    # Configuração de e-mail
    email_config = {
        'recipients': {
            'daily_report': daily_recipients,
            'alerts': alert_recipients,
            'errors': error_recipients
        },
        'sending': {
            'daily_report_time': '08:00',
            'timezone': 'America/Sao_Paulo',
            'weekdays_only': True,
            'immediate_open_insurance_alerts': True,
            'alert_relevance_threshold': 0.7
        },
        'gmail': {
            'credentials_file': 'config/credentials.json',
            'token_file': 'config/token.json',
            'sender_name': 'Insurance News Agent'
        },
        'templates': {
            'include_detailed_stats': True,
            'max_top_articles': 10,
            'max_open_insurance_articles': 5,
            'include_article_summaries': True,
            'max_summary_length': 200
        },
        'retry': {
            'max_attempts': 3,
            'delay_between_attempts': 60,
            'notify_on_failure': True
        },
        'logging': {
            'save_email_logs': True,
            'log_directory': 'logs/email',
            'log_retention_days': 30
        }
    }
    
    # Salva configuração
    config_path = Path('config/email_config.yaml')
    config_path.parent.mkdir(exist_ok=True)
    
    with open(config_path, 'w', encoding='utf-8') as f:
        yaml.dump(email_config, f, default_flow_style=False, allow_unicode=True)
    
    print(f"✅ Configuração de e-mail criada: {config_path}")
    print(f"📧 Destinatários relatório diário: {len(daily_recipients)}")
    print(f"🚨 Destinatários alertas: {len(alert_recipients)}")
    print(f"❌ Destinatários erros: {len(error_recipients)}")


if __name__ == "__main__":
    setup_email_config()

