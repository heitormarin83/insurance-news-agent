"""
Scheduler para execução automática no Railway
Executa coleta diária e outras tarefas agendadas
"""

import os
import time
import schedule
from datetime import datetime
from pathlib import Path

from src.main import InsuranceNewsAgent
from src.email_sender.email_manager import EmailManager
from src.utils.logger import get_logger

logger = get_logger("scheduler")


class InsuranceNewsScheduler:
    """Scheduler para execução automática"""
    
    def __init__(self):
        """Inicializa o scheduler"""
        self.agent = InsuranceNewsAgent()
        self.email_manager = EmailManager()
        
        # Configurações do ambiente
        self.timezone = os.getenv('TIMEZONE', 'America/Sao_Paulo')
        self.daily_time = os.getenv('DAILY_COLLECTION_TIME', '08:00')
        self.enable_email = os.getenv('ENABLE_EMAIL', 'true').lower() == 'true'
        
        logger.info("📅 Insurance News Scheduler inicializado")
        logger.info(f"⏰ Horário da coleta diária: {self.daily_time}")
        logger.info(f"📧 E-mail habilitado: {self.enable_email}")
    
    def daily_collection_job(self):
        """Job de coleta diária"""
        try:
            logger.info("🚀 Iniciando coleta diária agendada")
            
            # Executa coleta
            result = self.agent.run_daily_collection()
            
            if result['success']:
                logger.info(f"✅ Coleta diária concluída: {result['total_articles_collected']} artigos")
                
                # Envia e-mail se habilitado
                if self.enable_email:
                    try:
                        if self.email_manager.authenticate():
                            success = self.email_manager.send_daily_report(result['daily_report'])
                            
                            if success:
                                logger.info("📧 E-mail diário enviado com sucesso")
                                
                                # Envia alerta Open Insurance se houver
                                if result['open_insurance_articles_count'] > 0:
                                    open_insurance_articles = [
                                        article for article in result['daily_report'].top_articles 
                                        if article.open_insurance_related
                                    ]
                                    
                                    if open_insurance_articles:
                                        alert_success = self.email_manager.send_open_insurance_alert(open_insurance_articles)
                                        if alert_success:
                                            logger.info("🚨 Alerta Open Insurance enviado")
                            else:
                                logger.error("❌ Falha no envio do e-mail diário")
                        else:
                            logger.error("❌ Falha na autenticação do e-mail")
                    
                    except Exception as e:
                        logger.error(f"❌ Erro no envio de e-mail: {e}")
                        
                        # Tenta enviar notificação de erro
                        try:
                            self.email_manager.send_error_notification({
                                'error': 'Erro no envio do e-mail diário',
                                'details': str(e)
                            })
                        except:
                            pass
            else:
                logger.error("❌ Falha na coleta diária")
                
                # Envia notificação de erro
                if self.enable_email:
                    try:
                        if self.email_manager.authenticate():
                            self.email_manager.send_error_notification({
                                'error': 'Falha na coleta diária de notícias',
                                'details': 'A coleta diária falhou. Verifique os logs para mais detalhes.'
                            })
                    except Exception as e:
                        logger.error(f"❌ Erro ao enviar notificação de erro: {e}")
        
        except Exception as e:
            logger.error(f"❌ Erro crítico na coleta diária: {e}")
            
            # Tenta enviar notificação de erro crítico
            if self.enable_email:
                try:
                    if self.email_manager.authenticate():
                        self.email_manager.send_error_notification({
                            'error': 'Erro crítico no sistema',
                            'details': f'Erro crítico durante a execução: {str(e)}'
                        })
                except:
                    pass
    
    def weekly_source_test_job(self):
        """Job de teste semanal das fontes"""
        try:
            logger.info("🧪 Iniciando teste semanal das fontes")
            
            result = self.agent.test_sources()
            
            # Conta fontes com problemas
            failed_sources = sum(1 for source_result in result.values() if not source_result.get('success', False))
            total_sources = len(result)
            
            logger.info(f"📊 Teste concluído: {total_sources - failed_sources}/{total_sources} fontes funcionando")
            
            # Envia notificação se muitas fontes falharam
            if failed_sources > 5 and self.enable_email:
                try:
                    if self.email_manager.authenticate():
                        self.email_manager.send_error_notification({
                            'error': f'Muitas fontes com problemas: {failed_sources}/{total_sources}',
                            'details': f'Teste semanal identificou {failed_sources} fontes com problemas de {total_sources} total.'
                        })
                        logger.info("🚨 Notificação de fontes com problemas enviada")
                except Exception as e:
                    logger.error(f"❌ Erro ao enviar notificação de teste: {e}")
        
        except Exception as e:
            logger.error(f"❌ Erro no teste semanal: {e}")
    
    def setup_schedule(self):
        """Configura agendamentos"""
        try:
            # Coleta diária
            schedule.every().day.at(self.daily_time).do(self.daily_collection_job)
            logger.info(f"📅 Coleta diária agendada para {self.daily_time}")
            
            # Teste semanal das fontes (segunda-feira às 06:00)
            schedule.every().monday.at("06:00").do(self.weekly_source_test_job)
            logger.info("📅 Teste semanal agendado para segunda-feira às 06:00")
            
            # Log de status a cada hora
            schedule.every().hour.do(self.log_status)
            
        except Exception as e:
            logger.error(f"❌ Erro ao configurar agendamentos: {e}")
    
    def log_status(self):
        """Log de status do sistema"""
        try:
            stats = self.agent.get_statistics()
            logger.info(f"💓 Sistema ativo - {stats['total_sources']} fontes configuradas")
        except Exception as e:
            logger.error(f"❌ Erro no log de status: {e}")
    
    def run(self):
        """Executa o scheduler"""
        logger.info("🚀 Iniciando Insurance News Scheduler")
        
        # Configura agendamentos
        self.setup_schedule()
        
        # Cria diretórios necessários
        Path('data/reports').mkdir(parents=True, exist_ok=True)
        Path('logs').mkdir(parents=True, exist_ok=True)
        Path('config').mkdir(parents=True, exist_ok=True)
        
        # Log inicial
        logger.info("📊 Scheduler configurado e em execução")
        logger.info(f"⏰ Próxima execução: {schedule.next_run()}")
        
        # Loop principal
        while True:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verifica a cada minuto
                
            except KeyboardInterrupt:
                logger.info("⏹️ Scheduler interrompido pelo usuário")
                break
            
            except Exception as e:
                logger.error(f"❌ Erro no loop do scheduler: {e}")
                time.sleep(300)  # Espera 5 minutos antes de tentar novamente


def main():
    """Função principal"""
    # Configuração de ambiente
    os.environ.setdefault('TZ', 'America/Sao_Paulo')
    
    # Inicia scheduler
    scheduler = InsuranceNewsScheduler()
    scheduler.run()


if __name__ == "__main__":
    main()

