# scripts/send_daily_email.py
"""
Envia o relatório diário por e-mail (Railway).
- Usa GMAIL_EMAIL / GMAIL_APP_PASSWORD do ambiente (senha de app com 2FA).
- Destinatários vêm das ENVs:
    EMAIL_RECIPIENTS_DAILY, EMAIL_RECIPIENTS_ALERTS, EMAIL_RECIPIENTS_ERRORS
- Aceita --report para caminho explícito do arquivo (HTML ou JSON).
- Se não informado, tenta achar o relatório do dia automaticamente.
"""

import argparse
import datetime
import glob
import json
import os
import sys
from pathlib import Path
from zoneinfo import ZoneInfo

# Logger: tenta usar o do projeto; se não tiver, cai em logging básico
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

logger = get_logger("send_daily_email")

# EmailManager do projeto (já ajustado para ler ENV e sobrescrever recipients)
from src.email_sender.email_manager import EmailManager


def find_report_fallback() -> str | None:
    """
    Procura o relatório do dia em padrões comuns.
    Se não achar, pega o arquivo mais recente de data/reports.
    """
    tz = ZoneInfo(os.getenv("TZ", "America/Sao_Paulo"))
    today = datetime.datetime.now(tz).strftime("%Y-%m-%d")
    patterns = [
        f"data/reports/relatorio_seguros_{today}*.html",
        f"data/reports/relatorio_seguros_{today}*.json",
        f"data/reports/daily_report_{today}*.html",
        f"data/reports/daily_report_{today}*.json",
    ]
    candidates: list[str] = []
    for p in patterns:
        candidates.extend(glob.glob(p))

    if not candidates:
        # último recurso: arquivo mais recente em data/reports
        candidates = glob.glob("data/reports/*.*")

    if not candidates:
        return None

    # mais recente por mtime
    candidates.sort(key=lambda p: os.path.getmtime(p))
    return candidates[-1]


def build_subject(report_path: Path) -> str:
    """
    Monta o subject. Permite sobrescrever por ENV:
      EMAIL_SUBJECT_DAILY="Meu Assunto {date}"
    """
    tz = ZoneInfo(os.getenv("TZ", "America/Sao_Paulo"))
    date_str = datetime.datetime.now(tz).strftime("%Y-%m-%d")
    subject_tpl = os.getenv(
        "EMAIL_SUBJECT_DAILY",
        "Relatório Diário - Notícias de Seguros - {date}"
    )
    return subject_tpl.format(date=date_str)


def render_html_body(report_path: Path) -> str:
    """
    Se for .html, retorna o conteúdo.
    Se for .json, renderiza um HTML simples com <pre>.
    Outros formatos: lê como texto e embrulha em <pre>.
    """
    suffix = report_path.suffix.lower()
    try:
        if suffix == ".html":
            return report_path.read_text(encoding="utf-8")

        if suffix == ".json":
            data = json.loads(report_path.read_text(encoding="utf-8"))
            pretty = json.dumps(data, ensure_ascii=False, indent=2)
            return f"""<!doctype html>
<html lang="pt-br">
<head><meta charset="utf-8"><title>Relatório Diário (JSON)</title></head>
<body>
  <h2>Relatório Diário – Notícias de Seguros</h2>
  <p>Fonte: <code>{report_path}</code></p>
  <pre style="white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;">
{pretty}
  </pre>
</body>
</html>"""

        # fallback: lê como texto qualquer e mostra em <pre>
        raw = report_path.read_text(encoding="utf-8", errors="replace")
        return f"""<!doctype html>
<html lang="pt-br">
<head><meta charset="utf-8"><title>Relatório Diário (Texto)</title></head>
<body>
  <h2>Relatório Diário – Notícias de Seguros</h2>
  <p>Fonte: <code>{report_path}</code></p>
  <pre style="white-space: pre-wrap; font-family: ui-monospace, SFMono-Regular, Menlo, Monaco, Consolas, 'Liberation Mono', 'Courier New', monospace;">
{raw}
  </pre>
</body>
</html>"""
    except Exception as e:
        logger.error(f"Falha ao ler/renderizar o relatório: {e}")
        # Não aborta; manda um corpo mínimo avisando
        return f"""<!doctype html>
<html lang="pt-br">
<head><meta charset="utf-8"><title>Relatório Diário (Indisponível)</title></head>
<body>
  <h2>Relatório Diário – Notícias de Seguros</h2>
  <p>Não foi possível ler o relatório em <code>{report_path}</code>:</p>
  <pre>{e}</pre>
</body>
</html>"""


def main() -> int:
    parser = argparse.ArgumentParser(description="Envio de e-mail do relatório diário")
    parser.add_argument("--report", help="caminho do relatório (HTML ou JSON)")
    args = parser.parse_args()

    # Descobre o relatório
    if args.report:
        report_path = Path(args.report)
        if not report_path.exists():
            logger.error(f"--report especificado, mas o arquivo não existe: {report_path}")
            return 1
    else:
        found = find_report_fallback()
        if not found:
            logger.warning("Nenhum relatório encontrado. Nada a enviar.")
            # retorna 0 para não derrubar o worker; o scheduler já registra esse aviso
            return 0
        report_path = Path(found)

    logger.info(f"Usando relatório: {report_path}")

    # Monta subject e corpo HTML
    subject = build_subject(report_path)
    html_body = render_html_body(report_path)

    # Envia
    try:
        mgr = EmailManager("config/email_config.yaml")
        ok = mgr.send_email(subject=subject, html_body=html_body, list_key="daily_report")
        if ok:
            logger.info("✅ E-mail enviado com sucesso (daily_report).")
            return 0
        else:
            logger.error("❌ Falha ao enviar e-mail (daily_report). Verifique credenciais e destinatários.")
            return 2
    except Exception as e:
        logger.error(f"Erro inesperado no envio: {e}")
        return 3


if __name__ == "__main__":
    sys.exit(main())
