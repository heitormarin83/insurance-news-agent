*** a/src/email_sender/email_manager.py
--- b/src/email_sender/email_manager.py
@@
 import os
 import smtplib
 from email.mime.text import MIMEText
 from email.mime.multipart import MIMEMultipart
 import yaml
+from typing import List
 
 class EmailManager:
     def __init__(self, config_path: str):
-        self.gmail_email = os.getenv("GMAIL_EMAIL")
-        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
+        self.gmail_email = os.getenv("GMAIL_EMAIL", "").strip()
+        self.gmail_app_password = os.getenv("GMAIL_APP_PASSWORD", "").strip()
         self.config = self._load_config(config_path)
-        if not self.gmail_email or not self.gmail_app_password:
-            self._log_error("❌ GMAIL_EMAIL ou GMAIL_APP_PASSWORD não configurados nas variáveis de ambiente")
+        if not self.gmail_email or not self.gmail_app_password:
+            self._log_error("❌ GMAIL_EMAIL ou GMAIL_APP_PASSWORD ausentes no ambiente (Railway). Envio de e-mail será pulado.")
 
     def _load_config(self, config_path: str):
         abs_path = os.path.abspath(config_path)
         self._log_info(f"🔠 Caminho absoluto final do config: {abs_path}")
         with open(abs_path, "r", encoding="utf-8") as f:
             cfg = yaml.safe_load(f)
         self._log_info("🔠 Configuração de e-mail carregada")
-        self._log_info(f"🔠 Conteúdo carregado da configuração: {cfg}")
+        # Sobrescreve recipientes a partir de variáveis de ambiente, se existirem
+        def parse_list(env_key: str) -> List[str]:
+            raw = os.getenv(env_key, "")
+            if not raw:
+                return []
+            return [e.strip() for e in raw.split(",") if e.strip()]
+
+        recipients_env = {
+            "daily_report": parse_list("EMAIL_RECIPIENTS_DAILY"),
+            "alerts": parse_list("EMAIL_RECIPIENTS_ALERTS"),
+            "errors": parse_list("EMAIL_RECIPIENTS_ERRORS"),
+        }
+        for key, env_list in recipients_env.items():
+            if env_list:
+                cfg.setdefault("recipients", {})
+                cfg["recipients"][key] = env_list
+
+        self._log_info(f"🔠 Config final (com ENV aplicadas nos recipients): {cfg}")
         return cfg
 
     def authenticate(self):
-        if not self.gmail_email or not self.gmail_app_password:
-            self._log_error("❌ GMAIL_EMAIL e GMAIL_APP_PASSWORD não configurados corretamente.")
-            return None
+        if not self.gmail_email or not self.gmail_app_password:
+            self._log_error("❌ Credenciais ausentes. Pular autenticação.")
+            return None
         try:
             server = smtplib.SMTP(self.config["smtp"]["server"], self.config["smtp"]["port"])
             if self.config["smtp"].get("use_tls", True):
                 server.starttls()
             server.login(self.gmail_email, self.gmail_app_password)
             return server
         except Exception as e:
             self._log_error(f"❌ Falha na autenticação do e-mail: {e}")
             return None
 
     def send_email(self, subject: str, html_body: str, list_key: str):
-        recipients = self.config["recipients"].get(list_key, [])
+        recipients = self.config.get("recipients", {}).get(list_key, [])
         if not recipients:
             self._log_error(f"❌ Lista de destinatários vazia para '{list_key}'. E-mail não será enviado.")
             return False
-        server = self.authenticate()
+        server = self.authenticate()
         if not server:
-            self._log_error("❌ Falha na autenticação do e-mail")
+            self._log_error("❌ Sem servidor SMTP (credenciais ausentes ou inválidas). Pulando envio.")
             return False
         try:
             msg = MIMEMultipart("alternative")
             msg["From"] = f"{self.config['smtp'].get('sender_name', 'Insurance News Agent')} <{self.gmail_email}>"
             msg["To"] = ", ".join(recipients)
             msg["Subject"] = subject
             msg.attach(MIMEText(html_body, "html", "utf-8"))
             server.sendmail(self.gmail_email, recipients, msg.as_string())
             server.quit()
             self._log_info(f"✅ E-mail enviado para {recipients}")
             return True
         except Exception as e:
             self._log_error(f"❌ Erro no envio do e-mail: {e}")
             return False
