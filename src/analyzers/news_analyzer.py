""
Analisador de notícias para processamento e filtragem
"""

from typing import List, Dict, Any, Tuple
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import statistics

from src.models import NewsArticle, Region
from src.utils.logger import get_logger
from src.utils.text_processor import text_processor

logger = get_logger("news_analyzer")


class NewsAnalyzer:
    """Analisador de notícias coletadas"""
    
    def __init__(self):
        """Inicializa o analisador de notícias"""
        self.min_relevance_score = 0.1
        self.max_articles_per_source = 10
        
        logger.info("News Analyzer inicializado")
    
    def analyze_articles(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        Analisa lista de artigos e gera estatísticas
        
        Args:
            articles: Lista de artigos para análise
            
        Returns:
            Dicionário com análises e estatísticas
        """
        if not articles:
            return {
                'total_articles': 0,
                'analysis_timestamp': datetime.now(),
                'error': 'Nenhum artigo para analisar'
            }
        
        logger.info(f"Analisando {len(articles)} artigos")
        
        analysis = {
            'total_articles': len(articles),
            'analysis_timestamp': datetime.now(),
            'by_region': self._analyze_by_region(articles),
            'by_source': self._analyze_by_source(articles),
            'by_category': self._analyze_by_category(articles),
            'by_date': self._analyze_by_date(articles),
            'relevance_stats': self._analyze_relevance(articles),
            'open_insurance_stats': self._analyze_open_insurance(articles),
            'top_keywords': self._extract_top_keywords(articles),
            'quality_metrics': self._calculate_quality_metrics(articles)
        }
        
        logger.info(f"Análise concluída: {analysis['total_articles']} artigos processados")
        
        return analysis
    
    def _analyze_by_region(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Analisa artigos por região"""
        region_stats = defaultdict(int)
        region_articles = defaultdict(list)
        
        for article in articles:
            region = article.region.value
            region_stats[region] += 1
            region_articles[region].append(article)
        
        # Calcula estatísticas por região
        region_analysis = {}
        for region, count in region_stats.items():
            articles_in_region = region_articles[region]
            avg_relevance = statistics.mean([a.relevance_score for a in articles_in_region])
            open_insurance_count = sum(1 for a in articles_in_region if a.open_insurance_related)
            
            region_analysis[region] = {
                'count': count,
                'percentage': (count / len(articles)) * 100,
                'avg_relevance': round(avg_relevance, 3),
                'open_insurance_count': open_insurance_count,
                'top_sources': self._get_top_sources_in_region(articles_in_region)
            }
        
        return region_analysis
    
    def _analyze_by_source(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Analisa artigos por fonte"""
        source_stats = defaultdict(int)
        source_articles = defaultdict(list)
        
        for article in articles:
            source = article.source
            source_stats[source] += 1
            source_articles[source].append(article)
        
        # Ordena fontes por número de artigos
        sorted_sources = sorted(source_stats.items(), key=lambda x: x[1], reverse=True)
        
        source_analysis = {}
        for source, count in sorted_sources:
            articles_from_source = source_articles[source]
            avg_relevance = statistics.mean([a.relevance_score for a in articles_from_source])
            
            source_analysis[source] = {
                'count': count,
                'percentage': (count / len(articles)) * 100,
                'avg_relevance': round(avg_relevance, 3),
                'region': articles_from_source[0].region.value,
                'open_insurance_count': sum(1 for a in articles_from_source if a.open_insurance_related)
            }
        
        return source_analysis
    
    def _analyze_by_category(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Analisa artigos por categoria"""
        category_counter = Counter()
        
        for article in articles:
            for category in article.categories:
                category_counter[category] += 1
        
        total_categories = sum(category_counter.values())
        
        category_analysis = {}
        for category, count in category_counter.most_common():
            category_analysis[category] = {
                'count': count,
                'percentage': (count / total_categories) * 100 if total_categories > 0 else 0
            }
        
        return category_analysis
    
    def _analyze_by_date(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Analisa artigos por data"""
        date_stats = defaultdict(int)
        
        for article in articles:
            date_key = article.date_published.strftime('%Y-%m-%d')
            date_stats[date_key] += 1
        
        # Ordena por data
        sorted_dates = sorted(date_stats.items())
        
        # Calcula estatísticas temporais
        if articles:
            dates = [a.date_published for a in articles]
            oldest_date = min(dates)
            newest_date = max(dates)
            date_range = (newest_date - oldest_date).days
        else:
            oldest_date = newest_date = datetime.now()
            date_range = 0
        
        return {
            'by_day': dict(sorted_dates),
            'oldest_article': oldest_date.isoformat(),
            'newest_article': newest_date.isoformat(),
            'date_range_days': date_range,
            'articles_last_24h': self._count_articles_in_period(articles, hours=24),
            'articles_last_week': self._count_articles_in_period(articles, days=7)
        }
    
    def _analyze_relevance(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Analisa scores de relevância"""
        if not articles:
            return {}
        
        scores = [a.relevance_score for a in articles]
        
        return {
            'avg_score': round(statistics.mean(scores), 3),
            'median_score': round(statistics.median(scores), 3),
            'min_score': round(min(scores), 3),
            'max_score': round(max(scores), 3),
            'std_dev': round(statistics.stdev(scores) if len(scores) > 1 else 0, 3),
            'high_relevance_count': sum(1 for s in scores if s >= 0.7),
            'medium_relevance_count': sum(1 for s in scores if 0.3 <= s < 0.7),
            'low_relevance_count': sum(1 for s in scores if s < 0.3)
        }
    
    def _analyze_open_insurance(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Analisa artigos relacionados a Open Insurance"""
        open_insurance_articles = [a for a in articles if a.open_insurance_related]
        
        if not open_insurance_articles:
            return {
                'count': 0,
                'percentage': 0,
                'by_region': {},
                'by_source': {},
                'avg_relevance': 0
            }
        
        # Análise por região
        region_count = defaultdict(int)
        for article in open_insurance_articles:
            region_count[article.region.value] += 1
        
        # Análise por fonte
        source_count = defaultdict(int)
        for article in open_insurance_articles:
            source_count[article.source] += 1
        
        avg_relevance = statistics.mean([a.relevance_score for a in open_insurance_articles])
        
        return {
            'count': len(open_insurance_articles),
            'percentage': (len(open_insurance_articles) / len(articles)) * 100,
            'by_region': dict(region_count),
            'by_source': dict(source_count),
            'avg_relevance': round(avg_relevance, 3)
        }
    
    def _extract_top_keywords(self, articles: List[NewsArticle], top_n: int = 20) -> List[Tuple[str, int]]:
        """Extrai palavras-chave mais frequentes"""
        all_text = ""
        
        for article in articles:
            all_text += f" {article.title} {article.summary}"
        
        keywords = text_processor.extract_keywords(all_text, max_keywords=top_n * 2)
        
        # Conta frequência das keywords
        keyword_counter = Counter()
        for article in articles:
            article_text = f"{article.title} {article.summary}".lower()
            for keyword in keywords:
                if keyword in article_text:
                    keyword_counter[keyword] += 1
        
        return keyword_counter.most_common(top_n)
    
    def _calculate_quality_metrics(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Calcula métricas de qualidade dos artigos"""
        if not articles:
            return {}
        
        # Artigos com resumo
        with_summary = sum(1 for a in articles if a.summary and len(a.summary) > 50)
        
        # Artigos com conteúdo
        with_content = sum(1 for a in articles if a.content and len(a.content) > 100)
        
        # Artigos com categorias
        with_categories = sum(1 for a in articles if a.categories)
        
        # Artigos recentes (últimas 48h)
        recent_articles = self._count_articles_in_period(articles, hours=48)
        
        return {
            'with_summary_percentage': (with_summary / len(articles)) * 100,
            'with_content_percentage': (with_content / len(articles)) * 100,
            'with_categories_percentage': (with_categories / len(articles)) * 100,
            'recent_articles_percentage': (recent_articles / len(articles)) * 100,
            'avg_title_length': round(statistics.mean([len(a.title) for a in articles]), 1),
            'avg_summary_length': round(statistics.mean([len(a.summary) for a in articles if a.summary]), 1)
        }
    
    def _get_top_sources_in_region(self, articles: List[NewsArticle], top_n: int = 3) -> List[Dict[str, Any]]:
        """Obtém principais fontes em uma região"""
        source_count = defaultdict(int)
        
        for article in articles:
            source_count[article.source] += 1
        
        top_sources = []
        for source, count in sorted(source_count.items(), key=lambda x: x[1], reverse=True)[:top_n]:
            top_sources.append({
                'source': source,
                'count': count
            })
        
        return top_sources
    
    def _count_articles_in_period(self, articles: List[NewsArticle], days: int = 0, hours: int = 0) -> int:
        """Conta artigos em um período específico"""
        cutoff_time = datetime.now() - timedelta(days=days, hours=hours)
        return sum(1 for a in articles if a.date_published >= cutoff_time)
    
    def filter_articles(self, articles: List[NewsArticle], filters: Dict[str, Any]) -> List[NewsArticle]:
        """
        Filtra artigos baseado em critérios
        
        Args:
            articles: Lista de artigos
            filters: Critérios de filtragem
            
        Returns:
            Lista de artigos filtrados
        """
        filtered = articles.copy()
        
        # Filtro por relevância mínima
        min_relevance = filters.get('min_relevance', self.min_relevance_score)
        filtered = [a for a in filtered if a.relevance_score >= min_relevance]
        
        # Filtro por região
        if 'regions' in filters:
            allowed_regions = [Region(r) for r in filters['regions']]
            filtered = [a for a in filtered if a.region in allowed_regions]
        
        # Filtro por fonte
        if 'sources' in filters:
            allowed_sources = filters['sources']
            filtered = [a for a in filtered if a.source in allowed_sources]
        
        # Filtro por categoria
        if 'categories' in filters:
            required_categories = filters['categories']
            filtered = [a for a in filtered if any(cat in a.categories for cat in required_categories)]
        
        # Filtro por Open Insurance
        if filters.get('open_insurance_only', False):
            filtered = [a for a in filtered if a.open_insurance_related]
        
        # Filtro por período
        if 'max_age_hours' in filters:
            cutoff_time = datetime.now() - timedelta(hours=filters['max_age_hours'])
            filtered = [a for a in filtered if a.date_published >= cutoff_time]
        
        # Limita número de artigos por fonte
        max_per_source = filters.get('max_per_source', self.max_articles_per_source)
        if max_per_source > 0:
            filtered = self._limit_articles_per_source(filtered, max_per_source)
        
        logger.info(f"Filtros aplicados: {len(articles)} -> {len(filtered)} artigos")
        
        return filtered
    
    def _limit_articles_per_source(self, articles: List[NewsArticle], max_per_source: int) -> List[NewsArticle]:
        """Limita número de artigos por fonte"""
        source_articles = defaultdict(list)
        
        # Agrupa por fonte
        for article in articles:
            source_articles[article.source].append(article)
        
        # Ordena cada fonte por relevância e limita
        limited_articles = []
        for source, source_list in source_articles.items():
            # Ordena por relevância (maior primeiro)
            sorted_articles = sorted(source_list, key=lambda x: x.relevance_score, reverse=True)
            limited_articles.extend(sorted_articles[:max_per_source])
        
        # Ordena resultado final por relevância
        return sorted(limited_articles, key=lambda x: x.relevance_score, reverse=True)
    
    def get_top_articles(self, articles: List[NewsArticle], top_n: int = 10) -> List[NewsArticle]:
        """
        Obtém os principais artigos por relevância
        
        Args:
            articles: Lista de artigos
            top_n: Número de artigos a retornar
            
        Returns:
            Lista dos principais artigos
        """
        # Ordena por relevância (maior primeiro)
        sorted_articles = sorted(articles, key=lambda x: x.relevance_score, reverse=True)
        
        return sorted_articles[:top_n]

