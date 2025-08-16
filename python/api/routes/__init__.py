"""
Mercury Mapping Engine - API Routes
REST API エンドポイントの登録管理
"""
from flask import Blueprint, jsonify

def register_api_routes(app):
    """API routes を Flask アプリに登録"""
    
    try:
        # Health Check
        from .health import health_bp
        app.register_blueprint(health_bp, url_prefix='/api')
        print("✅ Health API registered")
        
    except ImportError as e:
        print(f"⚠️ Health API import failed: {e}")
    
    try:
        # Models API
        from .models import models_bp
        app.register_blueprint(models_bp, url_prefix='/api')
        print("✅ Models API registered")
        
    except ImportError as e:
        print(f"⚠️ Models API import failed: {e}")
    
    try:
        # Tokens API  
        from .tokens import tokens_bp
        app.register_blueprint(tokens_bp, url_prefix='/api')
        print("✅ Tokens API registered")
        
    except ImportError as e:
        print(f"⚠️ Tokens API import failed: {e}")
    
    try:
        # Analysis API
        from .analysis import analysis_bp
        app.register_blueprint(analysis_bp, url_prefix='/api')
        print("✅ Analysis API registered")
        
    except ImportError as e:
        print(f"⚠️ Analysis API import failed: {e}")
    
    # フォールバック: 基本的なヘルスチェック
    if not any(rule.endpoint and 'health' in rule.endpoint for rule in app.url_map.iter_rules()):
        health_bp = Blueprint('fallback_health', __name__)
        
        @health_bp.route('/health')
        def health_check():
            return jsonify({
                'status': 'ok', 
                'message': 'Mercury Mapping Engine API is running',
                'mode': 'fallback'
            })
        
        app.register_blueprint(health_bp, url_prefix='/api')
        print("✅ Fallback health check registered")

# パッケージ情報
__version__ = "1.0.0"
__all__ = ['register_api_routes']
