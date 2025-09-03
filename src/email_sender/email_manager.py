# src/email_sender/email_manager.py
from __future__ import annotations

import os
import smtplib
import ssl
import socket
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
from typing import Iterable, Optional, Dict, Any, List

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

def _split_emails(value: Optional[str]) -> List[str]:
    if not value:
        return []
    return [e.strip() for e in value.split(",") if e.strip()]

def _env_bool(name: str, default: bool) -> bool:
    v = os.getenv(name)
    if v is None:
        return default
    return str(v).strip().lower() in ("1", "true", "yes", "on")

def _shallow_merge(base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
    out = dict(base)
    for k, v in (override or {}).items():
        if isinstance(v, dict) and isinstance(out.get(k), dict):
            tmp = dict(out[k]); tmp.update(v); out[k] = tmp
        else:
            out[k] = v
    return out

class EmailManager:
    def __init__(self, config_path: str | os.PathLike = "config/email_config.yaml"):
        self.config_path = self._resolve_config_path(config_path)
        self.config = self._load_config_tolerant(self.config_path)
        self._apply_env_overrides()
        s = self.config.get("smtp", {})
        logger.info(f"🔠 Recipients: {self.config.get('recipients', {})}")
        logger.info(f"🔠 SMTP server={s.get('server')} port={s.get('port')} use_tls={s.get('use_tls')} sender_name={s.get('sender_name')}")

    @staticmethod
    def _resolve_config_path(path: str | os.PathLike) -> Path:
        p = Path(path)
        if p.is_file():
            return p
        candidate = Path(__file__).resolve().parents[2] / path
        return candidate if candidate.is_file() else p

    @staticmethod
    def _defaults() -> Dict[str, Any]:
        return {
            "recipients": {"alerts": [], "daily_report": [], "errors": []},
            "smtp": {"server": "smtp.gmail.com", "port": 587, "use_tls": True, "sender_name": "Insurance News Agent"},
            "templates": {
                "alert": {"subject": "Alerta - Insurance News Agent - {alert_type}", "template_file": "alert_template.html"},
                "daily_report": {"subject": "Relatório Diário - Notícias de Seguros - {date}", "template_file": "daily_report_template.html"},
                "error": {"subject": "Erro - Insurance News Agent - {error_type}", "template_file": "error_template.html"},
            },
        }

    def _load_config_tolerant(self, cfg_path: Path) -> Dict[str, Any]:
        base = self._defaults()
        try:
            if not cfg_path.exists():
                logger.warning(f"Config {cfg_path} não encontrada; usando defaults.")
                return base
            try:
                import yaml
            except Exception as e:
                logger.error(f"PyYAML indisponível ({e}); usando defaults.")
                return base
            with cfg_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
            return _shallow_merge(base, data if isinstance(data, dict) else {})
        except Exception as e:
            logger.error(f"Config YAML inválida ({cfg_path}); usando defaults. Erro: {e}")
            return base

    def _apply_env_overrides(self) -> None:
        rec = self.config.setdefault("recipients", {})
        env_daily  = _split_emails(os.getenv("EMAIL_RECIPIENTS_DAILY"))
        env_alerts = _split_emails(os.getenv("EMAIL_RECIPIENTS_ALERTS"))
        env_errors = _split_emails(os.getenv("EMAIL_RECIPIENTS_ERRORS"))

        if env_daily:  rec["daily_report"] = env_daily
        else:          rec.setdefault("daily_report", [])
        if env_alerts: rec["alerts"] = env_alerts
        else:          rec.setdefault("alerts", [])
        if env_errors: rec["errors"] = env_errors
        else:          rec.setdefault("errors", [])

        # Overrides SMTP opcionais
        smtp = self.config.setdefault("smtp", {})
        if os.getenv("SMTP_SERVER"):      smtp["server"] = os.getenv("SMTP_SERVER")
        if os.getenv("SMTP_PORT"):
            try:                          smtp["port"] = int(os.getenv("SMTP_PORT"))
            except Exception:             logger.warning("SMTP_PORT inválido; mantendo %s", smtp.get("port"))
        if os.getenv("SMTP_USE_TLS") is not None:
            smtp["use_tls"] = _env_bool("SMTP_USE_TLS", smtp.get("use_tls", True))
        if os.getenv("SMTP_SENDER_NAME"): smtp["sender_name"] = os.getenv("SMTP_SENDER_NAME")

    def send_email(
        self,
        subject: str,
        html_body: str,
        list_key: str = "daily_report",
        attachments: Optional[Iterable[os.PathLike | str]] = None,
        reply_to: Optional[str] = None,
    ) -> bool:
        gmail_user = os.getenv("GMAIL_EMAIL")
        gmail_pass = os.getenv("GMAIL_APP_PASSWORD")
        if not gmail_user or not gmail_pass:
            logger.error("❌ GMAIL_EMAIL e/ou GMAIL_APP_PASSWORD não configurados")
            return False

        smtp_cfg = self.config.get("smtp", {})
        server = smtp_cfg.get("server", "smtp.gmail.com")
        try:    port = int(smtp_cfg.get("port", 587))
        except: port = 587
        use_tls = bool(smtp_cfg.get("use_tls", True))
        sender_name = smtp_cfg.get("sender_name", "Insurance News Agent")

        recipients = self.config.get("recipients", {}).get(list_key, [])
        if not recipients:
            logger.error(f"❌ Lista de destinatários vazia para '{list_key}'")
            return False

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"{sender_name} <{gmail_user}>"
        msg["To"] = ", ".join(recipients)
        if reply_to:
            msg["Reply-To"] = reply_to
        msg.attach(MIMEText(html_body, "html", "utf-8"))

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

        debug_smtp = _env_bool("SMTP_DEBUG", False)
        force_ipv4 = _env_bool("SMTP_FORCE_IPV4", False)

        # Monkey-patch temporário para forçar IPv4 (contorna ambientes sem IPv6)
        orig_getaddrinfo = socket.getaddrinfo
        def only_v4(host, port, family=0, type=0, proto=0, flags=0):
            res = orig_getaddrinfo(host, port, family, type, proto, flags)
            v4 = [r for r in res if r[0] == socket.AF_INET]
            return v4 or res

        try:
            if force_ipv4:
                socket.getaddrinfo = only_v4  # força A-records

            # Tentativa 1: 587 + STARTTLS
            try:
                context = ssl.create_default_context()
                with smtplib.SMTP(server, 587 if use_tls else port, timeout=30) as smtp:
                    if debug_smtp: smtp.set_debuglevel(1)
                    smtp.ehlo()
                    if use_tls:
                        smtp.starttls(context=context)
                        smtp.ehlo()
                    smtp.login(gmail_user, gmail_pass)
                    smtp.sendmail(gmail_user, recipients, msg.as_string())
                logger.info(f"✅ E-mail enviado (via {server}:587 STARTTLS) para {recipients}")
                return True
            except smtplib.SMTPAuthenticationError as e:
                logger.exception(f"❌ Autenticação SMTP (587) falhou: {e}")
                return False
            except Exception as e:
                logger.warning(f"⚠️ 587/STARTTLS falhou: {e} — tentando 465/SSL...")

            # Tentativa 2: 465 + SSL
            try:
                context = ssl.create_default_context()
                with smtplib.SMTP_SSL(server, 465, context=context, timeout=30) as smtp:
                    if debug_smtp: smtp.set_debuglevel(1)
                    smtp.login(gmail_user, gmail_pass)
                    smtp.sendmail(gmail_user, recipients, msg.as_string())
                logger.info(f"✅ E-mail enviado (via {server}:465 SSL) para {recipients}")
                return True
            except smtplib.SMTPAuthenticationError as e:
                logger.exception(f"❌ Autenticação SMTP (465) falhou: {e}")
                return False
            except Exception as e:
                logger.exception(f"❌ Erro inesperado ao enviar e-mail (após fallback): {e}")
                return False

        finally:
            if force_ipv4:
                socket.getaddrinfo = orig_getaddrinfo
