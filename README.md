# 🤖 Insurance News Agent

Sistema automatizado de coleta e consolidação de notícias do mercado de seguros com envio diário por e-mail.

## 📋 Visão Geral

O Insurance News Agent é um sistema inteligente que:

- 🔍 **Coleta notícias** de múltiplas fontes especializadas em seguros
- 🌍 **Cobertura global**: Brasil, América do Sul, Estados Unidos e Europa
- 🔓 **Foco especial** em Open Insurance e regulamentações
- 📊 **Análise inteligente** com scoring de relevância
- 📧 **Relatórios diários** enviados automaticamente por e-mail
- 🚨 **Alertas especiais** para notícias sobre Open Insurance
- ⚡ **Execução automática** via GitHub Actions

## 🏗️ Arquitetura

```
insurance_news_agent/
├── src/
│   ├── scrapers/          # Coletores de notícias (RSS, Web Scraping)
│   ├── analyzers/         # Análise e processamento de notícias
│   ├── email_sender/      # Sistema de envio de e-mails
│   └── utils/             # Utilitários (config, logging, text processing)
├── config/                # Configurações (fontes, e-mail, credenciais)
├── scripts/               # Scripts para GitHub Actions
├── .github/workflows/     # Automação GitHub Actions
└── data/                  # Relatórios e dados gerados
```

## 🚀 Funcionalidades

### 📡 Coleta de Notícias
- **20 fontes** especializadas configuradas
- **RSS feeds** e **web scraping** inteligente
- **Filtragem automática** por relevância
- **Detecção de duplicatas**
- **Categorização automática**

### 🧠 Análise Inteligente
- **Scoring de relevância** baseado em palavras-chave
- **Detecção automática** de conteúdo sobre Open Insurance
- **Extração de resumos** e metadados
- **Classificação por região** e categoria

### 📧 Sistema de E-mail
- **Templates HTML** responsivos e profissionais
- **Relatórios diários** consolidados
- **Alertas especiais** para Open Insurance
- **Notificações de erro** do sistema
- **Múltiplas listas** de destinatários

### ⚙️ Automação
- **Execução diária** automática às 8:00 BRT
- **Execução manual** com parâmetros customizáveis
- **Monitoramento** semanal das fontes
- **Logs detalhados** e relatórios de execução

## 📊 Fontes de Notícias

### 🇧🇷 Brasil
- Revista Apólice
- CNseg - Notícias do Seguro
- Revista Segurador Brasil
- Revista Seguro Total
- Open Insurance Brasil

### 🌎 América do Sul
- Todo Riesgo (Argentina)
- Mercado Asegurador (Argentina)
- Fasecolda (Colômbia)
- Diario Financiero (Chile)

### 🇺🇸 Estados Unidos
- Insurance Journal
- Business Insurance
- PropertyCasualty360
- AM Best News
- Insurance Thought Leadership

### 🇪🇺 Europa
- EIOPA
- Insurance Europe
- FCA UK
- The Insurer
- Post Magazine UK

## 🛠️ Configuração

### 1. Configuração do Gmail API

1. Acesse o [Google Cloud Console](https://console.cloud.google.com/)
2. Crie um novo projeto ou selecione um existente
3. Ative a **Gmail API**
4. Crie credenciais **OAuth 2.0**
5. Baixe o arquivo `credentials.json`

### 2. Configuração do GitHub

#### Secrets necessários:
```
GMAIL_CREDENTIALS          # Conteúdo do credentials.json
GMAIL_TOKEN               # Token OAuth (opcional, gerado automaticamente)
EMAIL_RECIPIENTS_DAILY    # E-mails para relatório diário (separados por vírgula)
EMAIL_RECIPIENTS_ALERTS   # E-mails para alertas (separados por vírgula)
EMAIL_RECIPIENTS_ERRORS   # E-mails para erros (separados por vírgula)
```

#### Exemplo de configuração:
```
EMAIL_RECIPIENTS_DAILY=joao@empresa.com,maria@empresa.com,pedro@empresa.com
EMAIL_RECIPIENTS_ALERTS=joao@empresa.com,maria@empresa.com
EMAIL_RECIPIENTS_ERRORS=admin@empresa.com
```

### 3. Deploy no Railway

1. Conecte o repositório ao Railway
2. Configure as variáveis de ambiente
3. O sistema será executado automaticamente

## 📅 Execução Automática

### Execução Diária
- **Horário**: 7:00 UTC (4:00 BRT)
- **Frequência**: Todos os dias
- **Ação**: Coleta completa + envio de e-mail

### Teste de Fontes
- **Horário**: 6:00 UTC segunda-feira
- **Frequência**: Semanal
- **Ação**: Verifica saúde das fontes

### Execução Manual
- Disponível via GitHub Actions
- Parâmetros customizáveis
- Modo de teste disponível

## 📧 Exemplo de E-mail

O sistema gera relatórios HTML profissionais com:

- **Resumo executivo** do dia
- **Estatísticas** por região e fonte
- **Top 10 notícias** mais relevantes
- **Seção especial** para Open Insurance
- **Links diretos** para as notícias
- **Design responsivo** para mobile

## 🔧 Uso Local

### Instalação
```bash
git clone <repository>
cd insurance_news_agent
pip install -r requirements.txt
```

### Configuração
```bash
# Copie o credentials.json para config/
cp credentials.json config/

# Configure destinatários de e-mail
cp config/email_config.yaml.example config/email_config.yaml
# Edite o arquivo com seus destinatários
```

### Execução
```bash
# Teste das fontes
python -m src.main --action test

# Coleta completa
python -m src.main --action collect

# Coleta de fonte específica
python -m src.main --action collect --source revista_apolice

# Estatísticas do sistema
python -m src.main --action stats
```

## 📊 Monitoramento

### Logs
- **Logs gerais**: `logs/insurance_agent.log`
- **Logs de scraping**: `logs/scraping.log`
- **Logs de e-mail**: `logs/email.log`
- **Logs de erro**: `logs/errors.log`

### Relatórios
- **HTML**: `data/reports/relatorio_seguros_YYYY-MM-DD.html`
- **JSON**: `data/reports/relatorio_seguros_YYYY-MM-DD.json`

### GitHub Actions
- **Artifacts** com relatórios de cada execução
- **Job summaries** com estatísticas
- **Notificações** automáticas em caso de erro

## 🔒 Segurança

- **OAuth 2.0** para autenticação Gmail
- **Secrets** do GitHub para credenciais
- **Rate limiting** respeitoso com as fontes
- **Logs** sem informações sensíveis
- **Retry logic** para falhas temporárias

## 🤝 Contribuição

1. Fork o projeto
2. Crie uma branch para sua feature
3. Commit suas mudanças
4. Push para a branch
5. Abra um Pull Request

## 📝 Licença

Este projeto está sob a licença MIT. Veja o arquivo `LICENSE` para detalhes.

## 🆘 Suporte

Para dúvidas ou problemas:

1. Verifique os **logs** do sistema
2. Consulte a **documentação** das APIs
3. Abra uma **issue** no GitHub
4. Verifique o **status** das fontes de notícias

---

**Insurance News Agent** - Mantendo você informado sobre o mercado de seguros 🛡️

