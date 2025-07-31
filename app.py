"""
Aplicação Flask para deploy no Railway
Fornece API web para monitoramento e controle do Insurance News Agent
VERSÃO CORRIGIDA - Compatível com deduplicação e SMTP
"""

import os
import json
from datetime import datetime
from pathlib import Path
from flask import Flask, jsonify, request, render_template_string
from flask_cors import CORS

# Inicializa ambiente antes de importar outros módulos
from src.utils.environment import initialize_environment, get_config_summary, validate_environment

# Inicializa ambiente
env_initialized = initialize_environment()

from src.main import InsuranceNewsAgent
from src.email_sender.email_manager import EmailManager
from src.utils.logger import get_logger

# Configuração do Flask
app = Flask(__name__)
CORS(app)

logger = get_logger("flask_app")

# Inicializa componentes
agent = None
email_manager = None

if env_initialized:
    try:
        agent = InsuranceNewsAgent()
        email_manager = EmailManager()
        logger.info("✅ Componentes inicializados com sucesso")
    except Exception as e:
        logger.error(f"❌ Erro ao inicializar componentes: {e}")
else:
    logger.error("❌ Ambiente não foi inicializado corretamente")

# Garantia de que diretórios essenciais existem
for folder in ['data/reports', 'data/deduplication', 'logs', 'config']:
    Path(folder).mkdir(parents=True, exist_ok=True)

logger.info("✅ Flask app carregado com sucesso - pronto para servir via Gunicorn")

# ================== ROTAS ==================

DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Insurance News Agent</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; padding: 2rem; background: #f5f5f5; }
        .container { max-width: 1200px; margin: 0 auto; }
        .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 2rem; border-radius: 10px; margin-bottom: 2rem; }
        .stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(250px, 1fr)); gap: 1rem; margin-bottom: 2rem; }
        .stat-card { background: white; padding: 1.5rem; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }
        .stat-number { font-size: 2em; font-weight: bold; color: #667eea; }
        .actions { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 1rem; }
        .btn { background: #667eea; color: white; padding: 1rem; border: none; border-radius: 5px; cursor: pointer; text-decoration: none; text-align: center; }
        .btn:hover { background: #5a6fd8; }
        .status-online { color: #28a745; }
        .status-offline { color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Insurance News Agent</h1>
            <p>Sistema de coleta e análise de notícias do mercado de seguros</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_sources }}</div>
                <div>Fontes Configuradas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.regions }}</div>
                <div>Regiões Cobertas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number {{ stats.status_class }}">{{ stats.status }}</div>
                <div>Status do Sistema</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.dedup_count }}</div>
                <div>Artigos no Histórico</div>
            </div>
        </div>
        
        <div class="actions">
            <a href="/api/collect" class="btn">🚀 Executar Coleta</a>
            <a href="/api/test" class="btn">🧪 Testar Fontes</a>
            <a href="/api/reports" class="btn">📊 Ver Relatórios</a>
            <a href="/api/status" class="btn">📈 Status Detalhado</a>
        </div>
        
        <div style="margin-top: 2rem; text-align: center; color: #666;">
            <p>Última atualização: {{ current_time }}</p>
            <p>Sistema com deduplicação ativa e envio por SMTP</p>
        </div>
    </div>
</body>
</html>
"""

@app.route('/')
def dashboard():
    """Dashboard principal com estatísticas"""
    try:
        stats = agent.get_statistics() if agent else {}
        dedup_stats = stats.get('deduplication_stats', {})
        
        template_data = {
            'stats': {
                'total_sources': stats.get('total_sources', 0),
                'regions': len(stats.get('sources_by_region', {})),
                'status': '✅ Online' if agent else '❌ Offline',
                'status_class': 'status-online' if agent else 'status-offline',
                'dedup_count': dedup_stats.get('total_sent', 0)
            },
            'current_time': datetime.now().strftime('%d/%m/%Y às %H:%M')
        }
        return render_template_string(DASHBOARD_TEMPLATE, **template_data)
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}")
        return f"<h1>Erro no Dashboard</h1><p>{str(e)}</p>", 500

@app.route('/api/status')
def api_status():
    """Status detalhado do sistema"""
    try:
        if not agent:
            return jsonify({'error': 'Agent não inicializado'}), 500
            
        stats = agent.get_statistics()
        email_status = {}
        
        if email_manager:
            try:
                email_validation = email_manager.validate_configuration()
                email_status = {
                    'configured': email_validation['valid'],
                    'recipients_count': email_validation['recipients_count'],
                    'issues': email_validation.get('issues', [])
                }
            except Exception as e:
                email_status = {'error': str(e)}
        
        return jsonify({
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'system_stats': stats,
            'email_status': email_status,
            'environment': {
                'railway': bool(os.getenv('RAILWAY_ENVIRONMENT')),
                'production': env_initialized
            },
            'version': '2.0.0'
        })
    except Exception as e:
        logger.error(f"Erro no status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/collect', methods=['GET', 'POST'])
def api_collect():
    """Executa coleta de notícias"""
    try:
        if not agent:
            return jsonify({'error': 'Agent não inicializado'}), 500
            
        logger.info("🚀 Iniciando coleta via API")
        result = agent.run_daily_collection()
        
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Coleta executada com sucesso',
                'statistics': {
                    'total_articles_collected': result['total_articles_collected'],
                    'unique_articles_after_dedup': result['unique_articles_after_dedup'],
                    'duplicates_removed': result['duplicates_removed'],
                    'top_articles_count': result['top_articles_count'],
                    'other_articles_count': result['other_articles_count'],
                    'open_insurance_count': result['open_insurance_count'],
                    'successful_sources': result['successful_sources'],
                    'total_sources': result['total_sources_processed'],
                    'execution_time': result['execution_time']
                },
                'reports': {
                    'html': result['html_report_path'],
                    'json': result['json_report_path']
                },
                'deduplication': result['deduplication_stats']
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erro na coleta',
                'error': result.get('error', 'Erro desconhecido')
            }), 500
    except Exception as e:
        logger.error(f"❌ Erro na coleta via API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test')
def api_test():
    """Testa todas as fontes configuradas"""
    try:
        if not agent:
            return jsonify({'error': 'Agent não inicializado'}), 500
            
        logger.info("🧪 Testando fontes via API")
        result = agent.test_sources()
        return jsonify({
            'success': True, 
            'message': 'Teste concluído', 
            'results': result
        })
    except Exception as e:
        logger.error(f"❌ Erro no teste via API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports')
def api_reports():
    """Lista relatórios disponíveis"""
    try:
        reports_dir = Path('data/reports')
        if not reports_dir.exists():
            return jsonify({
                'reports': [],
                'message': 'Nenhum relatório encontrado'
            })
        
        reports = []
        # CORREÇÃO: Busca por daily_report_ ao invés de relatorio_seguros_
        for file_path in reports_dir.glob('daily_report_*.html'):
            date_str = file_path.stem.replace('daily_report_', '')
            json_path = file_path.with_suffix('.json')
            
            reports.append({
                'date': date_str,
                'html_file': str(file_path),
                'json_file': str(json_path) if json_path.exists() else None,
                'html_size': file_path.stat().st_size,
                'json_size': json_path.stat().st_size if json_path.exists() else 0
            })
        
        # Ordena por data (mais recente primeiro)
        reports.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            'reports': reports[:10],  # Últimos 10 relatórios
            'total': len(reports)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao listar relatórios: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    """Retorna logs recentes do sistema"""
    try:
        log_file = Path('logs/insurance_agent.log')
        if not log_file.exists():
            return jsonify({'logs': ['Log file not found']})
        
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Retorna últimas 100 linhas
        recent_logs = [line.strip() for line in lines[-100:]]
        
        return jsonify({
            'logs': recent_logs,
            'total_lines': len(lines),
            'log_file': str(log_file)
        })
    except Exception as e:
        logger.error(f"❌ Erro ao ler logs: {e}")
        return jsonify({'logs': [f'Erro: {e}'], 'error': str(e)})

@app.route('/api/email/test', methods=['POST'])
def api_test_email():
    """Testa envio de e-mail"""
    try:
        if not email_manager:
            return jsonify({'error': 'Email manager não inicializado'}), 500
        
        data = request.get_json() or {}
        test_email = data.get('email')
        
        if not test_email:
            return jsonify({'error': 'E-mail não fornecido'}), 400
        
        # Testa autenticação
        if not email_manager.authenticate():
            return jsonify({
                'success': False,
                'error': 'Falha na autenticação do e-mail'
            }), 500
        
        # Envia e-mail de teste
        success = email_manager.send_test_email(test_email)
        
        return jsonify({
            'success': success,
            'message': 'E-mail de teste enviado' if success else 'Falha no envio'
        })
        
    except Exception as e:
        logger.error(f"❌ Erro no teste de e-mail: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/health')
def health_check():
    """Health check para monitoramento"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'insurance-news-agent',
        'version': '2.0.0',
        'features': ['deduplication', 'smtp_email', 'multi_region']
    })

@app.route('/webhook/collect', methods=['POST'])
def webhook_collect():
    """Webhook para execução via GitHub Actions"""
    try:
        # Verifica token de autenticação se configurado
        auth_token = os.getenv('WEBHOOK_TOKEN')
        if auth_token:
            provided_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if provided_token != auth_token:
                return jsonify({'error': 'Unauthorized'}), 401
        
        if not agent:
            return jsonify({'error': 'Agent não inicializado'}), 500
        
        logger.info("🔗 Webhook acionado")
        result = agent.run_daily_collection()
        
        # Tenta enviar e-mail se solicitado
        send_email = request.json.get('send_email', True) if request.is_json else True
        email_sent = False
        
        if result['success'] and send_email and email_manager:
            try:
                if email_manager.authenticate():
                    # Carrega relatório do arquivo JSON
                    json_path = result.get('json_report_path')
                    if json_path and Path(json_path).exists():
                        with open(json_path, 'r', encoding='utf-8') as f:
                            report_data = json.load(f)
                        
                        # Cria objeto DailyReport simplificado para e-mail
                        from src.models import DailyReport
                        daily_report = DailyReport(
                            date=datetime.fromisoformat(report_data['date']),
                            total_articles=report_data['total_articles'],
                            top_articles=[],  # Simplificado para webhook
                            open_insurance_articles=[],
                            articles_by_region=report_data.get('articles_by_region', {}),
                            summary=report_data['summary']
                        )
                        
                        email_sent = email_manager.send_daily_report(daily_report)
                        
            except Exception as e:
                logger.error(f"Erro no envio de e-mail via webhook: {e}")
        
        return jsonify({
            'success': result['success'],
            'email_sent': email_sent,
            'statistics': {
                'total_articles_collected': result['total_articles_collected'],
                'unique_articles': result['unique_articles_after_dedup'],
                'duplicates_removed': result['duplicates_removed'],
                'execution_time': result['execution_time']
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

# Tratamento de erros
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint não encontrado'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Erro interno do servidor'}), 500

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 8000))
    logger.info(f"🚀 Iniciando servidor Flask na porta {port}")
    app.run(host="0.0.0.0", port=port, debug=False)
