"""
Scraper para RSS feeds
"""

import feedparser
from typing import List, Dict, Any
from datetime import datetime
import time

from .base_scraper import BaseScraper
from src.models import ScrapingResult
from src.utils.logger import get_logger

logger = get_logger("rss_scraper")


class RSScraper(BaseScraper):
    """Scraper para RSS feeds"""
    
    def __init__(self, source_config: Dict[str, Any]):
        """
        Inicializa o RSS scraper
        
        Args:
            source_config: Configuração da fonte RSS
        """
        super().__init__(source_config)
        
        # URL do RSS feed (pode ser diferente da URL principal)
        self.rss_url = source_config.get('rss_url', self.url)
        
        logger.info(f"RSS Scraper inicializado para {self.name}")
        logger.debug(f"RSS URL: {self.rss_url}")
    
    def scrape(self) -> ScrapingResult:
        """
        Executa scraping do RSS feed
        
        Returns:
            Resultado do scraping
        """
        start_time = time.time()
        articles = []
        error_message = ""
        
        try:
            logger.info(f"Iniciando scraping RSS para {self.name}")
            
            # Faz download do RSS feed
            response = self._make_request(self.rss_url)
            
            if not response:
                error_message = f"Falha ao acessar RSS feed: {self.rss_url}"
                logger.error(error_message)
                return ScrapingResult(
                    source=self.name,
                    success=False,
                    articles_found=0,
                    error_message=error_message,
                    execution_time=time.time() - start_time
                )
            
            # Parseia o RSS feed
            feed = feedparser.parse(response.content)
            
            if feed.bozo:
                logger.warning(f"RSS feed pode ter problemas de formato: {self.name}")
            
            logger.info(f"RSS feed parseado: {len(feed.entries)} entradas encontradas")
            
            # Processa cada entrada do feed
            for entry in feed.entries[:self.max_articles]:
                try:
                    raw_article = self._extract_article_from_entry(entry)
                    
                    if raw_article:
                        article = self._process_article(raw_article)
                        if article:
                            articles.append(article)
                            logger.debug(f"Artigo RSS processado: {article.title}")
                
                except Exception as e:
                    logger.error(f"Erro ao processar entrada RSS: {e}")
                    continue
            
            execution_time = time.time() - start_time
            
            logger.info(f"Scraping RSS concluído para {self.name}: "
                       f"{len(articles)} artigos válidos de {len(feed.entries)} entradas "
                       f"em {execution_time:.2f}s")
            
            return ScrapingResult(
                source=self.name,
                success=True,
                articles_found=len(articles),
                articles=articles,
                execution_time=execution_time
            )
            
        except Exception as e:
            error_message = f"Erro durante scraping RSS: {e}"
            logger.error(error_message)
            
            return ScrapingResult(
                source=self.name,
                success=False,
                articles_found=0,
                error_message=error_message,
                execution_time=time.time() - start_time
            )
    
    def _extract_article_from_entry(self, entry) -> Dict[str, Any]:
        """
        Extrai dados do artigo de uma entrada RSS
        
        Args:
            entry: Entrada do feed RSS
            
        Returns:
            Dicionário com dados do artigo
        """
        try:
            # Extrai título
            title = getattr(entry, 'title', '')
            
            # Extrai URL
            url = getattr(entry, 'link', '')
            
            # Extrai resumo/descrição
            summary = getattr(entry, 'summary', '') or getattr(entry, 'description', '')
            
            # Extrai conteúdo completo se disponível
            content = ''
            if hasattr(entry, 'content'):
                if isinstance(entry.content, list) and entry.content:
                    content = entry.content[0].get('value', '')
                else:
                    content = str(entry.content)
            
            # Se não tem conteúdo, usa o summary
            if not content:
                content = summary
            
            # Extrai data de publicação
            date_published = self._extract_date_from_entry(entry)
            
            # Extrai categorias/tags se disponíveis
            categories = []
            if hasattr(entry, 'tags'):
                categories = [tag.term for tag in entry.tags if hasattr(tag, 'term')]
            
            # Extrai autor se disponível
            author = getattr(entry, 'author', '')
            
            return {
                'title': title,
                'url': url,
                'summary': summary,
                'content': content,
                'date_published': date_published,
                'categories': categories,
                'author': author
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados da entrada RSS: {e}")
            return {}
    
    def _extract_date_from_entry(self, entry) -> datetime:
        """
        Extrai data de publicação da entrada RSS
        
        Args:
            entry: Entrada do feed RSS
            
        Returns:
            Data de publicação
        """
        # Tenta diferentes campos de data
        date_fields = ['published_parsed', 'updated_parsed', 'created_parsed']
        
        for field in date_fields:
            if hasattr(entry, field):
                time_struct = getattr(entry, field)
                if time_struct:
                    try:
                        return datetime(*time_struct[:6])
                    except (ValueError, TypeError):
                        continue
        
        # Tenta campos de string
        string_date_fields = ['published', 'updated', 'created']
        
        for field in string_date_fields:
            if hasattr(entry, field):
                date_str = getattr(entry, field)
                if date_str:
                    try:
                        return self._parse_date(date_str)
                    except:
                        continue
        
        # Se não encontrou data, usa data atual
        logger.warning(f"Data não encontrada para entrada RSS: {getattr(entry, 'title', 'Unknown')}")
        return datetime.now()
    
    def get_feed_info(self) -> Dict[str, Any]:
        """
        Obtém informações sobre o feed RSS
        
        Returns:
            Informações do feed
        """
        try:
            response = self._make_request(self.rss_url)
            if not response:
                return {}
            
            feed = feedparser.parse(response.content)
            
            return {
                'title': getattr(feed.feed, 'title', ''),
                'description': getattr(feed.feed, 'description', ''),
                'link': getattr(feed.feed, 'link', ''),
                'language': getattr(feed.feed, 'language', ''),
                'last_updated': getattr(feed.feed, 'updated', ''),
                'total_entries': len(feed.entries),
                'version': feed.version
            }
            
        except Exception as e:
            logger.error(f"Erro ao obter informações do feed: {e}")
            return {}

