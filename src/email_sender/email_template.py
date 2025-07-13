"""
Sistema de templates para e-mails de notícias de seguros
"""

from typing import List, Dict, Any
from datetime import datetime
from src.models import NewsArticle, DailyReport
from src.utils.logger import get_logger

logger = get_logger("email_template")


class EmailTemplate:
    """Gerador de templates para e-mails"""
    
    def __init__(self):
        """Inicializa o gerador de templates"""
        logger.info("Email Template inicializado")
    
    def generate_daily_report_email(self, report: DailyReport) -> Dict[str, str]:
        """
        Gera e-mail do relatório diário
        
        Args:
            report: Relatório diário
            
        Returns:
            Dicionário com subject e body
        """
        date_str = report.date.strftime('%d/%m/%Y')
        
        # Subject
        subject = f"📊 Relatório Diário - Notícias de Seguros | {date_str}"
        if report.open_insurance_articles:
            subject += f" | {len(report.open_insurance_articles)} Open Insurance"
        
        # Body HTML
        body = self._generate_daily_report_html(report)
        
        return {
            'subject': subject,
            'body': body
        }
    
    def _generate_daily_report_html(self, report: DailyReport) -> str:
        """
        Gera HTML do relatório diário
        
        Args:
            report: Relatório diário
            
        Returns:
            HTML do e-mail
        """
        date_str = report.date.strftime('%d de %B de %Y')
        generation_time = datetime.now().strftime('%d/%m/%Y às %H:%M')
        
        # Template base
        html_template = """
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
            max-width: 800px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            border-radius: 10px;
            overflow: hidden;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }}
        .header h1 {{
            margin: 0;
            font-size: 2.2em;
        }}
        .header .date {{
            font-size: 1.1em;
            opacity: 0.9;
            margin-top: 10px;
        }}
        .content {{
            padding: 30px;
        }}
        .summary {{
            background: #f8f9ff;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 25px;
            border-left: 4px solid #667eea;
        }}
        .summary h2 {{
            color: #667eea;
            margin-top: 0;
            font-size: 1.3em;
        }}
        .stats {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: 15px;
            margin-bottom: 25px;
        }}
        .stat-card {{
            background: #f8f9ff;
            padding: 15px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e1e5f2;
        }}
        .stat-number {{
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
            display: block;
        }}
        .stat-label {{
            color: #666;
            font-size: 0.9em;
            margin-top: 5px;
        }}
        .section {{
            margin-bottom: 30px;
        }}
        .section h2 {{
            color: #667eea;
            border-bottom: 2px solid #667eea;
            padding-bottom: 8px;
            margin-bottom: 15px;
            font-size: 1.4em;
        }}
        .article {{
            border-left: 4px solid #667eea;
            padding: 15px;
            margin-bottom: 15px;
            background: #f8f9ff;
            border-radius: 0 5px 5px 0;
        }}
        .article h3 {{
            margin: 0 0 8px 0;
            font-size: 1.1em;
        }}
        .article a {{
            color: #667eea;
            text-decoration: none;
        }}
        .article a:hover {{
            text-decoration: underline;
        }}
        .article-meta {{
            font-size: 0.85em;
            color: #666;
            margin-bottom: 8px;
        }}
        .article-summary {{
            color: #555;
            line-height: 1.4;
            font-size: 0.95em;
        }}
        .badge {{
            display: inline-block;
            background: #667eea;
            color: white;
            padding: 2px 6px;
            border-radius: 10px;
            font-size: 0.75em;
            margin-right: 4px;
        }}
        .open-insurance {{
            border-left-color: #e74c3c;
        }}
        .open-insurance .badge {{
            background: #e74c3c;
        }}
        .footer {{
            background: #f8f9fa;
            padding: 20px;
            text-align: center;
            color: #666;
            font-size: 0.9em;
        }}
        .footer a {{
            color: #667eea;
            text-decoration: none;
        }}
        @media (max-width: 600px) {{
            body {{
                padding: 10px;
            }}
            .header {{
                padding: 20px;
            }}
            .header h1 {{
                font-size: 1.8em;
            }}
            .content {{
                padding: 20px;
            }}
            .stats {{
                grid-template-columns: repeat(2, 1fr);
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>📊 Relatório Diário</h1>
            <div class="date">Notícias do Mercado de Seguros - {date}</div>
        </div>
        
        <div class="content">
            <div class="summary">
                <h2>📋 Resumo Executivo</h2>
                <p>{summary}</p>
            </div>
            
            <div class="stats">
                <div class="stat-card">
                    <span class="stat-number">{total_articles}</span>
                    <div class="stat-label">Total de Artigos</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{top_articles_count}</span>
                    <div class="stat-label">Artigos Principais</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{open_insurance_count}</span>
                    <div class="stat-label">Open Insurance</div>
                </div>
                <div class="stat-card">
                    <span class="stat-number">{regions_count}</span>
                    <div class="stat-label">Regiões</div>
                </div>
            </div>
            
            {open_insurance_section}
            
            <div class="section">
                <h2>🏆 Principais Notícias</h2>
                {top_articles_html}
            </div>
        </div>
        
        <div class="footer">
            <p><strong>Insurance News Agent</strong> - Relatório gerado automaticamente</p>
            <p>Gerado em: {generation_time}</p>
            <p>Para dúvidas ou sugestões, entre em contato com a equipe responsável.</p>
        </div>
    </div>
</body>
</html>
        """
        
        # Gera HTML dos artigos principais
        top_articles_html = ""
        for i, article in enumerate(report.top_articles[:10], 1):  # Limita a 10 para e-mail
            categories_html = "".join([f'<span class="badge">{cat}</span>' for cat in article.categories[:3]])
            
            top_articles_html += f"""
            <div class="article">
                <h3>{i}. <a href="{article.url}" target="_blank">{article.title}</a></h3>
                <div class="article-meta">
                    📍 {article.source} | {article.region.value} | 
                    📅 {article.date_published.strftime('%d/%m/%Y %H:%M')} | 
                    ⭐ {article.relevance_score:.2f}
                </div>
                <div class="article-meta">{categories_html}</div>
                <div class="article-summary">{article.summary[:200]}{'...' if len(article.summary) > 200 else ''}</div>
            </div>
            """
        
        # Gera seção Open Insurance se houver artigos
        open_insurance_section = ""
        if report.open_insurance_articles:
            open_insurance_html = ""
            for i, article in enumerate(report.open_insurance_articles[:5], 1):  # Limita a 5
                categories_html = "".join([f'<span class="badge">{cat}</span>' for cat in article.categories[:3]])
                
                open_insurance_html += f"""
                <div class="article open-insurance">
                    <h3>{i}. <a href="{article.url}" target="_blank">{article.title}</a></h3>
                    <div class="article-meta">
                        📍 {article.source} | {article.region.value} | 
                        📅 {article.date_published.strftime('%d/%m/%Y %H:%M')} | 
                        ⭐ {article.relevance_score:.2f}
                    </div>
                    <div class="article-meta">{categories_html}</div>
                    <div class="article-summary">{article.summary[:200]}{'...' if len(article.summary) > 200 else ''}</div>
                </div>
                """
            
            open_insurance_section = f"""
            <div class="section">
                <h2>🔓 Open Insurance</h2>
                <p style="color: #e74c3c; font-weight: bold; margin-bottom: 15px;">
                    ⚠️ ARTIGOS SOBRE OPEN INSURANCE IDENTIFICADOS
                </p>
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
    
    def generate_alert_email(self, articles: List[NewsArticle], alert_type: str = "open_insurance") -> Dict[str, str]:
        """
        Gera e-mail de alerta para notícias importantes
        
        Args:
            articles: Lista de artigos importantes
            alert_type: Tipo de alerta
            
        Returns:
            Dicionário com subject e body
        """
        if alert_type == "open_insurance":
            subject = f"🚨 ALERTA: {len(articles)} Notícias sobre Open Insurance"
            title = "🔓 Alerta Open Insurance"
            description = "Foram identificadas notícias importantes sobre Open Insurance:"
        else:
            subject = f"🚨 ALERTA: {len(articles)} Notícias Importantes"
            title = "⚠️ Alerta de Notícias"
            description = "Foram identificadas notícias importantes no mercado de seguros:"
        
        # HTML do alerta
        articles_html = ""
        for i, article in enumerate(articles[:5], 1):
            categories_html = "".join([f'<span class="badge">{cat}</span>' for cat in article.categories[:3]])
            
            articles_html += f"""
            <div class="article">
                <h3>{i}. <a href="{article.url}" target="_blank">{article.title}</a></h3>
                <div class="article-meta">
                    📍 {article.source} | {article.region.value} | 
                    📅 {article.date_published.strftime('%d/%m/%Y %H:%M')} | 
                    ⭐ {article.relevance_score:.2f}
                </div>
                <div class="article-meta">{categories_html}</div>
                <div class="article-summary">{article.summary[:300]}{'...' if len(article.summary) > 300 else ''}</div>
            </div>
            """
        
        body = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Alerta - Insurance News Agent</title>
            <style>
                body {{
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 20px;
                    background-color: #f8f9fa;
                }}
                .container {{
                    background: white;
                    border-radius: 10px;
                    overflow: hidden;
                    box-shadow: 0 4px 6px rgba(0,0,0,0.1);
                }}
                .header {{
                    background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
                    color: white;
                    padding: 30px;
                    text-align: center;
                }}
                .header h1 {{
                    margin: 0;
                    font-size: 2.2em;
                }}
                .content {{
                    padding: 30px;
                }}
                .alert-box {{
                    background: #fff3cd;
                    border: 1px solid #ffeaa7;
                    border-radius: 8px;
                    padding: 20px;
                    margin-bottom: 25px;
                }}
                .article {{
                    border-left: 4px solid #e74c3c;
                    padding: 15px;
                    margin-bottom: 15px;
                    background: #fff5f5;
                    border-radius: 0 5px 5px 0;
                }}
                .article h3 {{
                    margin: 0 0 8px 0;
                    font-size: 1.1em;
                }}
                .article a {{
                    color: #e74c3c;
                    text-decoration: none;
                }}
                .article a:hover {{
                    text-decoration: underline;
                }}
                .article-meta {{
                    font-size: 0.85em;
                    color: #666;
                    margin-bottom: 8px;
                }}
                .article-summary {{
                    color: #555;
                    line-height: 1.4;
                    font-size: 0.95em;
                }}
                .badge {{
                    display: inline-block;
                    background: #e74c3c;
                    color: white;
                    padding: 2px 6px;
                    border-radius: 10px;
                    font-size: 0.75em;
                    margin-right: 4px;
                }}
                .footer {{
                    background: #f8f9fa;
                    padding: 20px;
                    text-align: center;
                    color: #666;
                    font-size: 0.9em;
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>{title}</h1>
                    <div>Insurance News Agent</div>
                </div>
                
                <div class="content">
                    <div class="alert-box">
                        <p><strong>{description}</strong></p>
                        <p>Total de artigos: <strong>{len(articles)}</strong></p>
                        <p>Horário do alerta: <strong>{datetime.now().strftime('%d/%m/%Y às %H:%M')}</strong></p>
                    </div>
                    
                    {articles_html}
                </div>
                
                <div class="footer">
                    <p><strong>Insurance News Agent</strong> - Alerta gerado automaticamente</p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return {
            'subject': subject,
            'body': body
        }
    
    def generate_error_email(self, error_details: Dict[str, Any]) -> Dict[str, str]:
        """
        Gera e-mail de erro do sistema
        
        Args:
            error_details: Detalhes do erro
            
        Returns:
            Dicionário com subject e body
        """
        subject = "🚨 ERRO - Insurance News Agent"
        
        body = f"""
        <!DOCTYPE html>
        <html lang="pt-BR">
        <head>
            <meta charset="UTF-8">
            <title>Erro - Insurance News Agent</title>
            <style>
                body {{
                    font-family: Arial, sans-serif;
                    line-height: 1.6;
                    color: #333;
                    max-width: 600px;
                    margin: 0 auto;
                    padding: 20px;
                }}
                .error-box {{
                    background: #f8d7da;
                    border: 1px solid #f5c6cb;
                    border-radius: 5px;
                    padding: 20px;
                    margin-bottom: 20px;
                }}
                .error-title {{
                    color: #721c24;
                    font-weight: bold;
                    font-size: 1.2em;
                }}
            </style>
        </head>
        <body>
            <div class="error-box">
                <div class="error-title">🚨 Erro no Insurance News Agent</div>
                <p><strong>Horário:</strong> {datetime.now().strftime('%d/%m/%Y às %H:%M')}</p>
                <p><strong>Erro:</strong> {error_details.get('error', 'Erro desconhecido')}</p>
                <p><strong>Detalhes:</strong> {error_details.get('details', 'Sem detalhes adicionais')}</p>
            </div>
            
            <p>Por favor, verifique o sistema e tome as ações necessárias.</p>
            
            <hr>
            <p><small>Insurance News Agent - Sistema de Monitoramento</small></p>
        </body>
        </html>
        """
        
        return {
            'subject': subject,
            'body': body
        }

