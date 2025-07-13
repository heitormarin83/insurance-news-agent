"""
Processador de texto para análise de relevância e categorização de notícias
"""

import re
from typing import List, Dict, Tuple
from datetime import datetime
import unicodedata
from src.utils.config_loader import config_loader
from src.utils.logger import get_logger

logger = get_logger("text_processor")


class TextProcessor:
    """Processador de texto para análise de notícias de seguros"""
    
    def __init__(self):
        """Inicializa o processador de texto"""
        self.relevance_filters = config_loader.get_relevance_filters()
        
        # Compila palavras-chave para busca eficiente
        self.open_insurance_keywords = self._compile_keywords(
            self.relevance_filters.get('open_insurance_keywords', [])
        )
        self.high_priority_keywords = self._compile_keywords(
            self.relevance_filters.get('high_priority_keywords', [])
        )
        self.insurance_keywords = self._compile_keywords(
            self.relevance_filters.get('insurance_keywords', [])
        )
    
    def _compile_keywords(self, keywords: List[str]) -> List[re.Pattern]:
        """
        Compila lista de palavras-chave em padrões regex
        
        Args:
            keywords: Lista de palavras-chave
            
        Returns:
            Lista de padrões regex compilados
        """
        patterns = []
        for keyword in keywords:
            # Cria padrão que busca palavra completa (word boundary)
            pattern = re.compile(r'\b' + re.escape(keyword) + r'\b', re.IGNORECASE)
            patterns.append(pattern)
        return patterns
    
    def clean_text(self, text: str) -> str:
        """
        Limpa e normaliza texto
        
        Args:
            text: Texto a ser limpo
            
        Returns:
            Texto limpo e normalizado
        """
        if not text:
            return ""
        
        # Remove caracteres de controle
        text = ''.join(char for char in text if unicodedata.category(char)[0] != 'C')
        
        # Normaliza espaços em branco
        text = re.sub(r'\s+', ' ', text)
        
        # Remove espaços no início e fim
        text = text.strip()
        
        return text
    
    def extract_summary(self, content: str, max_length: int = 300) -> str:
        """
        Extrai resumo do conteúdo
        
        Args:
            content: Conteúdo completo
            max_length: Tamanho máximo do resumo
            
        Returns:
            Resumo extraído
        """
        if not content:
            return ""
        
        # Limpa o texto
        clean_content = self.clean_text(content)
        
        # Se o conteúdo é menor que o máximo, retorna como está
        if len(clean_content) <= max_length:
            return clean_content
        
        # Encontra o último ponto antes do limite
        truncated = clean_content[:max_length]
        last_period = truncated.rfind('.')
        
        if last_period > max_length * 0.7:  # Se o ponto está em posição razoável
            return truncated[:last_period + 1]
        else:
            # Se não há ponto em posição boa, corta na última palavra
            last_space = truncated.rfind(' ')
            if last_space > 0:
                return truncated[:last_space] + "..."
            else:
                return truncated + "..."
    
    def calculate_relevance_score(self, title: str, content: str = "") -> float:
        """
        Calcula score de relevância baseado em palavras-chave
        
        Args:
            title: Título da notícia
            content: Conteúdo da notícia
            
        Returns:
            Score de relevância (0.0 a 1.0)
        """
        text = f"{title} {content}".lower()
        score = 0.0
        
        # Pontuação por palavras-chave de alta prioridade
        high_priority_matches = sum(1 for pattern in self.high_priority_keywords if pattern.search(text))
        score += high_priority_matches * 0.3
        
        # Pontuação por palavras-chave de Open Insurance
        open_insurance_matches = sum(1 for pattern in self.open_insurance_keywords if pattern.search(text))
        score += open_insurance_matches * 0.4
        
        # Pontuação por palavras-chave gerais de seguros
        insurance_matches = sum(1 for pattern in self.insurance_keywords if pattern.search(text))
        score += insurance_matches * 0.1
        
        # Normaliza o score para 0-1
        return min(score, 1.0)
    
    def is_open_insurance_related(self, title: str, content: str = "") -> bool:
        """
        Verifica se a notícia é relacionada a Open Insurance
        
        Args:
            title: Título da notícia
            content: Conteúdo da notícia
            
        Returns:
            True se relacionada a Open Insurance
        """
        text = f"{title} {content}".lower()
        
        # Verifica se há pelo menos uma palavra-chave de Open Insurance
        for pattern in self.open_insurance_keywords:
            if pattern.search(text):
                return True
        
        return False
    
    def categorize_article(self, title: str, content: str = "") -> List[str]:
        """
        Categoriza artigo baseado no conteúdo
        
        Args:
            title: Título da notícia
            content: Conteúdo da notícia
            
        Returns:
            Lista de categorias
        """
        text = f"{title} {content}".lower()
        categories = []
        
        # Categorias baseadas em palavras-chave
        category_keywords = {
            'open_insurance': ['open insurance', 'open banking', 'seguros abertos', 'opin'],
            'regulation': ['regulamentação', 'susep', 'lei', 'circular', 'resolução', 'normativa'],
            'technology': ['tecnologia', 'digital', 'api', 'insurtech', 'inovação'],
            'market': ['mercado', 'setor', 'indústria', 'crescimento', 'vendas'],
            'claims': ['sinistro', 'indenização', 'claims', 'pagamento'],
            'auto': ['auto', 'veículo', 'carro', 'automóvel'],
            'life': ['vida', 'life', 'previdência'],
            'health': ['saúde', 'health', 'médico', 'hospitalar'],
            'property': ['patrimonial', 'property', 'residencial', 'empresarial'],
            'reinsurance': ['resseguro', 'reinsurance', 'ressegurador']
        }
        
        for category, keywords in category_keywords.items():
            for keyword in keywords:
                if keyword in text:
                    categories.append(category)
                    break
        
        # Se não encontrou categorias específicas, adiciona 'general'
        if not categories:
            categories.append('general')
        
        return categories
    
    def extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extrai palavras-chave principais do texto
        
        Args:
            text: Texto para extração
            max_keywords: Número máximo de palavras-chave
            
        Returns:
            Lista de palavras-chave
        """
        if not text:
            return []
        
        # Limpa o texto
        clean_text = self.clean_text(text.lower())
        
        # Remove palavras comuns (stop words)
        stop_words = {
            'de', 'da', 'do', 'das', 'dos', 'a', 'o', 'as', 'os', 'e', 'em', 'para',
            'com', 'por', 'que', 'se', 'na', 'no', 'nas', 'nos', 'um', 'uma', 'uns',
            'umas', 'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of',
            'with', 'by', 'is', 'are', 'was', 'were', 'be', 'been', 'have', 'has',
            'had', 'will', 'would', 'could', 'should', 'may', 'might', 'can'
        }
        
        # Extrai palavras (apenas letras, mínimo 3 caracteres)
        words = re.findall(r'\b[a-záàâãéèêíìîóòôõúùûç]{3,}\b', clean_text)
        
        # Remove stop words
        words = [word for word in words if word not in stop_words]
        
        # Conta frequência
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Ordena por frequência e retorna top palavras
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        return [word for word, freq in sorted_words[:max_keywords]]
    
    def is_insurance_related(self, title: str, content: str = "") -> bool:
        """
        Verifica se o conteúdo é relacionado a seguros
        
        Args:
            title: Título da notícia
            content: Conteúdo da notícia
            
        Returns:
            True se relacionado a seguros
        """
        text = f"{title} {content}".lower()
        
        # Verifica se há pelo menos uma palavra-chave de seguros
        for pattern in self.insurance_keywords:
            if pattern.search(text):
                return True
        
        return False


# Instância global do processador de texto
text_processor = TextProcessor()

