"""
Sistema de deduplicação de artigos para o Insurance News Agent
Evita que artigos já enviados apareçam novamente em relatórios futuros
"""

import json
import hashlib
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Set, Dict, Any
from dataclasses import dataclass

from src.models import NewsArticle
from src.utils.logger import get_logger

logger = get_logger("deduplication_manager")

@dataclass
class ArticleFingerprint:
    """Impressão digital de um artigo para deduplicação"""
    url_hash: str
    title_hash: str
    content_hash: str
    date_sent: datetime
    source: str
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'url_hash': self.url_hash,
            'title_hash': self.title_hash,
            'content_hash': self.content_hash,
            'date_sent': self.date_sent.isoformat(),
            'source': self.source
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ArticleFingerprint':
        return cls(
            url_hash=data['url_hash'],
            title_hash=data['title_hash'],
            content_hash=data['content_hash'],
            date_sent=datetime.fromisoformat(data['date_sent']),
            source=data['source']
        )


class DeduplicationManager:
    """
    Gerenciador de deduplicação de artigos
    Mantém histórico de artigos já enviados para evitar repetições
    """
    
    def __init__(self, storage_dir: str = "data/deduplication"):
        """
        Inicializa o gerenciador de deduplicação
        
        Args:
            storage_dir: Diretório para armazenar dados de deduplicação
        """
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        
        self.fingerprints_file = self.storage_dir / "sent_articles.json"
        self.sent_articles: Dict[str, ArticleFingerprint] = {}
        
        self.logger = logger
        self._load_sent_articles()
        
        self.logger.info(f"Deduplication Manager inicializado - {len(self.sent_articles)} artigos no histórico")
    
    def _load_sent_articles(self):
        """Carrega histórico de artigos já enviados"""
        if not self.fingerprints_file.exists():
            self.logger.info("Nenhum histórico de deduplicação encontrado - iniciando novo")
            return
        
        try:
            with open(self.fingerprints_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for key, fingerprint_data in data.items():
                self.sent_articles[key] = ArticleFingerprint.from_dict(fingerprint_data)
            
            self.logger.info(f"Carregado histórico de {len(self.sent_articles)} artigos enviados")
            
        except Exception as e:
            self.logger.error(f"Erro ao carregar histórico de deduplicação: {e}")
            self.sent_articles = {}
    
    def _save_sent_articles(self):
        """Salva histórico de artigos enviados"""
        try:
            data = {key: fingerprint.to_dict() for key, fingerprint in self.sent_articles.items()}
            
            with open(self.fingerprints_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            
            self.logger.debug(f"Histórico de deduplicação salvo - {len(self.sent_articles)} artigos")
            
        except Exception as e:
            self.logger.error(f"Erro ao salvar histórico de deduplicação: {e}")
    
    def _generate_fingerprint(self, article: NewsArticle) -> ArticleFingerprint:
        """
        Gera impressão digital de um artigo
        
        Args:
            article: Artigo para gerar fingerprint
            
        Returns:
            Fingerprint do artigo
        """
        # Hash da URL (identificador principal)
        url_hash = hashlib.md5(article.url.encode('utf-8')).hexdigest()
        
        # Hash do título (para detectar títulos similares)
        title_normalized = article.title.lower().strip()
        title_hash = hashlib.md5(title_normalized.encode('utf-8')).hexdigest()
        
        # Hash do conteúdo (título + resumo)
        content = f"{article.title} {article.summary}".lower().strip()
        content_hash = hashlib.md5(content.encode('utf-8')).hexdigest()
        
        return ArticleFingerprint(
            url_hash=url_hash,
            title_hash=title_hash,
            content_hash=content_hash,
            date_sent=datetime.now(),
            source=article.source
        )
    
    def _is_duplicate(self, article: NewsArticle) -> bool:
        """
        Verifica se um artigo é duplicado
        
        Args:
            article: Artigo para verificar
            
        Returns:
            True se for duplicado, False caso contrário
        """
        fingerprint = self._generate_fingerprint(article)
        
        # Verifica duplicação por URL (mais restritivo)
        url_key = f"url_{fingerprint.url_hash}"
        if url_key in self.sent_articles:
            self.logger.debug(f"Artigo duplicado por URL: {article.title[:50]}...")
            return True
        
        # Verifica duplicação por título (menos restritivo)
        title_key = f"title_{fingerprint.title_hash}"
        if title_key in self.sent_articles:
            # Verifica se é da mesma fonte (evita falsos positivos)
            existing = self.sent_articles[title_key]
            if existing.source == article.source:
                self.logger.debug(f"Artigo duplicado por título: {article.title[:50]}...")
                return True
        
        return False
    
    def filter_duplicates(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """
        Filtra artigos duplicados de uma lista
        
        Args:
            articles: Lista de artigos para filtrar
            
        Returns:
            Lista de artigos únicos (não duplicados)
        """
        if not articles:
            return articles
        
        unique_articles = []
        duplicates_count = 0
        
        for article in articles:
            if not self._is_duplicate(article):
                unique_articles.append(article)
            else:
                duplicates_count += 1
        
        self.logger.info(f"Filtrados {duplicates_count} artigos duplicados de {len(articles)} total")
        self.logger.info(f"Restaram {len(unique_articles)} artigos únicos")
        
        return unique_articles
    
    def mark_as_sent(self, articles: List[NewsArticle]):
        """
        Marca artigos como enviados (adiciona ao histórico)
        
        Args:
            articles: Lista de artigos que foram enviados
        """
        if not articles:
            return
        
        added_count = 0
        
        for article in articles:
            fingerprint = self._generate_fingerprint(article)
            
            # Adiciona por URL
            url_key = f"url_{fingerprint.url_hash}"
            if url_key not in self.sent_articles:
                self.sent_articles[url_key] = fingerprint
                added_count += 1
            
            # Adiciona por título
            title_key = f"title_{fingerprint.title_hash}"
            if title_key not in self.sent_articles:
                self.sent_articles[title_key] = fingerprint
        
        # Salva histórico atualizado
        self._save_sent_articles()
        
        self.logger.info(f"Marcados {added_count} novos artigos como enviados")
        self.logger.info(f"Total no histórico: {len(self.sent_articles)} fingerprints")
    
    def cleanup_old_entries(self, days_to_keep: int = 30):
        """
        Remove entradas antigas do histórico
        
        Args:
            days_to_keep: Número de dias para manter no histórico
        """
        cutoff_date = datetime.now() - timedelta(days=days_to_keep)
        
        old_keys = []
        for key, fingerprint in self.sent_articles.items():
            if fingerprint.date_sent < cutoff_date:
                old_keys.append(key)
        
        for key in old_keys:
            del self.sent_articles[key]
        
        if old_keys:
            self._save_sent_articles()
            self.logger.info(f"Removidas {len(old_keys)} entradas antigas do histórico")
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do sistema de deduplicação
        
        Returns:
            Dicionário com estatísticas
        """
        if not self.sent_articles:
            return {
                'total_sent': 0,
                'sources': {},
                'oldest_entry': None,
                'newest_entry': None
            }
        
        # Conta por fonte
        sources = {}
        dates = []
        
        for fingerprint in self.sent_articles.values():
            source = fingerprint.source
            sources[source] = sources.get(source, 0) + 1
            dates.append(fingerprint.date_sent)
        
        return {
            'total_sent': len(self.sent_articles),
            'sources': sources,
            'oldest_entry': min(dates).isoformat() if dates else None,
            'newest_entry': max(dates).isoformat() if dates else None
        }
