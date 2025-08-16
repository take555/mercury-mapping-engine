"""
Mercury Mapping Engine - API Routes Registration
APIルートの登録管理
"""
from flask import Blueprint
from .health import health_bp
from .models import models_bp
from .tokens import tokens_bp
from .analysis import analysis_bp


def register_api_routes(app):
    """APIルートをアプリケーションに登録"""
    
    # メインAPIブループリント
    api_bp = Blueprint('api', __name__, url_prefix='/api')
    
    # 各機能のブループリントを登録
    api_bp.register_blueprint(health_bp)
    api_bp.register_blueprint(models_bp)
    api_bp.register_blueprint(tokens_bp)
    api_bp.register_blueprint(analysis_bp)
    
    # アプリケーションに登録
    app.register_blueprint(api_bp)
    
    app.logger.info("✅ API routes registered")
    
    # 登録されたルート一覧をログ出力（デバッグ用）
    if app.config.get('DEBUG'):
        log_registered_routes(app)


def log_registered_routes(app):
    """登録されたルート一覧をログ出力"""
    app.logger.debug("Registered API routes:")
    for rule in app.url_map.iter_rules():
        if rule.rule.startswith('/api'):
            methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
            app.logger.debug(f"  {methods:10} {rule.rule}")


# エラーレスポンス用のヘルパー関数
def create_error_response(message, status_code=400, details=None):
    """統一されたエラーレスポンスを作成"""
    response = {
        'success': False,
        'error': message,
        'status_code': status_code
    }
    
    if details:
        response['details'] = details
    
    return response, status_code


def create_success_response(data=None, message=None):
    """統一された成功レスポンスを作成"""
    response = {
        'success': True
    }
    
    if data is not None:
        response['data'] = data
    
    if message:
        response['message'] = message
    
    return response