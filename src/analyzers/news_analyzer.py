"""
Analisador de notícias para o Insurance News Agent
Responsável por análise de relevância, classificação e processamento de artigos
"""

import re
import nltk
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
from textblob import TextBlob

from ..models import NewsArticle
from ..utils.logger import get_logger

# Download de recursos NLTK necessários
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt', quiet=True)

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords', quiet=True)

class NewsAnalyzer:
    """
    Analisador de notícias especializado em seguros
    """
    
    def __init__(self):
        self.logger = get_logger("news_analyzer")
        
        # Palavras-chave relacionadas a seguros (português e inglês)
        self.insurance_keywords = {
            'pt': [
                'seguro', 'seguros', 'seguradora', 'seguradoras', 'apólice', 'apólices',
                'prêmio', 'prêmios', 'sinistro', 'sinistros', 'indenização', 'resseguro',
                'corretora', 'corretor', 'susep', 'cnseg', 'fenaseg', 'bradesco seguros',
                'porto seguro', 'itaú seguros', 'zurich', 'allianz', 'mapfre',
                'seguro auto', 'seguro vida', 'seguro saúde', 'seguro residencial',
                'seguro empresarial', 'previdência', 'capitalização'
            ],
            'en': [
                'insurance', 'insurer', 'insurers', 'policy', 'policies', 'premium',
                'premiums', 'claim', 'claims', 'coverage', 'reinsurance', 'broker',
                'underwriting', 'actuarial', 'risk management', 'life insurance',
                'health insurance', 'auto insurance', 'property insurance',
                'casualty insurance', 'liability', 'deductible'
            ],
            'es': [
                'seguro', 'seguros', 'aseguradora', 'aseguradoras', 'póliza', 'pólizas',
                'prima', 'primas', 'siniestro', 'siniestros', 'reaseguro', 'corredor'
            ]
        }
        
        # Palavras-chave específicas para Open Insurance
        self.open_insurance_keywords = [
            'open insurance', 'open banking', 'api seguros', 'dados abertos',
            'compartilhamento dados', 'interoperabilidade', 'sandbox regulatório',
            'insurtech', 'tecnologia seguros', 'inovação seguros', 'digital insurance',
            'plataforma digital', 'ecossistema seguros', 'regulamentação digital'
        ]
        
        # Palavras irrelevantes que podem gerar falsos positivos
        self.irrelevant_keywords = [
            'segurança', 'security', 'secure', 'assegurar', 'garantir',
            'certeza', 'certo', 'insurance fraud' # fraude é relevante, mas pode ser muito específico
        ]
        
        self.logger.info("NewsAnalyzer inicializado")
    
    def analyze_articles(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        Analisa uma lista de artigos e retorna estatísticas
        
        Args:
            articles: Lista de artigos para analisar
            
        Returns:
            Dicionário com estatísticas da análise
        """
        self.logger.info(f"Analisando {len(articles)} artigos")
        
        stats = {
            'total_articles': len(articles),
            'relevant_articles': 0,
            'open_insurance_articles': 0,
            'articles_by_region': {},
            'articles_by_source': {},
            'articles_by_relevance': {'high': 0, 'medium': 0, 'low': 0},
            'keywords_frequency': {},
            'sentiment_analysis': {'positive': 0, 'neutral': 0, 'negative': 0}
        }
        
        open_insurance_articles = []
        
        for article in articles:
            # Análise de relevância
            relevance_score = self.calculate_relevance_score(article)
            article.relevance_score = relevance_score
            
            if relevance_score > 0.3:
                stats['relevant_articles'] += 1
                
                # Classificação por nível de relevância
                if relevance_score > 0.7:
                    stats['articles_by_relevance']['high'] += 1
                elif relevance_score > 0.5:
                    stats['articles_by_relevance']['medium'] += 1
                else:
                    stats['articles_by_relevance']['low'] += 1
            
            # Verificação de Open Insurance
            if self.is_open_insurance_related(article):
                stats['open_insurance_articles'] += 1
                open_insurance_articles.append(article)
                article.is_open_insurance = True
            
            # Contagem por região
            region = getattr(article, 'region', 'Unknown')
            stats['articles_by_region'][region] = stats['articles_by_region'].get(region, 0) + 1
            
            # Contagem por fonte
            source = article.source
            stats['articles_by_source'][source] = stats['articles_by_source'].get(source, 0) + 1
            
            # Análise de sentimento
            sentiment = self.analyze_sentiment(article)
            article.sentiment = sentiment
            stats['sentiment_analysis'][sentiment] += 1
            
            # Extração de palavras-chave
            keywords = self.extract_keywords(article)
            article.keywords = keywords
            for keyword in keywords:
                stats['keywords_frequency'][keyword] = stats['keywords_frequency'].get(keyword, 0) + 1
        
        stats['open_insurance_articles_list'] = open_insurance_articles
        
        self.logger.info(f"Análise concluída: {len(articles)} artigos, {stats['open_insurance_articles']} Open Insurance")
        
        return stats
    
    def calculate_relevance_score(self, article: NewsArticle) -> float:
        """
        Calcula score de relevância de um artigo (0-1)
        
        Args:
            article: Artigo para analisar
            
        Returns:
            Score de relevância entre 0 e 1
        """
        text = f"{article.title} {article.summary}".lower()
        score = 0.0
        
        # Pontuação por palavras-chave de seguros
        for lang, keywords in self.insurance_keywords.items():
            for keyword in keywords:
                if keyword.lower() in text:
                    # Palavras no título têm peso maior
                    if keyword.lower() in article.title.lower():
                        score += 0.15
                    else:
                        score += 0.05
        
        # Pontuação extra para Open Insurance
        for keyword in self.open_insurance_keywords:
            if keyword.lower() in text:
                score += 0.2
        
        # Penalização por palavras irrelevantes
        for keyword in self.irrelevant_keywords:
            if keyword.lower() in text:
                score -= 0.1
        
        # Normalização
        score = max(0.0, min(1.0, score))
        
        return score
    
    def is_relevant(self, text: str, threshold: float = 0.3) -> bool:
        """
        Verifica se um texto é relevante para seguros
        
        Args:
            text: Texto para analisar
            threshold: Limite mínimo de relevância
            
        Returns:
            True se relevante, False caso contrário
        """
        # Criar um artigo temporário para usar o método de cálculo
        temp_article = NewsArticle(
            title=text[:100],  # Primeiros 100 caracteres como título
            summary=text,
            url="",
            source="temp",
            published_date=datetime.now()
        )
        
        score = self.calculate_relevance_score(temp_article)
        return score >= threshold
    
    def is_open_insurance_related(self, article: NewsArticle) -> bool:
        """
        Verifica se um artigo está relacionado a Open Insurance
        
        Args:
            article: Artigo para verificar
            
        Returns:
            True se relacionado a Open Insurance
        """
        text = f"{article.title} {article.summary}".lower()
        
        for keyword in self.open_insurance_keywords:
            if keyword.lower() in text:
                return True
        
        return False
    
    def analyze_sentiment(self, article: NewsArticle) -> str:
        """
        Analisa o sentimento de um artigo
        
        Args:
            article: Artigo para analisar
            
        Returns:
            'positive', 'neutral' ou 'negative'
        """
        try:
            text = f"{article.title} {article.summary}"
            blob = TextBlob(text)
            polarity = blob.sentiment.polarity
            
            if polarity > 0.1:
                return 'positive'
            elif polarity < -0.1:
                return 'negative'
            else:
                return 'neutral'
        except Exception as e:
            self.logger.warning(f"Erro na análise de sentimento: {e}")
            return 'neutral'
    
    def extract_keywords(self, article: NewsArticle) -> List[str]:
        """
        Extrai palavras-chave relevantes de um artigo
        
        Args:
            article: Artigo para extrair palavras-chave
            
        Returns:
            Lista de palavras-chave
        """
        text = f"{article.title} {article.summary}".lower()
        keywords = []
        
        # Busca por palavras-chave conhecidas
        all_keywords = []
        for lang_keywords in self.insurance_keywords.values():
            all_keywords.extend(lang_keywords)
        all_keywords.extend(self.open_insurance_keywords)
        
        for keyword in all_keywords:
            if keyword.lower() in text:
                keywords.append(keyword)
        
        # Limita a 10 palavras-chave mais relevantes
        return keywords[:10]
    
    def classify_by_topic(self, article: NewsArticle) -> str:
        """
        Classifica um artigo por tópico
        
        Args:
            article: Artigo para classificar
            
        Returns:
            Categoria do tópico
        """
        text = f"{article.title} {article.summary}".lower()
        
        # Definição de tópicos e suas palavras-chave
        topics = {
            'regulamentação': ['regulamentação', 'susep', 'lei', 'norma', 'regulamento', 'compliance'],
            'tecnologia': ['tecnologia', 'digital', 'api', 'insurtech', 'inovação', 'artificial'],
            'mercado': ['mercado', 'vendas', 'crescimento', 'participação', 'concorrência'],
            'produtos': ['produto', 'apólice', 'cobertura', 'seguro auto', 'seguro vida'],
            'sinistros': ['sinistro', 'indenização', 'pagamento', 'ressarcimento'],
            'open_insurance': ['open insurance', 'dados abertos', 'compartilhamento', 'interoperabilidade']
        }
        
        topic_scores = {}
        for topic, keywords in topics.items():
            score = 0
            for keyword in keywords:
                if keyword in text:
                    score += 1
            topic_scores[topic] = score
        
        # Retorna o tópico com maior pontuação
        if topic_scores:
            return max(topic_scores, key=topic_scores.get)
        else:
            return 'geral'
    
    def get_trending_topics(self, articles: List[NewsArticle], limit: int = 5) -> List[Dict[str, Any]]:
        """
        Identifica tópicos em tendência
        
        Args:
            articles: Lista de artigos
            limit: Número máximo de tópicos
            
        Returns:
            Lista de tópicos em tendência
        """
        topic_counts = {}
        
        for article in articles:
            topic = self.classify_by_topic(article)
            topic_counts[topic] = topic_counts.get(topic, 0) + 1
        
        # Ordena por frequência
        trending = sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)
        
        return [
            {'topic': topic, 'count': count, 'percentage': (count / len(articles)) * 100}
            for topic, count in trending[:limit]
        ]
    
    def detect_duplicates(self, articles: List[NewsArticle], similarity_threshold: float = 0.8) -> List[List[NewsArticle]]:
        """
        Detecta artigos duplicados ou muito similares
        
        Args:
            articles: Lista de artigos
            similarity_threshold: Limite de similaridade (0-1)
            
        Returns:
            Lista de grupos de artigos similares
        """
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
                if similarity >= similarity_threshold:
                    similar_group.append(article2)
                    processed.add(j)
            
            if len(similar_group) > 1:
                duplicates.append(similar_group)
            
            processed.add(i)
        
        return duplicates
    
    def calculate_similarity(self, article1: NewsArticle, article2: NewsArticle) -> float:
        """
        Calcula similaridade entre dois artigos
        
        Args:
            article1: Primeiro artigo
            article2: Segundo artigo
            
        Returns:
            Score de similaridade (0-1)
        """
        # Similaridade baseada no título
        title1_words = set(article1.title.lower().split())
        title2_words = set(article2.title.lower().split())
        
        if not title1_words or not title2_words:
            return 0.0
        
        intersection = title1_words.intersection(title2_words)
        union = title1_words.union(title2_words)
        
        similarity = len(intersection) / len(union) if union else 0.0
        
        return similarity
    
    def filter_articles(self, articles: List[NewsArticle], criteria: Optional[Dict[str, Any]] = None) -> List[NewsArticle]:
        """
        Filtra artigos baseado em critérios de relevância
        
        Args:
            articles: Lista de artigos para filtrar
            criteria: Critérios de filtro (opcional)
            
        Returns:
            Lista de artigos filtrados
        """
        if not criteria:
            criteria = {}
        
        filtered = []
        min_relevance = criteria.get('min_relevance', 0.3)
        
        for article in articles:
            # Calcula relevância se não foi calculada ainda
            if not hasattr(article, 'relevance_score'):
                article.relevance_score = self.calculate_relevance_score(article)
            
            # Verifica relevância do artigo
            if article.relevance_score >= min_relevance:
                filtered.append(article)
        
        self.logger.info(f"Filtrados {len(filtered)} artigos de {len(articles)} total")
        return filtered
    
    def get_top_articles(self, articles: List[NewsArticle], top_n: int = 15) -> List[NewsArticle]:
        """
        Retorna os artigos mais relevantes
        
        Args:
            articles: Lista de artigos
            top_n: Número de artigos para retornar
            
        Returns:
            Lista dos artigos mais relevantes
        """
        # Calcula relevância se não foi calculada
        for article in articles:
            if not hasattr(article, 'relevance_score'):
                article.relevance_score = self.calculate_relevance_score(article)
        
        # Ordena por relevância (maior para menor)
        sorted_articles = sorted(articles, key=lambda x: x.relevance_score, reverse=True)
        
        self.logger.info(f"Selecionados {min(top_n, len(sorted_articles))} artigos mais relevantes de {len(articles)} total")
        
        return sorted_articles[:top_n]
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave do texto"""
        # Implementação básica de extração de keywords
        words = text.lower().split()
        # Filtrar palavras comuns
        stop_words = {'o', 'a', 'de', 'da', 'do', 'e', 'em', 'para', 'com', 'por', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}
        keywords = [word for word in words if word not in stop_words and len(word) > 3]
        return keywords[:10]  # Top 10 keywords

