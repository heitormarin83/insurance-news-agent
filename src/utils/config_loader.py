"""
Utilitário para carregar configurações do sistema
"""

import yaml
import os
from typing import Dict, Any
from pathlib import Path


class ConfigLoader:
    """Carregador de configurações do sistema"""
    
    def __init__(self, config_dir: str = None):
        """
        Inicializa o carregador de configurações
        
        Args:
            config_dir: Diretório de configurações (padrão: config/)
        """
        if config_dir is None:
            # Assume que está sendo executado da raiz do projeto
            self.config_dir = Path(__file__).parent.parent.parent / "config"
        else:
            self.config_dir = Path(config_dir)
    
    def load_sources_config(self) -> Dict[str, Any]:
        """
        Carrega configuração das fontes de notícias
        
        Returns:
            Dicionário com configurações das fontes
        """
        sources_file = self.config_dir / "sources.yaml"
        
        if not sources_file.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {sources_file}")
        
        with open(sources_file, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    
    def load_email_config(self) -> Dict[str, Any]:
        """
        Carrega configuração de e-mail
        
        Returns:
            Dicionário com configurações de e-mail
        """
        email_file = self.config_dir / "email.yaml"
        
        if not email_file.exists():
            # Retorna configuração padrão se arquivo não existir
            return {
                'smtp_server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
                'smtp_port': int(os.getenv('SMTP_PORT', '587')),
                'sender_email': os.getenv('SENDER_EMAIL', ''),
                'sender_password': os.getenv('SENDER_PASSWORD', ''),
                'recipient_emails': os.getenv('RECIPIENT_EMAILS', '').split(','),
                'use_tls': True
            }
        
        with open(email_file, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)
    
    def get_source_by_name(self, source_name: str) -> Dict[str, Any]:
        """
        Obtém configuração de uma fonte específica
        
        Args:
            source_name: Nome da fonte
            
        Returns:
            Configuração da fonte
        """
        sources = self.load_sources_config()
        
        # Busca em todas as regiões
        for region_sources in sources.values():
            if isinstance(region_sources, dict) and source_name in region_sources:
                return region_sources[source_name]
        
        raise ValueError(f"Fonte não encontrada: {source_name}")
    
    def get_enabled_sources(self) -> Dict[str, Dict[str, Any]]:
        """
        Obtém apenas as fontes habilitadas
        
        Returns:
            Dicionário com fontes habilitadas
        """
        sources = self.load_sources_config()
        enabled_sources = {}
        
        for region, region_sources in sources.items():
            if region == 'global_settings' or region == 'relevance_filters':
                continue
                
            if isinstance(region_sources, dict):
                for source_name, source_config in region_sources.items():
                    if source_config.get('enabled', True):
                        enabled_sources[source_name] = source_config
        
        return enabled_sources
    
    def get_sources_by_region(self, region: str) -> Dict[str, Dict[str, Any]]:
        """
        Obtém fontes de uma região específica
        
        Args:
            region: Nome da região
            
        Returns:
            Dicionário com fontes da região
        """
        sources = self.load_sources_config()
        
        if region not in sources:
            raise ValueError(f"Região não encontrada: {region}")
        
        return sources[region]
    
    def get_global_settings(self) -> Dict[str, Any]:
        """
        Obtém configurações globais
        
        Returns:
            Dicionário com configurações globais
        """
        sources = self.load_sources_config()
        return sources.get('global_settings', {})
    
    def get_relevance_filters(self) -> Dict[str, Any]:
        """
        Obtém filtros de relevância
        
        Returns:
            Dicionário com filtros de relevância
        """
        sources = self.load_sources_config()
        return sources.get('relevance_filters', {})


# Instância global do carregador de configurações
config_loader = ConfigLoader()

