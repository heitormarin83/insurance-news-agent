#!/usr/bin/env python3
"""
Script para coleta manual de fontes específicas
"""

import sys
import argparse
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.main import InsuranceNewsAgent
from src.utils.config_loader import config_loader
from src.utils.logger import get_logger

logger = get_logger("manual_collection")


def main():
    """Função principal"""
    parser = argparse.ArgumentParser(description='Coleta manual de notícias')
    parser.add_argument('--sources', help='Fontes específicas (separadas por vírgula)')
    parser.add_argument('--region', help='Filtrar por região')
    
    args = parser.parse_args()
    
    try:
        logger.info("🔧 Iniciando coleta manual")
        
        agent = InsuranceNewsAgent()
        
        if args.sources and args.sources != 'all':
            # Coleta de fontes específicas
            source_names = [s.strip() for s in args.sources.split(',')]
            logger.info(f"📡 Coletando fontes específicas: {source_names}")
            
            all_articles = []
            for source_name in source_names:
                try:
                    result = agent.collect_from_source(source_name)
                    if result.success:
                        all_articles.extend(result.articles)
                        logger.info(f"✅ {source_name}: {result.articles_found} artigos")
                    else:
                        logger.error(f"❌ {source_name}: {result.error_message}")
                except Exception as e:
                    logger.error(f"❌ Erro em {source_name}: {e}")
            
            # Gera relatório com artigos coletados
            if all_articles:
                daily_report = agent.report_generator.generate_daily_report(all_articles)
                html_path = agent.report_generator.save_report(daily_report, format='html')
                json_path = agent.report_generator.save_report(daily_report, format='json')
                
                logger.info(f"📊 Relatório gerado: {len(all_articles)} artigos")
                logger.info(f"💾 Relatórios salvos: {html_path}, {json_path}")
            
        elif args.region and args.region != 'all':
            # Coleta por região
            logger.info(f"🌍 Coletando por região: {args.region}")
            
            enabled_sources = config_loader.get_enabled_sources()
            region_sources = {name: config for name, config in enabled_sources.items() 
                            if config.get('region') == args.region}
            
            logger.info(f"📡 Fontes da região {args.region}: {len(region_sources)}")
            
            all_articles = []
            for source_name in region_sources.keys():
                try:
                    result = agent.collect_from_source(source_name)
                    if result.success:
                        all_articles.extend(result.articles)
                        logger.info(f"✅ {source_name}: {result.articles_found} artigos")
                    else:
                        logger.error(f"❌ {source_name}: {result.error_message}")
                except Exception as e:
                    logger.error(f"❌ Erro em {source_name}: {e}")
            
            # Gera relatório
            if all_articles:
                daily_report = agent.report_generator.generate_daily_report(all_articles)
                html_path = agent.report_generator.save_report(daily_report, format='html')
                json_path = agent.report_generator.save_report(daily_report, format='json')
                
                logger.info(f"📊 Relatório gerado: {len(all_articles)} artigos")
                logger.info(f"💾 Relatórios salvos: {html_path}, {json_path}")
        
        else:
            # Coleta completa
            logger.info("📡 Executando coleta completa")
            result = agent.run_daily_collection()
            
            if result['success']:
                logger.info(f"✅ Coleta concluída: {result['total_articles_collected']} artigos")
            else:
                logger.error("❌ Falha na coleta")
                sys.exit(1)
        
        print("SUCCESS: Coleta manual concluída")
    
    except Exception as e:
        logger.error(f"❌ Erro na coleta manual: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

