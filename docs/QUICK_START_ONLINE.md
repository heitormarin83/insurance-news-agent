# 🌐 Guia de Início Rápido ONLINE - Insurance News Agent

Este guia permite configurar o sistema usando **apenas ferramentas online** - sem instalar nada no seu PC!

## ⚡ Setup Completo Online (20 minutos)

### 1. Preparar Repositório GitHub (5 minutos)

#### Opção A: Fork do Repositório
1. Acesse o repositório no GitHub
2. Clique em **"Fork"** no canto superior direito
3. Escolha sua conta/organização

#### Opção B: Criar Novo Repositório
1. Vá para [github.com/new](https://github.com/new)
2. Nome: `insurance-news-agent`
3. Marque **"Add a README file"**
4. Clique **"Create repository"**
5. Faça upload dos arquivos do projeto

### 2. Configurar Gmail API (10 minutos)

#### 2.1 Google Cloud Console
1. Acesse [console.cloud.google.com](https://console.cloud.google.com)
2. **Criar projeto**:
   - Clique em "Select a project" → "New Project"
   - Nome: "Insurance News Agent"
   - Clique "Create"

#### 2.2 Ativar Gmail API
1. No menu lateral: **"APIs & Services"** → **"Library"**
2. Procure por **"Gmail API"**
3. Clique em **"Enable"**

#### 2.3 Criar Credenciais
1. Vá para **"APIs & Services"** → **"Credentials"**
2. Clique **"Create Credentials"** → **"OAuth 2.0 Client IDs"**
3. Se solicitado, configure OAuth consent screen:
   - User Type: **External**
   - App name: **Insurance News Agent**
   - User support email: seu e-mail
   - Scopes: adicione `https://www.googleapis.com/auth/gmail.send`
4. Application type: **Desktop application**
5. Name: **Insurance News Agent**
6. Clique **"Create"**
7. **Baixe o JSON** (será usado no passo 4)

### 3. Deploy no Railway (5 minutos)

#### 3.1 Conectar GitHub
1. Acesse [railway.app](https://railway.app)
2. Faça login com GitHub
3. Clique **"New Project"**
4. Selecione **"Deploy from GitHub repo"**
5. Escolha o repositório `insurance-news-agent`

#### 3.2 Aguardar Deploy Inicial
- Railway fará o primeiro deploy automaticamente
- Pode falhar (normal) - vamos configurar as variáveis

### 4. Configurar Variáveis de Ambiente

#### 4.1 No Railway Dashboard
1. Clique no seu projeto
2. Vá para aba **"Variables"**
3. Adicione as seguintes variáveis:

#### 4.2 Configurações Básicas
```
PORT=8000
FLASK_DEBUG=false
TIMEZONE=America/Sao_Paulo
DAILY_COLLECTION_TIME=08:00
ENABLE_EMAIL=true
```

#### 4.3 Destinatários de E-mail
```
EMAIL_RECIPIENTS_DAILY=seu-email@empresa.com,outro-email@empresa.com
EMAIL_RECIPIENTS_ALERTS=seu-email@empresa.com
EMAIL_RECIPIENTS_ERRORS=seu-email@empresa.com
```
> **Substitua pelos e-mails reais que devem receber os relatórios**

#### 4.4 Credenciais Gmail
1. Abra o arquivo JSON baixado do Google Cloud
2. **Copie todo o conteúdo** do arquivo
3. Adicione a variável:
```
GMAIL_CREDENTIALS={"installed":{"client_id":"seu_client_id","client_secret":"seu_client_secret","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","redirect_uris":["http://localhost"]}}
```
> **Cole o conteúdo exato do seu credentials.json**

#### 4.5 Configurações Opcionais
```
WEBHOOK_TOKEN=meu_token_secreto_123
MAX_ARTICLES_PER_SOURCE=50
RELEVANCE_THRESHOLD=0.5
ENABLE_OPEN_INSURANCE_ALERTS=true
LOG_LEVEL=INFO
```

### 5. Redeploy e Teste

#### 5.1 Forçar Novo Deploy
1. No Railway, vá para **"Deployments"**
2. Clique **"Deploy Now"** ou faça um commit no GitHub
3. Aguarde conclusão (2-3 minutos)

#### 5.2 Acessar Aplicação
1. No Railway, copie a **URL da aplicação**
2. Acesse no navegador: `https://seu-app.railway.app`
3. Você verá o dashboard do Insurance News Agent

## ✅ Testes Online

### 1. Dashboard Web
- Acesse `https://seu-app.railway.app`
- Clique em **"🧪 Testar Fontes"**
- Deve mostrar: `19/20 fontes funcionando`

### 2. Primeira Autenticação Gmail
1. Clique em **"🔍 Executar Coleta"**
2. Se aparecer erro de autenticação Gmail, é normal
3. Vamos configurar isso no próximo passo

### 3. Configurar Token Gmail (se necessário)

#### Se a autenticação falhar:
1. Use **GitHub Codespaces** (gratuito):
   - No seu repositório GitHub, clique **"Code"** → **"Codespaces"** → **"Create codespace"**
   - No terminal do Codespaces:
   ```bash
   pip install -r requirements.txt
   mkdir -p config
   # Cole o conteúdo do credentials.json em config/credentials.json
   python -c "from src.email_sender.gmail_sender import GmailSender; gs = GmailSender(); gs.authenticate()"
   ```
   - Siga o link de autenticação que aparecer
   - Copie o conteúdo de `config/token.json`
   - Adicione como variável `GMAIL_TOKEN` no Railway

## 🔄 Configurar Automação GitHub Actions

### 1. Secrets do GitHub
1. No seu repositório GitHub: **Settings** → **Secrets and variables** → **Actions**
2. Clique **"New repository secret"**
3. Adicione os seguintes secrets:

```
GMAIL_CREDENTIALS
(cole o conteúdo do credentials.json)

EMAIL_RECIPIENTS_DAILY
seu-email@empresa.com,outro-email@empresa.com

EMAIL_RECIPIENTS_ALERTS
seu-email@empresa.com

EMAIL_RECIPIENTS_ERRORS
seu-email@empresa.com

GMAIL_TOKEN
(se você gerou o token no passo anterior)
```

### 2. Testar GitHub Actions
1. Vá para aba **"Actions"** no GitHub
2. Clique em **"Manual News Collection"**
3. Clique **"Run workflow"**
4. Deixe configurações padrão e clique **"Run workflow"**

## 📧 Primeiro E-mail de Teste

### Via Dashboard Web
1. Acesse `https://seu-app.railway.app`
2. Clique **"🔍 Executar Coleta"**
3. Se tudo estiver configurado, você receberá um e-mail em alguns minutos

### Via API (usando navegador)
1. Abra nova aba: `https://seu-app.railway.app/api/collect`
2. Aguarde resposta JSON com estatísticas
3. Verifique seu e-mail

## 🎯 Verificações Finais

### ✅ Checklist de Funcionamento
- [ ] **Dashboard acessível**: `https://seu-app.railway.app`
- [ ] **Teste de fontes**: 19/20 funcionando
- [ ] **API respondendo**: `/api/status` retorna JSON
- [ ] **Gmail autenticado**: sem erros de autenticação
- [ ] **E-mail de teste recebido**
- [ ] **GitHub Actions funcionando**

### 📊 Monitoramento Contínuo
- **Logs Railway**: Dashboard → Deployments → View Logs
- **GitHub Actions**: Aba Actions do repositório
- **E-mails diários**: Chegam automaticamente às 8:00 BRT
- **API Status**: `https://seu-app.railway.app/api/status`

## 🚨 Troubleshooting Online

### Problema: Deploy falha no Railway
**Solução:**
1. Verifique logs no Railway Dashboard
2. Confirme que todas as variáveis estão configuradas
3. Tente redeploy manual

### Problema: Erro de autenticação Gmail
**Solução:**
1. Use GitHub Codespaces para gerar token
2. Verifique se `GMAIL_CREDENTIALS` está correto
3. Confirme que Gmail API está ativada

### Problema: E-mails não chegam
**Solução:**
1. Verifique pasta de spam
2. Confirme `EMAIL_RECIPIENTS_*` estão corretos
3. Teste via `/api/collect` e verifique logs

### Problema: GitHub Actions falha
**Solução:**
1. Verifique se todos os secrets estão configurados
2. Confirme formato dos e-mails (separados por vírgula)
3. Veja logs na aba Actions

## 🎉 Pronto!

Seu **Insurance News Agent** está funcionando 100% online! 

**O que acontece agora:**
- ⏰ **Execução automática** todos os dias às 8:00 BRT
- 📧 **E-mails diários** com as principais notícias
- 🚨 **Alertas especiais** para Open Insurance
- 📊 **Monitoramento** via dashboard web

**Próximos passos:**
- Monitore os primeiros e-mails
- Ajuste lista de destinatários se necessário
- Explore o dashboard e API
- Configure alertas personalizados

---

**🌐 Tudo funcionando apenas com ferramentas online!** 

Nenhuma instalação local necessária - o poder da nuvem! ☁️

---

**Quick Start Online Guide** - Insurance News Agent 🚀


