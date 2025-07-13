# ✅ Checklist de Deploy - Insurance News Agent

Este checklist garante que todos os passos necessários para o deploy sejam seguidos corretamente.

## 📋 Pré-Deploy

### 🔧 Configuração do Google Cloud

- [ ] **Projeto Google Cloud criado**
- [ ] **Gmail API ativada**
- [ ] **Credenciais OAuth 2.0 criadas**
- [ ] **OAuth Consent Screen configurado**
- [ ] **Arquivo credentials.json baixado**
- [ ] **Escopos corretos configurados**: `https://www.googleapis.com/auth/gmail.send`

### 📧 Configuração de E-mail

- [ ] **Lista de destinatários para relatório diário definida**
- [ ] **Lista de destinatários para alertas definida**
- [ ] **Lista de destinatários para erros definida**
- [ ] **E-mails de teste validados**

### 🔐 Configuração de Segurança

- [ ] **Token de webhook definido (opcional)**
- [ ] **Credenciais não commitadas no repositório**
- [ ] **Variáveis de ambiente documentadas**

## 🚂 Deploy no Railway

### 1. Preparação do Repositório

- [ ] **Código commitado no GitHub**
- [ ] **README.md atualizado**
- [ ] **requirements.txt validado**
- [ ] **Arquivos de configuração presentes**:
  - [ ] `railway.json`
  - [ ] `Procfile`
  - [ ] `nixpacks.toml`
  - [ ] `runtime.txt`

### 2. Configuração no Railway

- [ ] **Projeto Railway criado**
- [ ] **Repositório GitHub conectado**
- [ ] **Variáveis de ambiente configuradas**:

#### Básicas
- [ ] `PORT=8000`
- [ ] `FLASK_DEBUG=false`
- [ ] `TIMEZONE=America/Sao_Paulo`
- [ ] `DAILY_COLLECTION_TIME=08:00`
- [ ] `ENABLE_EMAIL=true`

#### E-mail
- [ ] `EMAIL_RECIPIENTS_DAILY=email1@empresa.com,email2@empresa.com`
- [ ] `EMAIL_RECIPIENTS_ALERTS=email1@empresa.com,email2@empresa.com`
- [ ] `EMAIL_RECIPIENTS_ERRORS=admin@empresa.com`

#### Gmail API
- [ ] `GMAIL_CREDENTIALS={"installed":{"client_id":"..."}}`
- [ ] `GMAIL_TOKEN={"token":"..."}` (opcional, gerado automaticamente)

#### Opcionais
- [ ] `WEBHOOK_TOKEN=seu_token_secreto`
- [ ] `MAX_ARTICLES_PER_SOURCE=50`
- [ ] `RELEVANCE_THRESHOLD=0.5`
- [ ] `ENABLE_OPEN_INSURANCE_ALERTS=true`
- [ ] `LOG_LEVEL=INFO`

### 3. Deploy e Verificação

- [ ] **Deploy executado com sucesso**
- [ ] **Aplicação iniciada sem erros**
- [ ] **URL da aplicação acessível**
- [ ] **Dashboard web funcionando**
- [ ] **API endpoints respondendo**

## 🧪 Testes Pós-Deploy

### Testes Básicos

- [ ] **Health check**: `GET /api/health`
- [ ] **Status do sistema**: `GET /api/status`
- [ ] **Dashboard web**: `GET /`
- [ ] **Teste de fontes**: `GET /api/test`

### Testes de Funcionalidade

- [ ] **Coleta manual**: `GET /api/collect`
- [ ] **Logs do sistema**: `GET /api/logs`
- [ ] **Listagem de relatórios**: `GET /api/reports`

### Testes de E-mail

- [ ] **Autenticação Gmail funcionando**
- [ ] **E-mail de teste enviado com sucesso**
- [ ] **Templates de e-mail renderizando corretamente**

## 🔄 Configuração de Automação

### GitHub Actions

- [ ] **Secrets configurados no GitHub**:
  - [ ] `GMAIL_CREDENTIALS`
  - [ ] `GMAIL_TOKEN`
  - [ ] `EMAIL_RECIPIENTS_DAILY`
  - [ ] `EMAIL_RECIPIENTS_ALERTS`
  - [ ] `EMAIL_RECIPIENTS_ERRORS`

- [ ] **Workflows funcionando**:
  - [ ] Daily collection (execução diária)
  - [ ] Manual collection (execução manual)
  - [ ] Test sources (teste semanal)

### Scheduler Railway

- [ ] **Scheduler configurado para execução automática**
- [ ] **Horário de execução validado**
- [ ] **Logs de execução funcionando**

## 📊 Monitoramento

### Logs e Métricas

- [ ] **Logs do Railway acessíveis**
- [ ] **Dashboard de monitoramento configurado**
- [ ] **Alertas de erro configurados**
- [ ] **Métricas de performance monitoradas**

### Notificações

- [ ] **E-mails de erro sendo enviados**
- [ ] **Alertas Open Insurance funcionando**
- [ ] **Relatórios diários sendo enviados**

## 🔧 Configurações Avançadas

### Performance

- [ ] **Timeout de requisições configurado**
- [ ] **Rate limiting implementado**
- [ ] **Cache configurado (se necessário)**
- [ ] **Otimizações de memória aplicadas**

### Segurança

- [ ] **HTTPS habilitado (automático no Railway)**
- [ ] **Variáveis sensíveis protegidas**
- [ ] **Logs sem informações sensíveis**
- [ ] **Rate limiting para API endpoints**

### Backup e Recuperação

- [ ] **Estratégia de backup de configurações**
- [ ] **Procedimento de recuperação documentado**
- [ ] **Versionamento de código mantido**

## 📝 Documentação

### Para Usuários

- [ ] **README.md completo**
- [ ] **Guia de configuração de e-mail**
- [ ] **Instruções de uso da API**
- [ ] **FAQ de problemas comuns**

### Para Desenvolvedores

- [ ] **Documentação técnica**
- [ ] **Guia de testes**
- [ ] **Arquitetura do sistema**
- [ ] **Procedimentos de manutenção**

## 🚀 Go-Live

### Checklist Final

- [ ] **Todos os testes passando**
- [ ] **Monitoramento ativo**
- [ ] **Equipe treinada**
- [ ] **Documentação completa**
- [ ] **Backup de configurações realizado**

### Primeira Execução

- [ ] **Coleta manual executada com sucesso**
- [ ] **E-mail de teste enviado**
- [ ] **Logs verificados**
- [ ] **Performance validada**

### Acompanhamento

- [ ] **Primeira execução automática monitorada**
- [ ] **E-mails diários sendo recebidos**
- [ ] **Alertas funcionando corretamente**
- [ ] **Sistema estável por 24h**

## 📞 Suporte e Manutenção

### Contatos

- [ ] **Equipe de suporte definida**
- [ ] **Procedimentos de escalação documentados**
- [ ] **Canais de comunicação estabelecidos**

### Manutenção

- [ ] **Cronograma de manutenção definido**
- [ ] **Procedimentos de atualização documentados**
- [ ] **Monitoramento contínuo configurado**

---

## ✅ Assinatura de Aprovação

**Deploy aprovado por:**

- [ ] **Desenvolvedor**: _________________ Data: _______
- [ ] **QA/Tester**: _________________ Data: _______
- [ ] **DevOps**: _________________ Data: _______
- [ ] **Product Owner**: _________________ Data: _______

**Sistema em produção desde:** _________________

---

**Deployment Checklist** - Insurance News Agent 🚀
