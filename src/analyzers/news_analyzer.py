"""
Analisador de notícias para o Insurance News Agent
Versão corrigida - com loguru e imports completos
"""

import re
import yaml
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter, defaultdict
from pathlib import Path
from datetime import datetime

from ..models import NewsArticle
from src.utils.logger import get_logger

class NewsAnalyzer:
    """Analisador de relevância e categorização de notícias de seguros"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Inicializa o analisador de notícias
        
        Args:
            config_path: Caminho para arquivo de configuração (opcional)
        """
        self.logger = get_logger("news_analyzer")
        
        # Carregar configuração
        if config_path:
            self.config = self._load_config(config_path)
        else:
            # Tentar carregar configuração padrão
            default_config_path = Path(__file__).parent.parent.parent / 'config' / 'news_analyzer_config.yaml'
            if default_config_path.exists():
                self.config = self._load_config(str(default_config_path))
            else:
                self.logger.warning("Arquivo de configuração não encontrado. Usando configuração padrão.")
                self.config = self._get_default_config()
        
        # Extrair configurações
        self.weights = self.config.get('weights', {})
        self.insurance_keywords = self.config.get('insurance_keywords', {})
        self.open_insurance_keywords = self.config.get('open_insurance_keywords', [])
        self.irrelevant_keywords = self.config.get('irrelevant_keywords', [])
        self.min_relevance_score = self.config.get('min_relevance_score', 0.3)
        
        self.logger.info("NewsAnalyzer inicializado com configuração externa")
    
    def _load_config(self, path: str) -> Dict[str, Any]:
        """
        Carrega configuração de arquivo YAML
        
        Args:
            path: Caminho para o arquivo de configuração
            
        Returns:
            Dict: Configuração carregada
        """
        try:
            with open(path, 'r', encoding='utf-8') as file:
                config = yaml.safe_load(file)
                self.logger.info(f"Configuração carregada de: {path}")
                return config
        except FileNotFoundError:
            self.logger.warning(f"Arquivo de configuração não encontrado: {path}. Usando configuração padrão.")
            return self._get_default_config()
        except Exception as e:
            self.logger.error(f"Erro ao carregar configuração: {e}. Usando configuração padrão.")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """
        Retorna configuração padrão caso arquivo não seja encontrado
        
        Returns:
            Dict: Configuração padrão
        """
        return {
            'weights': {
                'title': 0.4,
                'summary': 0.3,
                'content': 0.2,
                'source_priority': 0.1
            },
            'insurance_keywords': {
                'high_priority': [
                    'seguro', 'seguros', 'seguradora', 'seguradoras', 'insurance',
                    'apólice', 'sinistro', 'prêmio', 'cobertura', 'indenização',
                    'resseguro', 'corretora', 'corretor', 'susep', 'cnseg'
                ],
                'medium_priority': [
                    'risco', 'proteção', 'garantia', 'benefício', 'claim',
                    'underwriting', 'atuarial', 'regulamentação', 'compliance'
                ],
                'low_priority': [
                    'financeiro', 'investimento', 'economia', 'mercado',
                    'negócio', 'empresa', 'setor', 'indústria'
                ]
            },
            'open_insurance_keywords': [
                'open insurance', 'open banking', 'apis', 'integração',
                'plataforma digital', 'ecossistema', 'interoperabilidade',
                'dados abertos', 'compartilhamento', 'conectividade'
            ],
            'irrelevant_keywords': [
                'horóscopo', 'esporte', 'celebridade', 'fofoca',
                'receita culinária', 'moda', 'beleza', 'entretenimento'
            ],
            'min_relevance_score': 0.3,
            'source_priorities': {
                'high': 1.0,
                'medium': 0.8,
                'low': 0.6
            }
        }
    
    def analyze_articles(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        Analisa uma lista de artigos e retorna estatísticas
        
        Args:
            articles: Lista de artigos para analisar
            
        Returns:
            Dict: Estatísticas da análise
        """
        if not articles:
            self.logger.warning("Nenhum artigo fornecido para análise")
            return {
                'total_articles': 0,
                'relevant_articles': 0,
                'open_insurance_articles': 0,
                'top_keywords': [],
                'articles_by_region': {},
                'relevance_distribution': {}
            }
        
        # Calcular scores de relevância
        for article in articles:
            article.relevance_score = self.calculate_relevance_score(article)
        
        # Filtrar artigos relevantes
        relevant_articles = [art for art in articles if art.relevance_score >= self.min_relevance_score]
        
        # Identificar artigos Open Insurance
        open_insurance_articles = [art for art in relevant_articles if self.is_open_insurance(art)]
        
        # Extrair palavras-chave
        all_text = ' '.join([
            f"{art.title} {art.summary or ''} {art.content or ''}"
            for art in relevant_articles
        ])
        top_keywords = self._extract_keywords(all_text)
        
        # Distribuição por região
        articles_by_region = defaultdict(int)
        for article in relevant_articles:
            if hasattr(article, 'region') and article.region:
                region_name = article.region.value if hasattr(article.region, 'value') else str(article.region)
                articles_by_region[region_name] += 1
        
        # Distribuição de relevância
        relevance_distribution = {
            'alta (>0.7)': len([art for art in relevant_articles if art.relevance_score > 0.7]),
            'média (0.5-0.7)': len([art for art in relevant_articles if 0.5 <= art.relevance_score <= 0.7]),
            'baixa (0.3-0.5)': len([art for art in relevant_articles if 0.3 <= art.relevance_score < 0.5])
        }
        
        result = {
            'total_articles': len(articles),
            'relevant_articles': len(relevant_articles),
            'open_insurance_articles': len(open_insurance_articles),
            'top_keywords': top_keywords[:10],
            'articles_by_region': dict(articles_by_region),
            'relevance_distribution': relevance_distribution
        }
        
        self.logger.info(f"Análise concluída: {len(articles)} artigos, {len(open_insurance_articles)} Open Insurance")
        return result
    
    def calculate_relevance_score(self, article: NewsArticle) -> float:
        """
        Calcula score de relevância para um artigo
        
        Args:
            article: Artigo para calcular relevância
            
        Returns:
            float: Score de relevância (0.0 a 1.0)
        """
        score = 0.0
        
        # Score do título
        title_score = self._calculate_text_score(article.title or '')
        score += title_score * self.weights.get('title', 0.4)
        
        # Score do resumo
        summary_score = self._calculate_text_score(article.summary or '')
        score += summary_score * self.weights.get('summary', 0.3)
        
        # Score do conteúdo
        content_score = self._calculate_text_score(article.content or '')
        score += content_score * self.weights.get('content', 0.2)
        
        # Score da fonte (prioridade)
        source_score = self._get_source_priority_score(article.source)
        score += source_score * self.weights.get('source_priority', 0.1)
        
        # Penalizar se contém palavras irrelevantes
        if self._contains_irrelevant_content(article):
            score *= 0.5
        
        return min(1.0, max(0.0, score))
    
    def _calculate_text_score(self, text: str) -> float:
        """
        Calcula score de relevância para um texto
        
        Args:
            text: Texto para analisar
            
        Returns:
            float: Score do texto (0.0 a 1.0)
        """
        if not text:
            return 0.0
        
        text_lower = text.lower()
        score = 0.0
        
        # Palavras de alta prioridade
        high_priority = self.insurance_keywords.get('high_priority', [])
        for keyword in high_priority:
            if keyword.lower() in text_lower:
                score += 0.3
        
        # Palavras de média prioridade
        medium_priority = self.insurance_keywords.get('medium_priority', [])
        for keyword in medium_priority:
            if keyword.lower() in text_lower:
                score += 0.2
        
        # Palavras de baixa prioridade
        low_priority = self.insurance_keywords.get('low_priority', [])
        for keyword in low_priority:
            if keyword.lower() in text_lower:
                score += 0.1
        
        return min(1.0, score)
    
    def _get_source_priority_score(self, source: str) -> float:
        """
        Retorna score baseado na prioridade da fonte
        
        Args:
            source: Nome da fonte
            
        Returns:
            float: Score da fonte (0.0 a 1.0)
        """
        source_priorities = self.config.get('source_priorities', {})
        
        # Mapear fontes conhecidas para prioridades
        source_mapping = {
            'revista apólice': 'high',
            'seguro total': 'high',
            'insurance journal': 'high',
            'risk & insurance': 'medium',
            'insurance business': 'medium'
        }
        
        source_lower = source.lower()
        priority = source_mapping.get(source_lower, 'medium')
        
        return source_priorities.get(priority, 0.8)
    
    def _contains_irrelevant_content(self, article: NewsArticle) -> bool:
        """
        Verifica se artigo contém conteúdo irrelevante
        
        Args:
            article: Artigo para verificar
            
        Returns:
            bool: True se contém conteúdo irrelevante
        """
        text = f"{article.title or ''} {article.summary or ''}".lower()
        
        for keyword in self.irrelevant_keywords:
            if keyword.lower() in text:
                return True
        
        return False
    
    def is_open_insurance(self, article: NewsArticle) -> bool:
        """
        Verifica se artigo é sobre Open Insurance
        
        Args:
            article: Artigo para verificar
            
        Returns:
            bool: True se é sobre Open Insurance
        """
        text = f"{article.title or ''} {article.summary or ''} {article.content or ''}".lower()
        
        for keyword in self.open_insurance_keywords:
            if keyword.lower() in text:
                return True
        
        return False
    
    def is_relevant(self, article: NewsArticle) -> bool:
        """
        Verifica se artigo é relevante baseado no score mínimo
        
        Args:
            article: Artigo para verificar
            
        Returns:
            bool: True se é relevante
        """
        if not hasattr(article, 'relevance_score'):
            article.relevance_score = self.calculate_relevance_score(article)
        
        return article.relevance_score >= self.min_relevance_score
    
    def filter_articles(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """
        Filtra artigos relevantes
        
        Args:
            articles: Lista de artigos para filtrar
            
        Returns:
            List[NewsArticle]: Artigos relevantes
        """
        relevant_articles = []
        
        for article in articles:
            if not hasattr(article, 'relevance_score'):
                article.relevance_score = self.calculate_relevance_score(article)
            
            if article.relevance_score >= self.min_relevance_score:
                relevant_articles.append(article)
        
        # Ordenar por relevância (maior primeiro)
        relevant_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        self.logger.info(f"Filtrados {len(relevant_articles)} artigos relevantes de {len(articles)} total")
        return relevant_articles
    
    def get_top_articles(self, articles: List[NewsArticle], limit: int = 15) -> List[NewsArticle]:
        """
        Retorna os artigos mais relevantes
        
        Args:
            articles: Lista de artigos
            limit: Número máximo de artigos a retornar
            
        Returns:
            List[NewsArticle]: Artigos mais relevantes
        """
        # Calcular scores se não existirem
        for article in articles:
            if not hasattr(article, 'relevance_score'):
                article.relevance_score = self.calculate_relevance_score(article)
        
        # Filtrar apenas artigos relevantes
        relevant_articles = [art for art in articles if art.relevance_score >= self.min_relevance_score]
        
        # Ordenar por relevância
        relevant_articles.sort(key=lambda x: x.relevance_score, reverse=True)
        
        # Retornar top articles
        top_articles = relevant_articles[:limit]
        
        self.logger.info(f"Selecionados {len(top_articles)} artigos mais relevantes de {len(articles)} total")
        return top_articles
    
    def _extract_keywords(self, text: str, limit: int = 20) -> List[Tuple[str, int]]:
        """
        Extrai palavras-chave mais frequentes do texto
        
        Args:
            text: Texto para extrair palavras-chave
            limit: Número máximo de palavras-chave
            
        Returns:
            List[Tuple[str, int]]: Lista de (palavra, frequência)
        """
        if not text:
            return []
        
        # Limpar e normalizar texto
        text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = text.split()
        
        # Filtrar palavras muito curtas e stopwords
        stopwords = {
            'de', 'da', 'do', 'das', 'dos', 'a', 'o', 'as', 'os', 'e', 'ou',
            'para', 'por', 'com', 'em', 'na', 'no', 'nas', 'nos', 'que', 'se',
            'the', 'and', 'or', 'for', 'with', 'in', 'on', 'at', 'to', 'of'
        }
        
        filtered_words = [
            word for word in words 
            if len(word) > 3 and word not in stopwords
        ]
        
        # Contar frequências
        word_counts = Counter(filtered_words)
        
        return word_counts.most_common(limit)
    
    def generate_summary(self, articles: List[NewsArticle]) -> str:
        """
        Gera resumo textual da análise
        
        Args:
            articles: Lista de artigos analisados
            
        Returns:
            str: Resumo da análise
        """
        if not articles:
            return "Nenhum artigo foi analisado."
        
        analysis = self.analyze_articles(articles)
        
        # Construir resumo
        summary_parts = []
        
        # Estatísticas gerais
        total = analysis['total_articles']
        relevant = analysis['relevant_articles']
        open_insurance = analysis['open_insurance_articles']
        
        summary_parts.append(f"Foram coletados {total} artigos de notícias do mercado de seguros.")
        
        if relevant > 0:
            percentage = (relevant / total) * 100
            summary_parts.append(f"{relevant} artigos ({percentage:.1f}%) foram considerados relevantes.")
        
        # Distribuição por região
        if analysis['articles_by_region']:
            region_info = []
            for region, count in analysis['articles_by_region'].items():
                percentage = (count / relevant) * 100 if relevant > 0 else 0
                region_info.append(f"{region}: {count} artigos ({percentage:.1f}%)")
            
            summary_parts.append(f"Distribuição por região: {', '.join(region_info)}.")
        
        # Open Insurance
        if open_insurance > 0:
            summary_parts.append(f"Foram identificados {open_insurance} artigos específicos sobre Open Insurance.")
        else:
            summary_parts.append("Não foram identificados artigos específicos sobre Open Insurance hoje.")
        
        # Palavras-chave principais
        if analysis['top_keywords']:
            top_3_keywords = [kw[0] for kw in analysis['top_keywords'][:3]]
            summary_parts.append(f"Principais temas: {', '.join(top_3_keywords)}.")
        
        # Qualidade dos artigos
        if relevant > 0:
            recent_count = len([art for art in articles if self._is_recent(art)])
            if recent_count > 0:
                recent_percentage = (recent_count / total) * 100
                summary_parts.append(f"{recent_percentage:.0f}% dos artigos são das últimas 48 horas.")
        
        return ' '.join(summary_parts)
    
    def _is_recent(self, article: NewsArticle) -> bool:
        """
        Verifica se artigo é recente (últimas 48 horas)
        
        Args:
            article: Artigo para verificar
            
        Returns:
            bool: True se é recente
        """
        if not article.date_published:
            return False
        
        try:
            if isinstance(article.date_published, str):
                # Tentar parsear string de data
                article_date = datetime.fromisoformat(article.date_published.replace('Z', '+00:00'))
            else:
                article_date = article.date_published
            
            now = datetime.now(article_date.tzinfo) if article_date.tzinfo else datetime.now()
            diff = now - article_date
            
            return diff.days <= 2
        except Exception:
            return False
