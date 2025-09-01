# scheduler.py
import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

# --- PATHS: garante que a raiz e a pasta src estejam no PYTHONPATH ---
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))           # /app
sys.path.insert(0, str(BASE_DIR / "src"))   # /app/src

# --- LOGGER: tenta importar o seu; se não, cria um básico ---
try:
    from src.utils.logger import get_logger  # estrutura comum do seu repo
except Exception:
    import logging
    def get_logger(name: str):
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s | %(levelname)s | %(name)s:%(funcName)s:%(lineno)d - %(message)s"
        )
        return logging.getLogger(name)

logger = get_logger("scheduler")

# --- AGENTE: tenta importar da raiz (main.py) ou de src/main.py ---
try:
    from main import InsuranceNewsAgent     # se main.py estiver na raiz
except ModuleNotFoundError:
    from src.main import InsuranceNewsAgent # se estiver em src/main.py

# Configurações
RUN_AT = os.getenv("RUN_AT", "06:15")
TZ = os.getenv("TZ", "America/Sao_Paulo")

def parse_hhmm(s: str):
    try:
        hh, mm = s.split(":")
        return int(hh), int(mm)
    except Exception:
        return 6, 15  # fallback

def next_run(now, hh, mm):
    target = now.replace(hour=hh, minute=mm, second=0, microsecond=0)
    if target <= now:
        target = target + timedelta(days=1)
    return target

def send_daily_email_via_script():
    try:
        logger.info("📧 Enviando e-mail diário via scripts/send_daily_email.py ...")
        out = subprocess.run(
            ["python", "-u", "scripts/send_daily_email.py"],
            capture_output=True, text=True, check=False
        )
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
    try:
        logger.info("🚨 Enviando notificação de erro...")
        subprocess.run(
            ["python", "-u", "scripts/send_error_notification.py", "Insurance News Agent - Erro", msg],
            check=False
        )
    except Exception as e:
        logger.error(f"Falha ao acionar notificação de erro: {e}")

def run_once():
    try:
        agent = InsuranceNewsAgent()
        result = agent.run_daily_collection()
        logger.info(f"✅ Coleta OK: {result['unique_articles_after_dedup']} únicos "
                    f"(dup removidas: {result['duplicates_removed']})")
        # pegue os caminhos que o agente acabou de salvar
        report_html = result.get("html_report_path")
        report_json = result.get("json_report_path")
        report_path = report_html or report_json

if report_path:
    ok_email = send_daily_email_via_script(report_path)
else:
    logger.warning("⚠️ Não encontrei report_path no resultado. Vou tentar o auto-detect do sender.")
    ok_email = send_daily_email_via_script(None)

        if not ok_email:
            logger.warning("⚠️ E-mail diário não enviado (verifique credenciais/recipients).")
    except Exception as e:
        logger.error(f"💥 Erro na execução diária: {e}")
        send_error_notification(str(e))

def main():
    # (debug opcional)
    logger.info(f"PYTHONPATH: {sys.path}")

    hh, mm = parse_hhmm(RUN_AT)
    tz = ZoneInfo(TZ)

    if os.getenv("RUN_NOW", "").lower() in ("1", "true", "yes"):
        logger.info("RUN_NOW ativo — executando imediatamente uma coleta...")
        run_once()

    while True:
        now = datetime.now(tz)
        nr = next_run(now, hh, mm)
        sleep_sec = max(1, int((nr - now).total_seconds()))
        logger.info(f"⏰ Próxima execução diária: {nr.isoformat()} (em {sleep_sec}s)")
        time.sleep(sleep_sec)
        run_once()

if __name__ == "__main__":
    main()
