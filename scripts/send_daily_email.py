#!/usr/bin/env python3
"""
Script para envio do relatório diário por e-mail
"""

import sys
import json
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.email_sender.email_manager import EmailManager
from src.models import DailyReport, NewsArticle, Region
from src.utils.logger import get_logger

logger = get_logger("send_daily_email")


def load_daily_report() -> DailyReport:
    """Carrega relatório diário do arquivo JSON"""
    
    date_str = datetime.now().strftime('%Y-%m-%d')
    report_path = Path(f'data/reports/relatorio_seguros_{date_str}.json')
    
    if not report_path.exists():
        raise FileNotFoundError(f"Relatório não encontrado: {report_path}")
    
    with open(report_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Converte artigos de volta para objetos NewsArticle
    top_articles = []
    for article_data in data.get('top_articles', []):
        article = NewsArticle(
            title=article_data['title'],
            url=article_data['url'],
            source=article_data['source'],
            region=Region(article_data['region']),
            date_published=datetime.fromisoformat(article_data['date_published']),
            summary=article_data['summary'],
            categories=article_data['categories'],
            relevance_score=article_data['relevance_score'],
            open_insurance_related=article_data['open_insurance_related']
        )
        top_articles.append(article)
    
    # Converte artigos Open Insurance
    open_insurance_articles = []
    for article_data in data.get('open_insurance_articles', []):
        article = NewsArticle(
            title=article_data['title'],
            url=article_data['url'],
            source=article_data['source'],
            region=Region(article_data['region']),
            date_published=datetime.fromisoformat(article_data['date_published']),
            summary=article_data['summary'],
            categories=article_data['categories'],
            relevance_score=article_data['relevance_score'],
            open_insurance_related=True
        )
        open_insurance_articles.append(article)
    
    # Cria objeto DailyReport
    report = DailyReport(
        date=datetime.fromisoformat(data['date']),
        total_articles=data['total_articles'],
        articles_by_region=data['articles_by_region'],
        top_articles=top_articles,
        open_insurance_articles=open_insurance_articles,
        summary=data['summary']
    )
    
    return report


def main():
    """Função principal"""
    try:
        logger.info("🚀 Iniciando envio de e-mail diário")
        
        # Carrega relatório
        report = load_daily_report()
        logger.info(f"📊 Relatório carregado: {report.total_articles} artigos, "
                   f"{len(report.open_insurance_articles)} Open Insurance")
        
        # Inicializa gerenciador de e-mail
        email_manager = EmailManager()
        
        # Autentica
        if not email_manager.authenticate():
            logger.error("❌ Falha na autenticação do e-mail")
            sys.exit(1)
        
        # Valida configuração
        validation = email_manager.validate_configuration()
        if not validation['valid']:
            logger.error(f"❌ Configuração inválida: {validation['issues']}")
            sys.exit(1)
        
        logger.info(f"📧 Destinatários configurados: {validation['recipients_count']}")
        
        # Envia relatório diário
        success = email_manager.send_daily_report(report)
        
        if success:
            logger.info("✅ E-mail diário enviado com sucesso")
            
            # Envia alerta Open Insurance se houver artigos
            if report.open_insurance_articles:
                logger.info(f"🚨 Enviando alerta Open Insurance: {len(report.open_insurance_articles)} artigos")
                alert_success = email_manager.send_open_insurance_alert(report.open_insurance_articles)
                
                if alert_success:
                    logger.info("✅ Alerta Open Insurance enviado")
                else:
                    logger.error("❌ Falha no envio do alerta Open Insurance")
            
            print("SUCCESS: E-mail enviado com sucesso")
        else:
            logger.error("❌ Falha no envio do e-mail")
            sys.exit(1)
    
    except FileNotFoundError as e:
        logger.error(f"❌ Arquivo não encontrado: {e}")
        sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Erro inesperado: {e}")
        
        # Tenta enviar notificação de erro
        try:
            email_manager = EmailManager()
            if email_manager.authenticate():
                email_manager.send_error_notification({
                    'error': 'Erro no envio do e-mail diário',
                    'details': str(e)
                })
        except:
            pass
        
        sys.exit(1)


if __name__ == "__main__":
    main()

