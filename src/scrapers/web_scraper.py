"""
Scraper para web scraping de sites HTML
"""

from bs4 import BeautifulSoup
from typing import List, Dict, Any, Optional
from datetime import datetime
import time
import re
from urllib.parse import urljoin, urlparse

from .base_scraper import BaseScraper
from src.models import ScrapingResult
from src.utils.logger import get_logger

logger = get_logger("web_scraper")


class WebScraper(BaseScraper):
    """Scraper para sites HTML estáticos"""
    
    def __init__(self, source_config: Dict[str, Any]):
        """
        Inicializa o web scraper
        
        Args:
            source_config: Configuração da fonte web
        """
        super().__init__(source_config)
        
        # Seletores CSS para extração de dados
        self.selectors = source_config.get('selectors', {})
        
        # Configurações específicas de scraping
        self.follow_pagination = source_config.get('follow_pagination', False)
        self.max_pages = source_config.get('max_pages', 3)
        
        logger.info(f"Web Scraper inicializado para {self.name}")
        logger.debug(f"Seletores configurados: {self.selectors}")
    
    def scrape(self) -> ScrapingResult:
        """
        Executa web scraping do site
        
        Returns:
            Resultado do scraping
        """
        start_time = time.time()
        articles = []
        error_message = ""
        
        try:
            logger.info(f"Iniciando web scraping para {self.name}")
            
            # Lista de URLs para processar (começando com a URL principal)
            urls_to_process = [self.url]
            processed_urls = set()
            
            # Processa URLs (com paginação se habilitada)
            for page_num, url in enumerate(urls_to_process):
                if page_num >= self.max_pages:
                    break
                
                if url in processed_urls:
                    continue
                
                processed_urls.add(url)
                
                logger.debug(f"Processando página {page_num + 1}: {url}")
                
                # Faz requisição para a página
                response = self._make_request(url)
                
                if not response:
                    logger.warning(f"Falha ao acessar página: {url}")
                    continue
                
                # Parseia HTML
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Extrai artigos da página
                page_articles = self._extract_articles_from_page(soup, url)
                articles.extend(page_articles)
                
                logger.debug(f"Extraídos {len(page_articles)} artigos da página {page_num + 1}")
                
                # Busca próxima página se paginação habilitada
                if self.follow_pagination and page_num < self.max_pages - 1:
                    next_url = self._find_next_page_url(soup, url)
                    if next_url and next_url not in processed_urls:
                        urls_to_process.append(next_url)
                
                # Aplica delay entre páginas
                if page_num < len(urls_to_process) - 1:
                    self._delay_request()
            
            # Limita número de artigos
            articles = articles[:self.max_articles]
            
            execution_time = time.time() - start_time
            
            logger.info(f"Web scraping concluído para {self.name}: "
                       f"{len(articles)} artigos extraídos de {len(processed_urls)} páginas "
                       f"em {execution_time:.2f}s")
            
            return ScrapingResult(
                source=self.name,
                success=True,
                articles_found=len(articles),
                articles=articles,
                execution_time=execution_time
            )
            
        except Exception as e:
            error_message = f"Erro durante web scraping: {e}"
            logger.error(error_message)
            
            return ScrapingResult(
                source=self.name,
                success=False,
                articles_found=0,
                error_message=error_message,
                execution_time=time.time() - start_time
            )
    
    def _extract_articles_from_page(self, soup: BeautifulSoup, base_url: str) -> List[Dict[str, Any]]:
        """
        Extrai artigos de uma página HTML
        
        Args:
            soup: Objeto BeautifulSoup da página
            base_url: URL base para resolver links relativos
            
        Returns:
            Lista de artigos extraídos
        """
        articles = []
        
        try:
            # Busca elementos de artigos
            article_selector = self.selectors.get('articles', 'article, .post, .news-item')
            article_elements = soup.select(article_selector)
            
            logger.debug(f"Encontrados {len(article_elements)} elementos de artigo")
            
            for element in article_elements:
                try:
                    article_data = self._extract_article_data(element, base_url)
                    
                    if article_data and article_data.get('title') and article_data.get('url'):
                        # Processa o artigo
                        processed_article = self._process_article(article_data)
                        if processed_article:
                            articles.append(processed_article)
                
                except Exception as e:
                    logger.error(f"Erro ao extrair artigo individual: {e}")
                    continue
            
        except Exception as e:
            logger.error(f"Erro ao extrair artigos da página: {e}")
        
        return articles
    
    def _extract_article_data(self, element, base_url: str) -> Dict[str, Any]:
        """
        Extrai dados de um elemento de artigo
        
        Args:
            element: Elemento HTML do artigo
            base_url: URL base para resolver links
            
        Returns:
            Dicionário com dados do artigo
        """
        try:
            # Extrai título
            title = self._extract_text_by_selector(element, self.selectors.get('title', 'h1, h2, h3, .title'))
            
            # Extrai URL
            url = self._extract_link_by_selector(element, self.selectors.get('link', 'a'))
            if url:
                url = urljoin(base_url, url)
            
            # Extrai resumo
            summary = self._extract_text_by_selector(element, self.selectors.get('summary', '.summary, .excerpt, p'))
            
            # Extrai data
            date_str = self._extract_text_by_selector(element, self.selectors.get('date', '.date, .published, time'))
            date_published = self._parse_date(date_str) if date_str else datetime.now()
            
            # Extrai autor se disponível
            author = self._extract_text_by_selector(element, self.selectors.get('author', '.author, .by'))
            
            # Extrai categoria se disponível
            category = self._extract_text_by_selector(element, self.selectors.get('category', '.category, .tag'))
            
            return {
                'title': title,
                'url': url,
                'summary': summary,
                'content': summary,  # Para web scraping básico, usa summary como content
                'date_published': date_published,
                'author': author,
                'category': category
            }
            
        except Exception as e:
            logger.error(f"Erro ao extrair dados do elemento: {e}")
            return {}
    
    def _extract_text_by_selector(self, element, selector: str) -> str:
        """
        Extrai texto usando seletor CSS
        
        Args:
            element: Elemento HTML
            selector: Seletor CSS
            
        Returns:
            Texto extraído
        """
        try:
            found_element = element.select_one(selector)
            if found_element:
                return found_element.get_text(strip=True)
        except Exception as e:
            logger.debug(f"Erro ao extrair texto com seletor '{selector}': {e}")
        
        return ""
    
    def _extract_link_by_selector(self, element, selector: str) -> str:
        """
        Extrai link usando seletor CSS
        
        Args:
            element: Elemento HTML
            selector: Seletor CSS
            
        Returns:
            URL extraída
        """
        try:
            found_element = element.select_one(selector)
            if found_element:
                return found_element.get('href', '')
        except Exception as e:
            logger.debug(f"Erro ao extrair link com seletor '{selector}': {e}")
        
        return ""
    
    def _find_next_page_url(self, soup: BeautifulSoup, current_url: str) -> Optional[str]:
        """
        Busca URL da próxima página
        
        Args:
            soup: Objeto BeautifulSoup da página atual
            current_url: URL da página atual
            
        Returns:
            URL da próxima página ou None
        """
        try:
            # Seletores comuns para próxima página
            next_selectors = [
                'a[rel="next"]',
                '.next a',
                '.pagination .next',
                'a:contains("Próxima")',
                'a:contains("Next")',
                'a:contains(">")'
            ]
            
            for selector in next_selectors:
                try:
                    next_element = soup.select_one(selector)
                    if next_element and next_element.get('href'):
                        next_url = urljoin(current_url, next_element['href'])
                        logger.debug(f"Próxima página encontrada: {next_url}")
                        return next_url
                except:
                    continue
            
        except Exception as e:
            logger.debug(f"Erro ao buscar próxima página: {e}")
        
        return None
    
    def scrape_article_content(self, article_url: str) -> str:
        """
        Faz scraping do conteúdo completo de um artigo
        
        Args:
            article_url: URL do artigo
            
        Returns:
            Conteúdo completo do artigo
        """
        try:
            logger.debug(f"Fazendo scraping do conteúdo: {article_url}")
            
            response = self._make_request(article_url)
            if not response:
                return ""
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Seletores comuns para conteúdo de artigo
            content_selectors = [
                '.content',
                '.article-content',
                '.post-content',
                '.entry-content',
                'article .text',
                '.news-content',
                'main article'
            ]
            
            for selector in content_selectors:
                content_element = soup.select_one(selector)
                if content_element:
                    # Remove elementos indesejados
                    for unwanted in content_element.select('script, style, .ads, .advertisement'):
                        unwanted.decompose()
                    
                    content = content_element.get_text(separator=' ', strip=True)
                    if len(content) > 100:  # Só retorna se tem conteúdo substancial
                        return content
            
            # Se não encontrou com seletores específicos, tenta extrair do body
            body = soup.find('body')
            if body:
                # Remove elementos indesejados
                for unwanted in body.select('script, style, nav, header, footer, .sidebar, .ads'):
                    unwanted.decompose()
                
                content = body.get_text(separator=' ', strip=True)
                return content[:5000]  # Limita tamanho
            
        except Exception as e:
            logger.error(f"Erro ao fazer scraping do conteúdo: {e}")
        
        return ""
    
    def test_selectors(self) -> Dict[str, Any]:
        """
        Testa os seletores configurados na página principal
        
        Returns:
            Resultado dos testes
        """
        try:
            response = self._make_request(self.url)
            if not response:
                return {'error': 'Falha ao acessar página'}
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            results = {}
            
            for selector_name, selector in self.selectors.items():
                elements = soup.select(selector)
                results[selector_name] = {
                    'selector': selector,
                    'found_elements': len(elements),
                    'sample_text': elements[0].get_text(strip=True)[:100] if elements else None
                }
            
            return results
            
        except Exception as e:
            return {'error': f'Erro ao testar seletores: {e}'}

