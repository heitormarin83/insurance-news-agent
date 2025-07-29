"""
Analisador de notícias de seguros com IA
Responsável por analisar, classificar e filtrar artigos de notícias
"""

import logging
import re
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional, Tuple
from collections import defaultdict, Counter
import openai
from ..models import NewsArticle
from ..utils.config_loader import ConfigLoader

logger = logging.getLogger(__name__)

class NewsAnalyzer:
    """Analisador inteligente de notícias de seguros"""
    
    def __init__(self, config_path: str = "config/sources.yaml"):
        """
        Inicializa o analisador de notícias
        
        Args:
            config_path: Caminho para arquivo de configuração
        """
        self.config_loader = ConfigLoader(config_path)
        self.config = self.config_loader.load_config()
        
        # Configurações de relevância
        self.relevance_config = self.config.get('relevance_filters', {})
        self.open_insurance_keywords = self.relevance_config.get('open_insurance_keywords', [])
        self.high_priority_keywords = self.relevance_config.get('high_priority_keywords', [])
        self.insurance_keywords = self.relevance_config.get('insurance_keywords', [])
        
        # Configurações globais
        global_settings = self.config.get('global_settings', {})
        self.max_articles_per_source = global_settings.get('max_articles_per_source', 50)
        self.max_age_days = global_settings.get('max_age_days', 7)
        
        # Cliente OpenAI para análise avançada
        self.openai_client = openai.OpenAI()
        
        logger.info("NewsAnalyzer inicializado")
    
    def analyze_articles(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        """
        Analisa uma lista de artigos e retorna estatísticas e insights
        
        Args:
            articles: Lista de artigos para análise
            
        Returns:
            Dicionário com análise completa
        """
        logger.info(f"Analisando {len(articles)} artigos")
        
        if not articles:
            return {
                'total_articles': 0,
                'relevant_articles': 0,
                'open_insurance_articles': 0,
                'sources_summary': {},
                'trending_topics': [],
                'sentiment_analysis': {},
                'keywords_analysis': {},
                'regional_distribution': {},
                'articles_by_priority': {}
            }
        
        # Calcula scores de relevância para todos os artigos
        for article in articles:
            if not hasattr(article, 'relevance_score'):
                article.relevance_score = self.calculate_relevance_score(article)
        
        # Análises básicas
        relevant_articles = [a for a in articles if self.is_relevant(a)]
        open_insurance_articles = [a for a in articles if self.is_open_insurance_related(a)]
        
        # Análise por fonte
        sources_summary = self._analyze_by_source(articles)
        
        # Análise de tópicos em alta
        trending_topics = self.get_trending_topics(articles)
        
        # Análise de sentimento
        sentiment_analysis = self._analyze_sentiment_distribution(articles)
        
        # Análise de palavras-chave
        keywords_analysis = self._analyze_keywords_frequency(articles)
        
        # Distribuição regional
        regional_distribution = self._analyze_regional_distribution(articles)
        
        # Artigos por prioridade
        articles_by_priority = self._analyze_by_priority(articles)
        
        analysis_result = {
            'total_articles': len(articles),
            'relevant_articles': len(relevant_articles),
            'open_insurance_articles': len(open_insurance_articles),
            'sources_summary': sources_summary,
            'trending_topics': trending_topics,
            'sentiment_analysis': sentiment_analysis,
            'keywords_analysis': keywords_analysis,
            'regional_distribution': regional_distribution,
            'articles_by_priority': articles_by_priority,
            'analysis_timestamp': datetime.now().isoformat()
        }
        
        logger.info(f"Análise concluída: {len(articles)} artigos, {len(open_insurance_articles)} Open Insurance")
        
        return analysis_result
    
    def calculate_relevance_score(self, article: NewsArticle) -> float:
        """
        Calcula score de relevância de um artigo (0.0 a 1.0)
        
        Args:
            article: Artigo para análise
            
        Returns:
            Score de relevância
        """
        score = 0.0
        text_content = f"{article.title} {article.summary}".lower()
        
        # Pontuação base por palavras-chave de seguros
        insurance_matches = sum(1 for keyword in self.insurance_keywords 
                              if keyword.lower() in text_content)
        score += min(insurance_matches * 0.1, 0.3)  # Máximo 0.3
        
        # Pontuação extra para Open Insurance
        open_insurance_matches = sum(1 for keyword in self.open_insurance_keywords 
                                   if keyword.lower() in text_content)
        score += min(open_insurance_matches * 0.2, 0.4)  # Máximo 0.4
        
        # Pontuação para palavras-chave de alta prioridade
        high_priority_matches = sum(1 for keyword in self.high_priority_keywords 
                                  if keyword.lower() in text_content)
        score += min(high_priority_matches * 0.15, 0.3)  # Máximo 0.3
        
        # Bônus por recência (artigos mais recentes são mais relevantes)
        if article.date_published:
            hours_old = (datetime.now() - article.date_published).total_seconds() / 3600
            if hours_old < 24:
                score += 0.1  # Bônus para artigos de menos de 24h
            elif hours_old < 72:
                score += 0.05  # Bônus menor para artigos de menos de 72h
        
        return min(score, 1.0)  # Garante que não passe de 1.0
    
    def is_relevant(self, article: NewsArticle) -> bool:
        """
        Verifica se um artigo é relevante para seguros
        
        Args:
            article: Artigo para verificação
            
        Returns:
            True se relevante
        """
        if not hasattr(article, 'relevance_score'):
            article.relevance_score = self.calculate_relevance_score(article)
        
        return article.relevance_score >= 0.1  # Threshold mínimo
    
    def is_open_insurance_related(self, article: NewsArticle) -> bool:
        """
        Verifica se um artigo está relacionado ao Open Insurance
        
        Args:
            article: Artigo para verificação
            
        Returns:
            True se relacionado ao Open Insurance
        """
        text_content = f"{article.title} {article.summary}".lower()
        
        return any(keyword.lower() in text_content 
                  for keyword in self.open_insurance_keywords)
    
    def analyze_sentiment(self, article: NewsArticle) -> str:
        """
        Analisa o sentimento de um artigo usando IA
        
        Args:
            article: Artigo para análise
            
        Returns:
            Sentimento: 'positive', 'negative', 'neutral'
        """
        try:
            prompt = f"""
            Analise o sentimento da seguinte notícia sobre seguros e classifique como 'positive', 'negative' ou 'neutral':
            
            Título: {article.title}
            Resumo: {article.summary}
            
            Responda apenas com uma palavra: positive, negative ou neutral.
            """
            
            response = self.openai_client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                max_tokens=10,
                temperature=0.1
            )
            
            sentiment = response.choices[0].message.content.strip().lower()
            return sentiment if sentiment in ['positive', 'negative', 'neutral'] else 'neutral'
            
        except Exception as e:
            logger.warning(f"Erro na análise de sentimento: {e}")
            return 'neutral'
    
    def extract_keywords(self, articles: List[NewsArticle], top_n: int = 10) -> List[Tuple[str, int]]:
        """
        Extrai palavras-chave mais frequentes dos artigos
        
        Args:
            articles: Lista de artigos
            top_n: Número de palavras-chave a retornar
            
        Returns:
            Lista de tuplas (palavra-chave, frequência)
        """
        all_text = " ".join([f"{a.title} {a.summary}" for a in articles])
        keywords = self._extract_keywords(all_text)
        
        # Conta frequências
        keyword_counts = Counter(keywords)
        
        return keyword_counts.most_common(top_n)
    
    def classify_by_topic(self, article: NewsArticle) -> List[str]:
        """
        Classifica um artigo por tópicos
        
        Args:
            article: Artigo para classificação
            
        Returns:
            Lista de tópicos identificados
        """
        text_content = f"{article.title} {article.summary}".lower()
        topics = []
        
        # Mapeamento de tópicos e palavras-chave
        topic_keywords = {
            'regulamentacao': ['regulamentação', 'susep', 'lei', 'normativa', 'circular', 'resolução'],
            'open_insurance': ['open insurance', 'seguros abertos', 'apis', 'compartilhamento'],
            'tecnologia': ['digital', 'ia', 'inteligencia artificial', 'blockchain', 'insurtech'],
            'mercado': ['mercado', 'vendas', 'crescimento', 'participação', 'concorrência'],
            'produtos': ['seguro auto', 'seguro vida', 'seguro saude', 'previdencia'],
            'sinistros': ['sinistro', 'indenização', 'fraude', 'perda'],
            'corretores': ['corretor', 'corretora', 'intermediação', 'venda']
        }
        
        for topic, keywords in topic_keywords.items():
            if any(keyword in text_content for keyword in keywords):
                topics.append(topic)
        
        return topics if topics else ['geral']
    
    def get_trending_topics(self, articles: List[NewsArticle], top_n: int = 5) -> List[Dict[str, Any]]:
        """
        Identifica tópicos em alta
        
        Args:
            articles: Lista de artigos
            top_n: Número de tópicos a retornar
            
        Returns:
            Lista de tópicos em alta com estatísticas
        """
        topic_counts = defaultdict(int)
        topic_articles = defaultdict(list)
        
        for article in articles:
            topics = self.classify_by_topic(article)
            for topic in topics:
                topic_counts[topic] += 1
                topic_articles[topic].append(article)
        
        # Ordena por frequência
        trending = []
        for topic, count in sorted(topic_counts.items(), key=lambda x: x[1], reverse=True)[:top_n]:
            trending.append({
                'topic': topic,
                'article_count': count,
                'percentage': round((count / len(articles)) * 100, 1),
                'sample_titles': [a.title for a in topic_articles[topic][:3]]
            })
        
        return trending
    
    def detect_duplicates(self, articles: List[NewsArticle], similarity_threshold: float = 0.8) -> List[List[NewsArticle]]:
        """
        Detecta artigos duplicados ou muito similares
        
        Args:
            articles: Lista de artigos
            similarity_threshold: Threshold de similaridade (0.0 a 1.0)
            
        Returns:
            Lista de grupos de artigos similares
        """
        duplicate_groups = []
        processed = set()
        
        for i, article1 in enumerate(articles):
            if i in processed:
                continue
                
            similar_group = [article1]
            processed.add(i)
            
            for j, article2 in enumerate(articles[i+1:], i+1):
                if j in processed:
                    continue
                    
                similarity = self.calculate_similarity(article1, article2)
                if similarity >= similarity_threshold:
                    similar_group.append(article2)
                    processed.add(j)
            
            if len(similar_group) > 1:
                duplicate_groups.append(similar_group)
        
        return duplicate_groups
    
    def calculate_similarity(self, article1: NewsArticle, article2: NewsArticle) -> float:
        """
        Calcula similaridade entre dois artigos
        
        Args:
            article1: Primeiro artigo
            article2: Segundo artigo
            
        Returns:
            Score de similaridade (0.0 a 1.0)
        """
        # Similaridade simples baseada em palavras comuns
        text1 = f"{article1.title} {article1.summary}".lower()
        text2 = f"{article2.title} {article2.summary}".lower()
        
        words1 = set(re.findall(r'\w+', text1))
        words2 = set(re.findall(r'\w+', text2))
        
        if not words1 or not words2:
            return 0.0
        
        intersection = len(words1.intersection(words2))
        union = len(words1.union(words2))
        
        return intersection / union if union > 0 else 0.0
    
    def filter_articles(self, articles: List[NewsArticle], filters: Dict[str, Any] = None) -> List[NewsArticle]:
        """
        Filtra artigos baseado em critérios
        
        Args:
            articles: Lista de artigos
            filters: Dicionário com filtros a aplicar
            
        Returns:
            Lista de artigos filtrados
        """
        if not filters:
            filters = {}
        
        filtered = articles.copy()
        
        # Filtro por relevância mínima
        min_relevance = filters.get('min_relevance', 0.1)
        filtered = [a for a in filtered if self.calculate_relevance_score(a) >= min_relevance]
        
        # Filtro por período
        if 'max_age_hours' in filters:
            cutoff_time = datetime.now() - timedelta(hours=filters['max_age_hours'])
            filtered = [a for a in filtered if a.date_published >= cutoff_time]
        
        # Limita número de artigos por fonte
        max_per_source = filters.get('max_per_source', self.max_articles_per_source)
        if max_per_source > 0:
            filtered = self._limit_articles_per_source(filtered, max_per_source)
        
        logger.info(f"Filtrados {len(filtered)} artigos de {len(articles)} total")
        
        return filtered
    
    def get_top_articles(self, articles: List[NewsArticle], top_n: int = 10) -> List[NewsArticle]:
        """
        Obtém os principais artigos por relevância
        
        Args:
            articles: Lista de artigos
            top_n: Número de artigos a retornar
            
        Returns:
            Lista dos principais artigos ordenados por relevância
        """
        # Calcula score de relevância para artigos que não têm
        for article in articles:
            if not hasattr(article, 'relevance_score'):
                article.relevance_score = self.calculate_relevance_score(article)
        
        # Ordena por relevância (maior para menor)
        sorted_articles = sorted(articles, key=lambda x: x.relevance_score, reverse=True)
        
        logger.info(f"Selecionados {min(top_n, len(sorted_articles))} artigos mais relevantes de {len(articles)} total")
        
        return sorted_articles[:top_n]
    
    def _analyze_by_source(self, articles: List[NewsArticle]) -> Dict[str, Dict[str, Any]]:
        """Analisa artigos agrupados por fonte"""
        sources_data = defaultdict(lambda: {
            'count': 0,
            'avg_relevance': 0.0,
            'open_insurance_count': 0,
            'latest_article': None
        })
        
        for article in articles:
            source = article.source
            sources_data[source]['count'] += 1
            sources_data[source]['avg_relevance'] += article.relevance_score
            
            if self.is_open_insurance_related(article):
                sources_data[source]['open_insurance_count'] += 1
            
            if (sources_data[source]['latest_article'] is None or 
                article.date_published > sources_data[source]['latest_article'].date_published):
                sources_data[source]['latest_article'] = article
        
        # Calcula médias
        for source_data in sources_data.values():
            if source_data['count'] > 0:
                source_data['avg_relevance'] /= source_data['count']
                source_data['avg_relevance'] = round(source_data['avg_relevance'], 3)
        
        return dict(sources_data)
    
    def _analyze_sentiment_distribution(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """Analisa distribuição de sentimentos"""
        sentiment_counts = {'positive': 0, 'negative': 0, 'neutral': 0}
        
        # Para performance, analisa apenas uma amostra
        sample_size = min(20, len(articles))
        sample_articles = articles[:sample_size]
        
        for article in sample_articles:
            sentiment = self.analyze_sentiment(article)
            sentiment_counts[sentiment] += 1
        
        return sentiment_counts
    
    def _analyze_keywords_frequency(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """Analisa frequência de palavras-chave"""
        keywords = self.extract_keywords(articles, top_n=15)
        return dict(keywords)
    
    def _analyze_regional_distribution(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """Analisa distribuição regional"""
        regional_counts = defaultdict(int)
        
        for article in articles:
            # Assume que a região está no nome da fonte ou pode ser inferida
            if hasattr(article, 'region'):
                regional_counts[article.region] += 1
            else:
                regional_counts['Não especificado'] += 1
        
        return dict(regional_counts)
    
    def _analyze_by_priority(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """Analisa artigos por nível de prioridade"""
        priority_counts = {'high': 0, 'medium': 0, 'low': 0}
        
        for article in articles:
            if article.relevance_score >= 0.7:
                priority_counts['high'] += 1
            elif article.relevance_score >= 0.4:
                priority_counts['medium'] += 1
            else:
                priority_counts['low'] += 1
        
        return priority_counts
    
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
    
    def _extract_keywords(self, text: str) -> List[str]:
        """Extrai palavras-chave de um texto"""
        # Remove pontuação e converte para minúsculas
        clean_text = re.sub(r'[^\w\s]', ' ', text.lower())
        words = clean_text.split()
        
        # Remove palavras muito comuns (stop words)
        stop_words = {
            'de', 'da', 'do', 'das', 'dos', 'a', 'o', 'as', 'os', 'e', 'em', 'para', 'com', 'por',
            'que', 'se', 'na', 'no', 'nas', 'nos', 'um', 'uma', 'uns', 'umas', 'é', 'são', 'foi',
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by', 'is', 'are'
        }
        
        # Filtra palavras relevantes (mínimo 3 caracteres, não stop words)
        keywords = [word for word in words 
                   if len(word) >= 3 and word not in stop_words]
        
        return keywords

