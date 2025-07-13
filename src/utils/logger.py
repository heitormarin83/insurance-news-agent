"""
Sistema de logging para o agente de notícias de seguros
"""

import sys
from pathlib import Path
from loguru import logger
from datetime import datetime


class LoggerSetup:
    """Configuração do sistema de logging"""
    
    def __init__(self, log_dir: str = None):
        """
        Inicializa o sistema de logging
        
        Args:
            log_dir: Diretório para arquivos de log (padrão: logs/)
        """
        if log_dir is None:
            # Assume que está sendo executado da raiz do projeto
            self.log_dir = Path(__file__).parent.parent.parent / "logs"
        else:
            self.log_dir = Path(log_dir)
        
        # Cria diretório de logs se não existir
        self.log_dir.mkdir(exist_ok=True)
        
        # Remove configuração padrão do loguru
        logger.remove()
        
        # Configura logging
        self._setup_logging()
    
    def _setup_logging(self):
        """Configura os handlers de logging"""
        
        # Console output (apenas INFO e acima)
        logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level="INFO",
            colorize=True
        )
        
        # Arquivo de log geral (DEBUG e acima)
        logger.add(
            self.log_dir / "insurance_agent.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            rotation="1 day",
            retention="30 days",
            compression="zip"
        )
        
        # Arquivo de log de erros (ERROR e acima)
        logger.add(
            self.log_dir / "errors.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="ERROR",
            rotation="1 week",
            retention="12 weeks"
        )
        
        # Arquivo de log de scraping
        logger.add(
            self.log_dir / "scraping.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="DEBUG",
            filter=lambda record: "scraper" in record["name"].lower(),
            rotation="1 day",
            retention="7 days"
        )
        
        # Arquivo de log de e-mails
        logger.add(
            self.log_dir / "email.log",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            level="INFO",
            filter=lambda record: "email" in record["name"].lower(),
            rotation="1 week",
            retention="4 weeks"
        )
    
    def get_logger(self, name: str = None):
        """
        Obtém um logger com nome específico
        
        Args:
            name: Nome do logger
            
        Returns:
            Logger configurado
        """
        if name:
            return logger.bind(name=name)
        return logger


# Instância global do sistema de logging
log_setup = LoggerSetup()
app_logger = log_setup.get_logger("insurance_agent")


def get_logger(name: str):
    """
    Função utilitária para obter um logger nomeado
    
    Args:
        name: Nome do logger
        
    Returns:
        Logger configurado
    """
    return log_setup.get_logger(name)

