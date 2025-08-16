"""
Mercury Mapping Engine - Claude API Client
Claude API専用クライアント
"""
import requests
import json
import time
import re
from typing import Dict, List, Optional, Any, Tuple
from utils.logger import analysis_logger


class ClaudeClient:
    """Claude API専用クライアント"""
    
    def __init__(self, api_key: str, config: Optional[Dict] = None):
        self.api_key = api_key
        self.config = config or {}
        self.base_url = self.config.get('base_url', 'https://api.anthropic.com/v1')
        self.api_version = self.config.get('api_version', '2023-06-01')
        self.timeout = self.config.get('timeout', 60)
        self.default_model = self.config.get('default_model', 'claude-3-haiku-20240307')
        
        # API統計
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost_usd': 0.0
        }
        
        # モデル別トークン数制限
        self.token_limits = {
            'claude-3-haiku-20240307': 200000,
            'claude-3-sonnet-20240229': 200000,
            'claude-3-opus-20240229': 200000,
            'claude-3-5-sonnet-20240620': 200000
        }
    
    def call_api(self, prompt: str, model: Optional[str] = None, 
                 max_tokens: Optional[int] = None, **kwargs) -> Dict[str, Any]:
        """Claude APIを呼び出し"""
        model = model or self.default_model
        max_tokens = max_tokens or self._get_default_max_tokens(model)
        
        url = f"{self.base_url}/messages"
        headers = {
            "Content-Type": "application/json",
            "x-api-key": self.api_key,
            "anthropic-version": self.api_version
        }
        
        data = {
            "model": model,
            "max_tokens": max_tokens,
            "messages": [{"role": "user", "content": prompt}],
            **kwargs
        }
        
        start_time = time.time()
        self.stats['total_requests'] += 1
        
        try:
            analysis_logger.logger.debug(f"Claude API call: model={model}, max_tokens={max_tokens}")
            
            response = requests.post(url, headers=headers, json=data, timeout=self.timeout)
            response.raise_for_status()
            
            result = response.json()
            response_time = time.time() - start_time
            
            # 統計更新
            self.stats['successful_requests'] += 1
            usage = result.get('usage', {})
            input_tokens = usage.get('input_tokens', 0)
            output_tokens = usage.get('output_tokens', 0)
            
            self.stats['total_input_tokens'] += input_tokens
            self.stats['total_output_tokens'] += output_tokens
            
            # コスト計算
            cost = self.calculate_cost(model, input_tokens, output_tokens)
            self.stats['total_cost_usd'] += cost['total_cost_usd']
            
            analysis_logger.log_claude_api_call(model, input_tokens, cost['total_cost_usd'])
            
            return {
                'success': True,
                'response': result,
                'content': self._extract_content(result),
                'usage': usage,
                'cost': cost,
                'response_time_ms': round(response_time * 1000, 2),
                'model': model
            }
            
        except requests.exceptions.RequestException as e:
            self.stats['failed_requests'] += 1
            analysis_logger.log_error('claude_api_call', str(e))
            
            return {
                'success': False,
                'error': str(e),
                'error_type': 'request_error',
                'model': model
            }
        
        except Exception as e:
            self.stats['failed_requests'] += 1
            analysis_logger.log_error('claude_api_call', str(e))
            
            return {
                'success': False,
                'error': str(e),
                'error_type': 'unknown_error',
                'model': model
            }
    
    def count_tokens(self, prompt: str, model: Optional[str] = None) -> Dict[str, Any]:
        """プロンプトのトークン数を推定"""
        model = model or self.default_model
        
        try:
            # 簡易的なトークン数推定（4文字 = 1トークン）
            estimated_tokens = len(prompt) // 4
            
            # より精密な推定のためのヒューリスティック
            # 日本語は文字数 / 2, 英語は単語数 * 1.3
            japanese_chars = len(re.findall(r'[あ-ん|ア-ン|一-龯]', prompt))
            english_words = len(re.findall(r'[a-zA-Z]+', prompt))
            
            heuristic_tokens = int(japanese_chars / 2 + english_words * 1.3)
            
            # より保守的な推定値を採用
            estimated_tokens = max(estimated_tokens, heuristic_tokens)
            
            return {
                'success': True,
                'estimated_tokens': estimated_tokens,
                'model': model,
                'character_count': len(prompt),
                'japanese_chars': japanese_chars,
                'english_words': english_words,
                'token_limit': self.token_limits.get(model, 200000),
                'within_limit': estimated_tokens <= self.token_limits.get(model, 200000)
            }
            
        except Exception as e:
            analysis_logger.log_error('token_count', str(e))
            return {
                'success': False,
                'error': str(e),
                'model': model
            }
    
    def calculate_cost(self, model: str, input_tokens: int, output_tokens: int = 0) -> Dict[str, Any]:
        """API使用コストを計算"""
        
        # 2024年8月時点の料金（USD per 1M tokens）
        pricing = {
            'claude-3-haiku-20240307': {'input': 0.25, 'output': 1.25},
            'claude-3-sonnet-20240229': {'input': 3.0, 'output': 15.0},
            'claude-3-opus-20240229': {'input': 15.0, 'output': 75.0},
            'claude-3-5-sonnet-20240620': {'input': 3.0, 'output': 15.0}
        }
        
        if model not in pricing:
            # デフォルトはHaikuの料金を使用
            model_pricing = pricing['claude-3-haiku-20240307']
        else:
            model_pricing = pricing[model]
        
        input_cost = (input_tokens / 1_000_000) * model_pricing['input']
        output_cost = (output_tokens / 1_000_000) * model_pricing['output']
        total_cost = input_cost + output_cost
        
        return {
            'model': model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'input_cost_usd': round(input_cost, 6),
            'output_cost_usd': round(output_cost, 6),
            'total_cost_usd': round(total_cost, 6),
            'cost_breakdown': {
                'input_rate_per_1m': model_pricing['input'],
                'output_rate_per_1m': model_pricing['output']
            }
        }
    
    def estimate_cost(self, model: str, prompt: str, estimated_output_tokens: int = 1000) -> Dict[str, Any]:
        """プロンプトから推定コストを計算"""
        token_info = self.count_tokens(prompt, model)
        
        if not token_info['success']:
            return token_info
        
        estimated_input_tokens = token_info['estimated_tokens']
        return self.calculate_cost(model, estimated_input_tokens, estimated_output_tokens)
    
    def test_connection(self, model: Optional[str] = None) -> Dict[str, Any]:
        """API接続テスト"""
        model = model or self.default_model
        test_prompt = "Hello! Please respond with 'Connection test successful.'"
        
        result = self.call_api(test_prompt, model, max_tokens=50)
        
        if result['success']:
            content = result.get('content', '')
            success = 'successful' in content.lower()
            
            return {
                'success': success,
                'model': model,
                'response': content,
                'usage': result.get('usage', {}),
                'cost': result.get('cost', {}),
                'response_time_ms': result.get('response_time_ms', 0)
            }
        else:
            return {
                'success': False,
                'model': model,
                'error': result.get('error'),
                'error_type': result.get('error_type')
            }
    
    def get_stats(self) -> Dict[str, Any]:
        """API使用統計を取得"""
        success_rate = 0
        if self.stats['total_requests'] > 0:
            success_rate = self.stats['successful_requests'] / self.stats['total_requests']
        
        return {
            **self.stats,
            'success_rate': round(success_rate, 3),
            'avg_cost_per_request': (
                round(self.stats['total_cost_usd'] / max(self.stats['successful_requests'], 1), 6)
            )
        }
    
    def reset_stats(self):
        """統計をリセット"""
        self.stats = {
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'total_input_tokens': 0,
            'total_output_tokens': 0,
            'total_cost_usd': 0.0
        }
    
    def _get_default_max_tokens(self, model: str) -> int:
        """モデル別のデフォルト最大トークン数"""
        defaults = {
            'claude-3-haiku-20240307': 4000,
            'claude-3-sonnet-20240229': 4000,
            'claude-3-opus-20240229': 4000,
            'claude-3-5-sonnet-20240620': 4000
        }
        return defaults.get(model, 4000)
    
    def _extract_content(self, response: Dict) -> str:
        """APIレスポンスからコンテンツを抽出"""
        try:
            content = response.get('content', [])
            if isinstance(content, list) and len(content) > 0:
                return content[0].get('text', '')
            return str(content)
        except Exception as e:
            analysis_logger.log_error('content_extraction', str(e))
            return ''
    
    def validate_model(self, model: str) -> bool:
        """モデル名の有効性を検証"""
        valid_models = [
            'claude-3-haiku-20240307',
            'claude-3-sonnet-20240229', 
            'claude-3-opus-20240229',
            'claude-3-5-sonnet-20240620'
        ]
        return model in valid_models
    
    def get_recommended_model(self, task_type: str = 'general') -> str:
        """タスクタイプに基づいて推奨モデルを取得"""
        recommendations = {
            'fast': 'claude-3-haiku-20240307',        # 高速・低コスト
            'balanced': 'claude-3-sonnet-20240229',   # バランス
            'advanced': 'claude-3-5-sonnet-20240620', # 最新・高性能
            'complex': 'claude-3-opus-20240229',      # 最高性能
            'general': 'claude-3-haiku-20240307'      # デフォルト
        }
        return recommendations.get(task_type, self.default_model)
