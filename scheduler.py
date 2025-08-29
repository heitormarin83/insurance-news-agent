# scheduler.py (topo do arquivo)
import os
import sys
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
# garante que a raiz e a pasta src estejam no PYTHONPATH
sys.path.insert(0, str(BASE_DIR))
sys.path.insert(0, str(BASE_DIR / "src"))

try:
    # caso main.py esteja na raiz do repo
    from main import InsuranceNewsAgent
except ModuleNotFoundError:
    # fallback: caso main.py esteja em src/main.py
    from src.main import InsuranceNewsAgent

logger = get_logger("scheduler")

# Hora padrão do disparo diário (BRT). Você pode mudar via env RUN_AT="06:15"
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
    """
    Usa o script existente para enviar o e-mail do relatório diário.
    Ele depende das ENV GMAIL_EMAIL / GMAIL_APP_PASSWORD e dos recipients.
    """
    try:
        logger.info("📧 Enviando e-mail diário via scripts/send_daily_email.py ...")
        out = subprocess.run(
            ["python", "-u", "scripts/send_daily_email.py"],
            capture_output=True, text=True, check=False
        )
        logger.info("send_daily_email.py STDOUT:\n" + (out.stdout or ""))
        if out.returncode != 0:
            logger.error("send_daily_email.py STDERR:\n" + (out.stderr or ""))
            return False
        return True
    except Exception as e:
        logger.error(f"Erro ao chamar send_daily_email.py: {e}")
        return False

def send_error_notification(msg: str):
    # Tenta notificar por e-mail, mas não derruba o worker se não houver credenciais
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
        logger.info(f"✅ Coleta OK: {result['unique_articles_after_dedup']} artigos únicos "
                    f"(dup removidas: {result['duplicates_removed']})")
        ok_email = send_daily_email_via_script()
        if not ok_email:
            logger.warning("⚠️ E-mail diário não enviado (verifique credenciais e recipients).")
    except Exception as e:
        logger.error(f"💥 Erro na execução diária: {e}")
        # opcional: notificar erro
        send_error_notification(str(e))

def main():
    hh, mm = parse_hhmm(RUN_AT)
    tz = ZoneInfo(TZ)

    # Execução imediata opcional (para teste): RUN_NOW=true
    if os.getenv("RUN_NOW", "").lower() in ("1", "true", "yes"):
        logger.info("RUN_NOW ativo — executando imediatamente uma coleta...")
        run_once()

    while True:
        now = datetime.now(tz)
        nr = next_run(now, hh, mm)
        sleep_sec = (nr - now).total_seconds()
        logger.info(f"⏰ Próxima execução diária: {nr.isoformat()} (em {int(sleep_sec)}s)")
        time.sleep(max(1, int(sleep_sec)))
        run_once()

if __name__ == "__main__":
    main()
