"""
Mercury Mapping Engine - Index Page Routes
メインページルート
"""
from flask import Blueprint
import os

# ブループリント作成
index_bp = Blueprint('index', __name__)


@index_bp.route('/')
def index():
    """メインページ"""
    from flask import request, current_app
    
    current_app.logger.info("📍 TOP PAGE アクセス - Mercury Mapping Engine")
    current_app.logger.info(f"   - アクセス元IP: {request.remote_addr}")
    current_app.logger.info(f"   - User-Agent: {request.headers.get('User-Agent', 'Unknown')}")
    
    claude_status = "✅ 設定済み" if os.getenv('CLAUDE_API_KEY') and os.getenv('CLAUDE_API_KEY') != 'your-api-key-here' else "❌ 未設定"
    
    return f'''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Mercury Mapping Engine v2.0</title>
        <style>
            body {{ 
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                margin: 0; 
                padding: 0; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
            }}
            .container {{ 
                max-width: 1200px; 
                margin: 0 auto; 
                padding: 20px; 
            }}
            .header {{ 
                background: rgba(255, 255, 255, 0.1); 
                backdrop-filter: blur(10px);
                color: white; 
                padding: 40px; 
                border-radius: 20px; 
                margin-bottom: 30px; 
                text-align: center;
                box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
            }}
            .header h1 {{ 
                margin: 0; 
                font-size: 3em; 
                font-weight: 300; 
                text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.3);
            }}
            .header p {{ 
                font-size: 1.2em; 
                margin: 10px 0 0 0; 
                opacity: 0.9;
            }}
            .status-badge {{ 
                display: inline-block; 
                padding: 8px 16px; 
                border-radius: 20px; 
                font-weight: bold; 
                margin: 10px 0;
                background: rgba(255, 255, 255, 0.2);
            }}
            .feature-grid {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); 
                gap: 25px; 
                margin: 30px 0; 
            }}
            .feature-card {{ 
                background: rgba(255, 255, 255, 0.95); 
                padding: 30px; 
                border-radius: 15px; 
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
                transition: transform 0.3s ease, box-shadow 0.3s ease;
            }}
            .feature-card:hover {{ 
                transform: translateY(-5px); 
                box-shadow: 0 15px 40px rgba(0, 0, 0, 0.15);
            }}
            .feature-card h3 {{ 
                color: #333; 
                margin-top: 0; 
                font-size: 1.5em;
                display: flex;
                align-items: center;
                gap: 10px;
            }}
            .feature-card p {{ 
                color: #666; 
                line-height: 1.6; 
            }}
            .btn {{ 
                display: inline-block; 
                padding: 12px 25px; 
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                color: white; 
                text-decoration: none; 
                border-radius: 25px; 
                font-weight: 500;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
            }}
            .btn:hover {{ 
                transform: translateY(-2px); 
                box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
                text-decoration: none;
                color: white;
            }}
            .btn-primary {{ 
                background: linear-gradient(135deg, #4CAF50 0%, #45a049 100%); 
                font-size: 1.1em;
                padding: 15px 30px;
            }}
            .btn-secondary {{ 
                background: linear-gradient(135deg, #2196F3 0%, #1976D2 100%); 
            }}
            .btn-tertiary {{ 
                background: linear-gradient(135deg, #FF9800 0%, #F57C00 100%); 
            }}
            .highlight {{ 
                background: linear-gradient(135deg, #FFD700 0%, #FFA000 100%); 
                color: #333;
                font-weight: bold;
            }}
            .workflow-section {{ 
                background: rgba(255, 255, 255, 0.95); 
                padding: 40px; 
                border-radius: 15px; 
                margin: 30px 0;
                box-shadow: 0 10px 30px rgba(0, 0, 0, 0.1);
            }}
            .workflow-steps {{ 
                display: grid; 
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); 
                gap: 20px; 
                margin: 20px 0; 
            }}
            .step {{ 
                text-align: center; 
                padding: 20px; 
                background: #f8f9fa; 
                border-radius: 10px;
                border-left: 5px solid #667eea;
            }}
            .step-number {{ 
                display: inline-block; 
                width: 40px; 
                height: 40px; 
                background: #667eea; 
                color: white; 
                border-radius: 50%; 
                line-height: 40px; 
                font-weight: bold; 
                margin-bottom: 10px; 
            }}
            .footer {{ 
                text-align: center; 
                padding: 30px; 
                color: rgba(255, 255, 255, 0.8); 
                margin-top: 40px; 
            }}
            .api-links {{ 
                display: flex; 
                gap: 15px; 
                flex-wrap: wrap; 
                justify-content: center; 
                margin: 20px 0; 
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🎯 Mercury Mapping Engine</h1>
                <p>高精度カードデータマッピングシステム v2.0</p>
                <div class="status-badge">Claude API: {claude_status}</div>
            </div>
            
            <div class="feature-grid">
                <!-- 高精度分析機能 -->
                <div class="feature-card">
                    <h3>🚀 カードベース高精度分析</h3>
                    <p>実際のカードデータを比較して同じ商品を特定し、従来手法より遥かに高精度なフィールドマッピングを実現します。</p>
                    <a href="/test/files/enhanced" class="btn btn-primary">✨ 高精度分析を開始</a>
                </div>
                
                <!-- 従来分析との比較 -->
                <div class="feature-card">
                    <h3>📊 従来手法との比較</h3>
                    <p>フィールド名ベースの従来手法と新手法の結果を比較して、マッピング品質の向上を確認できます。</p>
                    <a href="/test/files" class="btn btn-secondary">📈 比較分析</a>
                </div>
                
                <!-- システム管理 -->
                <div class="feature-card">
                    <h3>⚙️ システム管理</h3>
                    <p>Claude APIモデル管理、ヘルスチェック、パフォーマンス監視など、システムの状態を総合的に管理できます。</p>
                    <div class="api-links">
                        <a href="/api/health" class="btn btn-tertiary">💚 ヘルスチェック</a>
                        <a href="/test/models" class="btn btn-tertiary">🤖 モデル管理</a>
                    </div>
                </div>
            </div>
            
            <div class="workflow-section">
                <h2 style="text-align: center; color: #333; margin-bottom: 30px;">🔄 カードベース分析の流れ</h2>
                <div class="workflow-steps">
                    <div class="step">
                        <div class="step-number">1</div>
                        <h4>データ準備</h4>
                        <p>A社・B社のCSVファイルを<code>uploads/</code>フォルダに配置</p>
                    </div>
                    <div class="step">
                        <div class="step-number">2</div>
                        <h4>カード特定</h4>
                        <p>システムが自動的に同じカードを特定・マッチング</p>
                    </div>
                    <div class="step">
                        <div class="step-number">3</div>
                        <h4>フィールド分析</h4>
                        <p>マッチしたカードからフィールド対応関係を高精度で分析</p>
                    </div>
                    <div class="step">
                        <div class="step-number">4</div>
                        <h4>ルール生成</h4>
                        <p>信頼度の高いマッピングルールを自動生成</p>
                    </div>
                </div>
                
                <div style="background: #e3f2fd; padding: 20px; border-radius: 10px; margin-top: 20px;">
                    <h3 style="color: #1976d2; margin-top: 0;">💡 新アーキテクチャの特徴</h3>
                    <ul style="color: #333; line-height: 1.6;">
                        <li><strong>従来手法:</strong> フィールド名の類似度のみで判定</li>
                        <li><strong>新手法:</strong> 実際のカードデータを比較→同じ商品を特定→フィールド対応を分析</li>
                        <li><strong>結果:</strong> より高精度で実用的なマッピングを実現</li>
                        <li><strong>拡張性:</strong> モジュール化により新機能追加が容易</li>
                    </ul>
                </div>
            </div>
            
            <div class="workflow-section">
                <h2 style="text-align: center; color: #333; margin-bottom: 20px;">🛠️ 開発者向け機能</h2>
                <div class="api-links">
                    <a href="/test/tokens" class="btn btn-secondary">💰 トークン計算</a>
                    <a href="/test/claude" class="btn btn-secondary">🔗 API接続テスト</a>
                    <a href="/api/health/database" class="btn btn-secondary">🗄️ DB状態確認</a>
                    <a href="/api/health/engine" class="btn btn-secondary">⚙️ エンジン状態</a>
                </div>
            </div>
            
            <div class="footer">
                <p>Mercury Mapping Engine v2.0 | 新アーキテクチャ実装完了</p>
                <p>トレーディングカード業界のデータ統合を革新</p>
            </div>
        </div>
    </body>
    </html>
    ''' 