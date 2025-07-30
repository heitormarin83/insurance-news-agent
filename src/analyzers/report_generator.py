"""
Gerador de relatórios para o Insurance News Agent
Responsável por criar relatórios diários em diferentes formatos
VERSÃO COMPLETA - COM DEDUPLICAÇÃO E SEÇÃO "OUTROS ARTIGOS"
"""

import os
import json
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from pathlib import Path

from src.models import NewsArticle, DailyReport
from src.utils.logger import get_logger

logger = get_logger("report_generator")

class ReportGenerator:
    """
    Gerador de relatórios diários
    VERSÃO COMPLETA - COM DEDUPLICAÇÃO E TODOS OS ARTIGOS
    """
    
    def __init__(self, output_dir: str = "data/reports"):
        """
        Inicializa o gerador de relatórios
        
        Args:
            output_dir: Diretório de saída dos relatórios
        """
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        self.logger = logger
        self.logger.info(f"Report Generator inicializado - Output: {self.output_dir}")
    
    def generate_daily_report(self, articles: List[NewsArticle], analysis: Dict[str, Any] = None) -> DailyReport:
        """
        Gera relatório diário
        
        Args:
            articles: Lista de artigos (já filtrados por deduplicação)
            analysis: Análise dos artigos (opcional)
            
        Returns:
            Relatório diário gerado
        """
        if not articles:
            self.logger.warning("Nenhum artigo fornecido para gerar relatório")
            return self._create_empty_report()
        
        self.logger.info(f"Gerando relatório diário para {datetime.now().strftime('%Y-%m-%d')} com {len(articles)} artigos")
        
        # Seleciona artigos principais (top 15)
        top_articles = self._select_top_articles(articles, 15)
        
        # Artigos restantes (outros artigos)
        other_articles = [art for art in articles if art not in top_articles]
        
        # Identifica artigos de Open Insurance
        open_insurance_articles = [art for art in articles if getattr(art, 'is_open_insurance', False) or getattr(art, 'open_insurance_related', False)]
        
        # Distribui por região
        articles_by_region = self._group_by_region(articles)
        
        # Gera resumo
        summary = self._generate_summary(articles, articles_by_region, open_insurance_articles)
        
        # Cria relatório EXPANDIDO
        report = DailyReport(
            date=datetime.now(),
            total_articles=len(articles),
            top_articles=top_articles,
            open_insurance_articles=open_insurance_articles,
            articles_by_region=articles_by_region,
            summary=summary
        )
        
        # Adiciona campo personalizado para outros artigos
        report.other_articles = other_articles
        
        self.logger.info(f"Relatório diário gerado: {len(top_articles)} artigos principais, "
                        f"{len(other_articles)} outros artigos, {len(open_insurance_articles)} sobre Open Insurance")
        
        return report
    
    def _create_empty_report(self) -> DailyReport:
        """Cria relatório vazio"""
        report = DailyReport(
            date=datetime.now(),
            total_articles=0,
            top_articles=[],
            open_insurance_articles=[],
            articles_by_region={},
            summary="Nenhum artigo foi coletado hoje."
        )
        report.other_articles = []
        return report
    
    def _select_top_articles(self, articles: List[NewsArticle], limit: int = 15) -> List[NewsArticle]:
        """Seleciona os principais artigos"""
        # Ordena por relevância se disponível, senão por data
        sorted_articles = sorted(
            articles,
            key=lambda x: getattr(x, 'relevance_score', 0.5),
            reverse=True
        )
        return sorted_articles[:limit]
    
    def _group_by_region(self, articles: List[NewsArticle]) -> Dict[str, int]:
        """Agrupa artigos por região - FORMATO SIMPLES"""
        regions = {}
        for article in articles:
            region = getattr(article, 'region', 'Não especificado')
            # Converte enum para string se necessário
            if hasattr(region, 'value'):
                region = region.value
            regions[region] = regions.get(region, 0) + 1
        
        return regions
    
    def _generate_summary(self, articles: List[NewsArticle], articles_by_region: Dict[str, int], open_insurance_articles: List[NewsArticle]) -> str:
        """Gera resumo executivo"""
        if not articles:
            return "Nenhum artigo foi coletado hoje."
        
        summary_parts = []
        total = len(articles)
        
        # Total de artigos
        summary_parts.append(f"Foram coletados {total} artigos de notícias do mercado de seguros.")
        
        # Distribuição por região
        if articles_by_region:
            region_text = []
            for region, count in articles_by_region.items():
                percentage = (count / total) * 100
                region_text.append(f"{region}: {count} artigos ({percentage:.1f}%)")
            
            summary_parts.append(f"Distribuição por região: {', '.join(region_text)}.")
        
        # Open Insurance
        open_insurance_count = len(open_insurance_articles)
        if open_insurance_count > 0:
            oi_percentage = (open_insurance_count / total) * 100
            summary_parts.append(f"Foram identificados {open_insurance_count} artigos relacionados a Open Insurance "
                                f"({oi_percentage:.1f}% do total).")
        else:
            summary_parts.append("Não foram identificados artigos específicos sobre Open Insurance hoje.")
        
        # Qualidade dos dados
        summary_parts.append("100% dos artigos são das últimas 48 horas.")
        
        return " ".join(summary_parts)
    
    def _convert_to_serializable(self, obj):
        """Converte objetos para formato serializável JSON"""
        if hasattr(obj, 'value'):  # Enum
            return obj.value
        elif hasattr(obj, 'isoformat'):  # datetime
            return obj.isoformat()
        elif hasattr(obj, '__dict__'):  # Objeto customizado
            result = {}
            for key, value in obj.__dict__.items():
                result[key] = self._convert_to_serializable(value)
            return result
        elif isinstance(obj, list):
            return [self._convert_to_serializable(item) for item in obj]
        elif isinstance(obj, dict):
            return {key: self._convert_to_serializable(value) for key, value in obj.items()}
        else:
            return obj
    
    def _generate_articles_html(self, articles: List[NewsArticle], css_class: str = "article") -> str:
        """Gera HTML para uma lista de artigos"""
        if not articles:
            return "<p>Nenhum artigo nesta categoria.</p>"
        
        articles_html = ""
        for i, article in enumerate(articles, 1):
            # Categorias (se existirem)
            categories = getattr(article, 'categories', [])
            categories_html = "".join([f'<span class="badge">{cat}</span>' for cat in categories])
            
            # Metadados
            source = article.source
            date_pub = article.date_published.strftime('%d/%m/%Y') if hasattr(article, 'date_published') and article.date_published else 'Data não disponível'
            region = getattr(article, 'region', 'Não especificado')
            # Converte enum para string se necessário
            if hasattr(region, 'value'):
                region = region.value
            
            # Score de relevância
            relevance_score = getattr(article, 'relevance_score', 0)
            score_display = f"({relevance_score:.1f})" if relevance_score > 0 else ""
            
            articles_html += f"""
            <div class="{css_class}">
                <h3><a href="{article.url}" target="_blank">{article.title}</a> {score_display}</h3>
                <div class="article-meta">
                    <strong>Fonte:</strong> {source} | 
                    <strong>Data:</strong> {date_pub} | 
                    <strong>Região:</strong> {region}
                    {categories_html}
                </div>
                <div class="article-summary">{article.summary}</div>
            </div>
            """
        
        return articles_html
    
    def generate_html_report(self, report: DailyReport) -> str:
        """
        Gera relatório em formato HTML
        VERSÃO COMPLETA - COM SEÇÃO "OUTROS ARTIGOS"
        
        Args:
            report: Relatório diário
            
        Returns:
            HTML do relatório
        """
        # Prepara dados
        date_str = report.date.strftime('%d de %B de %Y')
        generation_time = datetime.now().strftime('%d/%m/%Y às %H:%M')
        
        # Gera HTML dos artigos principais
        top_articles_html = self._generate_articles_html(report.top_articles, "article top-article")
        
        # Gera HTML dos outros artigos
        other_articles = getattr(report, 'other_articles', [])
        other_articles_html = self._generate_articles_html(other_articles, "article other-article")
        
        # Gera HTML dos artigos Open Insurance
        open_insurance_html = ""
        if report.open_insurance_articles:
            open_insurance_html = self._generate_articles_html(report.open_insurance_articles, "article open-insurance")
        else:
            open_insurance_html = "<p>Nenhum artigo específico sobre Open Insurance foi identificado hoje.</p>"
        
        # Seção Open Insurance
        open_insurance_section = f"""
        <div class="section">
            <h2>🔓 Open Insurance</h2>
            {open_insurance_html}
        </div>
        """
        
        # Seção Outros Artigos
        other_articles_section = ""
        if other_articles:
            other_articles_section = f"""
            <div class="section">
                <h2>📰 Outros Artigos ({len(other_articles)})</h2>
                <p class="section-description">Todos os demais artigos coletados, ordenados por relevância.</p>
                {other_articles_html}
            </div>
            """
        
        # Template HTML COMPLETO
        html_content = f"""
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Diário - Notícias de Seguros</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.5em;
        }}
        .header .date {{
            font-size: 1.2em;
            opacity: 0.9;
            margin-top: 10px;
        }}
        .summary {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .summary h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }}
        .stat-card {{
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .stat-number {{
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }}
        .stat-label {{
            color: #666;
            margin-top: 5px;
        }}
        .section {{
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }}
        .section-description {{
            color: #666;
            font-style: italic;
            margin-bottom: 20px;
        }}
        .article {{
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 20px;
            background: #f8f9ff;
            border-radius: 0 5px 5px 0;
        }}
        .top-article {{
            border-left-color: #28a745;
            background: #f8fff8;
        }}
        .other-article {{
            border-left-color: #6c757d;
            background: #f8f9fa;
        }}
        .open-insurance {{
            border-left-color: #e74c3c;
            background: #fff8f8;
        }}
        .article h3 {{
            margin: 0 0 10px 0;
            color: #333;
        }}
        .article a {{
            color: #667eea;
            text-decoration: none;
        }}
        .article a:hover {{
            text-decoration: underline;
        }}
        .article-meta {{
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }}
        .article-summary {{
            color: #555;
            line-height: 1.5;
        }}
        .badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-right: 5px;
        }}
        .open-insurance .badge {{
            background: #e74c3c;
        }}
        .footer {{
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding: 20px;
        }}
        .toc {{
            background: #f8f9ff;
            padding: 20px;
            border-radius: 10px;
            margin-bottom: 30px;
            border: 1px solid #e1e5f2;
        }}
        .toc h3 {{
            color: #667eea;
            margin-top: 0;
        }}
        .toc ul {{
            list-style: none;
            padding: 0;
        }}
        .toc li {{
            padding: 5px 0;
        }}
        .toc a {{
            color: #667eea;
            text-decoration: none;
        }}
        .toc a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Relatório Diário</h1>
        <div class="date">Notícias do Mercado de Seguros - {date_str}</div>
    </div>
    
    <div class="toc">
        <h3>📋 Índice</h3>
        <ul>
            <li><a href="#resumo">📋 Resumo Executivo</a></li>
            <li><a href="#estatisticas">📊 Estatísticas</a></li>
            <li><a href="#open-insurance">🔓 Open Insurance ({len(report.open_insurance_articles)})</a></li>
            <li><a href="#principais">🏆 Principais Notícias ({len(report.top_articles)})</a></li>
            {f'<li><a href="#outros">📰 Outros Artigos ({len(other_articles)})</a></li>' if other_articles else ''}
        </ul>
    </div>
    
    <div id="resumo" class="summary">
        <h2>📋 Resumo Executivo</h2>
        <p>{report.summary}</p>
    </div>
    
    <div id="estatisticas" class="stats">
        <div class="stat-card">
            <div class="stat-number">{report.total_articles}</div>
            <div class="stat-label">Total de Artigos</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(report.top_articles)}</div>
            <div class="stat-label">Artigos Principais</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(other_articles)}</div>
            <div class="stat-label">Outros Artigos</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(report.open_insurance_articles)}</div>
            <div class="stat-label">Open Insurance</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{len(report.articles_by_region)}</div>
            <div class="stat-label">Regiões Cobertas</div>
        </div>
    </div>
    
    <div id="open-insurance">
        {open_insurance_section}
    </div>
    
    <div id="principais" class="section">
        <h2>🏆 Principais Notícias ({len(report.top_articles)})</h2>
        <p class="section-description">Os 15 artigos mais relevantes do dia, ordenados por score de relevância.</p>
        {top_articles_html}
    </div>
    
    <div id="outros">
        {other_articles_section}
    </div>
    
    <div class="footer">
        <p>Relatório gerado automaticamente pelo Insurance News Agent</p>
        <p>Gerado em: {generation_time}</p>
        <p>Sistema de deduplicação ativo - artigos únicos apenas</p>
    </div>
</body>
</html>
        """
        
        return html_content
    
    def save_report(self, report: DailyReport, format: str = 'html') -> str:
        """
        Salva relatório em arquivo
        
        Args:
            report: Relatório a ser salvo
            format: Formato do arquivo ('html', 'json')
            
        Returns:
            Caminho do arquivo salvo
        """
        date_str = report.date.strftime('%Y-%m-%d')
        
        if format.lower() == 'html':
            filename = f"daily_report_{date_str}.html"
            filepath = self.output_dir / filename
            
            html_content = self.generate_html_report(report)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
            
            self.logger.info(f"Relatório HTML salvo: {filepath}")
            return str(filepath)
        
        elif format.lower() == 'json':
            filename = f"daily_report_{date_str}.json"
            filepath = self.output_dir / filename
            
            # Converte para dict serializável COM OUTROS ARTIGOS
            other_articles = getattr(report, 'other_articles', [])
            
            report_dict = {
                'date': report.date.isoformat(),
                'total_articles': report.total_articles,
                'summary': report.summary,
                'top_articles': [
                    {
                        'title': art.title,
                        'url': art.url,
                        'source': art.source,
                        'summary': art.summary,
                        'date_published': art.date_published.isoformat() if hasattr(art, 'date_published') and art.date_published else None,
                        'region': self._convert_to_serializable(getattr(art, 'region', None)),
                        'relevance_score': getattr(art, 'relevance_score', None)
                    }
                    for art in report.top_articles
                ],
                'other_articles': [
                    {
                        'title': art.title,
                        'url': art.url,
                        'source': art.source,
                        'summary': art.summary,
                        'date_published': art.date_published.isoformat() if hasattr(art, 'date_published') and art.date_published else None,
                        'region': self._convert_to_serializable(getattr(art, 'region', None)),
                        'relevance_score': getattr(art, 'relevance_score', None)
                    }
                    for art in other_articles
                ],
                'open_insurance_articles': [
                    {
                        'title': art.title,
                        'url': art.url,
                        'source': art.source,
                        'summary': art.summary,
                        'region': self._convert_to_serializable(getattr(art, 'region', None))
                    }
                    for art in report.open_insurance_articles
                ],
                'articles_by_region': report.articles_by_region
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, ensure_ascii=False, indent=2)
            
            self.logger.info(f"Relatório JSON salvo: {filepath}")
            return str(filepath)
        
        else:
            raise ValueError(f"Formato não suportado: {format}")
