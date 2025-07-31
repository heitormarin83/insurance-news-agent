"""
Email Manager - Versão Simplificada
Funciona mesmo sem configuração de e-mail
"""

import os
import yaml
from typing import List, Dict, Any, Optional
from pathlib import Path
from datetime import datetime

from src.utils.logger import get_logger

logger = get_logger("email_manager")


class EmailManager:
    """
    Gerenciador de e-mails simplificado
    Funciona mesmo sem configuração
    """
    
    def __init__(self, config_path: str = "config/email_config.yaml"):
        """
        Inicializa o gerenciador de e-mails
        
        Args:
            config_path: Caminho para arquivo de configuração
        """
        self.config_path = Path(config_path)
        self.config = self._load_config()
        self.authenticated = False
        self.logger = logger
        
        # Verifica se SMTP está configurado
        self.smtp_configured = bool(
            os.getenv('GMAIL_EMAIL') and 
            os.getenv('GMAIL_APP_PASSWORD')
        )
        
        if self.smtp_configured:
            self.logger.info("Email Manager inicializado (SMTP configurado)")
        else:
            self.logger.warning("Email Manager inicializado (SMTP não configurado)")
    
    def _load_config(self) -> Dict[str, Any]:
        """Carrega configuração de e-mail"""
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
            True se autenticação bem-sucedida ou não necessária
        """
        if not self.smtp_configured:
            self.logger.info("SMTP não configurado - pulando autenticação")
            return False
        
        try:
            # Testa configuração SMTP básica
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
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Valida configuração do sistema de e-mail
        
        Returns:
            Dicionário com status da validação
        """
        issues = []
        
        # Verifica credenciais SMTP
        if not os.getenv('GMAIL_EMAIL'):
            issues.append("GMAIL_EMAIL não configurado")
        
        if not os.getenv('GMAIL_APP_PASSWORD'):
            issues.append("GMAIL_APP_PASSWORD não configurado")
        
        # Conta destinatários
        recipients = self.config.get('recipients', {})
        daily_recipients = recipients.get('daily_report', [])
        
        if not daily_recipients:
            issues.append("Nenhum destinatário configurado para relatório diário")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'recipients_count': len(daily_recipients),
            'smtp_configured': self.smtp_configured,
            'config_loaded': bool(self.config)
        }
    
    def get_recipients_count(self) -> Dict[str, int]:
        """Retorna contagem de destinatários por categoria"""
        recipients = self.config.get('recipients', {})
        return {
            'daily_report': len(recipients.get('daily_report', [])),
            'alerts': len(recipients.get('alerts', [])),
            'errors': len(recipients.get('errors', []))
        }
    
    def send_daily_report(self, report) -> bool:
        """
        Envia relatório diário por e-mail
        
        Args:
            report: Relatório diário para enviar
            
        Returns:
            True se envio bem-sucedido ou não configurado
        """
        if not self.smtp_configured:
            self.logger.info("📧 E-mail não configurado - relatório salvo apenas localmente")
            return True  # Não é erro, apenas não configurado
        
        try:
            # Aqui seria a implementação real do SMTP
            # Por enquanto, simula sucesso se configurado
            recipients = self.config.get('recipients', {}).get('daily_report', [])
            
            if not recipients:
                self.logger.warning("Nenhum destinatário configurado")
                return True
            
            self.logger.info(f"📧 Simulando envio para {len(recipients)} destinatário(s)")
            self.logger.info("Para implementar SMTP real, use a versão completa do email_manager")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar relatório diário: {e}")
            return False
    
    def send_open_insurance_alert(self, articles) -> bool:
        """
        Envia alerta sobre artigos de Open Insurance
        
        Args:
            articles: Lista de artigos sobre Open Insurance
            
        Returns:
            True se envio bem-sucedido ou não configurado
        """
        if not self.smtp_configured:
            return True
        
        if not articles:
            return True
        
        self.logger.info(f"📧 Simulando alerta Open Insurance para {len(articles)} artigo(s)")
        return True
    
    def send_error_notification(self, error_details) -> bool:
        """
        Envia notificação de erro
        
        Args:
            error_details: Detalhes do erro
            
        Returns:
            True se envio bem-sucedido ou não configurado
        """
        if not self.smtp_configured:
            return True
        
        self.logger.info("📧 Simulando notificação de erro")
        return True
    
    def send_test_email(self, to_email: str) -> bool:
        """
        Envia e-mail de teste
        
        Args:
            to_email: Destinatário do teste
            
        Returns:
            True se teste bem-sucedido ou não configurado
        """
        if not self.smtp_configured:
            self.logger.warning("SMTP não configurado - não é possível enviar e-mail de teste")
            return False
        
        self.logger.info(f"📧 Simulando e-mail de teste para {to_email}")
        return True
    
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
                self.config_path.parent.mkdir(parents=True, exist_ok=True)
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


