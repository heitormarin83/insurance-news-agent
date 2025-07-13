"""
Gerenciador principal do sistema de e-mails
"""

import yaml
from typing import List, Dict, Any, Optional
from datetime import datetime, time
from pathlib import Path

from .gmail_sender import GmailSender
from .email_template import EmailTemplate
from src.models import DailyReport, NewsArticle
from src.utils.logger import get_logger

logger = get_logger("email_manager")


class EmailManager:
    """Gerenciador principal do sistema de e-mails"""
    
    def __init__(self, config_path: str = None):
        """
        Inicializa o gerenciador de e-mails
        
        Args:
            config_path: Caminho para arquivo de configuração
        """
        if config_path is None:
            config_path = Path(__file__).parent.parent.parent / "config" / "email_config.yaml"
        
        self.config_path = Path(config_path)
        self.config = self._load_config()
        
        # Inicializa componentes
        self.gmail_sender = GmailSender(
            credentials_path=self.config['gmail']['credentials_file'],
            token_path=self.config['gmail']['token_file']
        )
        self.email_template = EmailTemplate()
        
        # Estado de autenticação
        self.authenticated = False
        
        logger.info("Email Manager inicializado")
    
    def _load_config(self) -> Dict[str, Any]:
        """
        Carrega configuração de e-mail
        
        Returns:
            Configuração carregada
        """
        try:
            if not self.config_path.exists():
                logger.warning(f"Arquivo de configuração não encontrado: {self.config_path}")
                return self._get_default_config()
            
            with open(self.config_path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
            
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
    
    def authenticate(self) -> bool:
        """
        Autentica com Gmail API
        
        Returns:
            True se autenticação bem-sucedida
        """
        try:
            self.authenticated = self.gmail_sender.authenticate()
            
            if self.authenticated:
                logger.info("✅ Email Manager autenticado com sucesso")
            else:
                logger.error("❌ Falha na autenticação do Email Manager")
            
            return self.authenticated
            
        except Exception as e:
            logger.error(f"❌ Erro na autenticação: {e}")
            return False
    
    def send_daily_report(self, report: DailyReport) -> bool:
        """
        Envia relatório diário por e-mail
        
        Args:
            report: Relatório diário
            
        Returns:
            True se envio bem-sucedido
        """
        if not self.authenticated:
            logger.error("Email Manager não autenticado")
            return False
        
        try:
            logger.info("📧 Enviando relatório diário por e-mail")
            
            # Obtém destinatários
            recipients = self.config['recipients']['daily_report']
            
            if not recipients:
                logger.warning("Nenhum destinatário configurado para relatório diário")
                return False
            
            # Gera e-mail
            email_content = self.email_template.generate_daily_report_email(report)
            
            # Envia e-mail
            success = self.gmail_sender.send_email(
                to_emails=recipients,
                subject=email_content['subject'],
                body=email_content['body'],
                body_type='html'
            )
            
            if success:
                logger.info(f"✅ Relatório diário enviado para {len(recipients)} destinatários")
                self._log_email_sent('daily_report', recipients, email_content['subject'])
            else:
                logger.error("❌ Falha no envio do relatório diário")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar relatório diário: {e}")
            return False
    
    def send_open_insurance_alert(self, articles: List[NewsArticle]) -> bool:
        """
        Envia alerta sobre artigos de Open Insurance
        
        Args:
            articles: Lista de artigos sobre Open Insurance
            
        Returns:
            True se envio bem-sucedido
        """
        if not self.authenticated:
            logger.error("Email Manager não autenticado")
            return False
        
        if not articles:
            return True  # Nada para enviar
        
        try:
            logger.info(f"🚨 Enviando alerta Open Insurance: {len(articles)} artigos")
            
            # Obtém destinatários
            recipients = self.config['recipients']['alerts']
            
            if not recipients:
                logger.warning("Nenhum destinatário configurado para alertas")
                return False
            
            # Gera e-mail de alerta
            email_content = self.email_template.generate_alert_email(articles, 'open_insurance')
            
            # Envia e-mail
            success = self.gmail_sender.send_email(
                to_emails=recipients,
                subject=email_content['subject'],
                body=email_content['body'],
                body_type='html'
            )
            
            if success:
                logger.info(f"✅ Alerta Open Insurance enviado para {len(recipients)} destinatários")
                self._log_email_sent('open_insurance_alert', recipients, email_content['subject'])
            else:
                logger.error("❌ Falha no envio do alerta Open Insurance")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar alerta Open Insurance: {e}")
            return False
    
    def send_error_notification(self, error_details: Dict[str, Any]) -> bool:
        """
        Envia notificação de erro
        
        Args:
            error_details: Detalhes do erro
            
        Returns:
            True se envio bem-sucedido
        """
        if not self.authenticated:
            logger.error("Email Manager não autenticado")
            return False
        
        try:
            logger.info("🚨 Enviando notificação de erro")
            
            # Obtém destinatários
            recipients = self.config['recipients']['errors']
            
            if not recipients:
                logger.warning("Nenhum destinatário configurado para erros")
                return False
            
            # Gera e-mail de erro
            email_content = self.email_template.generate_error_email(error_details)
            
            # Envia e-mail
            success = self.gmail_sender.send_email(
                to_emails=recipients,
                subject=email_content['subject'],
                body=email_content['body'],
                body_type='html'
            )
            
            if success:
                logger.info(f"✅ Notificação de erro enviada para {len(recipients)} destinatários")
                self._log_email_sent('error_notification', recipients, email_content['subject'])
            else:
                logger.error("❌ Falha no envio da notificação de erro")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar notificação de erro: {e}")
            return False
    
    def send_test_email(self, test_email: str) -> bool:
        """
        Envia e-mail de teste
        
        Args:
            test_email: E-mail para teste
            
        Returns:
            True se envio bem-sucedido
        """
        if not self.authenticated:
            if not self.authenticate():
                return False
        
        try:
            logger.info(f"🧪 Enviando e-mail de teste para: {test_email}")
            
            success = self.gmail_sender.send_test_email(test_email)
            
            if success:
                logger.info("✅ E-mail de teste enviado com sucesso")
            else:
                logger.error("❌ Falha no envio do e-mail de teste")
            
            return success
            
        except Exception as e:
            logger.error(f"❌ Erro ao enviar e-mail de teste: {e}")
            return False
    
    def _log_email_sent(self, email_type: str, recipients: List[str], subject: str):
        """
        Registra log de e-mail enviado
        
        Args:
            email_type: Tipo de e-mail
            recipients: Lista de destinatários
            subject: Assunto do e-mail
        """
        try:
            if not self.config['logging']['save_email_logs']:
                return
            
            log_dir = Path(self.config['logging']['log_directory'])
            log_dir.mkdir(parents=True, exist_ok=True)
            
            log_file = log_dir / f"emails_sent_{datetime.now().strftime('%Y-%m')}.log"
            
            log_entry = {
                'timestamp': datetime.now().isoformat(),
                'type': email_type,
                'recipients': recipients,
                'subject': subject,
                'success': True
            }
            
            with open(log_file, 'a', encoding='utf-8') as f:
                f.write(f"{log_entry}\\n")
            
        except Exception as e:
            logger.error(f"Erro ao salvar log de e-mail: {e}")
    
    def get_recipients_count(self) -> Dict[str, int]:
        """
        Obtém contagem de destinatários por tipo
        
        Returns:
            Contagem de destinatários
        """
        return {
            'daily_report': len(self.config['recipients']['daily_report']),
            'alerts': len(self.config['recipients']['alerts']),
            'errors': len(self.config['recipients']['errors'])
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Valida configuração de e-mail
        
        Returns:
            Resultado da validação
        """
        issues = []
        
        # Verifica destinatários
        if not self.config['recipients']['daily_report']:
            issues.append("Nenhum destinatário configurado para relatório diário")
        
        if not self.config['recipients']['alerts']:
            issues.append("Nenhum destinatário configurado para alertas")
        
        if not self.config['recipients']['errors']:
            issues.append("Nenhum destinatário configurado para erros")
        
        # Verifica arquivos de credenciais
        credentials_file = Path(self.config['gmail']['credentials_file'])
        if not credentials_file.exists():
            issues.append(f"Arquivo credentials.json não encontrado: {credentials_file}")
        
        # Verifica configurações de horário
        try:
            time.fromisoformat(self.config['sending']['daily_report_time'])
        except ValueError:
            issues.append("Formato de horário inválido para daily_report_time")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'recipients_count': self.get_recipients_count()
        }
    
    def test_connection(self) -> bool:
        """
        Testa conexão com Gmail API
        
        Returns:
            True se conexão bem-sucedida
        """
        if not self.authenticated:
            return self.authenticate()
        
        return self.gmail_sender.test_connection()

