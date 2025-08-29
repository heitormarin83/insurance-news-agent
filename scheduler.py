"""
Scheduler para execução automática de tarefas do Insurance News Agent
Versão corrigida - campos corretos do modelo
"""

import schedule
import time
import threading
from datetime import datetime, timedelta
from typing import Optional, Callable, Dict, Any
import logging
from pathlib import Path

from src.main import InsuranceNewsAgent
from src.utils.logger import get_logger
from src.email_sender.email_manager import EmailManager

class NewsScheduler:
    """Agendador de tarefas para coleta automática de notícias"""
    
    def __init__(self):
        """Inicializa o scheduler"""
        self.logger = get_logger("scheduler")
        self.agent = None
        self.email_manager = None
        self.is_running = False
        self.scheduler_thread = None
        
        # Configurações padrão
        self.config = {
            'collection_time': '07:00',  # Horário da coleta diária (UTC)
            'timezone': 'UTC',
            'max_retries': 3,
            'retry_delay_minutes': 30,
            'cleanup_days': 7  # Dias para manter arquivos antigos
        }
        
        self.logger.info("NewsScheduler inicializado")
    
    def initialize_components(self) -> bool:
        """
        Inicializa os componentes necessários
        
        Returns:
            bool: True se inicialização foi bem-sucedida
        """
        try:
            # Inicializar agente de notícias
            self.agent = InsuranceNewsAgent()
            self.logger.info("✅ InsuranceNewsAgent inicializado")
            
            # Inicializar gerenciador de e-mail
            self.email_manager = EmailManager()
            self.logger.info("✅ EmailManager inicializado")
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro na inicialização dos componentes: {e}")
            return False
    
    def setup_daily_schedule(self) -> None:
        """Configura o agendamento diário"""
        collection_time = self.config['collection_time']
        
        # Agendar coleta diária
        schedule.every().day.at(collection_time).do(self._run_daily_collection)
        
        # Agendar limpeza semanal (domingo às 02:00)
        schedule.every().sunday.at("02:00").do(self._run_cleanup)
        
        self.logger.info(f"📅 Agendamento configurado: coleta diária às {collection_time} UTC")
    
    def _run_daily_collection(self) -> None:
        """Executa a coleta diária de notícias"""
        self.logger.info("🚀 Iniciando coleta diária de notícias")
        
        try:
            # Executar coleta
            result = self.agent.collect_and_analyze_news()
            
            if result and result.get('success', False):
                # Obter estatísticas do resultado
                total_articles = result.get('total_articles', 0)
                duplicates_removed = result.get('duplicates_removed', 0)
                report_path = result.get('report_path', '')
                
                self.logger.info(f"✅ Coleta concluída: {total_articles} artigos, {duplicates_removed} duplicatas removidas")
                
                # Enviar e-mail se relatório foi gerado
                if report_path and Path(report_path).exists():
                    self._send_daily_email(report_path, total_articles)
                else:
                    self.logger.warning("⚠️ Relatório não foi gerado - e-mail não enviado")
                    
            else:
                error_msg = result.get('error', 'Erro desconhecido') if result else 'Falha na coleta'
                self.logger.error(f"❌ Falha na coleta: {error_msg}")
                self._send_error_notification("Falha na coleta diária", error_msg)
                
        except Exception as e:
            self.logger.error(f"❌ Erro durante coleta diária: {e}")
            self._send_error_notification("Erro na coleta diária", str(e))
    
    def _send_daily_email(self, report_path: str, total_articles: int) -> None:
        """
        Envia e-mail com relatório diário
        
        Args:
            report_path: Caminho para o arquivo de relatório
            total_articles: Número total de artigos coletados
        """
        try:
            if not self.email_manager:
                self.logger.warning("⚠️ EmailManager não inicializado - pulando envio de e-mail")
                return
            
            # Preparar dados do e-mail
            today = datetime.now().strftime('%Y-%m-%d')
            subject = f"Relatório Diário - Notícias de Seguros - {today}"
            
            # Carregar relatório HTML se existir
            html_report_path = report_path.replace('.json', '.html')
            
            if Path(html_report_path).exists():
                with open(html_report_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
            else:
                html_content = f"""
                <h2>Relatório Diário - {today}</h2>
                <p>Total de artigos coletados: {total_articles}</p>
                <p>Relatório detalhado em anexo.</p>
                """
            
            # Enviar e-mail
            success = self.email_manager.send_daily_report(
                subject=subject,
                html_content=html_content,
                attachments=[report_path] if Path(report_path).exists() else []
            )
            
            if success:
                self.logger.info("✅ E-mail diário enviado com sucesso")
            else:
                self.logger.error("❌ Falha no envio do e-mail diário")
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar e-mail diário: {e}")
    
    def _send_error_notification(self, error_type: str, error_message: str) -> None:
        """
        Envia notificação de erro
        
        Args:
            error_type: Tipo do erro
            error_message: Mensagem de erro
        """
        try:
            if not self.email_manager:
                self.logger.warning("⚠️ EmailManager não inicializado - pulando notificação de erro")
                return
            
            subject = f"Erro - Insurance News Agent - {error_type}"
            
            html_content = f"""
            <h2>Erro no Insurance News Agent</h2>
            <p><strong>Tipo:</strong> {error_type}</p>
            <p><strong>Data/Hora:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}</p>
            <p><strong>Mensagem:</strong></p>
            <pre>{error_message}</pre>
            """
            
            success = self.email_manager.send_error_notification(
                subject=subject,
                html_content=html_content
            )
            
            if success:
                self.logger.info("✅ Notificação de erro enviada")
            else:
                self.logger.error("❌ Falha no envio da notificação de erro")
                
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar notificação: {e}")
    
    def _run_cleanup(self) -> None:
        """Executa limpeza de arquivos antigos"""
        self.logger.info("🧹 Iniciando limpeza de arquivos antigos")
        
        try:
            cleanup_date = datetime.now() - timedelta(days=self.config['cleanup_days'])
            base_dir = Path(__file__).parent.parent
            
            # Diretórios para limpeza
            cleanup_dirs = [
                base_dir / 'data' / 'reports',
                base_dir / 'logs',
                base_dir / 'logs' / 'email',
                base_dir / 'logs' / 'scrapers'
            ]
            
            total_removed = 0
            
            for directory in cleanup_dirs:
                if directory.exists():
                    for file_path in directory.iterdir():
                        if file_path.is_file():
                            # Verificar se arquivo é antigo
                            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            
                            if file_time < cleanup_date:
                                try:
                                    file_path.unlink()
                                    total_removed += 1
                                    self.logger.debug(f"Removido: {file_path}")
                                except Exception as e:
                                    self.logger.warning(f"Erro ao remover {file_path}: {e}")
            
            self.logger.info(f"✅ Limpeza concluída: {total_removed} arquivos removidos")
            
        except Exception as e:
            self.logger.error(f"❌ Erro durante limpeza: {e}")
    
    def run_manual_collection(self) -> Dict[str, Any]:
        """
        Executa coleta manual (para testes ou execução sob demanda)
        
        Returns:
            Dict: Resultado da coleta
        """
        self.logger.info("🔧 Executando coleta manual")
        
        try:
            if not self.agent:
                if not self.initialize_components():
                    return {'success': False, 'error': 'Falha na inicialização dos componentes'}
            
            result = self.agent.collect_and_analyze_news()
            
            if result and result.get('success', False):
                self.logger.info("✅ Coleta manual concluída com sucesso")
            else:
                self.logger.error("❌ Falha na coleta manual")
            
            return result
            
        except Exception as e:
            error_msg = f"Erro na coleta manual: {e}"
            self.logger.error(f"❌ {error_msg}")
            return {'success': False, 'error': error_msg}
    
    def start(self) -> None:
        """Inicia o scheduler em thread separada"""
        if self.is_running:
            self.logger.warning("⚠️ Scheduler já está em execução")
            return
        
        # Inicializar componentes
        if not self.initialize_components():
            self.logger.error("❌ Falha na inicialização - scheduler não iniciado")
            return
        
        # Configurar agendamentos
        self.setup_daily_schedule()
        
        # Iniciar thread do scheduler
        self.is_running = True
        self.scheduler_thread = threading.Thread(target=self._run_scheduler, daemon=True)
        self.scheduler_thread.start()
        
        self.logger.info("🚀 Scheduler iniciado com sucesso")
    
    def stop(self) -> None:
        """Para o scheduler"""
        if not self.is_running:
            self.logger.warning("⚠️ Scheduler não está em execução")
            return
        
        self.is_running = False
        schedule.clear()
        
        if self.scheduler_thread and self.scheduler_thread.is_alive():
            self.scheduler_thread.join(timeout=5)
        
        self.logger.info("🛑 Scheduler parado")
    
    def _run_scheduler(self) -> None:
        """Loop principal do scheduler"""
        self.logger.info("📅 Loop do scheduler iniciado")
        
        while self.is_running:
            try:
                schedule.run_pending()
                time.sleep(60)  # Verificar a cada minuto
            except Exception as e:
                self.logger.error(f"❌ Erro no loop do scheduler: {e}")
                time.sleep(60)
        
        self.logger.info("📅 Loop do scheduler finalizado")
    
    def get_next_run_time(self) -> Optional[datetime]:
        """
        Retorna o próximo horário de execução agendado
        
        Returns:
            Optional[datetime]: Próximo horário de execução
        """
        jobs = schedule.get_jobs()
        if not jobs:
            return None
        
        next_run = min(job.next_run for job in jobs)
        return next_run
    
    def get_status(self) -> Dict[str, Any]:
        """
        Retorna status do scheduler
        
        Returns:
            Dict: Status atual
        """
        next_run = self.get_next_run_time()
        
        return {
            'is_running': self.is_running,
            'next_run': next_run.isoformat() if next_run else None,
            'scheduled_jobs': len(schedule.get_jobs()),
            'agent_initialized': self.agent is not None,
            'email_manager_initialized': self.email_manager is not None,
            'collection_time': self.config['collection_time'],
            'cleanup_days': self.config['cleanup_days']
        }


def main():
    """Função principal para execução do scheduler"""
    # Configurar logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(name)s | %(message)s'
    )
    
    # Criar e iniciar scheduler
    scheduler = NewsScheduler()
    
    try:
        scheduler.start()
        
        # Manter o programa rodando
        while True:
            time.sleep(60)
            
    except KeyboardInterrupt:
        print("\n🛑 Interrompido pelo usuário")
        scheduler.stop()
    except Exception as e:
        print(f"\n❌ Erro fatal: {e}")
        scheduler.stop()


if __name__ == "__main__":
    main()
