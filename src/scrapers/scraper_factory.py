"""
Factory para criação de scrapers baseado no tipo de fonte
"""

from typing import Dict, Any, Optional
from src.models import SourceType
from .base_scraper import BaseScraper
from .rss_scraper import RSScraper
from .web_scraper import WebScraper
from src.utils.logger import get_logger

logger = get_logger("scraper_factory")


class ScraperFactory:
    """Factory para criação de scrapers"""
    
    @staticmethod
    def create_scraper(source_config: Dict[str, Any]) -> Optional[BaseScraper]:
        """
        Cria scraper apropriado baseado na configuração da fonte
        
        Args:
            source_config: Configuração da fonte
            
        Returns:
            Instância do scraper apropriado ou None se erro
        """
        try:
            source_type = source_config.get('source_type', 'web_scraping')
            source_name = source_config.get('name', 'Unknown')
            
            logger.debug(f"Criando scraper para {source_name} (tipo: {source_type})")
            
            if source_type == 'rss' or source_config.get('rss_url'):
                return RSScraper(source_config)
            
            elif source_type == 'web_scraping':
                return WebScraper(source_config)
            
            elif source_type == 'api':
                # TODO: Implementar API scraper no futuro
                logger.warning(f"API scraper não implementado ainda para {source_name}")
                return None
            
            else:
                logger.error(f"Tipo de fonte não suportado: {source_type} para {source_name}")
                return None
                
        except Exception as e:
            logger.error(f"Erro ao criar scraper: {e}")
            return None
    
    @staticmethod
    def get_supported_types() -> list:
        """
        Retorna lista de tipos de fonte suportados
        
        Returns:
            Lista de tipos suportados
        """
        return ['rss', 'web_scraping']
    
    @staticmethod
    def validate_source_config(source_config: Dict[str, Any]) -> bool:
        """
        Valida configuração de fonte
        
        Args:
            source_config: Configuração da fonte
            
        Returns:
            True se configuração é válida
        """
        try:
            # Campos obrigatórios
            required_fields = ['name', 'url', 'region', 'source_type']
            
            for field in required_fields:
                if field not in source_config:
                    logger.error(f"Campo obrigatório ausente: {field}")
                    return False
            
            # Valida tipo de fonte
            source_type = source_config.get('source_type')
            if source_type not in ScraperFactory.get_supported_types():
                logger.error(f"Tipo de fonte não suportado: {source_type}")
                return False
            
            # Validações específicas por tipo
            if source_type == 'rss':
                # Para RSS, deve ter rss_url ou url deve ser um feed
                if not source_config.get('rss_url') and not source_config.get('url'):
                    logger.error("RSS scraper requer rss_url ou url")
                    return False
            
            elif source_type == 'web_scraping':
                # Para web scraping, deve ter seletores ou usar padrões
                selectors = source_config.get('selectors', {})
                if not selectors:
                    logger.warning(f"Web scraper sem seletores específicos: {source_config.get('name')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Erro ao validar configuração: {e}")
            return False


