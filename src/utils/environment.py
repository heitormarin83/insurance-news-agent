"""
Configuração de ambiente para o Insurance News Agent
Versão corrigida - SEM OAuth, apenas SMTP
"""

import os
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import yaml

class EnvironmentSetup:
    """Classe para configuração do ambiente do sistema"""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
        self.base_dir = Path(__file__).parent.parent.parent
        
    def initialize_environment(self) -> bool:
        """
        Inicializa o ambiente completo do sistema
        
        Returns:
            bool: True se inicialização foi bem-sucedida
        """
        try:
            # 1. Criar diretórios necessários
            if not self.setup_directories():
                return False
                
            # 2. Configurar e-mail (SMTP apenas)
            if not self.setup_email_config():
                return False
                
            # 3. Validar configuração
            validation_result = self.validate_configuration()
            
            # 4. Exibir resumo
            self.display_config_summary(validation_result)
            
            return validation_result['is_valid']
            
        except Exception as e:
            self.logger.error(f"Erro na inicialização do ambiente: {e}")
            return False
    
    def setup_directories(self) -> bool:
        """
        Cria todos os diretórios necessários para o sistema
        
        Returns:
            bool: True se todos os diretórios foram criados
        """
        directories = [
            'config',
            'data',
            'data/reports',
            'data/deduplication',  # Novo: para sistema de deduplicação
            'logs',
            'logs/email',
            'logs/scrapers',
            'logs/analyzers'
        ]
        
        try:
            for directory in directories:
                dir_path = self.base_dir / directory
                dir_path.mkdir(parents=True, exist_ok=True)
                self.logger.debug(f"Diretório criado/verificado: {dir_path}")
            
            self.logger.info(f"✅ {len(directories)} diretórios criados/verificados com sucesso")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao criar diretórios: {e}")
            return False
    
    def setup_email_config(self) -> bool:
        """
        Configura o sistema de e-mail usando SMTP (sem OAuth)
        
        Returns:
            bool: True se configuração foi criada
        """
        try:
            config_path = self.base_dir / 'config' / 'email_config.yaml'
            
            # Configuração SMTP baseada em variáveis de ambiente
            email_config = {
                'smtp': {
                    'server': 'smtp.gmail.com',
                    'port': 587,
                    'use_tls': True,
                    'sender_name': 'Insurance News Agent'
                },
                'recipients': {
                    'daily_report': self._parse_email_list(os.getenv('EMAIL_RECIPIENTS_DAILY', '')),
                    'alerts': self._parse_email_list(os.getenv('EMAIL_RECIPIENTS_ALERTS', '')),
                    'errors': self._parse_email_list(os.getenv('EMAIL_RECIPIENTS_ERRORS', ''))
                },
                'templates': {
                    'daily_report': {
                        'subject': 'Relatório Diário - Notícias de Seguros - {date}',
                        'template_file': 'daily_report_template.html'
                    },
                    'alert': {
                        'subject': 'Alerta - Insurance News Agent - {alert_type}',
                        'template_file': 'alert_template.html'
                    },
                    'error': {
                        'subject': 'Erro - Insurance News Agent - {error_type}',
                        'template_file': 'error_template.html'
                    }
                }
            }
            
            # Salvar configuração
            with open(config_path, 'w', encoding='utf-8') as file:
                yaml.dump(email_config, file, default_flow_style=False, allow_unicode=True)
            
            # Contar destinatários configurados
            total_recipients = len(email_config['recipients']['daily_report'])
            
            self.logger.info(f"✅ Configuração de e-mail criada: {total_recipients} destinatários diários")
            return True
            
        except Exception as e:
            self.logger.error(f"Erro ao configurar e-mail: {e}")
            return False
    
    def _parse_email_list(self, email_string: str) -> List[str]:
        """
        Converte string de e-mails separados por vírgula em lista
        
        Args:
            email_string: String com e-mails separados por vírgula
            
        Returns:
            List[str]: Lista de e-mails válidos
        """
        if not email_string:
            return []
        
        emails = [email.strip() for email in email_string.split(',')]
        return [email for email in emails if email and '@' in email]
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Valida a configuração completa do sistema
        
        Returns:
            Dict: Resultado da validação com detalhes
        """
        validation = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'smtp_configured': False,
            'recipients_count': 0
        }
        
        # Validar variáveis de ambiente SMTP
        gmail_email = os.getenv('GMAIL_EMAIL')
        gmail_password = os.getenv('GMAIL_APP_PASSWORD')
        
        if gmail_email and gmail_password:
            validation['smtp_configured'] = True
            self.logger.info("✅ SMTP configurado corretamente")
        else:
            validation['warnings'].append("SMTP não configurado - e-mails não serão enviados")
            if not gmail_email:
                validation['warnings'].append("GMAIL_EMAIL não configurado")
            if not gmail_password:
                validation['warnings'].append("GMAIL_APP_PASSWORD não configurado")
        
        # Validar destinatários
        daily_recipients = self._parse_email_list(os.getenv('EMAIL_RECIPIENTS_DAILY', ''))
        validation['recipients_count'] = len(daily_recipients)
        
        if not daily_recipients:
            validation['warnings'].append("Nenhum destinatário configurado para relatórios diários")
        
        # Validar configurações numéricas
        try:
            max_articles = int(os.getenv('MAX_ARTICLES_PER_SOURCE', '50'))
            if max_articles <= 0:
                validation['errors'].append("MAX_ARTICLES_PER_SOURCE deve ser maior que 0")
        except (ValueError, TypeError):
            validation['warnings'].append("MAX_ARTICLES_PER_SOURCE inválido, usando padrão (50)")
        
        # Determinar se configuração é válida
        if validation['errors']:
            validation['is_valid'] = False
        
        return validation
    
    def display_config_summary(self, validation: Dict[str, Any]) -> None:
        """
        Exibe resumo da configuração do sistema
        
        Args:
            validation: Resultado da validação
        """
        print("\n" + "="*60)
        print("🔧 RESUMO DA CONFIGURAÇÃO - INSURANCE NEWS AGENT")
        print("="*60)
        
        # Status geral
        status = "✅ VÁLIDA" if validation['is_valid'] else "❌ INVÁLIDA"
        print(f"Status: {status}")
        
        # Configuração SMTP
        smtp_status = "✅ Configurado" if validation['smtp_configured'] else "⚠️ Não configurado"
        print(f"SMTP: {smtp_status}")
        
        # Destinatários
        recipients_count = validation['recipients_count']
        print(f"Destinatários: {recipients_count} configurados")
        
        # Variáveis de ambiente
        print(f"\n📧 VARIÁVEIS DE AMBIENTE:")
        env_vars = [
            ('GMAIL_EMAIL', os.getenv('GMAIL_EMAIL', 'Não configurado')),
            ('GMAIL_APP_PASSWORD', '***' if os.getenv('GMAIL_APP_PASSWORD') else 'Não configurado'),
            ('EMAIL_RECIPIENTS_DAILY', os.getenv('EMAIL_RECIPIENTS_DAILY', 'Não configurado')),
            ('EMAIL_RECIPIENTS_ALERTS', os.getenv('EMAIL_RECIPIENTS_ALERTS', 'Não configurado')),
            ('EMAIL_RECIPIENTS_ERRORS', os.getenv('EMAIL_RECIPIENTS_ERRORS', 'Não configurado'))
        ]
        
        for var_name, var_value in env_vars:
            print(f"  {var_name}: {var_value}")
        
        # Avisos
        if validation['warnings']:
            print(f"\n⚠️ AVISOS ({len(validation['warnings'])}):")
            for warning in validation['warnings']:
                print(f"  • {warning}")
        
        # Erros
        if validation['errors']:
            print(f"\n❌ ERROS ({len(validation['errors'])}):")
            for error in validation['errors']:
                print(f"  • {error}")
        
        print("="*60)
    
    def get_config_summary(self) -> Dict[str, Any]:
        """
        Retorna resumo da configuração para uso programático
        
        Returns:
            Dict: Resumo da configuração
        """
        validation = self.validate_configuration()
        
        return {
            'environment_valid': validation['is_valid'],
            'smtp_configured': validation['smtp_configured'],
            'recipients_count': validation['recipients_count'],
            'errors_count': len(validation['errors']),
            'warnings_count': len(validation['warnings']),
            'base_directory': str(self.base_dir),
            'config_files': {
                'email_config': (self.base_dir / 'config' / 'email_config.yaml').exists(),
                'sources_config': (self.base_dir / 'config' / 'sources.yaml').exists(),
                'news_analyzer_config': (self.base_dir / 'config' / 'news_analyzer_config.yaml').exists()
            }
        }


def initialize_environment() -> bool:
    """
    Função principal para inicializar o ambiente
    
    Returns:
        bool: True se inicialização foi bem-sucedida
    """
    setup = EnvironmentSetup()
    return setup.initialize_environment()


def get_environment_summary() -> Dict[str, Any]:
    """
    Retorna resumo do ambiente configurado
    
    Returns:
        Dict: Resumo da configuração
    """
    setup = EnvironmentSetup()
    return setup.get_config_summary()


if __name__ == "__main__":
    # Configurar logging para execução direta
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )
    
    # Inicializar ambiente
    success = initialize_environment()
    
    if success:
        print("\n🎉 Ambiente inicializado com sucesso!")
    else:
        print("\n❌ Falha na inicialização do ambiente!")
        exit(1)
