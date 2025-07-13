# 🚀 Guia de Início Rápido - Insurance News Agent

Este guia permite que você tenha o sistema funcionando em **menos de 30 minutos**.

## ⚡ Setup Rápido (5 minutos)

### 1. Clone o Repositório
```bash
git clone <seu-repositorio>
cd insurance_news_agent
```

### 2. Instale Dependências
```bash
pip install -r requirements.txt
```

### 3. Teste Básico
```bash
# Teste as fontes de notícias (sem e-mail)
python -m src.main --action test
```

**Resultado esperado:** `19/20 fontes funcionando (95.0%)`

## 📧 Configuração de E-mail (10 minutos)

### 1. Google Cloud Console

1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. Crie projeto → Ative Gmail API → Crie credenciais OAuth 2.0
3. Baixe `credentials.json`

### 2. Configuração Local

```bash
# Copie credenciais
mkdir -p config
cp ~/Downloads/credentials.json config/

# Configure destinatários
cp config/email_config.yaml.example config/email_config.yaml
# Edite o arquivo com seus e-mails
```

### 3. Teste de E-mail

```bash
python -c "
from src.email_sender.gmail_sender import GmailSender
sender = GmailSender()
sender.authenticate()  # Abrirá navegador para autorização
sender.send_test_email('seu-email@exemplo.com')
"
```

## 🚂 Deploy no Railway (15 minutos)

### 1. Preparação

1. Faça push do código para GitHub
2. Acesse [railway.app](https://railway.app)
3. Conecte repositório GitHub

### 2. Variáveis de Ambiente

No Railway, configure:

```bash
# Básico
PORT=8000
FLASK_DEBUG=false
ENABLE_EMAIL=true

# E-mails (substitua pelos seus)
EMAIL_RECIPIENTS_DAILY=email1@empresa.com,email2@empresa.com
EMAIL_RECIPIENTS_ALERTS=email1@empresa.com
EMAIL_RECIPIENTS_ERRORS=admin@empresa.com

# Gmail (cole conteúdo do credentials.json)
GMAIL_CREDENTIALS={"installed":{"client_id":"...","client_secret":"..."}}
```

### 3. Deploy

1. Railway fará deploy automaticamente
2. Acesse URL fornecida
3. Teste via dashboard web

## ✅ Verificação Rápida

### Dashboard Web
- Acesse `https://seu-app.railway.app`
- Clique em "🧪 Testar Fontes"
- Clique em "🔍 Executar Coleta"

### API
```bash
# Status
curl https://seu-app.railway.app/api/status

# Teste
curl https://seu-app.railway.app/api/test
```

## 🔄 Automação GitHub Actions

### 1. Configurar Secrets

No GitHub, vá para Settings → Secrets:

```
GMAIL_CREDENTIALS={"installed":{"client_id":"..."}}
EMAIL_RECIPIENTS_DAILY=email1@empresa.com,email2@empresa.com
EMAIL_RECIPIENTS_ALERTS=email1@empresa.com
EMAIL_RECIPIENTS_ERRORS=admin@empresa.com
```

### 2. Execução Automática

- **Diária**: 7:00 UTC (4:00 BRT) automaticamente
- **Manual**: Via GitHub Actions tab
- **Teste**: Segunda-feira 6:00 UTC

## 🎯 Casos de Uso Comuns

### Execução Manual
```bash
# Local
python -m src.main --action collect

# Via API
curl https://seu-app.railway.app/api/collect
```

### Teste de Fonte Específica
```bash
python -m src.main --action collect --source revista_apolice
```

### Monitoramento
```bash
# Logs
curl https://seu-app.railway.app/api/logs

# Relatórios
curl https://seu-app.railway.app/api/reports
```

## 🚨 Troubleshooting Rápido

### Problema: Fontes não funcionam
**Solução:** Normal, algumas fontes podem estar temporariamente indisponíveis

### Problema: Erro de autenticação Gmail
**Solução:** 
1. Verifique `GMAIL_CREDENTIALS`
2. Execute autenticação local primeiro
3. Copie token gerado para `GMAIL_TOKEN`

### Problema: E-mails não chegam
**Solução:**
1. Verifique spam/lixo eletrônico
2. Teste com `send_test_email()`
3. Verifique logs de erro

### Problema: Deploy falha no Railway
**Solução:**
1. Verifique variáveis de ambiente
2. Consulte logs do Railway
3. Verifique `requirements.txt`

## 📊 Exemplo de E-mail Gerado

O sistema gera relatórios HTML profissionais com:

- **Resumo executivo** do dia
- **Top 10 notícias** mais relevantes  
- **Estatísticas** por região
- **Alertas especiais** para Open Insurance
- **Links diretos** para notícias
- **Design responsivo**

## 🔗 Links Úteis

- **Dashboard**: `https://seu-app.railway.app`
- **API Status**: `https://seu-app.railway.app/api/status`
- **GitHub Actions**: Aba Actions do repositório
- **Railway Logs**: Dashboard do Railway
- **Google Cloud**: [console.cloud.google.com](https://console.cloud.google.com)

## 📞 Suporte

1. **Logs do sistema**: Primeira fonte de informação
2. **GitHub Issues**: Para bugs e melhorias  
3. **Railway Discord**: Para problemas de infraestrutura
4. **Documentação completa**: `docs/` directory

---

**🎉 Parabéns! Seu Insurance News Agent está funcionando!**

O sistema agora coleta notícias automaticamente e envia relatórios diários por e-mail. 

**Próximos passos:**
- Monitore primeiros e-mails
- Ajuste lista de destinatários
- Configure alertas personalizados
- Explore API endpoints

---

**Quick Start Guide** - Insurance News Agent ⚡

