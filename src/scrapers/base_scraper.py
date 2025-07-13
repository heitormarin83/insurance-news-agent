"""
Classe base para todos os scrapers de notícias
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import time
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from src.models import NewsArticle, NewsSource, ScrapingResult, Region
from src.utils.logger import get_logger
from src.utils.text_processor import text_processor

logger = get_logger("base_scraper")


class BaseScraper(ABC):
    """Classe base para todos os scrapers"""
    
    def __init__(self, source_config: Dict[str, Any]):
        """
        Inicializa o scraper base
        
        Args:
            source_config: Configuração da fonte de notícias
        """
        self.config = source_config
        self.name = source_config.get('name', 'Unknown')
        self.url = source_config.get('url', '')
        self.region = Region(source_config.get('region', 'Brasil'))
        self.priority = source_config.get('priority', 'medium')
        self.enabled = source_config.get('enabled', True)
        self.max_articles = source_config.get('max_articles', 50)
        self.max_age_days = source_config.get('max_age_days', 7)
        
        # Configurações de request
        self.timeout = source_config.get('timeout', 30)
        self.retry_attempts = source_config.get('retry_attempts', 3)
        self.delay_between_requests = source_config.get('delay_between_requests', 2)
        
        # Headers padrão
        self.headers = {
            'User-Agent': source_config.get('user_agent', 
                'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'),
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'pt-BR,pt;q=0.9,en;q=0.8',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        # Adiciona headers customizados se fornecidos
        custom_headers = source_config.get('headers', {})
        self.headers.update(custom_headers)
        
        # Configura sessão HTTP com retry
        self.session = self._create_session()
        
        logger.info(f"Scraper inicializado para {self.name} ({self.region.value})")
    
    def _create_session(self) -> requests.Session:
        """
        Cria sessão HTTP com configurações de retry
        
        Returns:
            Sessão HTTP configurada
        """
        session = requests.Session()
        
        # Configura retry strategy
        retry_strategy = Retry(
            total=self.retry_attempts,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
            allowed_methods=["HEAD", "GET", "OPTIONS"]
        )
        
        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        
        # Define headers padrão
        session.headers.update(self.headers)
        
        return session
    
    def _make_request(self, url: str, **kwargs) -> Optional[requests.Response]:
        """
        Faz requisição HTTP com tratamento de erros
        
        Args:
            url: URL para requisição
            **kwargs: Argumentos adicionais para requests
            
        Returns:
            Response object ou None se erro
        """
        try:
            logger.debug(f"Fazendo requisição para: {url}")
            
            response = self.session.get(
                url,
                timeout=self.timeout,
                **kwargs
            )
            
            response.raise_for_status()
            
            logger.debug(f"Requisição bem-sucedida: {response.status_code}")
            return response
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Erro na requisição para {url}: {e}")
            return None
    
    def _is_article_recent(self, article_date: datetime) -> bool:
        """
        Verifica se artigo está dentro do período de interesse
        
        Args:
            article_date: Data do artigo
            
        Returns:
            True se artigo é recente
        """
        if not article_date:
            return True  # Se não tem data, considera recente
        
        cutoff_date = datetime.now() - timedelta(days=self.max_age_days)
        return article_date >= cutoff_date
    
    def _process_article(self, raw_article: Dict[str, Any]) -> Optional[NewsArticle]:
        """
        Processa artigo bruto em NewsArticle
        
        Args:
            raw_article: Dados brutos do artigo
            
        Returns:
            NewsArticle processado ou None se inválido
        """
        try:
            # Extrai dados básicos
            title = text_processor.clean_text(raw_article.get('title', ''))
            url = raw_article.get('url', '')
            summary = text_processor.clean_text(raw_article.get('summary', ''))
            content = text_processor.clean_text(raw_article.get('content', ''))
            
            # Valida dados obrigatórios
            if not title or not url:
                logger.warning(f"Artigo inválido - título ou URL ausente: {raw_article}")
                return None
            
            # Processa data
            date_published = raw_article.get('date_published')
            if isinstance(date_published, str):
                # Tenta parsear string de data
                date_published = self._parse_date(date_published)
            elif not isinstance(date_published, datetime):
                date_published = datetime.now()
            
            # Verifica se artigo é recente
            if not self._is_article_recent(date_published):
                logger.debug(f"Artigo muito antigo, ignorando: {title}")
                return None
            
            # Verifica se é relacionado a seguros
            if not text_processor.is_insurance_related(title, content):
                logger.debug(f"Artigo não relacionado a seguros, ignorando: {title}")
                return None
            
            # Cria NewsArticle
            article = NewsArticle(
                title=title,
                url=url,
                source=self.name,
                region=self.region,
                date_published=date_published,
                summary=summary or text_processor.extract_summary(content),
                content=content,
                categories=text_processor.categorize_article(title, content),
                relevance_score=text_processor.calculate_relevance_score(title, content),
                open_insurance_related=text_processor.is_open_insurance_related(title, content),
                language=raw_article.get('language', 'pt' if self.region == Region.BRASIL else 'en')
            )
            
            logger.debug(f"Artigo processado: {title} (score: {article.relevance_score:.2f})")
            return article
            
        except Exception as e:
            logger.error(f"Erro ao processar artigo: {e}")
            return None
    
    def _parse_date(self, date_str: str) -> datetime:
        """
        Tenta parsear string de data em datetime
        
        Args:
            date_str: String de data
            
        Returns:
            Objeto datetime
        """
        # Formatos comuns de data
        date_formats = [
            '%Y-%m-%d %H:%M:%S',
            '%Y-%m-%d',
            '%d/%m/%Y %H:%M:%S',
            '%d/%m/%Y',
            '%d de %B de %Y',
            '%B %d, %Y',
            '%Y-%m-%dT%H:%M:%S',
            '%Y-%m-%dT%H:%M:%SZ',
        ]
        
        # Mapeamento de meses em português
        month_mapping = {
            'janeiro': 'January', 'fevereiro': 'February', 'março': 'March',
            'abril': 'April', 'maio': 'May', 'junho': 'June',
            'julho': 'July', 'agosto': 'August', 'setembro': 'September',
            'outubro': 'October', 'novembro': 'November', 'dezembro': 'December'
        }
        
        # Substitui meses em português
        date_str_en = date_str.lower()
        for pt_month, en_month in month_mapping.items():
            date_str_en = date_str_en.replace(pt_month, en_month)
        
        # Tenta parsear com diferentes formatos
        for fmt in date_formats:
            try:
                return datetime.strptime(date_str_en, fmt)
            except ValueError:
                continue
        
        # Se não conseguiu parsear, retorna data atual
        logger.warning(f"Não foi possível parsear data: {date_str}")
        return datetime.now()
    
    def _delay_request(self):
        """Aplica delay entre requisições"""
        if self.delay_between_requests > 0:
            time.sleep(self.delay_between_requests)
    
    @abstractmethod
    def scrape(self) -> ScrapingResult:
        """
        Método abstrato para scraping
        
        Returns:
            Resultado do scraping
        """
        pass
    
    def is_enabled(self) -> bool:
        """
        Verifica se o scraper está habilitado
        
        Returns:
            True se habilitado
        """
        return self.enabled
    
    def get_source_info(self) -> Dict[str, Any]:
        """
        Retorna informações da fonte
        
        Returns:
            Dicionário com informações da fonte
        """
        return {
            'name': self.name,
            'url': self.url,
            'region': self.region.value,
            'priority': self.priority,
            'enabled': self.enabled,
            'max_articles': self.max_articles,
            'max_age_days': self.max_age_days
        }

