# scheduler.py
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

try:
    from zoneinfo import ZoneInfo  # Python 3.9+
except Exception:
    ZoneInfo = None  # fallback sem timezone

# --- PATHS: garanta que raiz e src estejam no PYTHONPATH ---
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))           # /app
sys.path.insert(0, str(BASE_DIR / "src"))   # /app/src

# --- LOGGER: usa o do projeto; se faltar, cria um básico ---
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

logger = get_logger("scheduler")

# --- AGENTE: importa da raiz (main.py) ou de src/main.py ---
try:
    from main import InsuranceNewsAgent     # se main.py estiver na raiz
except ModuleNotFoundError:
    from src.main import InsuranceNewsAgent # se estiver em src/main.py

# Configurações por ENV
RUN_AT = os.getenv("RUN_AT", "06:15")                 # horário diário (BRT)
TZ = os.getenv("TZ", "America/Sao_Paulo")             # fuso
RUN_NOW = os.getenv("RUN_NOW", "").lower() in ("1", "true", "yes")  # executa já uma vez

def parse_hhmm(s: str):
    try:
        hh, mm = s.split(":")
        return int(hh), int(mm)
    except Exception:
        return 6, 15  # fallback 06:15

def now_tz():
    if ZoneInfo:
        return datetime.now(ZoneInfo(TZ))
    return datetime.now()

def next_run(now, hh, mm):
    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if target <= now:
        target += timedelta(days=1)
    return target

def send_daily_email_via_script(report_path: str | None = None) -> bool:
    """Chama scripts/send_daily_email.py (passa --report se veio do agent)."""
    try:
        cmd = ["python", "-u", "-m", "scripts.send_daily_email"]
        if report_path:
    cmd += ["--report", str(report_path)]
        logger.info(f"📧 Executando: {' '.join(cmd)}")
        out = subprocess.run(cmd, capture_output=True, text=True)
        if out.stdout:
            logger.info("send_daily_email.py STDOUT:\n" + out.stdout)
        if out.returncode != 0:
            logger.error("send_daily_email.py STDERR:\n" + (out.stderr or ""))
            return False
        return True
    except Exception as e:
        logger.error(f"Erro ao chamar send_daily_email.py: {e}")
        return False

def send_error_notification(msg: str):
    """Tenta notificar por e-mail, mas não derruba o worker se falhar."""
    try:
        subprocess.run(
            ["python", "-u", "scripts/send_error_notification.py", "Insurance News Agent - Erro", msg],
            check=False
        )
    except Exception as e:
        logger.error(f"Falha ao acionar notificação de erro: {e}")

def run_once():
    """Executa a coleta do dia e envia o e-mail."""
    try:
        agent = InsuranceNewsAgent()
        result = agent.run_daily_collection()
        logger.info(
            f"✅ Coleta OK: {result['unique_articles_after_dedup']} únicos "
            f"(dup removidas: {result['duplicates_removed']})"
        )

        # Pega caminho salvo pelo ReportGenerator
        report_html = result.get("html_report_path")
        report_json = result.get("json_report_path")
        report_path = report_html or report_json
        if report_path:
            logger.info(f"🗂️ Report detectado: {report_path}")
        else:
            logger.warning("⚠️ Nenhum caminho de relatório no resultado; sender tentará auto-descobrir.")

        ok_email = send_daily_email_via_script(report_path)
        if not ok_email:
            logger.warning("⚠️ E-mail diário não enviado (verifique credenciais e recipients no Railway).")
    except Exception as e:
        logger.error(f"💥 Erro na execução diária: {e}")
        send_error_notification(str(e))

def main():
    logger.info(f"PYTHONPATH: {sys.path}")
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
