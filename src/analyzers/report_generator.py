"""
Gerador de relatórios consolidados de notícias
"""

from typing import List, Dict, Any
from datetime import datetime
import json
from pathlib import Path

from src.models import NewsArticle, DailyReport
from src.analyzers.news_analyzer import NewsAnalyzer
from src.utils.logger import get_logger

logger = get_logger("report_generator")


class ReportGenerator:
    """Gerador de relatórios de notícias"""
    
    def __init__(self, output_dir: str = None):
        """
        Inicializa o gerador de relatórios
        
        Args:
            output_dir: Diretório para salvar relatórios
        """
        if output_dir is None:
            self.output_dir = Path(__file__).parent.parent.parent / "data" / "reports"
        else:
            self.output_dir = Path(output_dir)
        
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.analyzer = NewsAnalyzer()
        
        logger.info(f"Report Generator inicializado - Output: {self.output_dir}")
    
    def generate_daily_report(self, articles: List[NewsArticle], date: datetime = None) -> DailyReport:
        """
        Gera relatório diário consolidado
        
        Args:
            articles: Lista de artigos do dia
            date: Data do relatório (padrão: hoje)
            
        Returns:
            Relatório diário gerado
        """
        if date is None:
            date = datetime.now()
        
        logger.info(f"Gerando relatório diário para {date.strftime('%Y-%m-%d')} com {len(articles)} artigos")
        
        # Analisa artigos
        analysis = self.analyzer.analyze_articles(articles)
        
        # Filtra e seleciona principais artigos
        filtered_articles = self.analyzer.filter_articles(articles, {
            'min_relevance': 0.2,
            'max_per_source': 5
        })
        
        top_articles = self.analyzer.get_top_articles(filtered_articles, top_n=15)
        open_insurance_articles = [a for a in filtered_articles if a.open_insurance_related]
        
        # Gera resumo executivo
        summary = self._generate_executive_summary(analysis, top_articles, open_insurance_articles)
        
        # Cria relatório
        report = DailyReport(
            date=date,
            total_articles=len(articles),
            articles_by_region=analysis.get('by_region', {}),
            top_articles=top_articles,
            open_insurance_articles=open_insurance_articles,
            summary=summary
        )
        
        logger.info(f"Relatório diário gerado: {len(top_articles)} artigos principais, "
                   f"{len(open_insurance_articles)} sobre Open Insurance")
        
        return report
    
    def _generate_executive_summary(self, analysis: Dict[str, Any], 
                                   top_articles: List[NewsArticle],
                                   open_insurance_articles: List[NewsArticle]) -> str:
        """
        Gera resumo executivo do relatório
        
        Args:
            analysis: Análise dos artigos
            top_articles: Principais artigos
            open_insurance_articles: Artigos sobre Open Insurance
            
        Returns:
            Resumo executivo
        """
        summary_parts = []
        
        # Estatísticas gerais
        total = analysis.get('total_articles', 0)
        summary_parts.append(f"Foram coletados {total} artigos de notícias do mercado de seguros.")
        
        # Distribuição por região
        by_region = analysis.get('by_region', {})
        if by_region:
            region_text = []
            for region, stats in by_region.items():
                count = stats.get('count', 0)
                percentage = stats.get('percentage', 0)
                region_text.append(f"{region}: {count} artigos ({percentage:.1f}%)")
            
            summary_parts.append(f"Distribuição por região: {', '.join(region_text)}.")
        
        # Open Insurance
        open_insurance_stats = analysis.get('open_insurance_stats', {})
        oi_count = open_insurance_stats.get('count', 0)
        oi_percentage = open_insurance_stats.get('percentage', 0)
        
        if oi_count > 0:
            summary_parts.append(f"Foram identificados {oi_count} artigos relacionados a Open Insurance "
                                f"({oi_percentage:.1f}% do total).")
        else:
            summary_parts.append("Não foram identificados artigos específicos sobre Open Insurance hoje.")
        
        # Principais categorias
        by_category = analysis.get('by_category', {})
        if by_category:
            top_categories = sorted(by_category.items(), key=lambda x: x[1]['count'], reverse=True)[:3]
            category_text = []
            for category, stats in top_categories:
                count = stats.get('count', 0)
                category_text.append(f"{category} ({count})")
            
            summary_parts.append(f"Principais categorias: {', '.join(category_text)}.")
        
        # Qualidade dos dados
        quality = analysis.get('quality_metrics', {})
        recent_percentage = quality.get('recent_articles_percentage', 0)
        summary_parts.append(f"{recent_percentage:.1f}% dos artigos são das últimas 48 horas.")
        
        # Principais fontes
        by_source = analysis.get('by_source', {})
        if by_source:
            top_sources = sorted(by_source.items(), key=lambda x: x[1]['count'], reverse=True)[:3]
            source_text = []
            for source, stats in top_sources:
                count = stats.get('count', 0)
                source_text.append(f"{source} ({count})")
            
            summary_parts.append(f"Principais fontes: {', '.join(source_text)}.")
        
        return " ".join(summary_parts)
    
    def generate_html_report(self, report: DailyReport) -> str:
        """
        Gera relatório em formato HTML
        
        Args:
            report: Relatório diário
            
        Returns:
            HTML do relatório
        """
        html_template = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Relatório Diário - Notícias de Seguros</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            text-align: center;
        }
        .header h1 {
            margin: 0;
            font-size: 2.5em;
        }
        .header .date {
            font-size: 1.2em;
            opacity: 0.9;
            margin-top: 10px;
        }
        .summary {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .summary h2 {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: white;
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .stat-number {
            font-size: 2.5em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .section {
            background: white;
            padding: 25px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .section h2 {
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 10px;
            margin-bottom: 20px;
        }
        .article {
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 20px;
            background: #f8f9ff;
            border-radius: 0 5px 5px 0;
        }
        .article h3 {
            margin: 0 0 10px 0;
            color: #333;
        }
        .article a {
            color: #667eea;
            text-decoration: none;
        }
        .article a:hover {
            text-decoration: underline;
        }
        .article-meta {
            font-size: 0.9em;
            color: #666;
            margin-bottom: 10px;
        }
        .article-summary {
            color: #555;
            line-height: 1.5;
        }
        .badge {
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 0.8em;
            margin-right: 5px;
        }
        .open-insurance {
            border-left-color: #e74c3c;
        }
        .open-insurance .badge {
            background: #e74c3c;
        }
        .footer {
            text-align: center;
            color: #666;
            margin-top: 40px;
            padding: 20px;
        }
    </style>
</head>
<body>
    <div class="header">
        <h1>📊 Relatório Diário</h1>
        <div class="date">Notícias do Mercado de Seguros - {date}</div>
    </div>
    
    <div class="summary">
        <h2>📋 Resumo Executivo</h2>
        <p>{summary}</p>
    </div>
    
    <div class="stats">
        <div class="stat-card">
            <div class="stat-number">{total_articles}</div>
            <div class="stat-label">Total de Artigos</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{top_articles_count}</div>
            <div class="stat-label">Artigos Principais</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{open_insurance_count}</div>
            <div class="stat-label">Open Insurance</div>
        </div>
        <div class="stat-card">
            <div class="stat-number">{regions_count}</div>
            <div class="stat-label">Regiões Cobertas</div>
        </div>
    </div>
    
    {open_insurance_section}
    
    <div class="section">
        <h2>🏆 Principais Notícias</h2>
        {top_articles_html}
    </div>
    
    <div class="footer">
        <p>Relatório gerado automaticamente pelo Insurance News Agent</p>
        <p>Gerado em: {generation_time}</p>
    </div>
</body>
</html>
        """
        
        # Prepara dados para o template
        date_str = report.date.strftime('%d de %B de %Y')
        generation_time = datetime.now().strftime('%d/%m/%Y às %H:%M')
        
        # Gera HTML dos artigos principais
        top_articles_html = ""
        for i, article in enumerate(report.top_articles, 1):
            categories_html = "".join([f'<span class="badge">{cat}</span>' for cat in article.categories])
            
            top_articles_html += f"""
            <div class="article">
                <h3>{i}. <a href="{article.url}" target="_blank">{article.title}</a></h3>
                <div class="article-meta">
                    📍 {article.source} | {article.region.value} | 
                    📅 {article.date_published.strftime('%d/%m/%Y %H:%M')} | 
                    ⭐ Relevância: {article.relevance_score:.2f}
                </div>
                <div class="article-meta">{categories_html}</div>
                <div class="article-summary">{article.summary}</div>
            </div>
            """
        
        # Gera seção Open Insurance se houver artigos
        open_insurance_section = ""
        if report.open_insurance_articles:
            open_insurance_html = ""
            for i, article in enumerate(report.open_insurance_articles, 1):
                categories_html = "".join([f'<span class="badge">{cat}</span>' for cat in article.categories])
                
                open_insurance_html += f"""
                <div class="article open-insurance">
                    <h3>{i}. <a href="{article.url}" target="_blank">{article.title}</a></h3>
                    <div class="article-meta">
                        📍 {article.source} | {article.region.value} | 
                        📅 {article.date_published.strftime('%d/%m/%Y %H:%M')} | 
                        ⭐ Relevância: {article.relevance_score:.2f}
                    </div>
                    <div class="article-meta">{categories_html}</div>
                    <div class="article-summary">{article.summary}</div>
                </div>
                """
            
            open_insurance_section = f"""
            <div class="section">
                <h2>🔓 Open Insurance</h2>
                {open_insurance_html}
            </div>
            """
        
        # Preenche template
        html_content = html_template.format(
            date=date_str,
            summary=report.summary,
            total_articles=report.total_articles,
            top_articles_count=len(report.top_articles),
            open_insurance_count=len(report.open_insurance_articles),
            regions_count=len(report.articles_by_region),
            open_insurance_section=open_insurance_section,
            top_articles_html=top_articles_html,
            generation_time=generation_time
        )
        
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
        
        if format == 'html':
            filename = f"relatorio_seguros_{date_str}.html"
            filepath = self.output_dir / filename
            
            html_content = self.generate_html_report(report)
            
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(html_content)
        
        elif format == 'json':
            filename = f"relatorio_seguros_{date_str}.json"
            filepath = self.output_dir / filename
            
            # Converte para dicionário serializável
            report_dict = {
                'date': report.date.isoformat(),
                'total_articles': report.total_articles,
                'articles_by_region': report.articles_by_region,
                'summary': report.summary,
                'top_articles': [
                    {
                        'title': a.title,
                        'url': a.url,
                        'source': a.source,
                        'region': a.region.value,
                        'date_published': a.date_published.isoformat(),
                        'summary': a.summary,
                        'categories': a.categories,
                        'relevance_score': a.relevance_score,
                        'open_insurance_related': a.open_insurance_related
                    }
                    for a in report.top_articles
                ],
                'open_insurance_articles': [
                    {
                        'title': a.title,
                        'url': a.url,
                        'source': a.source,
                        'region': a.region.value,
                        'date_published': a.date_published.isoformat(),
                        'summary': a.summary,
                        'categories': a.categories,
                        'relevance_score': a.relevance_score
                    }
                    for a in report.open_insurance_articles
                ]
            }
            
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(report_dict, f, ensure_ascii=False, indent=2)
        
        else:
            raise ValueError(f"Formato não suportado: {format}")
        
        logger.info(f"Relatório salvo: {filepath}")
        return str(filepath)
    
    def generate_email_content(self, report: DailyReport) -> Dict[str, str]:
        """
        Gera conteúdo para e-mail baseado no relatório
        
        Args:
            report: Relatório diário
            
        Returns:
            Dicionário com subject e body do e-mail
        """
        date_str = report.date.strftime('%d/%m/%Y')
        
        # Subject
        subject = f"📊 Relatório Diário de Seguros - {date_str}"
        if report.open_insurance_articles:
            subject += f" | {len(report.open_insurance_articles)} Open Insurance"
        
        # Body em HTML
        body = self.generate_html_report(report)
        
        return {
            'subject': subject,
            'body': body
        }

