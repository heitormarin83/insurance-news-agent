"""
Modelos de dados para o sistema de notícias de seguros
"""

from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional
from enum import Enum


class Region(Enum):
    """Regiões de cobertura de notícias"""
    BRASIL = "Brasil"
    AMERICA_SUL = "América do Sul"
    EUA = "Estados Unidos"
    EUROPA = "Europa"


class Priority(Enum):
    """Níveis de prioridade das notícias"""
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class SourceType(Enum):
    """Tipos de fonte de notícias"""
    RSS = "rss"
    WEB_SCRAPING = "web_scraping"
    API = "api"


@dataclass
class NewsSource:
    """Configuração de uma fonte de notícias"""
    name: str
    url: str
    region: Region
    source_type: SourceType
    priority: Priority
    update_frequency_hours: int = 2
    selectors: Optional[dict] = None
    headers: Optional[dict] = None
    enabled: bool = True


@dataclass
class NewsArticle:
    """Artigo de notícia coletado"""
    title: str
    url: str
    source: str
    region: Region
    date_published: datetime
    summary: str = ""
    content: str = ""
    categories: List[str] = field(default_factory=list)
    relevance_score: float = 0.0
    open_insurance_related: bool = False
    language: str = "pt"
    
    def __post_init__(self):
        """Validações após inicialização"""
        if not self.title:
            raise ValueError("Título é obrigatório")
        if not self.url:
            raise ValueError("URL é obrigatória")
        if not self.source:
            raise ValueError("Fonte é obrigatória")


@dataclass
class DailyReport:
    """Relatório diário consolidado"""
    date: datetime
    total_articles: int
    articles_by_region: dict
    top_articles: List[NewsArticle]
    open_insurance_articles: List[NewsArticle]
    summary: str = ""
    
    def __post_init__(self):
        """Calcular estatísticas após inicialização"""
        if not self.articles_by_region:
            self.articles_by_region = {}
        
        # Calcular total se não fornecido
        if self.total_articles == 0:
            self.total_articles = sum(self.articles_by_region.values())


@dataclass
class ScrapingResult:
    """Resultado de uma operação de scraping"""
    source: str
    success: bool
    articles_found: int
    articles: List[NewsArticle] = field(default_factory=list)
    error_message: str = ""
    execution_time: float = 0.0
    timestamp: datetime = field(default_factory=datetime.now)


@dataclass
class EmailConfig:
    """Configuração para envio de e-mails"""
    smtp_server: str
    smtp_port: int
    sender_email: str
    sender_password: str
    recipient_emails: List[str]
    use_tls: bool = True
    
    def __post_init__(self):
        """Validações de configuração de e-mail"""
        if not self.recipient_emails:
            raise ValueError("Lista de destinatários não pode estar vazia")
        if "@" not in self.sender_email:
            raise ValueError("E-mail do remetente inválido")


# Constantes para categorização
OPEN_INSURANCE_KEYWORDS = [
    "open insurance", "open banking", "seguros abertos", "sistema de seguros aberto",
    "opin", "apis de seguros", "compartilhamento de dados", "fida", "eiopa",
    "dados abertos seguros", "interoperabilidade seguros"
]

HIGH_PRIORITY_KEYWORDS = [
    "regulamentação", "susep", "cnseg", "lei de seguros", "nova lei",
    "circular susep", "resolução", "normativa", "compliance",
    "open insurance", "transformação digital", "insurtech"
]

INSURANCE_KEYWORDS = [
    "seguro", "seguros", "insurance", "assurance", "apólice", "sinistro",
    "prêmio", "resseguro", "corretora", "seguradora", "insurtech",
    "proteção", "cobertura", "indenização", "subscrição"
]

