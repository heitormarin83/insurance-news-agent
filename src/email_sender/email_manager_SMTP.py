"""
Email Manager - Versão SMTP
Substitui a complexidade do Gmail API por SMTP simples
"""

import os
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from src.models import DailyReport, NewsArticle
from src.utils.logger import get_logger

# Importa o SMTP Sender ao invés do Gmail Sender
import sys
sys.path.insert(0, str(Path(__file__).parent.parent.parent))
from smtp_sender import SMTPSender
from src.email_sender.email_template import EmailTemplate

logger = get_logger("email_manager")


class EmailManager:
    """
    Gerenciador de e-mails usando SMTP
    Versão simplificada sem OAuth
    """
    
    def __init__(self, config_path: str = "config/email_config.yaml"):
        """
        Inicializa o gerenciador de e-mails
        
        Args:
            config_path: Caminho para arquivo de configuração
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Usa SMTP Sender ao invés de Gmail Sender
        self.sender = SMTPSender()
        self.template = EmailTemplate()
        
        self.logger = logger
        self.logger.info("Email Manager inicializado (SMTP)")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração de e-mail"""
        try:
            if not self.config_path.exists():
                logger.warning(f"Arquivo de configuração não encontrado: {self.config_path}")
                return self._get_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            logger.info("Configuração de e-mail carregada")
            return config
            
        except Exception as e:
            logger.error(f"Erro ao carregar configuração: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Retorna configuração padrão"""
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
        """
        Autentica com o serviço de e-mail
        
        Returns:
            True se autenticação bem-sucedida
        """
        try:
            return self.sender.authenticate()
        except Exception as e:
            self.logger.error(f"❌ Falha na autenticação do Email Manager: {e}")
            return False
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Valida configuração do sistema de e-mail
        
        Returns:
            Dicionário com status da validação
        """
        # Valida SMTP
        smtp_validation = self.sender.validate_configuration()
        
        # Conta destinatários
        recipients = self.config.get('recipients', {})
        daily_recipients = recipients.get('daily_report', [])
        
        # Validação geral
        issues = []
        if not smtp_validation['valid']:
            issues.extend(smtp_validation['issues'])
        
        if not daily_recipients:
            issues.append("Nenhum destinatário configurado para relatório diário")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'recipients_count': len(daily_recipients),
            'smtp_status': smtp_validation,
            'config_loaded': bool(self.config)
        }
    
    def send_daily_report(self, report: DailyReport) -> bool:
        """
        Envia relatório diário por e-mail
        
        Args:
            report: Relatório diário para enviar
            
        Returns:
            True se envio bem-sucedido
        """
        try:
            # Obtém destinatários
            recipients = self.config.get('recipients', {}).get('daily_report', [])
            
            if not recipients:
                self.logger.warning("Nenhum destinatário configurado para relatório diário")
                return False
            
            # Gera conteúdo do e-mail
            subject = f"📊 Relatório Diário de Seguros - {report.date.strftime('%d/%m/%Y')}"
            
            # Gera HTML usando template
            html_body = self.template.generate_daily_report_html(report)
            
            # Gera versão texto
            text_body = self.template.generate_daily_report_text(report)
            
            # Envia e-mail
            success = self.sender.send_email(
                to_emails=recipients,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
            if success:
                self.logger.info(f"✅ Relatório diário enviado para {len(recipients)} destinatário(s)")
            else:
                self.logger.error("❌ Falha no envio do relatório diário")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar relatório diário: {e}")
            return False
    
    def send_open_insurance_alert(self, articles: List[NewsArticle]) -> bool:
        """
        Envia alerta sobre artigos de Open Insurance
        
        Args:
            articles: Lista de artigos sobre Open Insurance
            
        Returns:
            True se envio bem-sucedido
        """
        try:
            if not articles:
                return True  # Nada para enviar
            
            # Obtém destinatários
            recipients = self.config.get('recipients', {}).get('alerts', [])
            
            if not recipients:
                self.logger.info("Nenhum destinatário configurado para alertas")
                return True
            
            # Gera conteúdo do alerta
            subject = f"🚨 Alerta Open Insurance - {len(articles)} novo(s) artigo(s)"
            
            html_body = self.template.generate_open_insurance_alert_html(articles)
            text_body = self.template.generate_open_insurance_alert_text(articles)
            
            # Envia e-mail
            success = self.sender.send_email(
                to_emails=recipients,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
            if success:
                self.logger.info(f"✅ Alerta Open Insurance enviado para {len(recipients)} destinatário(s)")
            else:
                self.logger.error("❌ Falha no envio do alerta Open Insurance")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar alerta Open Insurance: {e}")
            return False
    
    def send_error_notification(self, error_details: Dict[str, Any]) -> bool:
        """
        Envia notificação de erro
        
        Args:
            error_details: Detalhes do erro
            
        Returns:
            True se envio bem-sucedido
        """
        try:
            # Obtém destinatários
            recipients = self.config.get('recipients', {}).get('errors', [])
            
            if not recipients:
                self.logger.info("Nenhum destinatário configurado para erros")
                return True
            
            # Gera conteúdo da notificação
            subject = f"❌ Erro no Insurance News Agent - {datetime.now().strftime('%d/%m/%Y %H:%M')}"
            
            html_body = self.template.generate_error_notification_html(error_details)
            text_body = self.template.generate_error_notification_text(error_details)
            
            # Envia e-mail
            success = self.sender.send_email(
                to_emails=recipients,
                subject=subject,
                html_body=html_body,
                text_body=text_body
            )
            
            if success:
                self.logger.info(f"✅ Notificação de erro enviada para {len(recipients)} destinatário(s)")
            else:
                self.logger.error("❌ Falha no envio da notificação de erro")
            
            return success
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar notificação de erro: {e}")
            return False
    
    def send_test_email(self, to_email: str) -> bool:
        """
        Envia e-mail de teste
        
        Args:
            to_email: Destinatário do teste
            
        Returns:
            True se teste bem-sucedido
        """
        return self.sender.send_test_email(to_email)
    
    def add_recipient(self, email: str, category: str = 'daily_report') -> bool:
        """
        Adiciona destinatário à configuração
        
        Args:
            email: E-mail do destinatário
            category: Categoria (daily_report, alerts, errors)
            
        Returns:
            True se adicionado com sucesso
        """
        try:
            if 'recipients' not in self.config:
                self.config['recipients'] = {}
            
            if category not in self.config['recipients']:
                self.config['recipients'][category] = []
            
            if email not in self.config['recipients'][category]:
                self.config['recipients'][category].append(email)
                
                # Salva configuração atualizada
                with open(self.config_path, 'w', encoding='utf-8') as f:
                    yaml.dump(self.config, f, default_flow_style=False, allow_unicode=True)
                
                self.logger.info(f"Destinatário adicionado: {email} ({category})")
                return True
            else:
                self.logger.info(f"Destinatário já existe: {email} ({category})")
                return True
                
        except Exception as e:
            self.logger.error(f"Erro ao adicionar destinatário: {e}")
            return False

