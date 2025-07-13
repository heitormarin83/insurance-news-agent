"""
Módulo de scrapers para coleta de notícias de seguros
"""

from .base_scraper import BaseScraper
from .rss_scraper import RSScraper
from .web_scraper import WebScraper
from .scraper_factory import ScraperFactory

__all__ = ['BaseScraper', 'RSScraper', 'WebScraper', 'ScraperFactory']

