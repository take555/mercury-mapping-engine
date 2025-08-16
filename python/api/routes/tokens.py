"""
Mercury Mapping Engine - Tokens API Routes
トークン計算APIルート
"""
from flask import Blueprint, request, current_app
import os
import requests
from api.routes import create_success_response, create_error_response

# ブループリント作成
tokens_bp = Blueprint('tokens', __name__)


@tokens_bp.route('/tokens/count', methods=['POST'])
def count_tokens():
    """プロンプトのトークン数をカウント"""
    try:
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        if not claude_api_key or claude_api_key == 'your-api-key-here':
            return create_error_response('Claude API key not configured', 400)
        
        data = request.get_json()
        if not data:
            return create_error_response('Request body is required', 400)
        
        prompt = data.get('prompt', '')
        model = data.get('model', 'claude-3-haiku-20240307')
        
        if not prompt:
            return create_error_response('Prompt is required', 400)
        
        # Claude APIでトークン数を計算
        token_count = _count_tokens_with_api(claude_api_key, prompt, model)
        
        if token_count is not None:
            # コスト見積もり
            estimated_cost = _estimate_cost(model, token_count)
            
            return create_success_response({
                'model': model,
                'input_tokens': token_count,
                'estimated_cost': estimated_cost,
                'prompt_length': len(prompt),
                'method': 'claude_api'
            })
        else:
            # フォールバック: 簡易計算
            estimated_tokens = _estimate_tokens_simple(prompt)
            estimated_cost = _estimate_cost(model, estimated_tokens)
            
            return create_success_response({
                'model': model,
                'input_tokens': estimated_tokens,
                'estimated_cost': estimated_cost,
                'prompt_length': len(prompt),
                'method': 'estimation',
                'warning': 'API token count failed, using estimation'
            })
            
    except Exception as e:
        current_app.logger.error(f"Token count error: {e}")
        return create_error_response(f"Token count failed: {str(e)}", 500)


@tokens_bp.route('/tokens/estimate', methods=['POST'])
def estimate_tokens():
    """簡易トークン数推定（APIを使わない）"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response('Request body is required', 400)
        
        prompt = data.get('prompt', '')
        model = data.get('model', 'claude-3-haiku-20240307')
        
        if not prompt:
            return create_error_response('Prompt is required', 400)
        
        # 複数の推定方法
        estimates = {
            'simple': _estimate_tokens_simple(prompt),
            'word_based': _estimate_tokens_word_based(prompt),
            'character_based': _estimate_tokens_character_based(prompt)
        }
        
        # 平均値を使用
        average_estimate = sum(estimates.values()) // len(estimates)
        
        # コスト見積もり
        estimated_cost = _estimate_cost(model, average_estimate)
        
        return create_success_response({
            'model': model,
            'estimated_tokens': average_estimate,
            'estimation_methods': estimates,
            'estimated_cost': estimated_cost,
            'prompt_length': len(prompt),
            'method': 'estimation_only',
            'note': 'This is an estimation. Use /tokens/count for accurate count.'
        })
        
    except Exception as e:
        current_app.logger.error(f"Token estimation error: {e}")
        return create_error_response(f"Token estimation failed: {str(e)}", 500)


@tokens_bp.route('/tokens/cost', methods=['POST'])
def calculate_cost():
    """トークン数からコストを計算"""
    try:
        data = request.get_json()
        if not data:
            return create_error_response('Request body is required', 400)
        
        input_tokens = data.get('input_tokens', 0)
        output_tokens = data.get('output_tokens', 0)
        model = data.get('model', 'claude-3-haiku-20240307')
        
        if input_tokens < 0 or output_tokens < 0:
            return create_error_response('Token counts must be non-negative', 400)
        
        # コスト計算
        cost_breakdown = _estimate_cost(model, input_tokens, output_tokens)
        
        return create_success_response({
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'cost_breakdown': cost_breakdown,
            'total_cost_usd': cost_breakdown['total_cost_usd'],
            'total_cost_jpy': cost_breakdown['total_cost_jpy']
        })
        
    except Exception as e:
        current_app.logger.error(f"Cost calculation error: {e}")
        return create_error_response(f"Cost calculation failed: {str(e)}", 500)


def _count_tokens_with_api(api_key, prompt, model):
    """Claude APIを使用してトークン数をカウント"""
    try:
        url = "https://api.anthropic.com/v1/messages/count_tokens"
        
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": model,
            "messages": [
                {
                    "role": "user", 
                    "content": prompt
                }
            ]
        }
        
        response = requests.post(url, headers=headers, json=data, timeout=30)
        
        if response.status_code == 200:
            result = response.json()
            return result.get('input_tokens', 0)
        else:
            current_app.logger.warning(f"Token count API failed: {response.status_code}")
            return None
            
    except Exception as e:
        current_app.logger.error(f"Token count API error: {e}")
        return None


def _estimate_tokens_simple(text):
    """簡易トークン数推定（文字数÷4）"""
    return max(1, len(text) // 4)


def _estimate_tokens_word_based(text):
    """単語ベースのトークン数推定"""
    import re
    
    # 英語の単語数
    english_words = len(re.findall(r'\b[a-zA-Z]+\b', text))
    
    # 日本語の文字数（ひらがな、カタカナ、漢字）
    japanese_chars = len(re.findall(r'[ひらがなカタカナ一-龯]', text))
    
    # 推定：英語1単語≈1トークン、日本語2文字≈1トークン
    estimated_tokens = english_words + (japanese_chars // 2)
    
    return max(1, estimated_tokens)


def _estimate_tokens_character_based(text):
    """文字種別ベースのトークン数推定"""
    import re
    
    # 文字種別カウント
    ascii_chars = len(re.findall(r'[a-zA-Z0-9]', text))
    japanese_chars = len(re.findall(r'[ひらがなカタカナ一-龯]', text))
    symbols = len(re.findall(r'[^\w\s]', text))
    spaces = text.count(' ')
    
    # 推定係数
    estimated = (ascii_chars * 0.3) + (japanese_chars * 0.7) + (symbols * 0.5) + (spaces * 0.1)
    
    return max(1, int(estimated))


def _estimate_cost(model, input_tokens, output_tokens=0):
    """モデル別コスト見積もり"""
    # 2024年時点の概算価格（実際の価格は公式サイトで確認）
    pricing = {
        'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25},  # per 1M tokens
        'claude-3-sonnet-20240229': {'input': 3.0, 'output': 15.0},
        'claude-3-opus-20240229': {'input': 15.0, 'output': 75.0},
        'claude-3-5-sonnet-20241022': {'input': 3.0, 'output': 15.0},
        'claude-3-5-haiku-20241022': {'input': 1.0, 'output': 5.0}
    }
    
    # デフォルト価格
    default_price = {'input': 3.0, 'output': 15.0}
    
    # モデル価格を取得
    model_pricing = pricing.get(model, default_price)
    
    # コスト計算（USD）
    input_cost = (input_tokens / 1_000_000) * model_pricing['input']
    output_cost = (output_tokens / 1_000_000) * model_pricing['output']
    total_cost = input_cost + output_cost
    
    return {
        'input_cost_usd': round(input_cost, 6),
        'output_cost_usd': round(output_cost, 6),
        'total_cost_usd': round(total_cost, 6),
        'input_cost_jpy': round(input_cost * 150, 3),  # 概算レート
        'output_cost_jpy': round(output_cost * 150, 3),
        'total_cost_jpy': round(total_cost * 150, 3),
        'exchange_rate': 150,
        'pricing_per_1m_tokens': model_pricing
    }