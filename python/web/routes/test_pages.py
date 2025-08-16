"""
Mercury Mapping Engine - Test Pages Routes
テストページ群ルート
"""
from flask import Blueprint, request, current_app
import os
import requests
import json
from config.settings import Config

# ブループリント作成
test_bp = Blueprint('test', __name__)


@test_bp.route('/test/claude')
def test_claude_api():
    """Claude API接続テスト"""
    try:
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        if not claude_api_key or claude_api_key == 'your-api-key-here':
            return _render_error_page("Claude API Key未設定", ".envファイルでCLAUDE_API_KEYを設定してください")
        
        # シンプルなテストプロンプト
        test_prompt = """
以下のフィールド対応を分析してください：

A社: name, price
B社: カード名, 値段

JSON形式で回答してください：
{"mappings": [{"field_type": "name", "company_a_field": "name", "company_b_field": "カード名", "confidence": 0.9, "reasoning": "テスト"}]}
"""
        
        response = _call_claude_api(claude_api_key, test_prompt)
        
        if response:
            return f"""
            <h2>✅ Claude API接続テスト成功</h2>
            <h3>レスポンス:</h3>
            <pre style="background: #f0f8ff; padding: 15px; border-radius: 5px; overflow-x: auto;">{json.dumps(response, indent=2, ensure_ascii=False)}</pre>
            <p><a href="/">← トップページに戻る</a></p>
            """
        else:
            return _render_error_page("Claude API接続テスト失敗", "APIからのレスポンスを取得できませんでした")
        
    except Exception as e:
        return _render_error_page("Claude API接続テスト失敗", str(e))


@test_bp.route('/test/models')
def test_models_page():
    """モデル一覧表示ページ"""
    try:
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        if not claude_api_key or claude_api_key == 'your-api-key-here':
            return _render_error_page("Claude API Key未設定", ".envファイルでCLAUDE_API_KEYを設定してください")
        
        # APIからモデル一覧を取得
        models = _fetch_available_models(claude_api_key)
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Claude モデル一覧 - Mercury Mapping Engine</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f0f0f0; font-weight: bold; }}
                .status-official {{ color: green; }}
                .status-fallback {{ color: orange; }}
                .nav {{ margin: 20px 0; }}
                .nav a {{ margin-right: 15px; padding: 8px 16px; background: #2196f3; color: white; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <h1>🤖 Claude モデル一覧</h1>
            <p>取得されたモデル数: <strong>{len(models)}</strong></p>
            
            <table>
            <tr>
                <th>表示名</th>
                <th>モデルID</th>
                <th>特性</th>
                <th>データソース</th>
                <th>テスト</th>
            </tr>
        """
        
        for model in models:
            source_class = "status-official" if model.get('source') == 'official_api' else "status-fallback"
            source_text = "🌐 公式API" if model.get('source') == 'official_api' else "📋 フォールバック"
            
            characteristics = model.get('characteristics', {})
            char_text = f"{characteristics.get('performance', 'unknown')} / {characteristics.get('cost', 'unknown')} / {characteristics.get('speed', 'unknown')}"
            
            test_link = f'<a href="/test/model/{model["id"]}">詳細テスト</a>'
            
            html += f"""
            <tr>
                <td><strong>{model['name']}</strong></td>
                <td style="font-family: monospace; font-size: 12px;">{model['id']}</td>
                <td>{char_text}</td>
                <td class="{source_class}">{source_text}</td>
                <td>{test_link}</td>
            </tr>
            """
        
        html += f"""
            </table>
            
            <h2>💡 モデル特性ガイド</h2>
            <ul>
                <li><strong>Haiku:</strong> 高速・低コスト - 簡単なタスクに最適</li>
                <li><strong>Sonnet:</strong> バランス - 一般的な用途に推奨</li>
                <li><strong>Opus:</strong> 高精度・高コスト - 複雑なタスクに最適</li>
                <li><strong>3.5シリーズ:</strong> 最新版 - 改善された性能</li>
            </ul>
            
            <div class="nav">
                <a href="/">🏠 トップページ</a>
                <a href="/test/tokens">💰 トークン計算</a>
                <a href="/test/claude">🔗 API接続テスト</a>
                <a href="/api/models">📊 JSON API</a>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return _render_error_page("モデル一覧取得エラー", str(e))


@test_bp.route('/test/model/<model_id>')
def test_specific_model(model_id):
    """特定モデルの詳細テストページ"""
    try:
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        if not claude_api_key or claude_api_key == 'your-api-key-here':
            return _render_error_page("Claude API Key未設定", ".envファイルでCLAUDE_API_KEYを設定してください")
        
        # モデル情報取得
        model_info = _get_model_info(claude_api_key, model_id)
        
        if not model_info:
            return _render_error_page("モデル情報取得失敗", f"モデル '{model_id}' の情報を取得できませんでした。")
        
        # テスト実行
        test_prompt = "以下の2つのフィールドは同じ意味ですか？\nA: 'カード名'\nB: 'card_name'\n\nJSON形式で回答: {\"same_meaning\": true/false, \"confidence\": 0.0-1.0}"
        
        test_result = _test_model_functionality(claude_api_key, model_id, test_prompt)
        
        characteristics = model_info.get('characteristics', {})
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>モデル詳細: {model_info.get('name', model_id)} - Mercury Mapping Engine</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .success {{ color: green; background: #e8f5e8; padding: 15px; border-radius: 5px; }}
                .error {{ color: red; background: #ffe6e6; padding: 15px; border-radius: 5px; }}
                table {{ border-collapse: collapse; width: 100%; margin: 20px 0; }}
                th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
                th {{ background-color: #f0f0f0; }}
                pre {{ background: #f0f8ff; padding: 15px; border-radius: 5px; overflow-x: auto; }}
                .nav {{ margin: 20px 0; }}
                .nav a {{ margin-right: 15px; padding: 8px 16px; background: #2196f3; color: white; text-decoration: none; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <h1>🤖 モデル詳細: {model_info.get('name', model_id)}</h1>
            
            <h2>📋 基本情報</h2>
            <table>
                <tr><th>項目</th><th>値</th></tr>
                <tr><td>モデルID</td><td style="font-family: monospace;">{model_info['id']}</td></tr>
                <tr><td>表示名</td><td>{model_info.get('display_name', 'N/A')}</td></tr>
                <tr><td>作成日</td><td>{model_info.get('created_at', 'N/A')}</td></tr>
                <tr><td>データソース</td><td>{'🌐 公式API' if model_info.get('source') == 'official_api' else '📋 フォールバック'}</td></tr>
            </table>
            
            <h2>⚡ 性能特性</h2>
            <table>
                <tr><th>項目</th><th>評価</th></tr>
                <tr><td>性能</td><td>{characteristics.get('performance', 'unknown')}</td></tr>
                <tr><td>コスト</td><td>{characteristics.get('cost', 'unknown')}</td></tr>
                <tr><td>速度</td><td>{characteristics.get('speed', 'unknown')}</td></tr>
                <tr><td>推奨最大トークン</td><td>{characteristics.get('max_tokens', 'N/A')}</td></tr>
            </table>
            
            <h2>🎯 推奨用途</h2>
            <ul>
        """
        
        for use_case in characteristics.get('use_cases', ['汎用タスク']):
            html += f"<li>{use_case}</li>"
        
        html += f"""
            </ul>
            
            <h2>🧪 接続テスト結果</h2>
        """
        
        if test_result.get('success'):
            html += f"""
            <div class="success">
                <h3>✅ テスト成功</h3>
                <p><strong>レスポンス時間:</strong> {test_result.get('response_time_ms', 'N/A')}ms</p>
            </div>
            <h4>テストレスポンス:</h4>
            <pre>{test_result.get('response', 'No response')}</pre>
            """
        else:
            html += f"""
            <div class="error">
                <h3>❌ テスト失敗</h3>
                <p><strong>エラー:</strong> {test_result.get('error', 'Unknown error')}</p>
            </div>
            """
        
        html += f"""
            <div class="nav">
                <a href="/test/models">← モデル一覧に戻る</a>
                <a href="/test/files/enhanced?model={model_id}">このモデルで分析実行</a>
                <a href="/">🏠 トップページ</a>
            </div>
        </body>
        </html>
        """
        
        return html
        
    except Exception as e:
        return _render_error_page("モデルテストエラー", str(e))


@test_bp.route('/test/tokens')
def test_tokens_page():
    """トークン計算テストページ"""
    return '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>Claude Token Count テスト - Mercury Mapping Engine</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }
            .form-container { background: #f8f9fa; padding: 30px; border-radius: 10px; margin: 20px 0; }
            .result-container { background: #e3f2fd; padding: 20px; border-radius: 10px; margin: 20px 0; }
            textarea { width: 100%; min-height: 200px; padding: 15px; border: 1px solid #ddd; border-radius: 5px; font-family: monospace; }
            select, button { padding: 10px 15px; margin: 10px 5px; border: 1px solid #ddd; border-radius: 5px; }
            button { background: #2196f3; color: white; cursor: pointer; font-weight: bold; }
            button:hover { background: #1976d2; }
            table { border-collapse: collapse; width: 100%; margin: 15px 0; }
            th, td { border: 1px solid #ddd; padding: 12px; text-align: left; }
            th { background-color: #f0f0f0; }
            .nav a { margin-right: 15px; padding: 8px 16px; background: #2196f3; color: white; text-decoration: none; border-radius: 4px; }
        </style>
    </head>
    <body>
        <h1>💰 Claude Token Count テスト</h1>
        
        <div class="form-container">
            <h3>📝 トークン計算</h3>
            <form id="tokenForm">
                <label for="model"><strong>モデル選択:</strong></label><br>
                <select id="model" name="model">
                    <option value="claude-3-haiku-20240307">Claude 3 Haiku (安い)</option>
                    <option value="claude-3-sonnet-20240229">Claude 3 Sonnet</option>
                    <option value="claude-3-opus-20240229">Claude 3 Opus (高い)</option>
                    <option value="claude-3-5-sonnet-20241022">Claude 3.5 Sonnet</option>
                </select><br><br>
                
                <label for="prompt"><strong>プロンプト:</strong></label><br>
                <textarea id="prompt" placeholder="ここにプロンプトを入力してください...">
以下の2つのCSVデータセットのフィールド対応を分析してください。

【A社データ】
フィールド: カード名, レアリティ, シリーズ, 価格
サンプル:
行1: カード名='ファイヤードラゴン' レアリティ='レア' シリーズ='第1弾' 価格='150'

【B社データ】  
フィールド: 名称, 希少度, セット, 値段
サンプル:
行1: 名称='ファイヤードラゴン' 希少度='R' セット='SET001' 値段='150'

結果をJSON形式で出力してください：
{
  "mappings": [
    {
      "field_type": "カード名",
      "company_a_field": "カード名",
      "company_b_field": "名称", 
      "confidence": 0.95,
      "reasoning": "判断理由"
    }
  ]
}
                </textarea><br><br>
                
                <button type="button" onclick="countTokensAPI()">🎯 正確なトークン数 (API)</button>
                <button type="button" onclick="estimateTokens()">⚡ 高速推定</button>
            </form>
        </div>
        
        <div id="result" class="result-container" style="display: none;"></div>
        
        <div style="margin: 30px 0;">
            <h3>📊 トークン計算について</h3>
            <ul>
                <li><strong>正確なトークン数:</strong> Claude APIを使用した正確な計算（API呼び出しあり）</li>
                <li><strong>高速推定:</strong> 複数手法による推定（APIなし、即座に結果表示）</li>
                <li><strong>コスト:</strong> 2024年時点の概算価格（実際の料金は公式サイトで確認）</li>
            </ul>
        </div>
        
        <div class="nav">
            <a href="/">🏠 トップページ</a>
            <a href="/test/claude">🔗 API接続テスト</a>
            <a href="/test/models">🤖 モデル一覧</a>
        </div>
        
        <script>
        async function countTokensAPI() {
            const prompt = document.getElementById('prompt').value;
            const model = document.getElementById('model').value;
            
            if (!prompt.trim()) {
                alert('プロンプトを入力してください');
                return;
            }
            
            document.getElementById('result').style.display = 'block';
            document.getElementById('result').innerHTML = '<p>⏳ 計算中...</p>';
            
            try {
                const response = await fetch('/api/tokens/count', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt, model: model })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const cost = data.data.estimated_cost;
                    document.getElementById('result').innerHTML = `
                        <h3>✅ 正確なトークン計算結果</h3>
                        <table>
                        <tr><th>項目</th><th>値</th></tr>
                        <tr><td>モデル</td><td>${data.data.model}</td></tr>
                        <tr><td>プロンプト文字数</td><td>${data.data.prompt_length.toLocaleString()}</td></tr>
                        <tr><td>入力トークン数</td><td>${data.data.input_tokens.toLocaleString()}</td></tr>
                        <tr><td>推定コスト (USD)</td><td>${cost.total_cost_usd.toFixed(6)}</td></tr>
                        <tr><td>推定コスト (円)</td><td>約${cost.total_cost_jpy.toFixed(2)}円</td></tr>
                        <tr><td>計算方法</td><td>${data.data.method}</td></tr>
                        </table>
                    `;
                } else {
                    document.getElementById('result').innerHTML = `
                        <h3>❌ エラー</h3>
                        <p>${data.error}</p>
                    `;
                }
            } catch (error) {
                document.getElementById('result').innerHTML = `
                    <h3>❌ エラー</h3>
                    <p>リクエストに失敗しました: ${error.message}</p>
                `;
            }
        }
        
        async function estimateTokens() {
            const prompt = document.getElementById('prompt').value;
            const model = document.getElementById('model').value;
            
            if (!prompt.trim()) {
                alert('プロンプトを入力してください');
                return;
            }
            
            document.getElementById('result').style.display = 'block';
            document.getElementById('result').innerHTML = '<p>⚡ 推定中...</p>';
            
            try {
                const response = await fetch('/api/tokens/estimate', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ prompt: prompt, model: model })
                });
                
                const data = await response.json();
                
                if (data.success) {
                    const estimates = data.data.estimation_methods;
                    const cost = data.data.estimated_cost;
                    
                    document.getElementById('result').innerHTML = `
                        <h3>⚡ 高速推定結果</h3>
                        <table>
                        <tr><th>項目</th><th>値</th></tr>
                        <tr><td>推定トークン数</td><td>${data.data.estimated_tokens.toLocaleString()}</td></tr>
                        <tr><td>推定コスト (USD)</td><td>${cost.total_cost_usd.toFixed(6)}</td></tr>
                        <tr><td>推定コスト (円)</td><td>約${cost.total_cost_jpy.toFixed(2)}円</td></tr>
                        </table>
                        
                        <h4>推定手法別結果</h4>
                        <table>
                        <tr><th>手法</th><th>推定トークン数</th></tr>
                        <tr><td>簡易推定 (文字数÷4)</td><td>${estimates.simple}</td></tr>
                        <tr><td>単語ベース推定</td><td>${estimates.word_based}</td></tr>
                        <tr><td>文字種別推定</td><td>${estimates.character_based}</td></tr>
                        </table>
                        
                        <p><em>※ これは推定値です。正確な値は「正確なトークン数」で計算してください。</em></p>
                    `;
                } else {
                    document.getElementById('result').innerHTML = `
                        <h3>❌ エラー</h3>
                        <p>${data.error}</p>
                    `;
                }
            } catch (error) {
                document.getElementById('result').innerHTML = `
                    <h3>❌ エラー</h3>
                    <p>リクエストに失敗しました: ${error.message}</p>
                `;
            }
        }
        </script>
    </body>
    </html>
    '''


def _call_claude_api(api_key, prompt, model='claude-3-haiku-20240307'):
    """Claude APIを呼び出し"""
    try:
        url = "https://api.anthropic.com/v1/messages"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": model,
            "max_tokens": 1000,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=60)
        response.raise_for_status()
        
        return response.json()
        
    except Exception as e:
        current_app.logger.error(f"Claude API call failed: {e}")
        return None


def _fetch_available_models(api_key):
    """利用可能なモデル一覧を取得"""
    try:
        url = "https://api.anthropic.com/v1/models"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            data = response.json()
            models = []
            
            for model_info in data.get('data', []):
                model_id = model_info.get('id')
                display_name = model_info.get('display_name', model_id)
                
                models.append({
                    'id': model_id,
                    'name': _enhance_model_display_name(model_id, display_name),
                    'display_name': display_name,
                    'created_at': model_info.get('created_at'),
                    'available': True,
                    'source': 'official_api',
                    'characteristics': _get_model_characteristics(model_id)
                })
            
            return models
        else:
            return _get_fallback_models()
            
    except Exception as e:
        current_app.logger.error(f"Error fetching models: {e}")
        return _get_fallback_models()


def _get_model_info(api_key, model_id):
    """特定モデルの情報を取得"""
    models = _fetch_available_models(api_key)
    for model in models:
        if model['id'] == model_id:
            return model
    return None


def _test_model_functionality(api_key, model_id, prompt):
    """モデルの機能テスト"""
    import time
    
    try:
        start_time = time.time()
        response = _call_claude_api(api_key, prompt, model_id)
        response_time = (time.time() - start_time) * 1000
        
        if response:
            return {
                'success': True,
                'response': response.get('content', [{}])[0].get('text', 'No response'),
                'response_time_ms': round(response_time, 2)
            }
        else:
            return {
                'success': False,
                'error': 'No response from API'
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def _get_fallback_models():
    """フォールバックモデル一覧"""
    return [
        {
            'id': 'claude-3-haiku-20240307',
            'name': 'Claude 3 Haiku (高速・低コスト)',
            'display_name': 'Claude 3 Haiku',
            'available': True,
            'source': 'fallback',
            'characteristics': _get_model_characteristics('claude-3-haiku-20240307')
        },
        {
            'id': 'claude-3-sonnet-20240229',
            'name': 'Claude 3 Sonnet (バランス)',
            'display_name': 'Claude 3 Sonnet',
            'available': True,
            'source': 'fallback',
            'characteristics': _get_model_characteristics('claude-3-sonnet-20240229')
        },
        {
            'id': 'claude-3-opus-20240229',
            'name': 'Claude 3 Opus (高精度・高コスト)',
            'display_name': 'Claude 3 Opus',
            'available': True,
            'source': 'fallback',
            'characteristics': _get_model_characteristics('claude-3-opus-20240229')
        },
        {
            'id': 'claude-3-5-sonnet-20241022',
            'name': 'Claude 3.5 Sonnet (最新・推奨)',
            'display_name': 'Claude 3.5 Sonnet',
            'available': True,
            'source': 'fallback',
            'characteristics': _get_model_characteristics('claude-3-5-sonnet-20241022')
        }
    ]


def _enhance_model_display_name(model_id, original_display_name):
    """モデル表示名を強化"""
    model_enhancements = {
        'claude-3-haiku': '(高速・低コスト)',
        'claude-3-sonnet': '(バランス)',
        'claude-3-opus': '(高精度・高コスト)',
        'claude-3-5-sonnet': '(最新・推奨)',
        'claude-3-5-haiku': '(最新・高速)',
        'claude-sonnet-4': '(最新・高性能)'
    }
    
    for key, enhancement in model_enhancements.items():
        if key in model_id.lower():
            return f"{original_display_name} {enhancement}"
    
    return original_display_name


def _get_model_characteristics(model_id):
    """モデル特性情報を取得"""
    characteristics = {
        'performance': 'unknown',
        'cost': 'unknown',
        'speed': 'unknown',
        'use_cases': [],
        'max_tokens': 1000
    }
    
    if 'haiku' in model_id.lower():
        characteristics.update({
            'performance': 'good',
            'cost': 'low',
            'speed': 'fast',
            'use_cases': ['簡単なタスク', '高速処理', 'コスト重視'],
            'max_tokens': 1000
        })
    elif 'sonnet' in model_id.lower():
        if '3.5' in model_id or '4' in model_id:
            characteristics.update({
                'performance': 'excellent',
                'cost': 'medium',
                'speed': 'medium',
                'use_cases': ['一般的なタスク', 'バランス重視', '推奨'],
                'max_tokens': 2000
            })
        else:
            characteristics.update({
                'performance': 'very_good',
                'cost': 'medium',
                'speed': 'medium',
                'use_cases': ['一般的なタスク', 'バランス重視'],
                'max_tokens': 2000
            })
    elif 'opus' in model_id.lower():
        characteristics.update({
            'performance': 'excellent',
            'cost': 'high',
            'speed': 'slow',
            'use_cases': ['複雑なタスク', '高精度重視', '研究・分析'],
            'max_tokens': 3000
        })
    
    return characteristics


def _render_error_page(title, message, details=None):
    """エラーページの生成"""
    details_html = f"<details><summary>詳細情報</summary><pre>{details}</pre></details>" if details else ""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title} - Mercury Mapping Engine</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .error {{ color: #d32f2f; background: #ffe6e6; padding: 20px; border-radius: 8px; border-left: 5px solid #f44336; }}
            .nav {{ margin: 20px 0; }}
            .nav a {{ padding: 8px 16px; background: #2196f3; color: white; text-decoration: none; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="error">
            <h1>{title}</h1>
            <p>{message}</p>
            {details_html}
        </div>
        <div class="nav">
            <a href="/">← トップページに戻る</a>
        </div>
    </body>
    </html>
    """