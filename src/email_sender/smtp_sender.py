"""
SMTP Sender - Versão simplificada para envio de e-mails via Gmail
Substitui a complexidade do OAuth por SMTP simples
"""

import smtplib
import os
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import List, Optional, Dict, Any
from pathlib import Path

from src.utils.logger import get_logger

logger = get_logger("smtp_sender")


class SMTPSender:
    """
    Sender de e-mail usando SMTP simples
    Muito mais fácil que OAuth para configurar
    """
    
    def __init__(self):
        """Inicializa o SMTP Sender"""
        self.smtp_server = "smtp.gmail.com"
        self.smtp_port = 587
        
        # Carrega credenciais das variáveis de ambiente
        self.email = os.getenv('GMAIL_EMAIL')
        self.password = os.getenv('GMAIL_APP_PASSWORD')
        
        self.authenticated = False
        self.logger = logger
        
        if not self.email or not self.password:
            self.logger.error("❌ Credenciais SMTP não configuradas")
            self.logger.error("Configure GMAIL_EMAIL e GMAIL_APP_PASSWORD nas variáveis de ambiente")
        else:
            self.logger.info("SMTP Sender inicializado")
    
    def authenticate(self) -> bool:
        """
        Testa autenticação SMTP
        
        Returns:
            True se autenticação bem-sucedida
        """
        if not self.email or not self.password:
            self.logger.error("❌ Credenciais não configuradas")
            return False
        
        try:
            self.logger.info("🔐 Testando autenticação SMTP...")
            
            # Testa conexão
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            server.quit()
            
            self.authenticated = True
            self.logger.info("✅ Autenticação SMTP bem-sucedida")
            return True
            
        except smtplib.SMTPAuthenticationError as e:
            self.logger.error(f"❌ Erro de autenticação SMTP: {e}")
            self.logger.error("Verifique se:")
            self.logger.error("1. Email e App Password estão corretos")
            self.logger.error("2. Autenticação de 2 fatores está ativa")
            self.logger.error("3. App Password foi gerado corretamente")
            return False
            
        except Exception as e:
            self.logger.error(f"❌ Erro na conexão SMTP: {e}")
            return False
    
    def send_email(self, 
                   to_emails: List[str], 
                   subject: str, 
                   html_body: str, 
                   text_body: Optional[str] = None,
                   attachments: Optional[List[str]] = None) -> bool:
        """
        Envia e-mail via SMTP
        
        Args:
            to_emails: Lista de destinatários
            subject: Assunto do e-mail
            html_body: Corpo em HTML
            text_body: Corpo em texto (opcional)
            attachments: Lista de caminhos de anexos (opcional)
            
        Returns:
            True se envio bem-sucedido
        """
        if not self.email or not self.password:
            self.logger.error("❌ Credenciais não configuradas")
            return False
        
        if not to_emails:
            self.logger.error("❌ Nenhum destinatário especificado")
            return False
        
        try:
            # Cria mensagem
            msg = MIMEMultipart('alternative')
            msg['From'] = self.email
            msg['To'] = ', '.join(to_emails)
            msg['Subject'] = subject
            
            # Adiciona corpo texto (se fornecido)
            if text_body:
                text_part = MIMEText(text_body, 'plain', 'utf-8')
                msg.attach(text_part)
            
            # Adiciona corpo HTML
            html_part = MIMEText(html_body, 'html', 'utf-8')
            msg.attach(html_part)
            
            # Adiciona anexos (se fornecidos)
            if attachments:
                for attachment_path in attachments:
                    if Path(attachment_path).exists():
                        self._add_attachment(msg, attachment_path)
                    else:
                        self.logger.warning(f"Anexo não encontrado: {attachment_path}")
            
            # Conecta e envia
            self.logger.info(f"📧 Enviando e-mail para {len(to_emails)} destinatário(s)...")
            
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email, self.password)
            
            # Envia para todos os destinatários
            server.send_message(msg)
            server.quit()
            
            self.logger.info(f"✅ E-mail enviado com sucesso para: {', '.join(to_emails)}")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ Erro ao enviar e-mail: {e}")
            return False
    
    def _add_attachment(self, msg: MIMEMultipart, file_path: str):
        """Adiciona anexo à mensagem"""
        try:
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            
            filename = Path(file_path).name
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {filename}'
            )
            
            msg.attach(part)
            self.logger.debug(f"Anexo adicionado: {filename}")
            
        except Exception as e:
            self.logger.error(f"Erro ao adicionar anexo {file_path}: {e}")
    
    def validate_configuration(self) -> Dict[str, Any]:
        """
        Valida configuração do SMTP
        
        Returns:
            Dicionário com status da validação
        """
        issues = []
        
        if not self.email:
            issues.append("GMAIL_EMAIL não configurado")
        
        if not self.password:
            issues.append("GMAIL_APP_PASSWORD não configurado")
        
        if self.email and '@' not in self.email:
            issues.append("GMAIL_EMAIL inválido")
        
        return {
            'valid': len(issues) == 0,
            'issues': issues,
            'email_configured': bool(self.email),
            'password_configured': bool(self.password),
            'smtp_server': self.smtp_server,
            'smtp_port': self.smtp_port
        }
    
    def send_test_email(self, to_email: str) -> bool:
        """
        Envia e-mail de teste
        
        Args:
            to_email: Destinatário do teste
            
        Returns:
            True se teste bem-sucedido
        """
        subject = "🧪 Teste - Insurance News Agent"
        
        html_body = """
        <html>
        <body>
            <h2>✅ Teste de E-mail Bem-sucedido!</h2>
            <p>Este é um e-mail de teste do <strong>Insurance News Agent</strong>.</p>
            <p>Se você recebeu esta mensagem, o sistema de e-mail está funcionando corretamente.</p>
            <hr>
            <p><em>Sistema configurado via SMTP</em></p>
        </body>
        </html>
        """
        
        text_body = """
        ✅ Teste de E-mail Bem-sucedido!
        
        Este é um e-mail de teste do Insurance News Agent.
        Se você recebeu esta mensagem, o sistema de e-mail está funcionando corretamente.
        
        Sistema configurado via SMTP
        """
        
        return self.send_email([to_email], subject, html_body, text_body)
