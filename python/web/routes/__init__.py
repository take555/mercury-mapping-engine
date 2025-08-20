"""
Mercury Mapping Engine - Web Routes Registration
Webページルートの登録管理
"""
from flask import Blueprint
from .index import index_bp
# from .test_pages import test_bp
from .enhanced import enhanced_bp


def register_web_routes(app):
    """Webルートをアプリケーションに登録"""
    
    # 各機能のブループリントを直接登録
    app.register_blueprint(index_bp)
    # app.register_blueprint(test_bp)
    app.register_blueprint(enhanced_bp)
    
    app.logger.info("✅ Web routes registered")
    
    # 登録されたルート一覧をログ出力（デバッグ用）
    if app.config.get('DEBUG'):
        log_registered_web_routes(app)


def log_registered_web_routes(app):
    """登録されたWebルート一覧をログ出力"""
    app.logger.debug("Registered Web routes:")
    for rule in app.url_map.iter_rules():
        if not rule.rule.startswith('/api'):
            methods = ', '.join(rule.methods - {'HEAD', 'OPTIONS'})
            app.logger.debug(f"  {methods:10} {rule.rule}")


# HTML生成用のヘルパー関数
def render_error_page(title, message, details=None):
    """エラーページのHTML生成"""
    details_html = f"<pre>{details}</pre>" if details else ""
    
    return f"""
    <html>
    <head>
        <title>{title} - Mercury Mapping Engine</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .error {{ color: #d32f2f; }}
            .details {{ background: #f5f5f5; padding: 15px; margin: 15px 0; border-radius: 5px; }}
        </style>
    </head>
    <body>
        <h1 class="error">{title}</h1>
        <p>{message}</p>
        {details_html}
        <p><a href="/">← トップページに戻る</a></p>
    </body>
    </html>
    """


def render_success_page(title, content):
    """成功ページのHTML生成"""
    return f"""
    <html>
    <head>
        <title>{title} - Mercury Mapping Engine</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .success {{ color: #2e7d32; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
            th {{ background-color: #f0f0f0; }}
            .nav {{ margin: 20px 0; }}
            .nav a {{ margin-right: 15px; }}
        </style>
    </head>
    <body>
        <h1 class="success">{title}</h1>
        {content}
        <div class="nav">
            <a href="/">← トップページに戻る</a>
        </div>
    </body>
    </html>
    """