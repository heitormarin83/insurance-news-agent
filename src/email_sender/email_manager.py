# src/email_sender/email_manager.py
from __future__ import annotations

import os
import smtplib
import ssl
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Iterable, List, Optional, Dict, Any

# Logger do projeto; se faltar, usa um básico
try:
    from src.utils.logger import get_logger
except Exception:
    import logging
    def get_logger(name: str):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
        )
        return logging.getLogger(name)

logger = get_logger("src.email_sender.email_manager")

try:
    import yaml
except Exception as e:
    logger.error("PyYAML não está instalado. Adicione 'PyYAML' ao requirements.txt.")
    raise


def _split_emails(value: Optional[str]) -> List[str]:
    """Converte 'a@x,b@y ,  c@z' -> ['a@x','b@y','c@z']"""
    if not value:
        return []
    return [e.strip() for e in value.split(",") if e.strip()]


class EmailManager:
    """
    Envia e-mails via SMTP (Gmail/Workspace) usando:
      - Credenciais nas ENVs: GMAIL_EMAIL / GMAIL_APP_PASSWORD
      - Destinatários nas ENVs: EMAIL_RECIPIENTS_DAILY / ALERTS / ERRORS
      - Configurações default em config/email_config.yaml
    """

    def __init__(self, config_path: str | os.PathLike = "config/email_config.yaml"):
        self.config_path = self._resolve_config_path(config_path)
        self.config = self._load_config()
        self._apply_env_overrides()
        logger.info("🔠 Configuração de e-mail carregada")
        logger.info(
            "🔠 Conteúdo carregado da configuração (com ENV aplicadas nos recipients): %s",
            {
                "recipients": self.config.get("recipients", {}),
                "smtp": self.config.get("smtp", {}),
                "templates": list(self.config.get("templates", {}).keys()),
            },
        )

    # ---------- Carregamento e overrides ----------

    def _resolve_config_path(self, path: str | os.PathLike) -> Path:
        p = Path(path)
        if p.is_file():
            return p
        # tenta relativo ao diretório do app
        candidate = Path(__file__).resolve().parents[2] / path  # .../src/email_sender/ -> raiz
        return candidate if candidate.is_file() else p

    def _load_config(self) -> Dict[str, Any]:
        if not self.config_path.exists():
            raise FileNotFoundError(f"Arquivo de configuração não encontrado: {self.config_path}")
        with self.config_path.open("r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def _apply_env_overrides(self) -> None:
        """Sobrescreve destinatários via ENV, se fornecidos."""
        rec = self.config.setdefault("recipients", {})
        env_daily  = _split_emails(os.getenv("EMAIL_RECIPIENTS_DAILY"))
        env_alerts = _split_emails(os.getenv("EMAIL_RECIPIENTS_ALERTS"))
        env_errors = _split_emails(os.getenv("EMAIL_RECIPIENTS_ERRORS"))

        if env_daily:
            rec["daily_report"] = env_daily
        else:
            rec.setdefault("daily_report", [])

        if env_alerts:
            rec["alerts"] = env_alerts
        else:
            rec.setdefault("alerts", [])

        if env_errors:
            rec["errors"] = env_errors
        else:
            rec.setdefault("errors", [])

    # ---------- Envio ----------

    def send_email(
        self,
        subject: str,
        html_body: str,
        list_key: str = "daily_report",
        attachments: Optional[Iterable[os.PathLike | str]] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        """
        Envia e-mail HTML para a lista indicada (default: daily_report).
        Retorna True/False.
        """
        gmail_user = os.getenv("GMAIL_EMAIL")
        gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

        if not gmail_user or not gmail_pass:
            logger.error("❌ GMAIL_EMAIL e/ou GMAIL_APP_PASSWORD não configurados nas variáveis de ambiente")
            return False

        smtp_cfg = self.config.get("smtp", {})
        server = smtp_cfg.get("server", "smtp.gmail.com")
        port = int(smtp_cfg.get("port", 587))
        use_tls = bool(smtp_cfg.get("use_tls", True))
        sender_name = smtp_cfg.get("sender_name", "Insurance News Agent")

        recipients = self.config.get("recipients", {}).get(list_key, [])
        if not recipients:
            logger.error(f"❌ Lista de destinatários vazia para '{list_key}'. Defina EMAIL_RECIPIENTS_{list_key.upper()} ou ajuste o YAML.")
            return False

        # Monta mensagem
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{gmail_user}>"
        msg["To"] = ", ".join(recipients)
        if reply_to:
            msg["Reply-To"] = reply_to

        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Anexos (opcional)
        for fpath in (attachments or []):
            p = Path(fpath)
            if not p.exists():
                logger.warning(f"Anexo não encontrado e ignorado: {p}")
                continue
            part = MIMEBase("application", "octet-stream")
            part.set_payload(p.read_bytes())
            encoders.encode_base64(part)
            part.add_header("Content-Disposition", f'attachment; filename="{p.name}"')
            msg.attach(part)

        # Envio SMTP
        try:
            if use_tls and port == 587:
                context = ssl.create_default_context()
                with smtplib.SMTP(server, port) as smtp:
                    smtp.ehlo()
                    smtp.starttls(context=context)
                    smtp.ehlo()
                    smtp.login(gmail_user, gmail_pass)
                    smtp.sendmail(gmail_user, recipients, msg.as_string())
            else:
                # TLS implicito (465) ou sem TLS (não recomendado)
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(server, port, context=context) as smtp:
                    smtp.login(gmail_user, gmail_pass)
                    smtp.sendmail(gmail_user, recipients, msg.as_string())
            logger.info("✅ E-mail enviado para %s (lista: %s)", recipients, list_key)
            return True
        except smtplib.SMTPAuthenticationError as e:
            logger.error(f"❌ Falha na autenticação SMTP: {e}")
            return False
        except Exception as e:
            logger.error(f"❌ Erro inesperado ao enviar e-mail: {e}")
            return False
