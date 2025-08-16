"""
Mercury Mapping Engine - Models API Routes
Claudeモデル管理APIルート
"""
from flask import Blueprint, current_app
import os
import requests
from .helpers import create_success_response, create_error_response

# ブループリント作成
models_bp = Blueprint('models', __name__)


@models_bp.route('/models')
def get_models():
    """利用可能なClaudeモデル一覧を取得"""
    try:
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        if not claude_api_key or claude_api_key == 'your-api-key-here':
            return create_error_response('Claude API key not configured', 400, {
                'models': _get_fallback_models()
            })
        
        # 公式APIからモデル一覧を取得
        models = _fetch_models_from_api(claude_api_key)
        
        if not models:
            models = _get_fallback_models()
        
        return create_success_response({
            'models': models,
            'total': len(models),
            'available_count': len([m for m in models if m.get('available', False)]),
            'source': models[0].get('source', 'fallback') if models else 'fallback'
        })
        
    except Exception as e:
        current_app.logger.error(f"Models API error: {e}")
        return create_error_response(f"Failed to fetch models: {str(e)}", 500, {
            'fallback_models': _get_fallback_models()
        })


@models_bp.route('/models/<model_id>')
def get_model_info(model_id):
    """特定モデルの詳細情報を取得"""
    try:
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        if not claude_api_key or claude_api_key == 'your-api-key-here':
            return create_error_response('Claude API key not configured', 400)
        
        # 公式APIからモデル詳細を取得
        model_info = _fetch_model_info_from_api(claude_api_key, model_id)
        
        if not model_info:
            # フォールバックモデル情報
            model_info = _get_fallback_model_info(model_id)
            
        if not model_info:
            return create_error_response(f'Model {model_id} not found', 404)
        
        return create_success_response(model_info)
        
    except Exception as e:
        current_app.logger.error(f"Model info API error: {e}")
        return create_error_response(f"Failed to fetch model info: {str(e)}", 500)


@models_bp.route('/models/<model_id>/test', methods=['POST'])
def test_model(model_id):
    """特定モデルの動作テスト"""
    try:
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        if not claude_api_key or claude_api_key == 'your-api-key-here':
            return create_error_response('Claude API key not configured', 400)
        
        # 簡単なテストプロンプト
        test_prompt = "以下の2つのフィールドは同じ意味ですか？\nA: 'カード名'\nB: 'card_name'\n\nJSON形式で回答: {\"same_meaning\": true/false, \"confidence\": 0.0-1.0}"
        
        # APIテスト実行
        test_result = _test_model_api(claude_api_key, model_id, test_prompt)
        
        return create_success_response({
            'model_id': model_id,
            'test_status': 'success' if test_result['success'] else 'failed',
            'response_preview': test_result.get('response', ''),
            'response_time_ms': test_result.get('response_time_ms'),
            'error': test_result.get('error')
        })
        
    except Exception as e:
        current_app.logger.error(f"Model test error: {e}")
        return create_error_response(f"Model test failed: {str(e)}", 500)


def _fetch_models_from_api(api_key):
    """公式APIからモデル一覧を取得"""
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
                
                enhanced_name = _enhance_model_display_name(model_id, display_name)
                
                models.append({
                    'id': model_id,
                    'name': enhanced_name,
                    'display_name': display_name,
                    'created_at': model_info.get('created_at'),
                    'available': True,
                    'source': 'official_api',
                    'characteristics': _get_model_characteristics(model_id)
                })
            
            return models
        else:
            current_app.logger.warning(f"Models API failed: {response.status_code}")
            return None
            
    except Exception as e:
        current_app.logger.error(f"Error fetching models: {e}")
        return None


def _fetch_model_info_from_api(api_key, model_id):
    """公式APIから特定モデル情報を取得"""
    try:
        url = f"https://api.anthropic.com/v1/models/{model_id}"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        
        if response.status_code == 200:
            model_info = response.json()
            
            return {
                'id': model_info.get('id'),
                'display_name': model_info.get('display_name'),
                'created_at': model_info.get('created_at'),
                'type': model_info.get('type'),
                'enhanced_name': _enhance_model_display_name(
                    model_info.get('id'), 
                    model_info.get('display_name')
                ),
                'characteristics': _get_model_characteristics(model_info.get('id')),
                'source': 'official_api'
            }
        else:
            return None
            
    except Exception as e:
        current_app.logger.error(f"Error fetching model info: {e}")
        return None


def _test_model_api(api_key, model_id, prompt):
    """モデルAPIテスト実行"""
    import time
    
    try:
        start_time = time.time()
        
        url = "https://api.anthropic.com/v1/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": model_id,
            "max_tokens": 100,
            "messages": [{"role": "user", "content": prompt}]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response_time = (time.time() - start_time) * 1000
        
        if response.status_code == 200:
            result = response.json()
            response_text = result.get('content', [{}])[0].get('text', 'No response')
            
            return {
                'success': True,
                'response': response_text[:200],  # 最初の200文字のみ
                'response_time_ms': round(response_time, 2)
            }
        else:
            return {
                'success': False,
                'error': f"API error: {response.status_code}",
                'response_time_ms': round(response_time, 2)
            }
            
    except Exception as e:
        return {
            'success': False,
            'error': str(e)
        }


def _get_fallback_models():
    """フォールバック用モデルリスト"""
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


def _get_fallback_model_info(model_id):
    """フォールバック用モデル詳細情報"""
    fallback_models = _get_fallback_models()
    for model in fallback_models:
        if model['id'] == model_id:
            return model
    return None


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
