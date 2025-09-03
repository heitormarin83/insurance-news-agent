# src/email_sender/email_manager.py
from __future__ import annotations

"""
EmailManager: envio de e-mails via SMTP (Gmail/Workspace).

- Lê configurações do YAML (config/email_config.yaml), mas é tolerante a arquivo
  faltando ou inválido: cai em defaults seguros.
- Sobrescreve as listas de destinatários via variáveis de ambiente:
    EMAIL_RECIPIENTS_DAILY, EMAIL_RECIPIENTS_ALERTS, EMAIL_RECIPIENTS_ERRORS
- Credenciais via ambiente:
    GMAIL_EMAIL, GMAIL_APP_PASSWORD  (senha de app; 2FA ativado)
"""

import os
import smtplib
import ssl
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Iterable, Optional, Dict, Any, List

# -------------------------------------------------------------------------
# Logger do projeto; se indisponível, cria um básico.
# -------------------------------------------------------------------------
try:
    from src.utils.logger import get_logger
except Exception:
    import logging

    def get_logger(name: str):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s",
        )
        return logging.getLogger(name)

logger = get_logger("src.email_sender.email_manager")

# -------------------------------------------------------------------------
# Utils
# -------------------------------------------------------------------------
def _split_emails(value: Optional[str]) -> List[str]:
    """Converte 'a@x,b@y ,  c@z' -> ['a@x','b@y','c@z']"""
    if not value:
        return []
    return [e.strip() for e in value.split(",") if e.strip()]


def _shallow_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    """Merge raso (apenas nível superior) para manter defaults."""
    result = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(result.get(k), dict):
            tmp = dict(result[k])
            tmp.update(v)
            result[k] = tmp
        else:
            result[k] = v
    return result


# -------------------------------------------------------------------------
# Classe principal
# -------------------------------------------------------------------------
class EmailManager:
    """
    Envia e-mails HTML com anexos opcionais.

    Prioridade de configuração:
      1) Defaults internos
      2) YAML (se válido)
      3) Variáveis de ambiente para *destinatários* (ENV vence o YAML)
    """

    def __init__(self, config_path: str | os.PathLike = "config/email_config.yaml"):
        self.config_path = self._resolve_config_path(config_path)
        self.config = self._load_config_tolerant(self.config_path)
        self._apply_env_overrides()
        # Log seguro (não expõe senhas)
        logger.info(
            "🔠 Config de e-mail carregada (recipients resolvidos): %s",
            self.config.get("recipients", {}),
        )
        logger.info(
            "🔠 SMTP host=%s port=%s use_tls=%s sender_name=%s",
            self.config.get("smtp", {}).get("server"),
            self.config.get("smtp", {}).get("port"),
            self.config.get("smtp", {}).get("use_tls"),
            self.config.get("smtp", {}).get("sender_name"),
        )

    # ------------------------- Carregamento -------------------------------

    @staticmethod
    def _resolve_config_path(path: str | os.PathLike) -> Path:
        p = Path(path)
        if p.is_file():
            return p
        # Tenta a partir da raiz do app (…/src/email_sender -> sobe 2 níveis)
        candidate = Path(__file__).resolve().parents[2] / path
        return candidate if candidate.is_file() else p

    @staticmethod
    def _defaults() -> Dict[str, Any]:
        return {
            "recipients": {
                "alerts": [],
                "daily_report": [],
                "errors": [],
            },
            "smtp": {
                "server": "smtp.gmail.com",
                "port": 587,
                "use_tls": True,
                "sender_name": "Insurance News Agent",
            },
            "templates": {
                "alert": {
                    "subject": "Alerta - Insurance News Agent - {alert_type}",
                    "template_file": "alert_template.html",
                },
                "daily_report": {
                    "subject": "Relatório Diário - Notícias de Seguros - {date}",
                    "template_file": "daily_report_template.html",
                },
                "error": {
                    "subject": "Erro - Insurance News Agent - {error_type}",
                    "template_file": "error_template.html",
                },
            },
        }

    def _load_config_tolerant(self, cfg_path: Path) -> Dict[str, Any]:
        """
        Carrega YAML de forma tolerante:
          - Se não existir -> defaults
          - Se inválido -> loga o erro e retorna defaults
          - Se válido -> merge raso em cima dos defaults
        """
        base = self._defaults()
        try:
            if not cfg_path.exists():
                logger.warning("Config %s não encontrada; usando defaults.", cfg_path)
                return base
            try:
                import yaml
            except Exception as e:
                logger.error("PyYAML não disponível (%s); usando defaults.", e)
                return base

            with cfg_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            if not isinstance(data, dict):
                logger.error("Config YAML não é dict (%s); usando defaults.", type(data).__name__)
                return base
            return _shallow_merge(base, data)
        except Exception as e:
            logger.error("Config YAML inválida (%s); usando defaults. Erro: %s", cfg_path, e)
            return base

    def _apply_env_overrides(self) -> None:
        """Sobrescreve listas de destinatários via ENV (se fornecidas)."""
        rec = self.config.setdefault("recipients", {})
        env_daily = _split_emails(os.getenv("EMAIL_RECIPIENTS_DAILY"))
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

    # --------------------------- Envio -----------------------------------

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
        Retorna True (sucesso) / False (falha).
        """
        gmail_user = os.getenv("GMAIL_EMAIL")
        gmail_pass = os.getenv("GMAIL_APP_PASSWORD")

        if not gmail_user or not gmail_pass:
            logger.error("❌ GMAIL_EMAIL e/ou GMAIL_APP_PASSWORD não configurados nas variáveis de ambiente")
            return False

        smtp_cfg = self.config.get("smtp", {})
        server = smtp_cfg.get("server", "smtp.gmail.com")
        try:
            port = int(smtp_cfg.get("port", 587))
        except Exception:
            port = 587
        use_tls = bool(smtp_cfg.get("use_tls", True))
        sender_name = smtp_cfg.get("sender_name", "Insurance News Agent")

        recipients = self.config.get("recipients", {}).get(list_key, [])
        if not recipients:
            logger.error(
                "❌ Lista de destinatários vazia para '%s'. Defina EMAIL_RECIPIENTS_%s ou ajuste o YAML.",
                list_key,
                list_key.upper(),
            )
            return False

        # Monta a mensagem
        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{gmail_user}>"
        msg["To"] = ", ".join(recipients)
        if reply_to:
            msg["Reply-To"] = reply_to

        msg.attach(MIMEText(html_body, "html", "utf-8"))

        # Anexos opcionais
        for fpath in (attachments or []):
            p = Path(fpath)
            if not p.exists():
                logger.warning("Anexo não encontrado e ignorado: %s", p)
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
                # TLS implícito (465) ou sem TLS (não recomendado)
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(server, port, context=context) as smtp:
                    smtp.login(gmail_user, gmail_pass)
                    smtp.sendmail(gmail_user, recipients, msg.as_string())
            logger.info("✅ E-mail enviado para %s (lista: %s)", recipients, list_key)
            return True

        except smtplib.SMTPAuthenticationError as e:
            logger.error("❌ Falha na autenticação SMTP: %s", e)
            return False
        except Exception as e:
            logger.error("❌ Erro inesperado ao enviar e-mail: %s", e)
            return False
