"""
Aplicação Flask para deploy no Railway
Fornece API web para monitoramento e controle do Insurance News Agent
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
for folder in ['data/reports', 'logs', 'config']:
    Path(folder).mkdir(parents=True, exist_ok=True)

logger.info("✅ Flask app carregado com sucesso - pronto para servir via Gunicorn")

# ================== ROTAS ==================

DASHBOARD_TEMPLATE = """<!DOCTYPE html>..."""  # Mantenha seu HTML completo aqui

@app.route('/')
def dashboard():
    try:
        stats = agent.get_statistics()
        template_data = {
            'stats': {
                'total_sources': stats.get('total_sources', 0),
                'regions': len(stats.get('sources_by_region', {})),
                'last_execution': 'Hoje',
                'status': '✅ Online'
            },
            'current_time': datetime.now().strftime('%d/%m/%Y às %H:%M')
        }
        return render_template_string(DASHBOARD_TEMPLATE, **template_data)
    except Exception as e:
        logger.error(f"Erro no dashboard: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/status')
def api_status():
    try:
        stats = agent.get_statistics()
        return jsonify({
            'status': 'online',
            'timestamp': datetime.now().isoformat(),
            'system_stats': stats,
            'email_config': email_manager.get_recipients_count() if email_manager else {},
            'version': '1.0.0'
        })
    except Exception as e:
        logger.error(f"Erro no status: {e}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/collect', methods=['GET', 'POST'])
def api_collect():
    try:
        logger.info("🚀 Iniciando coleta via API")
        result = agent.run_daily_collection()
        if result['success']:
            return jsonify({
                'success': True,
                'message': 'Coleta executada com sucesso',
                'statistics': {
                    'total_articles': result['total_articles_collected'],
                    'successful_sources': result['successful_sources'],
                    'total_sources': result['total_sources_processed'],
                    'execution_time': result['execution_time'],
                    'open_insurance_articles': result['open_insurance_articles_count']
                },
                'reports': {
                    'html': result['report_html_path'],
                    'json': result['report_json_path']
                }
            })
        else:
            return jsonify({
                'success': False,
                'message': 'Erro na coleta'
            }), 500
    except Exception as e:
        logger.error(f"❌ Erro na coleta via API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/test')
def api_test():
    try:
        logger.info("🧪 Testando fontes via API")
        result = agent.test_sources()
        return jsonify({'success': True, 'message': 'Teste concluído', 'results': result})
    except Exception as e:
        logger.error(f"❌ Erro no teste via API: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/reports')
def api_reports():
    try:
        reports_dir = Path('data/reports')
        if not reports_dir.exists():
            return jsonify({'reports': [], 'message': 'Nenhum relatório encontrado'})
        reports = []
        for file_path in reports_dir.glob('relatorio_seguros_*.html'):
            date_str = file_path.stem.replace('relatorio_seguros_', '')
            reports.append({
                'date': date_str,
                'html_file': str(file_path),
                'json_file': str(file_path.with_suffix('.json')),
                'size': file_path.stat().st_size
            })
        reports.sort(key=lambda x: x['date'], reverse=True)
        return jsonify({'reports': reports[:10], 'total': len(reports)})
    except Exception as e:
        logger.error(f"❌ Erro ao listar relatórios: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/logs')
def api_logs():
    try:
        log_file = Path('logs/insurance_agent.log')
        if not log_file.exists():
            return jsonify({'logs': ['Log file not found']})
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        return jsonify({'logs': [line.strip() for line in lines[-50:]], 'total_lines': len(lines)})
    except Exception as e:
        logger.error(f"❌ Erro ao ler logs: {e}")
        return jsonify({'logs': [f'Erro: {e}'], 'error': str(e)})

@app.route('/api/health')
def health_check():
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'insurance-news-agent'
    })

@app.route('/webhook/collect', methods=['POST'])
def webhook_collect():
    try:
        auth_token = os.getenv('WEBHOOK_TOKEN')
        if auth_token:
            provided_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if provided_token != auth_token:
                return jsonify({'error': 'Unauthorized'}), 401
        logger.info("🔗 Webhook acionado")
        result = agent.run_daily_collection()
        send_email = request.json.get('send_email', True) if request.is_json else True
        if result['success'] and send_email:
            try:
                if email_manager.authenticate():
                    email_manager.send_daily_report(result['daily_report'])
            except Exception as e:
                logger.error(f"Erro no envio de e-mail: {e}")
        return jsonify({
            'success': result['success'],
            'statistics': {
                'total_articles': result['total_articles_collected'],
                'execution_time': result['execution_time']
            }
        })
    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500

