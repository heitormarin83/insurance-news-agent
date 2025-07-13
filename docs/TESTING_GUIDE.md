# 🧪 Guia de Testes - Insurance News Agent

Este documento descreve como testar o Insurance News Agent em diferentes cenários.

## 📋 Testes Básicos

### 1. Teste das Fontes de Notícias

```bash
# Testa todas as fontes configuradas
python -m src.main --action test

# Resultado esperado: 19/20 fontes funcionando (95%)
```

**Saída esperada:**
```
🧪 Testando fontes de notícias...
✅ revista_apolice: OK (200) em 1.23s
✅ cnseg_noticias: OK (200) em 0.89s
❌ risk_insurance: Falha na conexão (403)
...
🧪 Testes concluídos: 19/20 fontes funcionando (95.0%)
```

### 2. Teste de Configuração de Ambiente

```bash
# Testa configuração do ambiente
python -c "from src.utils.environment import validate_environment; print(validate_environment())"
```

### 3. Teste de Coleta Básica

```bash
# Executa coleta de uma fonte específica
python -m src.main --action collect --source revista_apolice

# Executa coleta completa (pode demorar)
python -m src.main --action collect
```

## 🌐 Testes da Aplicação Web

### 1. Iniciar Aplicação Flask

```bash
# Inicia aplicação em modo desenvolvimento
python app.py
```

**Saída esperada:**
```
🚀 Iniciando Insurance News Agent Flask App na porta 8000
* Running on all addresses (0.0.0.0)
* Running on http://127.0.0.1:8000
* Running on http://[::1]:8000
```

### 2. Testar Endpoints da API

```bash
# Health check
curl http://localhost:8000/api/health

# Status do sistema
curl http://localhost:8000/api/status

# Testar fontes via API
curl http://localhost:8000/api/test

# Dashboard web
curl http://localhost:8000/
```

## 📧 Testes de E-mail

### 1. Configuração de Credenciais

```bash
# Configurar credenciais Gmail (apenas primeira vez)
mkdir -p config
# Copiar credentials.json para config/

# Testar autenticação
python -c "
from src.email_sender.gmail_sender import GmailSender
sender = GmailSender()
print('Autenticação:', sender.authenticate())
print('Teste conexão:', sender.test_connection())
"
```

### 2. Teste de Envio

```bash
# Enviar e-mail de teste
python -c "
from src.email_sender.gmail_sender import GmailSender
sender = GmailSender()
if sender.authenticate():
    result = sender.send_test_email('seu-email@exemplo.com')
    print('E-mail enviado:', result)
"
```

### 3. Teste de Templates

```bash
# Testar geração de templates
python -c "
from src.email_sender.email_template import EmailTemplate
from src.models import DailyReport
from datetime import datetime

template = EmailTemplate()
# Criar relatório de teste
report = DailyReport(
    date=datetime.now(),
    total_articles=10,
    articles_by_region={'Brasil': 5, 'EUA': 3, 'Europa': 2},
    top_articles=[],
    open_insurance_articles=[],
    summary='Relatório de teste'
)

email = template.generate_daily_report_email(report)
print('Subject:', email['subject'])
print('Body length:', len(email['body']))
"
```

## 🔄 Testes de Automação

### 1. Teste do Scheduler

```bash
# Testar configuração de agendamento
python -c "
from scheduler import InsuranceNewsScheduler
scheduler = InsuranceNewsScheduler()
scheduler.setup_schedule()
print('Scheduler configurado com sucesso')
"
```

### 2. Teste de GitHub Actions (Local)

```bash
# Simular execução do GitHub Actions
export EMAIL_RECIPIENTS_DAILY="test@exemplo.com"
export EMAIL_RECIPIENTS_ALERTS="test@exemplo.com"
export EMAIL_RECIPIENTS_ERRORS="admin@exemplo.com"

python scripts/setup_email_config.py
python scripts/manual_collection.py --sources "revista_apolice"
```

## 🚂 Testes de Deploy

### 1. Teste Local com Variáveis de Ambiente

```bash
# Configurar variáveis de ambiente
export PORT=8000
export FLASK_DEBUG=false
export TIMEZONE=America/Sao_Paulo
export ENABLE_EMAIL=false

# Testar inicialização
python app.py
```

### 2. Teste de Configuração Railway

```bash
# Simular ambiente Railway
export RAILWAY_ENVIRONMENT=production
export PORT=8000

# Testar configuração de ambiente
python -c "
from src.utils.environment import initialize_environment
result = initialize_environment()
print('Ambiente Railway:', result)
"
```

## 📊 Testes de Performance

### 1. Teste de Tempo de Coleta

```bash
# Medir tempo de coleta por fonte
python -c "
import time
from src.main import InsuranceNewsAgent

agent = InsuranceNewsAgent()
start_time = time.time()

# Testar fonte específica
result = agent.collect_from_source('revista_apolice')
end_time = time.time()

print(f'Tempo de coleta: {end_time - start_time:.2f}s')
print(f'Artigos coletados: {result.articles_found if result.success else 0}')
"
```

### 2. Teste de Memória

```bash
# Monitorar uso de memória durante coleta
python -c "
import psutil
import os
from src.main import InsuranceNewsAgent

process = psutil.Process(os.getpid())
print(f'Memória inicial: {process.memory_info().rss / 1024 / 1024:.2f} MB')

agent = InsuranceNewsAgent()
result = agent.run_daily_collection()

print(f'Memória final: {process.memory_info().rss / 1024 / 1024:.2f} MB')
print(f'Artigos coletados: {result[\"total_articles_collected\"]}')
"
```

## 🔍 Testes de Qualidade

### 1. Teste de Relevância

```bash
# Testar sistema de scoring
python -c "
from src.utils.text_processor import TextProcessor

processor = TextProcessor()
text = 'Open Insurance revoluciona o mercado de seguros no Brasil'
score = processor.calculate_relevance_score(text)
open_insurance = processor.is_open_insurance_related(text)

print(f'Score de relevância: {score:.2f}')
print(f'Relacionado a Open Insurance: {open_insurance}')
"
```

### 2. Teste de Detecção de Duplicatas

```bash
# Testar detecção de artigos duplicados
python -c "
from src.analyzers.news_analyzer import NewsAnalyzer
from src.models import NewsArticle, Region
from datetime import datetime

analyzer = NewsAnalyzer()

# Criar artigos de teste
article1 = NewsArticle(
    title='Seguro auto cresce 10% no Brasil',
    url='http://exemplo1.com',
    source='Fonte 1',
    region=Region.BRASIL,
    date_published=datetime.now(),
    summary='Crescimento do seguro auto',
    categories=['seguros'],
    relevance_score=0.8
)

article2 = NewsArticle(
    title='Seguro automotivo tem crescimento de 10% no país',
    url='http://exemplo2.com',
    source='Fonte 2',
    region=Region.BRASIL,
    date_published=datetime.now(),
    summary='Aumento do seguro de carros',
    categories=['seguros'],
    relevance_score=0.7
)

similarity = analyzer.calculate_similarity(article1, article2)
print(f'Similaridade: {similarity:.2f}')
print(f'São duplicatas: {similarity > 0.8}')
"
```

## 🚨 Testes de Erro

### 1. Teste de Fonte Indisponível

```bash
# Testar comportamento com fonte offline
python -c "
from src.scrapers.scraper_factory import ScraperFactory

# Tentar acessar fonte que retorna erro 403
scraper = ScraperFactory.create_scraper({
    'name': 'Teste Erro',
    'type': 'web',
    'url': 'https://httpstat.us/403',
    'region': 'Brasil'
})

result = scraper.collect_articles()
print(f'Sucesso: {result.success}')
print(f'Erro: {result.error_message}')
"
```

### 2. Teste de Recuperação de Erro

```bash
# Testar sistema de retry
python -c "
from src.scrapers.base_scraper import BaseScraper
import requests

class TestScraper(BaseScraper):
    def collect_articles(self):
        # Simular erro temporário
        try:
            response = self._make_request('https://httpstat.us/500')
            return self._create_success_result([])
        except Exception as e:
            return self._create_error_result(str(e))

scraper = TestScraper('Teste', 'Brasil', {})
result = scraper.collect_articles()
print(f'Resultado: {result.success}')
"
```

## 📝 Checklist de Testes

### ✅ Testes Obrigatórios

- [ ] Teste de fontes (19/20 funcionando)
- [ ] Teste de coleta básica
- [ ] Teste de aplicação Flask
- [ ] Teste de configuração de ambiente
- [ ] Teste de templates de e-mail
- [ ] Teste de API endpoints

### ✅ Testes de Integração

- [ ] Teste de coleta completa
- [ ] Teste de geração de relatório
- [ ] Teste de envio de e-mail
- [ ] Teste de scheduler
- [ ] Teste de webhook

### ✅ Testes de Deploy

- [ ] Teste local com variáveis de ambiente
- [ ] Teste de configuração Railway
- [ ] Teste de GitHub Actions
- [ ] Teste de performance
- [ ] Teste de recuperação de erro

## 🔧 Troubleshooting

### Problemas Comuns

1. **Erro de autenticação Gmail**
   - Verificar credentials.json
   - Verificar escopos OAuth
   - Regenerar token.json

2. **Fontes não funcionando**
   - Verificar conectividade
   - Verificar mudanças no site
   - Verificar rate limiting

3. **Erro de memória**
   - Reduzir MAX_ARTICLES_PER_SOURCE
   - Implementar processamento em lotes
   - Verificar vazamentos de memória

4. **Performance lenta**
   - Otimizar seletores CSS
   - Implementar cache
   - Usar processamento paralelo

---

**Testing Guide** - Insurance News Agent 🧪


