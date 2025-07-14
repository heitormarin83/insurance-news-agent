"""
Analisador de notícias para processamento e classificação
"""

import re
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import nltk
from textblob import TextBlob

from src.models import NewsArticle, Region
from src.utils.logger import get_logger
from src.utils.text_processor import TextProcessor

logger = get_logger("news_analyzer")


class NewsAnalyzer:
    """Analisador de notícias com IA para classificação e processamento"""
    
    def __init__(self):
        """Inicializa o analisador"""
        self.text_processor = TextProcessor()
        self._download_nltk_data()
        logger.info("NewsAnalyzer inicializado")
    
    def _download_nltk_data(self):
        """Baixa dados necessários do NLTK"""
        try:
            nltk.download('punkt', quiet=True)
            nltk.download('stopwords', quiet=True)
            nltk.download('vader_lexicon', quiet=True)
        except Exception as e:
            logger.warning(f"Erro ao baixar dados NLTK: {e}")
    
    def analyze_articles(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        Analisa lista de artigos e retorna estatísticas
        
        Args:
            articles: Lista de artigos para analisar
            
        Returns:
            Dicionário com estatísticas e análises
        """
        try:
            if not articles:
                return self._empty_analysis()
            
            logger.info(f"Analisando {len(articles)} artigos")
            
            # Análises básicas
            total_articles = len(articles)
            articles_by_region = self._count_by_region(articles)
            articles_by_source = self._count_by_source(articles)
            articles_by_category = self._count_by_category(articles)
            
            # Análises avançadas
            top_articles = self._get_top_articles(articles, limit=10)
            open_insurance_articles = self._filter_open_insurance(articles)
            trending_keywords = self._extract_trending_keywords(articles)
            sentiment_analysis = self._analyze_sentiment(articles)
            
            # Estatísticas temporais
            time_distribution = self._analyze_time_distribution(articles)
            
            analysis = {
                'total_articles': total_articles,
                'articles_by_region': articles_by_region,
                'articles_by_source': articles_by_source,
                'articles_by_category': articles_by_category,
                'top_articles': top_articles,
                'open_insurance_articles': open_insurance_articles,
                'open_insurance_count': len(open_insurance_articles),
                'trending_keywords': trending_keywords,
                'sentiment_analysis': sentiment_analysis,
                'time_distribution': time_distribution,
                'analysis_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Análise concluída: {total_articles} artigos, {len(open_insurance_articles)} Open Insurance")
            return analysis
            
        except Exception as e:
            logger.error(f"Erro na análise de artigos: {e}")
            return self._empty_analysis()
    
    def _empty_analysis(self) -> Dict[str, Any]:
        """Retorna análise vazia"""
        return {
            'total_articles': 0,
            'articles_by_region': {},
            'articles_by_source': {},
            'articles_by_category': {},
            'top_articles': [],
            'open_insurance_articles': [],
            'open_insurance_count': 0,
            'trending_keywords': [],
            'sentiment_analysis': {},
            'time_distribution': {},
            'analysis_timestamp': datetime.now().isoformat()
        }
    
    def _count_by_region(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """Conta artigos por região"""
        count = {}
        for article in articles:
            region = article.region.value if article.region else 'Desconhecido'
            count[region] = count.get(region, 0) + 1
        return count
    
    def _count_by_source(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """Conta artigos por fonte"""
        count = {}
        for article in articles:
            source = article.source or 'Desconhecido'
            count[source] = count.get(source, 0) + 1
        return count
    
    def _count_by_category(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """Conta artigos por categoria"""
        count = {}
        for article in articles:
            for category in article.categories:
                count[category] = count.get(category, 0) + 1
        return count
    
    def _get_top_articles(self, articles: List[NewsArticle], limit: int = 10) -> List[Dict[str, Any]]:
        """Retorna top artigos por relevância"""
        try:
            # Ordena por score de relevância
            sorted_articles = sorted(
                articles, 
                key=lambda x: x.relevance_score or 0, 
                reverse=True
            )
            
            top_articles = []
            for article in sorted_articles[:limit]:
                top_articles.append({
                    'title': article.title,
                    'url': article.url,
                    'source': article.source,
                    'region': article.region.value if article.region else 'Desconhecido',
                    'relevance_score': article.relevance_score,
                    'date_published': article.date_published.isoformat() if article.date_published else None,
                    'summary': article.summary[:200] + '...' if article.summary and len(article.summary) > 200 else article.summary,
                    'open_insurance_related': article.open_insurance_related,
                    'categories': article.categories
                })
            
            return top_articles
            
        except Exception as e:
            logger.error(f"Erro ao obter top artigos: {e}")
            return []
    
    def _filter_open_insurance(self, articles: List[NewsArticle]) -> List[NewsArticle]:
        """Filtra artigos relacionados a Open Insurance"""
        return [article for article in articles if article.open_insurance_related]
    
    def _extract_trending_keywords(self, articles: List[NewsArticle], limit: int = 20) -> List[Dict[str, Any]]:
        """Extrai palavras-chave em tendência"""
        try:
            keyword_count = {}
            
            for article in articles:
                # Combina título e resumo para análise
                text = f"{article.title} {article.summary or ''}"
                keywords = self.text_processor.extract_keywords(text)
                
                for keyword in keywords:
                    keyword_count[keyword] = keyword_count.get(keyword, 0) + 1
            
            # Ordena por frequência
            trending = sorted(
                keyword_count.items(), 
                key=lambda x: x[1], 
                reverse=True
            )[:limit]
            
            return [
                {'keyword': keyword, 'count': count, 'relevance': count / len(articles)}
                for keyword, count in trending
            ]
            
        except Exception as e:
            logger.error(f"Erro ao extrair keywords: {e}")
            return []
    
    def _analyze_sentiment(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Analisa sentimento geral dos artigos"""
        try:
            if not articles:
                return {'positive': 0, 'neutral': 0, 'negative': 0, 'average_polarity': 0.0}
            
            sentiments = {'positive': 0, 'neutral': 0, 'negative': 0}
            total_polarity = 0.0
            
            for article in articles:
                text = f"{article.title} {article.summary or ''}"
                
                try:
                    blob = TextBlob(text)
                    polarity = blob.sentiment.polarity
                    total_polarity += polarity
                    
                    if polarity > 0.1:
                        sentiments['positive'] += 1
                    elif polarity < -0.1:
                        sentiments['negative'] += 1
                    else:
                        sentiments['neutral'] += 1
                        
                except Exception:
                    sentiments['neutral'] += 1
            
            average_polarity = total_polarity / len(articles) if articles else 0.0
            
            return {
                **sentiments,
                'average_polarity': round(average_polarity, 3),
                'total_analyzed': len(articles)
            }
            
        except Exception as e:
            logger.error(f"Erro na análise de sentimento: {e}")
            return {'positive': 0, 'neutral': 0, 'negative': 0, 'average_polarity': 0.0}
    
    def _analyze_time_distribution(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """Analisa distribuição temporal dos artigos"""
        try:
            now = datetime.now()
            time_buckets = {
                'last_hour': 0,
                'last_6_hours': 0,
                'last_24_hours': 0,
                'last_week': 0,
                'older': 0
            }
            
            for article in articles:
                if not article.date_published:
                    time_buckets['older'] += 1
                    continue
                
                time_diff = now - article.date_published
                
                if time_diff <= timedelta(hours=1):
                    time_buckets['last_hour'] += 1
                elif time_diff <= timedelta(hours=6):
                    time_buckets['last_6_hours'] += 1
                elif time_diff <= timedelta(hours=24):
                    time_buckets['last_24_hours'] += 1
                elif time_diff <= timedelta(days=7):
                    time_buckets['last_week'] += 1
                else:
                    time_buckets['older'] += 1
            
            return time_buckets
            
        except Exception as e:
            logger.error(f"Erro na análise temporal: {e}")
            return {'last_hour': 0, 'last_6_hours': 0, 'last_24_hours': 0, 'last_week': 0, 'older': 0}
    
    def calculate_similarity(self, article1: NewsArticle, article2: NewsArticle) -> float:
        """
        Calcula similaridade entre dois artigos
        
        Args:
            article1: Primeiro artigo
            article2: Segundo artigo
            
        Returns:
            Score de similaridade (0.0 a 1.0)
        """
        try:
            text1 = f"{article1.title} {article1.summary or ''}"
            text2 = f"{article2.title} {article2.summary or ''}"
            
            return self.text_processor.calculate_similarity(text1, text2)
            
        except Exception as e:
            logger.error(f"Erro ao calcular similaridade: {e}")
            return 0.0
    
    def find_duplicates(self, articles: List[NewsArticle], threshold: float = 0.8) -> List[List[NewsArticle]]:
        """
        Encontra artigos duplicados ou muito similares
        
        Args:
            articles: Lista de artigos
            threshold: Limite de similaridade para considerar duplicata
            
        Returns:
            Lista de grupos de artigos similares
        """
        try:
            duplicates = []
            processed = set()
            
            for i, article1 in enumerate(articles):
                if i in processed:
                    continue
                
                similar_group = [article1]
                
                for j, article2 in enumerate(articles[i+1:], i+1):
                    if j in processed:
                        continue
                    
                    similarity = self.calculate_similarity(article1, article2)
                    
                    if similarity >= threshold:
                        similar_group.append(article2)
                        processed.add(j)
                
                if len(similar_group) > 1:
                    duplicates.append(similar_group)
                
                processed.add(i)
            
            logger.info(f"Encontrados {len(duplicates)} grupos de artigos similares")
            return duplicates
            
        except Exception as e:
            logger.error(f"Erro ao encontrar duplicatas: {e}")
            return []
    
    def classify_article_importance(self, article: NewsArticle) -> str:
        """
        Classifica importância do artigo
        
        Args:
            article: Artigo para classificar
            
        Returns:
            Nível de importância: 'alta', 'média', 'baixa'
        """
        try:
            score = article.relevance_score or 0.0
            
            # Fatores que aumentam importância
            if article.open_insurance_related:
                score += 0.2
            
            if 'regulamentação' in article.title.lower():
                score += 0.15
            
            if any(keyword in article.title.lower() for keyword in ['susep', 'cnseg', 'bacen']):
                score += 0.1
            
            # Classificação
            if score >= 0.8:
                return 'alta'
            elif score >= 0.5:
                return 'média'
            else:
                return 'baixa'
                
        except Exception as e:
            logger.error(f"Erro ao classificar importância: {e}")
            return 'baixa'
    
    def generate_summary_insights(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        Gera insights resumidos sobre os artigos
        
        Args:
            articles: Lista de artigos
            
        Returns:
            Dicionário com insights
        """
        try:
            if not articles:
                return {'insights': [], 'highlights': []}
            
            insights = []
            highlights = []
            
            # Insight sobre Open Insurance
            open_insurance_count = len([a for a in articles if a.open_insurance_related])
            if open_insurance_count > 0:
                insights.append(f"Foram encontradas {open_insurance_count} notícias relacionadas ao Open Insurance")
                
                if open_insurance_count >= 3:
                    highlights.append("Alto volume de notícias sobre Open Insurance")
            
            # Insight sobre regiões
            regions = self._count_by_region(articles)
            most_active_region = max(regions.items(), key=lambda x: x[1]) if regions else None
            
            if most_active_region:
                insights.append(f"Região mais ativa: {most_active_region[0]} com {most_active_region[1]} notícias")
            
            # Insight sobre fontes
            sources = self._count_by_source(articles)
            if len(sources) >= 5:
                insights.append(f"Diversidade de fontes: {len(sources)} fontes diferentes")
            
            # Insight sobre timing
            recent_articles = [a for a in articles if a.date_published and 
                             (datetime.now() - a.date_published) <= timedelta(hours=24)]
            
            if len(recent_articles) >= len(articles) * 0.7:
                highlights.append("Maioria das notícias são recentes (últimas 24h)")
            
            return {
                'insights': insights,
                'highlights': highlights,
                'total_articles': len(articles),
                'analysis_quality': 'alta' if len(articles) >= 10 else 'média' if len(articles) >= 5 else 'baixa'
            }
            
        except Exception as e:
            logger.error(f"Erro ao gerar insights: {e}")
            return {'insights': [], 'highlights': []}


