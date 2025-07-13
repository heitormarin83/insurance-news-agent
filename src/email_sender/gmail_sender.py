"""
Sistema de envio de e-mails usando Gmail API
"""

import os
import base64
import json
from typing import List, Dict, Any, Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path

from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

from src.utils.logger import get_logger

logger = get_logger("gmail_sender")


class GmailSender:
    """Sistema de envio de e-mails via Gmail API"""
    
    # Escopos necessários para envio de e-mails
    SCOPES = ['https://www.googleapis.com/auth/gmail.send']
    
    def __init__(self, credentials_path: str = None, token_path: str = None):
        """
        Inicializa o Gmail Sender
        
        Args:
            credentials_path: Caminho para arquivo credentials.json
            token_path: Caminho para arquivo token.json
        """
        if credentials_path is None:
            credentials_path = Path(__file__).parent.parent.parent / "config" / "credentials.json"
        if token_path is None:
            token_path = Path(__file__).parent.parent.parent / "config" / "token.json"
        
        self.credentials_path = Path(credentials_path)
        self.token_path = Path(token_path)
        
        self.service = None
        self.authenticated = False
        
        logger.info("Gmail Sender inicializado")
    
    def authenticate(self) -> bool:
        """
        Autentica com Google API
        
        Returns:
            True se autenticação bem-sucedida
        """
        try:
            creds = None
            
            # Carrega token existente se disponível
            if self.token_path.exists():
                creds = Credentials.from_authorized_user_file(str(self.token_path), self.SCOPES)
            
            # Se não há credenciais válidas, faz o fluxo de autenticação
            if not creds or not creds.valid:
                if creds and creds.expired and creds.refresh_token:
                    logger.info("Renovando token de acesso...")
                    creds.refresh(Request())
                else:
                    if not self.credentials_path.exists():
                        logger.error(f"Arquivo credentials.json não encontrado: {self.credentials_path}")
                        return False
                    
                    logger.info("Iniciando fluxo de autenticação OAuth...")
                    flow = InstalledAppFlow.from_client_secrets_file(
                        str(self.credentials_path), self.SCOPES)
                    creds = flow.run_local_server(port=0)
                
                # Salva credenciais para próxima execução
                with open(self.token_path, 'w') as token:
                    token.write(creds.to_json())
                
                logger.info("Token salvo para futuras execuções")
            
            # Constrói serviço Gmail
            self.service = build('gmail', 'v1', credentials=creds)
            self.authenticated = True
            
            logger.info("✅ Autenticação Gmail bem-sucedida")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro na autenticação Gmail: {e}")
            return False
    
    def send_email(self, 
                   to_emails: List[str], 
                   subject: str, 
                   body: str, 
                   body_type: str = 'html',
                   attachments: List[str] = None) -> bool:
        """
        Envia e-mail via Gmail API
        
        Args:
            to_emails: Lista de e-mails destinatários
            subject: Assunto do e-mail
            body: Corpo do e-mail
            body_type: Tipo do corpo ('html' ou 'plain')
            attachments: Lista de caminhos para anexos
            
        Returns:
            True se envio bem-sucedido
        """
        if not self.authenticated:
            logger.error("Gmail não autenticado. Execute authenticate() primeiro.")
            return False
        
        try:
            logger.info(f"📧 Enviando e-mail para {len(to_emails)} destinatários")
            
            # Cria mensagem
            message = self._create_message(to_emails, subject, body, body_type, attachments)
            
            # Envia mensagem
            result = self.service.users().messages().send(
                userId='me', 
                body=message
            ).execute()
            
            logger.info(f"✅ E-mail enviado com sucesso. ID: {result['id']}")
            return True
            
        except HttpError as e:
            logger.error(f"❌ Erro HTTP ao enviar e-mail: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro ao enviar e-mail: {e}")
            return False
    
    def _create_message(self, 
                       to_emails: List[str], 
                       subject: str, 
                       body: str, 
                       body_type: str = 'html',
                       attachments: List[str] = None) -> Dict[str, str]:
        """
        Cria mensagem de e-mail
        
        Args:
            to_emails: Lista de e-mails destinatários
            subject: Assunto
            body: Corpo do e-mail
            body_type: Tipo do corpo
            attachments: Lista de anexos
            
        Returns:
            Mensagem formatada para Gmail API
        """
        # Cria mensagem multipart se há anexos
        if attachments:
            message = MIMEMultipart()
        else:
            message = MIMEText(body, body_type, 'utf-8')
        
        # Define cabeçalhos
        message['to'] = ', '.join(to_emails)
        message['subject'] = subject
        
        # Adiciona corpo se é multipart
        if attachments:
            if body_type == 'html':
                body_part = MIMEText(body, 'html', 'utf-8')
            else:
                body_part = MIMEText(body, 'plain', 'utf-8')
            message.attach(body_part)
            
            # Adiciona anexos
            for attachment_path in attachments:
                self._add_attachment(message, attachment_path)
        
        # Codifica mensagem
        raw_message = base64.urlsafe_b64encode(message.as_bytes()).decode('utf-8')
        
        return {'raw': raw_message}
    
    def _add_attachment(self, message: MIMEMultipart, file_path: str):
        """
        Adiciona anexo à mensagem
        
        Args:
            message: Mensagem MIMEMultipart
            file_path: Caminho do arquivo
        """
        try:
            file_path = Path(file_path)
            
            if not file_path.exists():
                logger.warning(f"Arquivo de anexo não encontrado: {file_path}")
                return
            
            with open(file_path, 'rb') as attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
            
            encoders.encode_base64(part)
            part.add_header(
                'Content-Disposition',
                f'attachment; filename= {file_path.name}'
            )
            
            message.attach(part)
            logger.debug(f"Anexo adicionado: {file_path.name}")
            
        except Exception as e:
            logger.error(f"Erro ao adicionar anexo {file_path}: {e}")
    
    def test_connection(self) -> bool:
        """
        Testa conexão com Gmail API
        
        Returns:
            True se conexão bem-sucedida
        """
        if not self.authenticated:
            return self.authenticate()
        
        try:
            # Tenta obter perfil do usuário
            profile = self.service.users().getProfile(userId='me').execute()
            email = profile.get('emailAddress', 'Unknown')
            
            logger.info(f"✅ Conexão Gmail OK. Usuário: {email}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Erro ao testar conexão Gmail: {e}")
            return False
    
    def send_test_email(self, to_email: str) -> bool:
        """
        Envia e-mail de teste
        
        Args:
            to_email: E-mail destinatário
            
        Returns:
            True se envio bem-sucedido
        """
        subject = "🧪 Teste - Insurance News Agent"
        body = """
        <html>
        <body>
            <h2>🧪 E-mail de Teste</h2>
            <p>Este é um e-mail de teste do <strong>Insurance News Agent</strong>.</p>
            <p>Se você recebeu este e-mail, o sistema de envio está funcionando corretamente!</p>
            <hr>
            <p><small>Enviado automaticamente pelo Insurance News Agent</small></p>
        </body>
        </html>
        """
        
        return self.send_email([to_email], subject, body, 'html')
    
    def get_user_info(self) -> Dict[str, Any]:
        """
        Obtém informações do usuário autenticado
        
        Returns:
            Informações do usuário
        """
        if not self.authenticated:
            return {}
        
        try:
            profile = self.service.users().getProfile(userId='me').execute()
            return {
                'email': profile.get('emailAddress', ''),
                'messages_total': profile.get('messagesTotal', 0),
                'threads_total': profile.get('threadsTotal', 0),
                'history_id': profile.get('historyId', '')
            }
        except Exception as e:
            logger.error(f"Erro ao obter informações do usuário: {e}")
            return {}


def setup_gmail_credentials():
    """
    Função auxiliar para configurar credenciais do Gmail
    Deve ser executada uma vez para configurar o OAuth
    """
    print("🔧 Configuração do Gmail API")
    print("1. Acesse: https://console.cloud.google.com/")
    print("2. Crie um novo projeto ou selecione um existente")
    print("3. Ative a Gmail API")
    print("4. Crie credenciais OAuth 2.0")
    print("5. Baixe o arquivo credentials.json")
    print("6. Coloque o arquivo em: config/credentials.json")
    print()
    print("Após configurar, execute o sistema para fazer a autenticação inicial.")


if __name__ == "__main__":
    # Exemplo de uso
    setup_gmail_credentials()

