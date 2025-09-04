# scheduler.py
"""
Agendador do Insurance News Agent (processo worker no Railway).

- Executa a coleta diária (scraping + análise + geração de relatório).
- Localiza o relatório salvo (HTML/JSON) e chama o sender via módulo:
    python -u -m scripts.send_daily_email --report <caminho>
- Possui gatilho imediato via RUN_NOW=true (em Variables do Railway).
- Agenda diário configurável por RUN_AT=HH:MM (fuso TZ, ex.: America/Sao_Paulo).
- Diagnóstico opcional de SMTP: DIAG_SMTP=true (roda scripts.diagnose_smtp).

Requisitos:
- Ter os pacotes como módulos (crie vazios se necessário):
    src/__init__.py
    scripts/__init__.py
"""

from __future__ import annotations

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

# -------- Timezone --------
try:
    from zoneinfo import ZoneInfo  # Python >=3.9
except Exception:  # fallback sem tz
    ZoneInfo = None

# -------- PATHS (garantir que /app e /app/src estejam no sys.path) --------
BASE_DIR = Path(__file__).resolve().parent
if str(BASE_DIR) not in sys.path:
    sys.path.insert(0, str(BASE_DIR))          # /app
if str(BASE_DIR / "src") not in sys.path:
    sys.path.insert(0, str(BASE_DIR / "src"))  # /app/src

# -------- Logger (usa do projeto; se faltar, cria um simples) --------
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

logger = get_logger("scheduler")

# -------- Importa o agente (main na raiz ou dentro de src/) --------
try:
    from main import InsuranceNewsAgent  # se main.py está na raiz do repo
except ModuleNotFoundError:
    from src.main import InsuranceNewsAgent  # se estiver em src/main.py

# -------- Config via ENV --------
RUN_AT = os.getenv("RUN_AT", "06:15")                # HH:MM no fuso TZ
TZ = os.getenv("TZ", "America/Sao_Paulo")            # ex.: America/Sao_Paulo
RUN_NOW = os.getenv("RUN_NOW", "").lower() in ("1", "true", "yes")
DIAG_SMTP = os.getenv("DIAG_SMTP", "").lower() in ("1", "true", "yes")

# ====================== utilitários ======================

def parse_hhmm(s: str) -> tuple[int, int]:
    try:
        hh, mm = s.strip().split(":")
        return int(hh), int(mm)
    except Exception:
        logger.warning("RUN_AT inválido (%r). Usando 06:15.", s)
        return 6, 15

def now_tz() -> datetime:
    if ZoneInfo:
        try:
            return datetime.now(ZoneInfo(TZ))
        except Exception:
            logger.warning("TZ inválido (%r). Usando hora local sem tz.", TZ)
    return datetime.now()

def next_run(from_dt: datetime, hh: int, mm: int) -> datetime:
    target = from_dt.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if target <= from_dt:
        target += timedelta(days=1)
    return target

def _subprocess_env_with_pythonpath() -> dict:
    """Gera env para subprocessos garantindo PYTHONPATH com /app e /app/src."""
    env = os.environ.copy()
    extra = f"{BASE_DIR}:{BASE_DIR/'src'}"
    current = env.get("PYTHONPATH", "")
    env["PYTHONPATH"] = extra if not current else f"{extra}:{current}"
    return env

# =================== integrações auxiliares ===================

def run_smtp_diagnose_if_requested() -> None:
    """Roda diagnóstico de conectividade SMTP (se DIAG_SMTP=true)."""
    if not DIAG_SMTP:
        return
    try:
        logger.info("🔎 Rodando diagnóstico SMTP (scripts.diagnose_smtp)")
        cmd = ["python", "-u", "-m", "scripts.diagnose_smtp"]
        out = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=_subprocess_env_with_pythonpath(),
            timeout=120,
        )
        if out.stdout:
            logger.info("SMTP DIAG STDOUT:\n" + out.stdout)
        if out.stderr:
            logger.error("SMTP DIAG STDERR:\n" + out.stderr)
    except Exception as e:
        logger.exception(f"Falha ao executar diagnóstico SMTP: {e}")

def send_daily_email_via_script(report_path: str | None) -> bool:
    """
    Chama o sender via módulo (-m) para evitar problemas de path:
        python -u -m scripts.send_daily_email --report <caminho>
    """
    try:
        cmd = ["python", "-u", "-m", "scripts.send_daily_email"]
        if report_path:
            cmd += ["--report", str(report_path)]

        logger.info("📧 Executando: %s", " ".join(cmd))
        out = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env=_subprocess_env_with_pythonpath(),
            timeout=300,
        )
        if out.stdout:
            logger.info("send_daily_email.py STDOUT:\n" + out.stdout)
        if out.returncode != 0:
            logger.error("send_daily_email.py STDERR:\n" + (out.stderr or ""))
            return False
        return True
    except Exception as e:
        logger.exception(f"Erro ao chamar send_daily_email.py: {e}")
        return False

def send_error_notification(subject: str, msg: str) -> None:
    """
    Tenta mandar uma notificação de erro (não derruba o worker se falhar).
    Requer existir scripts/send_error_notification.py (opcional).
    """
    try:
        cmd = ["python", "-u", "-m", "scripts.send_error_notification", subject, msg]
        subprocess.run(
            cmd,
            check=False,
            env=_subprocess_env_with_pythonpath(),
            timeout=120,
        )
    except Exception as e:
        logger.error(f"Falha ao acionar notificação de erro: {e}")

# =================== ciclo de execução ===================

def run_once() -> None:
    """
    Executa uma coleta completa e tenta enviar o relatório por e-mail.
    """
    try:
        agent = InsuranceNewsAgent()
        result = agent.run_daily_collection()

        uniques = result.get("unique_articles_after_dedup")
        removed = result.get("duplicates_removed")
        logger.info(f"✅ Coleta OK: {uniques} artigos únicos (duplicatas removidas: {removed})")

        report_html = result.get("html_report_path")
        report_json = result.get("json_report_path")
        report_path = report_html or report_json

        if report_path:
            logger.info(f"🗂️ Report detectado: {report_path}")
        else:
            logger.warning("⚠️ Nenhum caminho de relatório no resultado; o sender tentará localizar automaticamente.")

        ok = send_daily_email_via_script(report_path)
        if not ok:
            logger.error("❌ Falha ao enviar e-mail (daily_report). Verifique credenciais, rede e destinatários.")
    except Exception as e:
        logger.exception(f"💥 Erro na execução diária: {e}")
        send_error_notification("Insurance News Agent - Erro", str(e))

def main() -> None:
    logger.info(f"PYTHONPATH: {sys.path}")

    # Diagnóstico opcional (para checar rede/SMTP quando precisar)
    run_smtp_diagnose_if_requested()

    hh, mm = parse_hhmm(RUN_AT)

    if RUN_NOW:
        logger.info("RUN_NOW ativo — executando imediatamente uma coleta...")
        run_once()

    while True:
        now = now_tz()
        nr = next_run(now, hh, mm)
        sleep_sec = max(1, int((nr - now).total_seconds()))
        logger.info(f"⏰ Próxima execução diária: {nr.isoformat()} (em {sleep_sec}s)")
        time.sleep(sleep_sec)
        run_once()

if __name__ == "__main__":
    main()
