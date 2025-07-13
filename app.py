"""
Aplicação Flask para deploy no Railway
Fornece API web para monitoramento e controle do Insurance News Agent
"""

import os
import json
from datetime import datetime, timedelta
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
CORS(app)  # Permite CORS para todas as rotas

logger = get_logger("flask_app")

# Inicializa componentes apenas se ambiente foi configurado
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

# Template HTML simples para dashboard
DASHBOARD_TEMPLATE = """
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Insurance News Agent - Dashboard</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 10px;
            padding: 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .header {
            text-align: center;
            margin-bottom: 30px;
            padding-bottom: 20px;
            border-bottom: 2px solid #667eea;
        }
        .header h1 {
            color: #667eea;
            margin: 0;
        }
        .stats {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 30px;
        }
        .stat-card {
            background: #f8f9ff;
            padding: 20px;
            border-radius: 8px;
            text-align: center;
            border: 1px solid #e1e5f2;
        }
        .stat-number {
            font-size: 2em;
            font-weight: bold;
            color: #667eea;
        }
        .stat-label {
            color: #666;
            margin-top: 5px;
        }
        .actions {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 15px;
            margin-bottom: 30px;
        }
        .action-btn {
            background: #667eea;
            color: white;
            padding: 15px 20px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            text-align: center;
            font-size: 1em;
        }
        .action-btn:hover {
            background: #5a6fd8;
        }
        .status {
            background: #e8f5e8;
            padding: 15px;
            border-radius: 5px;
            border-left: 4px solid #4caf50;
            margin-bottom: 20px;
        }
        .logs {
            background: #f8f8f8;
            padding: 15px;
            border-radius: 5px;
            font-family: monospace;
            font-size: 0.9em;
            max-height: 300px;
            overflow-y: auto;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 Insurance News Agent</h1>
            <p>Sistema de Coleta e Análise de Notícias de Seguros</p>
        </div>
        
        <div class="stats">
            <div class="stat-card">
                <div class="stat-number">{{ stats.total_sources }}</div>
                <div class="stat-label">Fontes Configuradas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.regions }}</div>
                <div class="stat-label">Regiões Cobertas</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.last_execution }}</div>
                <div class="stat-label">Última Execução</div>
            </div>
            <div class="stat-card">
                <div class="stat-number">{{ stats.status }}</div>
                <div class="stat-label">Status do Sistema</div>
            </div>
        </div>
        
        <div class="actions">
            <a href="/api/collect" class="action-btn">🔍 Executar Coleta</a>
            <a href="/api/test" class="action-btn">🧪 Testar Fontes</a>
            <a href="/api/status" class="action-btn">📊 Status Detalhado</a>
            <a href="/api/reports" class="action-btn">📄 Relatórios</a>
        </div>
        
        <div class="status">
            <strong>Status:</strong> Sistema operacional e monitorando {{ stats.total_sources }} fontes de notícias.
            <br><strong>Última atualização:</strong> {{ current_time }}
        </div>
        
        <h3>📋 Logs Recentes</h3>
        <div class="logs" id="logs">
            Carregando logs...
        </div>
    </div>
    
    <script>
        // Atualiza logs a cada 30 segundos
        function updateLogs() {
            fetch('/api/logs')
                .then(response => response.json())
                .then(data => {
                    document.getElementById('logs').innerHTML = data.logs.join('\\n');
                })
                .catch(error => {
                    document.getElementById('logs').innerHTML = 'Erro ao carregar logs: ' + error;
                });
        }
        
        // Carrega logs inicialmente
        updateLogs();
        
        // Atualiza logs periodicamente
        setInterval(updateLogs, 30000);
    </script>
</body>
</html>
"""


@app.route('/')
def dashboard():
    """Dashboard principal"""
    try:
        # Obtém estatísticas do sistema
        stats = agent.get_statistics()
        
        # Dados para o template
        template_data = {
            'stats': {
                'total_sources': stats.get('total_sources', 0),
                'regions': len(stats.get('sources_by_region', {})),
                'last_execution': 'Hoje',  # TODO: implementar tracking
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
    """Status da API"""
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
    """Executa coleta de notícias"""
    try:
        logger.info("🚀 Iniciando coleta via API")
        
        # Executa coleta
        result = agent.run_daily_collection()
        
        if result['success']:
            logger.info(f"✅ Coleta concluída: {result['total_articles_collected']} artigos")
            
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
                'message': 'Erro na coleta',
                'error': 'Falha na execução'
            }), 500
    
    except Exception as e:
        logger.error(f"❌ Erro na coleta via API: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro interno',
            'error': str(e)
        }), 500


@app.route('/api/test')
def api_test():
    """Testa todas as fontes"""
    try:
        logger.info("🧪 Testando fontes via API")
        
        result = agent.test_sources()
        
        return jsonify({
            'success': True,
            'message': 'Teste concluído',
            'results': result
        })
    
    except Exception as e:
        logger.error(f"❌ Erro no teste via API: {e}")
        return jsonify({
            'success': False,
            'message': 'Erro no teste',
            'error': str(e)
        }), 500


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
        for file_path in reports_dir.glob('relatorio_seguros_*.html'):
            date_str = file_path.stem.replace('relatorio_seguros_', '')
            reports.append({
                'date': date_str,
                'html_file': str(file_path),
                'json_file': str(file_path.with_suffix('.json')),
                'size': file_path.stat().st_size
            })
        
        # Ordena por data (mais recente primeiro)
        reports.sort(key=lambda x: x['date'], reverse=True)
        
        return jsonify({
            'reports': reports[:10],  # Últimos 10 relatórios
            'total': len(reports)
        })
    
    except Exception as e:
        logger.error(f"❌ Erro ao listar relatórios: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


@app.route('/api/logs')
def api_logs():
    """Retorna logs recentes"""
    try:
        log_file = Path('logs/insurance_agent.log')
        
        if not log_file.exists():
            return jsonify({
                'logs': ['Log file not found'],
                'message': 'Arquivo de log não encontrado'
            })
        
        # Lê últimas 50 linhas
        with open(log_file, 'r', encoding='utf-8') as f:
            lines = f.readlines()
            recent_lines = lines[-50:] if len(lines) > 50 else lines
        
        return jsonify({
            'logs': [line.strip() for line in recent_lines],
            'total_lines': len(lines)
        })
    
    except Exception as e:
        logger.error(f"❌ Erro ao ler logs: {e}")
        return jsonify({
            'logs': [f'Erro ao ler logs: {e}'],
            'error': str(e)
        })


@app.route('/api/health')
def health_check():
    """Health check para monitoramento"""
    return jsonify({
        'status': 'healthy',
        'timestamp': datetime.now().isoformat(),
        'service': 'insurance-news-agent'
    })


@app.route('/webhook/collect', methods=['POST'])
def webhook_collect():
    """Webhook para execução via GitHub Actions ou outros serviços"""
    try:
        # Verifica token de autorização se configurado
        auth_token = os.getenv('WEBHOOK_TOKEN')
        if auth_token:
            provided_token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if provided_token != auth_token:
                return jsonify({'error': 'Unauthorized'}), 401
        
        logger.info("🔗 Webhook de coleta acionado")
        
        # Executa coleta
        result = agent.run_daily_collection()
        
        # Envia e-mail se configurado
        send_email = request.json.get('send_email', True) if request.is_json else True
        
        if result['success'] and send_email:
            try:
                if email_manager.authenticate():
                    email_manager.send_daily_report(result['daily_report'])
                    logger.info("📧 E-mail enviado via webhook")
            except Exception as e:
                logger.error(f"❌ Erro no envio de e-mail via webhook: {e}")
        
        return jsonify({
            'success': result['success'],
            'message': 'Webhook executado com sucesso',
            'statistics': {
                'total_articles': result['total_articles_collected'],
                'execution_time': result['execution_time']
            }
        })
    
    except Exception as e:
        logger.error(f"❌ Erro no webhook: {e}")
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    # Configuração para produção
    port = int(os.environ.get('PORT', 8000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    
    logger.info(f"🚀 Iniciando Insurance News Agent Flask App na porta {port}")
    
    # Cria diretórios necessários
    Path('data/reports').mkdir(parents=True, exist_ok=True)
    Path('logs').mkdir(parents=True, exist_ok=True)
    Path('config').mkdir(parents=True, exist_ok=True)
    
    # Inicia aplicação
    app.run(host='0.0.0.0', port=port, debug=debug)

