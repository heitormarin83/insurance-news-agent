"""
Sistema principal do Insurance News Agent
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

logger = get_logger("main")


class InsuranceNewsAgent:
    """Agente principal para coleta e processamento de notícias de seguros"""
    
    def __init__(self):
        """Inicializa o agente de notícias"""
        self.config = config_loader.load_sources_config()
        self.global_settings = config_loader.get_global_settings()
        self.analyzer = NewsAnalyzer()
        self.report_generator = ReportGenerator()
        
        logger.info("Insurance News Agent inicializado")
    
    def run_daily_collection(self) -> Dict[str, Any]:
        """
        Executa coleta diária de notícias
        
        Returns:
            Resultado da coleta e processamento
        """
        start_time = time.time()
        
        logger.info("🚀 Iniciando coleta diária de notícias de seguros")
        
        # Coleta notícias de todas as fontes
        all_articles = []
        scraping_results = []
        
        enabled_sources = config_loader.get_enabled_sources()
        
        logger.info(f"📡 Coletando de {len(enabled_sources)} fontes habilitadas")
        
        for source_name, source_config in enabled_sources.items():
            try:
                logger.info(f"🔍 Processando fonte: {source_name}")
                
                # Cria scraper apropriado
                scraper = ScraperFactory.create_scraper(source_config)
                
                if not scraper:
                    logger.warning(f"❌ Não foi possível criar scraper para {source_name}")
                    continue
                
                if not scraper.is_enabled():
                    logger.info(f"⏭️ Fonte desabilitada: {source_name}")
                    continue
                
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
        
        # Análise e geração de relatório
        logger.info(f"📊 Analisando {len(all_articles)} artigos coletados")
        
        # Gera relatório diário
        daily_report = self.report_generator.generate_daily_report(all_articles)
        
        # Salva relatório
        html_path = self.report_generator.save_report(daily_report, format='html')
        json_path = self.report_generator.save_report(daily_report, format='json')
        
        execution_time = time.time() - start_time
        
        # Resultado final
        result = {
            'success': True,
            'execution_time': execution_time,
            'total_sources_processed': len(scraping_results),
            'successful_sources': sum(1 for r in scraping_results if r.success),
            'total_articles_collected': len(all_articles),
            'top_articles_count': len(daily_report.top_articles),
            'open_insurance_articles_count': len(daily_report.open_insurance_articles),
            'report_html_path': html_path,
            'report_json_path': json_path,
            'daily_report': daily_report,
            'scraping_results': scraping_results
        }
        
        logger.info(f"🎉 Coleta diária concluída em {execution_time:.2f}s")
        logger.info(f"📈 Estatísticas: {result['successful_sources']}/{result['total_sources_processed']} "
                   f"fontes bem-sucedidas, {result['total_articles_collected']} artigos coletados")
        
        return result
    
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
                
                # Cria scraper
                scraper = ScraperFactory.create_scraper(source_config)
                
                if not scraper:
                    test_results[source_name] = {
                        'success': False,
                        'error': 'Não foi possível criar scraper'
                    }
                    continue
                
                # Testa conexão básica
                start_time = time.time()
                response = scraper._make_request(scraper.url)
                test_time = time.time() - start_time
                
                if response:
                    test_results[source_name] = {
                        'success': True,
                        'status_code': response.status_code,
                        'response_time': round(test_time, 2),
                        'content_length': len(response.content),
                        'source_type': source_config.get('source_type'),
                        'region': source_config.get('region')
                    }
                    logger.info(f"✅ {source_name}: OK ({response.status_code}) em {test_time:.2f}s")
                else:
                    test_results[source_name] = {
                        'success': False,
                        'error': 'Falha na requisição HTTP'
                    }
                    logger.warning(f"❌ {source_name}: Falha na conexão")
                
            except Exception as e:
                test_results[source_name] = {
                    'success': False,
                    'error': str(e)
                }
                logger.error(f"💥 {source_name}: {e}")
        
        # Estatísticas dos testes
        total_sources = len(test_results)
        successful_sources = sum(1 for r in test_results.values() if r.get('success', False))
        
        summary = {
            'total_sources': total_sources,
            'successful_sources': successful_sources,
            'success_rate': (successful_sources / total_sources) * 100 if total_sources > 0 else 0,
            'test_timestamp': datetime.now().isoformat(),
            'results': test_results
        }
        
        logger.info(f"🧪 Testes concluídos: {successful_sources}/{total_sources} "
                   f"fontes funcionando ({summary['success_rate']:.1f}%)")
        
        return summary
    
    def collect_from_source(self, source_name: str) -> ScrapingResult:
        """
        Coleta notícias de uma fonte específica
        
        Args:
            source_name: Nome da fonte
            
        Returns:
            Resultado do scraping
        """
        try:
            source_config = config_loader.get_source_by_name(source_name)
            
            scraper = ScraperFactory.create_scraper(source_config)
            
            if not scraper:
                return ScrapingResult(
                    source=source_name,
                    success=False,
                    articles_found=0,
                    error_message="Não foi possível criar scraper"
                )
            
            logger.info(f"🔍 Coletando de fonte específica: {source_name}")
            
            result = scraper.scrape()
            
            if result.success:
                logger.info(f"✅ {source_name}: {result.articles_found} artigos coletados")
            else:
                logger.error(f"❌ {source_name}: {result.error_message}")
            
            return result
            
        except Exception as e:
            logger.error(f"💥 Erro ao coletar de {source_name}: {e}")
            return ScrapingResult(
                source=source_name,
                success=False,
                articles_found=0,
                error_message=str(e)
            )
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtém estatísticas do sistema
        
        Returns:
            Estatísticas do sistema
        """
        enabled_sources = config_loader.get_enabled_sources()
        
        # Conta fontes por região
        by_region = {}
        by_type = {}
        
        for source_name, source_config in enabled_sources.items():
            region = source_config.get('region', 'Unknown')
            source_type = source_config.get('source_type', 'Unknown')
            
            by_region[region] = by_region.get(region, 0) + 1
            by_type[source_type] = by_type.get(source_type, 0) + 1
        
        return {
            'total_sources': len(enabled_sources),
            'sources_by_region': by_region,
            'sources_by_type': by_type,
            'global_settings': self.global_settings,
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
            print(f"Coleta concluída: {result['total_articles_collected']} artigos")
    
    elif args.action == 'test':
        result = agent.test_sources()
        print(f"Testes: {result['successful_sources']}/{result['total_sources']} fontes OK")
    
    elif args.action == 'stats':
        stats = agent.get_statistics()
        print(f"Estatísticas: {stats['total_sources']} fontes configuradas")
        print(f"Por região: {stats['sources_by_region']}")


if __name__ == "__main__":
    main()

