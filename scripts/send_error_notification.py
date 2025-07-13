#!/usr/bin/env python3
"""
Script para envio de notificação de erro
"""

import sys
import os
from datetime import datetime
from pathlib import Path

# Adiciona o diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.email_sender.email_manager import EmailManager
from src.utils.logger import get_logger

logger = get_logger("send_error_notification")


def main():
    """Função principal"""
    try:
        logger.info("🚨 Enviando notificação de erro")
        
        # Lê log de erro se disponível
        error_log_path = os.getenv('ERROR_LOG', 'collection_output.log')
        error_details = {
            'error': 'Falha na execução da coleta de notícias',
            'details': 'Erro durante a execução do GitHub Actions'
        }
        
        if Path(error_log_path).exists():
            with open(error_log_path, 'r', encoding='utf-8') as f:
                log_content = f.read()
                
            # Pega as últimas linhas do log
            log_lines = log_content.split('\n')
            last_lines = log_lines[-20:]  # Últimas 20 linhas
            
            error_details['details'] = '\n'.join(last_lines)
        
        # Adiciona informações do ambiente
        error_details['timestamp'] = datetime.now().isoformat()
        error_details['github_run_id'] = os.getenv('GITHUB_RUN_ID', 'Unknown')
        error_details['github_workflow'] = os.getenv('GITHUB_WORKFLOW', 'Unknown')
        
        # Inicializa gerenciador de e-mail
        email_manager = EmailManager()
        
        # Autentica
        if not email_manager.authenticate():
            logger.error("❌ Falha na autenticação do e-mail")
            sys.exit(1)
        
        # Envia notificação de erro
        success = email_manager.send_error_notification(error_details)
        
        if success:
            logger.info("✅ Notificação de erro enviada")
            print("SUCCESS: Notificação de erro enviada")
        else:
            logger.error("❌ Falha no envio da notificação de erro")
            sys.exit(1)
    
    except Exception as e:
        logger.error(f"❌ Erro ao enviar notificação: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()

