"""
Mercury Mapping Engine - Main Application
軽量化されたメインアプリケーション
"""
from flask import Flask
import os
import sys

# プロジェクトルートをPythonパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.settings import Config
from config.database import init_db
from api.routes import register_api_routes
from web.routes import register_web_routes
from utils.logger import setup_logging


def create_app(config_name='default'):
    """アプリケーションファクトリー"""
    app = Flask(__name__)
    
    # 設定読み込み
    app.config.from_object(Config.get_config(config_name))
    
    # 日本語対応
    app.config['JSON_AS_ASCII'] = False
    
    # ログ設定
    setup_logging(app)
    
    # データベース初期化
    init_db(app)
    
    # ルート登録
    register_api_routes(app)
    register_web_routes(app)
    
    # エラーハンドラー登録
    register_error_handlers(app)
    
    app.logger.info("Mercury Mapping Engine initialized")
    
    return app


def register_error_handlers(app):
    """エラーハンドラーの登録"""
    
    @app.errorhandler(404)
    def not_found(error):
        return """
        <h1>404 - ページが見つかりません</h1>
        <p><a href="/">トップページに戻る</a></p>
        """, 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"Internal server error: {error}")
        return """
        <h1>500 - サーバーエラー</h1>
        <p>システムエラーが発生しました。</p>
        <p><a href="/">トップページに戻る</a></p>
        """, 500


if __name__ == '__main__':
    # 開発環境での実行
    app = create_app('development')
    
    host = os.getenv('FLASK_HOST', '0.0.0.0')
    port = int(os.getenv('FLASK_PORT', 5000))
    debug = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    print("=" * 50)
    print("🚀 Mercury Mapping Engine Starting...")
    print(f"📍 URL: http://{host}:{port}")
    print(f"🔧 Debug Mode: {debug}")
    print(f"🗄️  Database: {app.config.get('DATABASE_URL', 'MySQL')}")
    print(f"🤖 Claude API: {'✅ Configured' if os.getenv('CLAUDE_API_KEY') else '❌ Not Configured'}")
    print("=" * 50)
    
    app.run(host=host, port=port, debug=debug)