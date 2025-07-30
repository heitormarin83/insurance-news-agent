"""
Sistema principal do Insurance News Agent
VERSÃO COM DEDUPLICAÇÃO INTEGRADA
"""

import asyncio
from typing import List, Dict, Any
from datetime import datetime
import time

from src.models import NewsArticle, ScrapingResult
from src.scrapers import ScraperFactory
from src.analyzers import NewsAnalyzer, ReportGenerator
from src.utils.config_loader import config_loader
from src.utils.logger import get_logger

# Importa o sistema de deduplicação
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from deduplication_manager import DeduplicationManager

logger = get_logger("main")


class InsuranceNewsAgent:
    """Agente principal para coleta e processamento de notícias de seguros"""
    
    def __init__(self):
        """Inicializa o agente de notícias"""
        self.config = config_loader.load_sources_config()
        self.global_settings = config_loader.get_global_settings()
        self.analyzer = NewsAnalyzer()
        self.report_generator = ReportGenerator()
        
        # Inicializa sistema de deduplicação
        self.deduplication_manager = DeduplicationManager()
        
        logger.info("Insurance News Agent inicializado com sistema de deduplicação")
    
    def run_daily_collection(self) -> Dict[str, Any]:
        """
        Executa coleta diária de notícias COM DEDUPLICAÇÃO
        
        Returns:
            Resultado da coleta e processamento
        """
        start_time = time.time()
        
        logger.info("🚀 Iniciando coleta diária de notícias de seguros")
        
        # Limpeza automática do histórico (mantém 30 dias)
        self.deduplication_manager.cleanup_old_entries(days_to_keep=30)
        
        # Coleta notícias de todas as fontes
        all_articles = []
        scraping_results = []
        
        enabled_sources = config_loader.get_enabled_sources()
        
        logger.info(f"📡 Coletando de {len(enabled_sources)} fontes habilitadas")
        
        for source_name, source_config in enabled_sources.items():
            try:
                logger.info(f"🔍 Processando fonte: {source_name}")
                
                # Cria scraper para a fonte
                scraper = ScraperFactory.create_scraper(source_config)
                
                # Executa scraping
                result = scraper.scrape()
                scraping_results.append(result)
                
                if result.success:
                    all_articles.extend(result.articles)
                    logger.info(f"✅ {source_name}: {result.articles_found} artigos coletados "
                               f"em {result.execution_time:.2f}s")
                else:
                    logger.error(f"❌ {source_name}: {result.error_message}")
                
                # Delay entre fontes para ser respeitoso
                time.sleep(self.global_settings.get('delay_between_requests', 2))
                
            except Exception as e:
                logger.error(f"💥 Erro ao processar fonte {source_name}: {e}")
                continue
        
        logger.info(f"📊 Total coletado: {len(all_articles)} artigos de {len(scraping_results)} fontes")
        
        # APLICAR DEDUPLICAÇÃO
        logger.info("🔍 Aplicando filtro de deduplicação...")
        unique_articles = self.deduplication_manager.filter_duplicates(all_articles)
        
        if len(unique_articles) < len(all_articles):
            duplicates_removed = len(all_articles) - len(unique_articles)
            logger.info(f"🗑️ Removidos {duplicates_removed} artigos duplicados")
        
        # Análise e geração de relatório
        logger.info(f"📊 Analisando {len(unique_articles)} artigos únicos")
        
        # Gera relatório diário
        daily_report = self.report_generator.generate_daily_report(unique_articles)
        
        # Salva relatório
        html_path = self.report_generator.save_report(daily_report, format='html')
        json_path = self.report_generator.save_report(daily_report, format='json')
        
        # MARCA ARTIGOS COMO ENVIADOS
        logger.info("📝 Marcando artigos como enviados no histórico...")
        self.deduplication_manager.mark_as_sent(unique_articles)
        
        execution_time = time.time() - start_time
        
        # Estatísticas de deduplicação
        dedup_stats = self.deduplication_manager.get_statistics()
        
        # Resultado final
        result = {
            'success': True,
            'execution_time': execution_time,
            'total_sources_processed': len(scraping_results),
            'successful_sources': sum(1 for r in scraping_results if r.success),
            'total_articles_collected': len(all_articles),
            'unique_articles_after_dedup': len(unique_articles),
            'duplicates_removed': len(all_articles) - len(unique_articles),
            'top_articles_count': len(daily_report.top_articles),
            'other_articles_count': len(getattr(daily_report, 'other_articles', [])),
            'open_insurance_count': len(daily_report.open_insurance_articles),
            'html_report_path': html_path,
            'json_report_path': json_path,
            'deduplication_stats': dedup_stats
        }
        
        logger.info(f"🎉 Coleta diária concluída em {execution_time:.2f}s")
        logger.info(f"📈 Estatísticas: {result['successful_sources']}/{result['total_sources_processed']} fontes bem-sucedidas, "
                   f"{result['unique_articles_after_dedup']} artigos únicos")
        
        return result
    
    def collect_from_source(self, source_name: str) -> ScrapingResult:
        """
        Coleta notícias de uma fonte específica
        
        Args:
            source_name: Nome da fonte para coletar
            
        Returns:
            Resultado da coleta
        """
        logger.info(f"🎯 Coletando de fonte específica: {source_name}")
        
        enabled_sources = config_loader.get_enabled_sources()
        
        if source_name not in enabled_sources:
            error_msg = f"Fonte '{source_name}' não encontrada ou não habilitada"
            logger.error(error_msg)
            return ScrapingResult(
                source=source_name,
                success=False,
                articles_found=0,
                error_message=error_msg
            )
        
        try:
            source_config = enabled_sources[source_name]
            scraper = ScraperFactory.create_scraper(source_config)
            result = scraper.scrape()
            
            if result.success:
                logger.info(f"✅ {source_name}: {result.articles_found} artigos coletados")
                
                # Aplica deduplicação também para fonte específica
                unique_articles = self.deduplication_manager.filter_duplicates(result.articles)
                result.articles = unique_articles
                result.articles_found = len(unique_articles)
                
            return result
            
        except Exception as e:
            error_msg = f"Erro ao coletar de {source_name}: {e}"
            logger.error(error_msg)
            return ScrapingResult(
                source=source_name,
                success=False,
                articles_found=0,
                error_message=error_msg
            )
    
    def test_sources(self) -> Dict[str, Any]:
        """
        Testa todas as fontes configuradas
        
        Returns:
            Resultado dos testes
        """
        logger.info("🧪 Testando todas as fontes configuradas")
        
        enabled_sources = config_loader.get_enabled_sources()
        test_results = {}
        
        for source_name, source_config in enabled_sources.items():
            try:
                logger.info(f"🔍 Testando fonte: {source_name}")
                
                scraper = ScraperFactory.create_scraper(source_config)
                result = scraper.scrape()
                
                test_results[source_name] = {
                    'success': result.success,
                    'articles_found': result.articles_found,
                    'execution_time': result.execution_time,
                    'error_message': result.error_message if not result.success else None
                }
                
                if result.success:
                    logger.info(f"✅ {source_name}: {result.articles_found} artigos")
                else:
                    logger.error(f"❌ {source_name}: {result.error_message}")
                
                # Delay entre testes
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"💥 Erro ao testar {source_name}: {e}")
                test_results[source_name] = {
                    'success': False,
                    'articles_found': 0,
                    'execution_time': 0,
                    'error_message': str(e)
                }
        
        successful_sources = sum(1 for r in test_results.values() if r['success'])
        
        return {
            'total_sources': len(test_results),
            'successful_sources': successful_sources,
            'success_rate': (successful_sources / len(test_results)) * 100 if test_results else 0,
            'results': test_results
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Retorna estatísticas do sistema
        
        Returns:
            Estatísticas do sistema
        """
        enabled_sources = config_loader.get_enabled_sources()
        
        # Estatísticas por região
        by_region = {}
        for source_config in enabled_sources.values():
            region = source_config.get('region', 'Não especificado')
            by_region[region] = by_region.get(region, 0) + 1
        
        # Estatísticas por tipo
        by_type = {}
        for source_config in enabled_sources.values():
            source_type = source_config.get('source_type', 'Não especificado')
            by_type[source_type] = by_type.get(source_type, 0) + 1
        
        # Estatísticas de deduplicação
        dedup_stats = self.deduplication_manager.get_statistics()
        
        return {
            'total_sources': len(enabled_sources),
            'sources_by_region': by_region,
            'sources_by_type': by_type,
            'global_settings': self.global_settings,
            'deduplication_stats': dedup_stats,
            'system_timestamp': datetime.now().isoformat()
        }


def main():
    """Função principal para execução standalone"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Insurance News Agent')
    parser.add_argument('--action', choices=['collect', 'test', 'stats'], 
                       default='collect', help='Ação a executar')
    parser.add_argument('--source', help='Nome da fonte específica para coletar')
    
    args = parser.parse_args()
    
    agent = InsuranceNewsAgent()
    
    if args.action == 'collect':
        if args.source:
            result = agent.collect_from_source(args.source)
            print(f"Resultado: {result.success}, Artigos: {result.articles_found}")
        else:
            result = agent.run_daily_collection()
            print(f"Coleta concluída: {result['unique_articles_after_dedup']} artigos únicos")
            print(f"Duplicatas removidas: {result['duplicates_removed']}")
    
    elif args.action == 'test':
        result = agent.test_sources()
        print(f"Testes: {result['successful_sources']}/{result['total_sources']} fontes OK")
    
    elif args.action == 'stats':
        stats = agent.get_statistics()
        print(f"Estatísticas: {stats['total_sources']} fontes configuradas")
        print(f"Por região: {stats['sources_by_region']}")
        print(f"Deduplicação: {stats['deduplication_stats']['total_sent']} artigos no histórico")


if __name__ == "__main__":
    main()
