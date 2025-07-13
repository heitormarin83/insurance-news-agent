"""
Utilitário para configuração de ambiente e variáveis
"""

import os
import json
from pathlib import Path
from typing import Dict, Any, Optional

from src.utils.logger import get_logger

logger = get_logger("environment")


class EnvironmentConfig:
    """Gerenciador de configuração de ambiente"""
    
    def __init__(self):
        """Inicializa configuração de ambiente"""
        self.is_production = self._detect_production()
        self.is_railway = self._detect_railway()
        
        logger.info(f"Ambiente detectado - Produção: {self.is_production}, Railway: {self.is_railway}")
    
    def _detect_production(self) -> bool:
        """Detecta se está em ambiente de produção"""
        return (
            os.getenv('FLASK_DEBUG', 'false').lower() == 'false' and
            os.getenv('RAILWAY_ENVIRONMENT') == 'production'
        )
    
    def _detect_railway(self) -> bool:
        """Detecta se está rodando no Railway"""
        return 'RAILWAY_ENVIRONMENT' in os.environ
    
    def setup_gmail_credentials(self) -> bool:
        """
        Configura credenciais do Gmail a partir de variáveis de ambiente
        
        Returns:
            True se configuração bem-sucedida
        """
        try:
            config_dir = Path('config')
            config_dir.mkdir(exist_ok=True)
            
            # Configura credentials.json
            gmail_credentials = os.getenv('GMAIL_CREDENTIALS')
            if gmail_credentials:
                credentials_path = config_dir / 'credentials.json'
                
                # Parse JSON se for string
                if isinstance(gmail_credentials, str):
                    credentials_data = json.loads(gmail_credentials)
                else:
                    credentials_data = gmail_credentials
                
                with open(credentials_path, 'w') as f:
                    json.dump(credentials_data, f, indent=2)
                
                logger.info("✅ Credenciais Gmail configuradas")
            else:
                logger.warning("⚠️ GMAIL_CREDENTIALS não encontrado")
                return False
            
            # Configura token.json se disponível
            gmail_token = os.getenv('GMAIL_TOKEN')
            if gmail_token:
                token_path = config_dir / 'token.json'
                
                # Parse JSON se for string
                if isinstance(gmail_token, str):
                    token_data = json.loads(gmail_token)
                else:
                    token_data = gmail_token
                
                with open(token_path, 'w') as f:
                    json.dump(token_data, f, indent=2)
                
                logger.info("✅ Token Gmail configurado")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar credenciais Gmail: {e}")
            return False
    
    def setup_email_config(self) -> bool:
        """
        Configura arquivo de e-mail a partir de variáveis de ambiente
        
        Returns:
            True se configuração bem-sucedida
        """
        try:
            import yaml
            
            # Obtém destinatários das variáveis de ambiente
            daily_recipients = self._parse_email_list('EMAIL_RECIPIENTS_DAILY')
            alert_recipients = self._parse_email_list('EMAIL_RECIPIENTS_ALERTS')
            error_recipients = self._parse_email_list('EMAIL_RECIPIENTS_ERRORS')
            
            # Configuração de e-mail
            email_config = {
                'recipients': {
                    'daily_report': daily_recipients,
                    'alerts': alert_recipients,
                    'errors': error_recipients
                },
                'sending': {
                    'daily_report_time': os.getenv('DAILY_COLLECTION_TIME', '08:00'),
                    'timezone': os.getenv('TIMEZONE', 'America/Sao_Paulo'),
                    'weekdays_only': True,
                    'immediate_open_insurance_alerts': os.getenv('ENABLE_OPEN_INSURANCE_ALERTS', 'true').lower() == 'true',
                    'alert_relevance_threshold': float(os.getenv('RELEVANCE_THRESHOLD', '0.7'))
                },
                'gmail': {
                    'credentials_file': 'config/credentials.json',
                    'token_file': 'config/token.json',
                    'sender_name': 'Insurance News Agent'
                },
                'templates': {
                    'include_detailed_stats': True,
                    'max_top_articles': int(os.getenv('MAX_TOP_ARTICLES', '10')),
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
                    'log_retention_days': int(os.getenv('LOG_RETENTION_DAYS', '30'))
                }
            }
            
            # Salva configuração
            config_path = Path('config/email_config.yaml')
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(email_config, f, default_flow_style=False, allow_unicode=True)
            
            logger.info(f"✅ Configuração de e-mail criada: {len(daily_recipients)} destinatários diários")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar e-mail: {e}")
            return False
    
    def _parse_email_list(self, env_var: str) -> list:
        """
        Parse lista de e-mails de variável de ambiente
        
        Args:
            env_var: Nome da variável de ambiente
            
        Returns:
            Lista de e-mails
        """
        email_string = os.getenv(env_var, '')
        if not email_string:
            return []
        
        emails = [email.strip() for email in email_string.split(',') if email.strip()]
        return emails
    
    def setup_directories(self):
        """Cria diretórios necessários"""
        directories = [
            'config',
            'data/reports',
            'logs',
            'logs/email'
        ]
        
        for directory in directories:
            Path(directory).mkdir(parents=True, exist_ok=True)
        
        logger.info("✅ Diretórios criados")
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo da configuração
        
        Returns:
            Dicionário com resumo da configuração
        """
        return {
            'environment': {
                'is_production': self.is_production,
                'is_railway': self.is_railway,
                'timezone': os.getenv('TIMEZONE', 'America/Sao_Paulo'),
                'daily_time': os.getenv('DAILY_COLLECTION_TIME', '08:00')
            },
            'email': {
                'enabled': os.getenv('ENABLE_EMAIL', 'true').lower() == 'true',
                'daily_recipients': len(self._parse_email_list('EMAIL_RECIPIENTS_DAILY')),
                'alert_recipients': len(self._parse_email_list('EMAIL_RECIPIENTS_ALERTS')),
                'error_recipients': len(self._parse_email_list('EMAIL_RECIPIENTS_ERRORS'))
            },
            'collection': {
                'max_articles_per_source': int(os.getenv('MAX_ARTICLES_PER_SOURCE', '50')),
                'relevance_threshold': float(os.getenv('RELEVANCE_THRESHOLD', '0.5')),
                'open_insurance_alerts': os.getenv('ENABLE_OPEN_INSURANCE_ALERTS', 'true').lower() == 'true'
            },
            'logging': {
                'level': os.getenv('LOG_LEVEL', 'INFO'),
                'retention_days': int(os.getenv('LOG_RETENTION_DAYS', '30'))
            }
        }
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Valida configuração do ambiente
        
        Returns:
            Resultado da validação
        """
        issues = []
        warnings = []
        
        # Verifica credenciais Gmail
        if not os.getenv('GMAIL_CREDENTIALS'):
            issues.append("GMAIL_CREDENTIALS não configurado")
        
        # Verifica destinatários de e-mail
        if not self._parse_email_list('EMAIL_RECIPIENTS_DAILY'):
            warnings.append("Nenhum destinatário para relatório diário")
        
        if not self._parse_email_list('EMAIL_RECIPIENTS_ERRORS'):
            warnings.append("Nenhum destinatário para erros")
        
        # Verifica configurações numéricas
        try:
            float(os.getenv('RELEVANCE_THRESHOLD', '0.5'))
        except ValueError:
            issues.append("RELEVANCE_THRESHOLD deve ser um número")
        
        try:
            int(os.getenv('MAX_ARTICLES_PER_SOURCE', '50'))
        except ValueError:
            issues.append("MAX_ARTICLES_PER_SOURCE deve ser um número")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'warnings': warnings,
            'config_summary': self.get_config_summary()
        }
    
    def initialize_environment(self) -> bool:
        """
        Inicializa ambiente completo
        
        Returns:
            True se inicialização bem-sucedida
        """
        try:
            logger.info("🚀 Inicializando ambiente...")
            
            # Cria diretórios
            self.setup_directories()
            
            # Configura credenciais Gmail
            gmail_success = self.setup_gmail_credentials()
            
            # Configura e-mail
            email_success = self.setup_email_config()
            
            # Valida configuração
            validation = self.validate_configuration()
            
            if validation['issues']:
                logger.error(f"❌ Problemas na configuração: {validation['issues']}")
                return False
            
            if validation['warnings']:
                logger.warning(f"⚠️ Avisos: {validation['warnings']}")
            
            logger.info("✅ Ambiente inicializado com sucesso")
            return gmail_success and email_success
            
        except Exception as e:
            logger.error(f"❌ Erro na inicialização do ambiente: {e}")
            return False


# Instância global
env_config = EnvironmentConfig()


def initialize_environment() -> bool:
    """
    Função de conveniência para inicializar ambiente
    
    Returns:
        True se inicialização bem-sucedida
    """
    return env_config.initialize_environment()


def get_config_summary() -> Dict[str, Any]:
    """
    Função de conveniência para obter resumo da configuração
    
    Returns:
        Resumo da configuração
    """
    return env_config.get_config_summary()


def validate_environment() -> Dict[str, Any]:
    """
    Função de conveniência para validar ambiente
    
    Returns:
        Resultado da validação
    """
    return env_config.validate_configuration()

