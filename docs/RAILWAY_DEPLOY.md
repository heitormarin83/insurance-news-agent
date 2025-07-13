# 🚀 Deploy no Railway - Insurance News Agent

Este guia explica como fazer o deploy do Insurance News Agent no Railway.

## 📋 Pré-requisitos

1. **Conta no Railway**: [railway.app](https://railway.app)
2. **Conta Google Cloud**: Para Gmail API
3. **Repositório GitHub**: Com o código do projeto

## 🔧 Configuração do Gmail API

### 1. Google Cloud Console

1. Acesse [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a **Gmail API**:
   - Vá para "APIs & Services" > "Library"
   - Procure por "Gmail API"
   - Clique em "Enable"

### 2. Credenciais OAuth 2.0

1. Vá para "APIs & Services" > "Credentials"
2. Clique em "Create Credentials" > "OAuth 2.0 Client IDs"
3. Configure:
   - Application type: **Desktop application**
   - Name: **Insurance News Agent**
4. Baixe o arquivo `credentials.json`

### 3. Configurar OAuth Consent Screen

1. Vá para "APIs & Services" > "OAuth consent screen"
2. Configure:
   - User Type: **External** (para uso geral) ou **Internal** (apenas sua organização)
   - App name: **Insurance News Agent**
   - User support email: Seu e-mail
   - Scopes: Adicione `https://www.googleapis.com/auth/gmail.send`

## 🚂 Deploy no Railway

### 1. Conectar Repositório

1. Acesse [railway.app](https://railway.app)
2. Clique em "New Project"
3. Selecione "Deploy from GitHub repo"
4. Escolha o repositório do Insurance News Agent

### 2. Configurar Variáveis de Ambiente

No painel do Railway, vá para "Variables" e adicione:

#### Configurações Básicas
```
PORT=8000
FLASK_DEBUG=false
TIMEZONE=America/Sao_Paulo
DAILY_COLLECTION_TIME=08:00
ENABLE_EMAIL=true
```

#### E-mail Recipients
```
EMAIL_RECIPIENTS_DAILY=email1@empresa.com,email2@empresa.com,email3@empresa.com
EMAIL_RECIPIENTS_ALERTS=email1@empresa.com,email2@empresa.com
EMAIL_RECIPIENTS_ERRORS=admin@empresa.com
```

#### Gmail API Credentials
```
GMAIL_CREDENTIALS={"installed":{"client_id":"seu_client_id","client_secret":"seu_client_secret","auth_uri":"https://accounts.google.com/o/oauth2/auth","token_uri":"https://oauth2.googleapis.com/token","auth_provider_x509_cert_url":"https://www.googleapis.com/oauth2/v1/certs","redirect_uris":["http://localhost"]}}
```

> **Importante**: Cole o conteúdo completo do arquivo `credentials.json` na variável `GMAIL_CREDENTIALS`

#### Configurações Opcionais
```
WEBHOOK_TOKEN=seu_token_secreto_para_webhooks
MAX_ARTICLES_PER_SOURCE=50
RELEVANCE_THRESHOLD=0.5
ENABLE_OPEN_INSURANCE_ALERTS=true
LOG_LEVEL=INFO
```

### 3. Deploy

1. O Railway fará o deploy automaticamente
2. Aguarde a conclusão (pode levar alguns minutos)
3. Acesse a URL fornecida pelo Railway

## 🔐 Autenticação Gmail (Primeira Execução)

### Método 1: Via Dashboard Web

1. Acesse a URL do seu app no Railway
2. Clique em "🧪 Testar Fontes" ou "🔍 Executar Coleta"
3. O sistema tentará autenticar automaticamente

### Método 2: Configuração Manual

Se a autenticação automática falhar:

1. **Execute localmente primeiro**:
   ```bash
   git clone <seu-repositorio>
   cd insurance_news_agent
   pip install -r requirements.txt
   
   # Copie o credentials.json para config/
   cp credentials.json config/
   
   # Execute para gerar token
   python -c "from src.email_sender.gmail_sender import GmailSender; gs = GmailSender(); gs.authenticate()"
   ```

2. **Copie o token gerado**:
   ```bash
   cat config/token.json
   ```

3. **Adicione no Railway**:
   - Vá para "Variables"
   - Adicione `GMAIL_TOKEN` com o conteúdo do arquivo `token.json`

## 📊 Monitoramento

### Dashboard Web

Acesse `https://seu-app.railway.app` para ver:

- Status do sistema
- Estatísticas de coleta
- Logs em tempo real
- Controles manuais

### API Endpoints

- `GET /api/status` - Status do sistema
- `GET /api/collect` - Executar coleta manual
- `GET /api/test` - Testar fontes
- `GET /api/reports` - Listar relatórios
- `GET /api/logs` - Logs recentes
- `POST /webhook/collect` - Webhook para execução externa

### Logs do Railway

1. No painel do Railway, vá para "Deployments"
2. Clique no deployment ativo
3. Veja os logs em tempo real

## ⚙️ Configuração de Execução

### Execução Automática

O sistema executa automaticamente:

- **Coleta diária**: Horário configurado em `DAILY_COLLECTION_TIME`
- **Teste de fontes**: Segunda-feira às 06:00
- **Logs de status**: A cada hora

### Execução Manual

Via dashboard web ou API:

```bash
# Executar coleta
curl https://seu-app.railway.app/api/collect

# Testar fontes
curl https://seu-app.railway.app/api/test

# Ver status
curl https://seu-app.railway.app/api/status
```

### Webhook Externo

Configure webhook para execução via GitHub Actions ou outros serviços:

```bash
curl -X POST https://seu-app.railway.app/webhook/collect \
  -H "Authorization: Bearer SEU_WEBHOOK_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"send_email": true}'
```

## 🔧 Troubleshooting

### Erro de Autenticação Gmail

1. Verifique se `GMAIL_CREDENTIALS` está correto
2. Certifique-se de que a Gmail API está ativada
3. Verifique os escopos OAuth configurados

### Erro de E-mail

1. Verifique `EMAIL_RECIPIENTS_*` estão no formato correto
2. Teste a autenticação via `/api/status`
3. Verifique logs para erros específicos

### Erro de Coleta

1. Teste fontes individuais via `/api/test`
2. Verifique conectividade de rede
3. Analise logs para fontes específicas com problema

### Performance

1. Ajuste `MAX_ARTICLES_PER_SOURCE` se necessário
2. Configure `RELEVANCE_THRESHOLD` para filtrar melhor
3. Monitore uso de recursos no Railway

## 📈 Escalabilidade

### Recursos Railway

- **Starter Plan**: Adequado para uso básico
- **Pro Plan**: Recomendado para uso intensivo
- **Team Plan**: Para múltiplas instâncias

### Otimizações

1. **Cache**: Implementar cache Redis se necessário
2. **Database**: Adicionar PostgreSQL para histórico
3. **Queue**: Usar Celery para processamento assíncrono
4. **CDN**: Para servir relatórios estáticos

## 🔒 Segurança

### Variáveis Sensíveis

- Nunca commite credenciais no código
- Use variáveis de ambiente do Railway
- Configure `WEBHOOK_TOKEN` para proteger endpoints

### Acesso

- Configure domínio customizado se necessário
- Use HTTPS sempre (Railway fornece automaticamente)
- Monitore logs para acessos suspeitos

## 📞 Suporte

Para problemas específicos:

1. **Logs do Railway**: Primeira fonte de informação
2. **Dashboard do app**: Status e estatísticas
3. **GitHub Issues**: Para bugs e melhorias
4. **Railway Discord**: Para problemas de infraestrutura

---

**Railway Deploy Guide** - Insurance News Agent 🚂
