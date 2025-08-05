import re
import logging
import yaml
from typing import List, Dict, Any, Optional
from datetime import datetime
from collections import defaultdict, Counter
from ..models import NewsArticle

logger = logging.getLogger(__name__)

class NewsAnalyzer:
    def __init__(self, config_path: str = 'config/news_analyzer_config.yaml'):
        self.logger = logger
        self.config = self._load_config(config_path)
        self.weights = self.config.get('weights', {})
        self.insurance_keywords = self.config.get('insurance_keywords', {})
        self.open_insurance_keywords = self.config.get('open_insurance_keywords', [])
        self.irrelevant_keywords = self.config.get('irrelevant_keywords', [])
        self.irrelevant_contexts = self.config.get('irrelevant_contexts', {})
        self.topics = self.config.get('topics', {})
        self.logger.info("NewsAnalyzer initialized with external configuration.")

    def _load_config(self, path: str) -> Dict[str, Any]:
        with open(path, 'r', encoding='utf-8') as file:
            return yaml.safe_load(file)

    def analyze_articles(self, articles: List[NewsArticle]) -> Dict[str, Any]:
        stats = defaultdict(int)
        stats['total_articles'] = len(articles)
        stats['articles_by_region'] = defaultdict(int)
        stats['articles_by_source'] = defaultdict(int)
        stats['articles_by_relevance'] = {'high': 0, 'medium': 0, 'low': 0}
        stats['keywords_frequency'] = Counter()
        stats['sentiment_analysis'] = {'positive': 0, 'neutral': 0, 'negative': 0}
        open_insurance_articles = []

        for article in articles:
            relevance_score = self.calculate_relevance_score(article)
            article.relevance_score = relevance_score

            if relevance_score > 0.3:
                stats['relevant_articles'] += 1
                if relevance_score > 0.7:
                    stats['articles_by_relevance']['high'] += 1
                elif relevance_score > 0.5:
                    stats['articles_by_relevance']['medium'] += 1
                else:
                    stats['articles_by_relevance']['low'] += 1

            if self.is_open_insurance_related(article):
                stats['open_insurance_articles'] += 1
                open_insurance_articles.append(article)

            stats['articles_by_region'][getattr(article, 'region', 'Unknown')] += 1
            stats['articles_by_source'][article.source] += 1

            sentiment = self.analyze_sentiment(article)
            article.sentiment = sentiment
            stats['sentiment_analysis'][sentiment] += 1

            keywords = self.extract_keywords(article)
            article.keywords = keywords
            stats['keywords_frequency'].update(keywords)

        stats['open_insurance_articles_list'] = open_insurance_articles

        self.logger.info(f"Análise concluída: {stats['total_articles']} artigos, {stats['open_insurance_articles']} Open Insurance.")
        self.logger.info(f"Top palavras-chave: {stats['keywords_frequency'].most_common(5)}")

        return stats

    def calculate_relevance_score(self, article: NewsArticle) -> float:
        text = f"{article.title} {article.summary}".lower()
        score = 0.0

        for lang, keywords in self.insurance_keywords.items():
            for keyword in keywords:
                if re.search(rf'\\b{re.escape(keyword)}\\b', text):
                    if keyword in article.title.lower():
                        score += self.weights.get('title_keyword', 0.15)
                    else:
                        score += self.weights.get('summary_keyword', 0.05)

        for keyword in self.open_insurance_keywords:
            if re.search(rf'\\b{re.escape(keyword)}\\b', text):
                score += self.weights.get('open_insurance_bonus', 0.2)

        for keyword in self.irrelevant_keywords:
            if re.search(rf'\\b{re.escape(keyword)}\\b', text):
                context_words = self.irrelevant_contexts.get(keyword, [])
                if any(context_word in text for context_word in context_words):
                    score += 0  # Context valid, no penalty
                else:
                    score += self.weights.get('irrelevant_penalty', -0.1)

        score = min(1.0, max(0.0, score))
        return score

    def is_open_insurance_related(self, article: NewsArticle) -> bool:
        text = f"{article.title} {article.summary}".lower()
        return any(re.search(rf'\\b{re.escape(k)}\\b', text) for k in self.open_insurance_keywords)

    def analyze_sentiment(self, article: NewsArticle) -> str:
        text = f"{article.title} {article.summary}".lower()
        pos_keywords = self.config.get('positive_keywords', [])
        neg_keywords = self.config.get('negative_keywords', [])

        score = sum(1 for k in pos_keywords if k in text) - sum(1 for k in neg_keywords if k in text)
        if score >= 2:
            return 'positive'
        elif score <= -2:
            return 'negative'
        else:
            return 'neutral'

    def extract_keywords(self, article: NewsArticle) -> List[str]:
        text = f"{article.title} {article.summary}".lower()
        keywords = []

        all_keywords = sum(self.insurance_keywords.values(), []) + self.open_insurance_keywords
        for keyword in all_keywords:
            if re.search(rf'\\b{re.escape(keyword)}\\b', text):
                keywords.append(keyword)

        return keywords[:10]

    def classify_by_topic(self, article: NewsArticle) -> str:
        text = f"{article.title} {article.summary}".lower()
        topic_scores = {}
        for topic, keywords in self.topics.items():
            topic_scores[topic] = sum(1 for k in keywords if k in text)

        return max(topic_scores, key=topic_scores.get, default='geral')

    def detect_duplicates(self, articles: List[NewsArticle], threshold: float = 0.8) -> List[List[NewsArticle]]:
        duplicates = []
        processed = set()
        for i, article1 in enumerate(articles):
            if i in processed:
                continue
            group = [article1]
            for j, article2 in enumerate(articles[i+1:], i+1):
                if j in processed:
                    continue
                sim = self.calculate_similarity(article1, article2)
                if sim >= threshold:
                    group.append(article2)
                    processed.add(j)
            if len(group) > 1:
                duplicates.append(group)
            processed.add(i)
        return duplicates

    def calculate_similarity(self, article1: NewsArticle, article2: NewsArticle) -> float:
        tokens1 = set(re.findall(r'\\w{3,}', article1.title.lower()))
        tokens2 = set(re.findall(r'\\w{3,}', article2.title.lower()))
        if not tokens1 or not tokens2:
            return 0.0
        intersection = tokens1 & tokens2
        union = tokens1 | tokens2
        return len(intersection) / len(union)

    def filter_articles(self, articles: List[NewsArticle], min_relevance: float = 0.3) -> List[NewsArticle]:
        filtered = [a for a in articles if getattr(a, 'relevance_score', self.calculate_relevance_score(a)) >= min_relevance]
        self.logger.info(f"Filtrados {len(filtered)} artigos de {len(articles)} total")
        return filtered

    def get_top_articles(self, articles: List[NewsArticle], top_n: int = 15) -> List[NewsArticle]:
        articles = sorted(articles, key=lambda a: getattr(a, 'relevance_score', self.calculate_relevance_score(a)), reverse=True)
        self.logger.info(f"Selecionados {min(top_n, len(articles))} artigos mais relevantes de {len(articles)} total")
        return articles[:top_n]

    def get_trending_topics(self, articles: List[NewsArticle], limit: int = 5) -> List[Dict[str, Any]]:
        topic_counts = Counter(self.classify_by_topic(a) for a in articles)
        total = len(articles)
        trending = topic_counts.most_common(limit)
        return [{'topic': topic, 'count': count, 'percentage': (count / total) * 100} for topic, count in trending]

    def _extract_keywords(self, text: str) -> List[str]:
        clean_text = re.sub(r'[^\\w\\s]', ' ', text.lower())
        words = clean_text.split()
        stop_words = set(self.config.get('stop_words', []))
        return [w for w in words if len(w) >= 3 and w not in stop_words]
