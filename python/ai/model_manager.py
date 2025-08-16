"""
Mercury Mapping Engine - Model Manager
Claude AIモデルの管理とメタデータ提供
"""
from typing import Dict, List, Optional, Any
from datetime import datetime
from utils.logger import analysis_logger


class ModelManager:
    """Claude AIモデル管理クラス"""
    
    def __init__(self):
        """モデル情報とメタデータを初期化"""
        self.models = {
            'claude-3-haiku-20240307': {
                'name': 'Claude 3 Haiku',
                'family': 'claude-3',
                'version': '20240307',
                'tier': 'fast',
                'context_window': 200000,
                'max_output_tokens': 4096,
                'pricing': {
                    'input_per_1m': 0.25,
                    'output_per_1m': 1.25,
                    'currency': 'USD'
                },
                'capabilities': {
                    'text_analysis': True,
                    'code_generation': True,
                    'reasoning': 'basic',
                    'multilingual': True,
                    'vision': False
                },
                'recommended_for': ['quick_analysis', 'simple_mapping', 'text_processing'],
                'description': '高速・低コストのモデル。基本的な分析タスクに最適',
                'release_date': '2024-03-07',
                'status': 'available'
            },
            
            'claude-3-sonnet-20240229': {
                'name': 'Claude 3 Sonnet', 
                'family': 'claude-3',
                'version': '20240229',
                'tier': 'balanced',
                'context_window': 200000,
                'max_output_tokens': 4096,
                'pricing': {
                    'input_per_1m': 3.0,
                    'output_per_1m': 15.0,
                    'currency': 'USD'
                },
                'capabilities': {
                    'text_analysis': True,
                    'code_generation': True,
                    'reasoning': 'advanced',
                    'multilingual': True,
                    'vision': True
                },
                'recommended_for': ['balanced_analysis', 'complex_mapping', 'field_analysis'],
                'description': 'バランスの良いモデル。多くのタスクに適応可能',
                'release_date': '2024-02-29',
                'status': 'available'
            },
            
            'claude-3-opus-20240229': {
                'name': 'Claude 3 Opus',
                'family': 'claude-3', 
                'version': '20240229',
                'tier': 'premium',
                'context_window': 200000,
                'max_output_tokens': 4096,
                'pricing': {
                    'input_per_1m': 15.0,
                    'output_per_1m': 75.0,
                    'currency': 'USD'
                },
                'capabilities': {
                    'text_analysis': True,
                    'code_generation': True,
                    'reasoning': 'expert',
                    'multilingual': True,
                    'vision': True
                },
                'recommended_for': ['complex_analysis', 'advanced_mapping', 'expert_reasoning'],
                'description': '最高性能モデル。複雑で高精度な分析が必要な場合',
                'release_date': '2024-02-29',
                'status': 'available'
            },
            
            'claude-3-5-sonnet-20240620': {
                'name': 'Claude 3.5 Sonnet',
                'family': 'claude-3-5',
                'version': '20240620', 
                'tier': 'advanced',
                'context_window': 200000,
                'max_output_tokens': 4096,
                'pricing': {
                    'input_per_1m': 3.0,
                    'output_per_1m': 15.0,
                    'currency': 'USD'
                },
                'capabilities': {
                    'text_analysis': True,
                    'code_generation': True,
                    'reasoning': 'advanced_plus',
                    'multilingual': True,
                    'vision': True
                },
                'recommended_for': ['latest_analysis', 'improved_mapping', 'code_analysis'],
                'description': '最新の改良モデル。Sonnetの性能向上版',
                'release_date': '2024-06-20',
                'status': 'available'
            }
        }
        
        # タスク別推奨モデル
        self.task_recommendations = {
            'csv_analysis': {
                'fast': 'claude-3-haiku-20240307',
                'balanced': 'claude-3-sonnet-20240229',
                'best': 'claude-3-5-sonnet-20240620'
            },
            'field_mapping': {
                'fast': 'claude-3-haiku-20240307', 
                'balanced': 'claude-3-5-sonnet-20240620',
                'best': 'claude-3-opus-20240229'
            },
            'card_matching': {
                'fast': 'claude-3-haiku-20240307',
                'balanced': 'claude-3-sonnet-20240229', 
                'best': 'claude-3-5-sonnet-20240620'
            },
            'data_validation': {
                'fast': 'claude-3-haiku-20240307',
                'balanced': 'claude-3-sonnet-20240229',
                'best': 'claude-3-opus-20240229'  
            }
        }
    
    def get_available_models(self) -> List[Dict[str, Any]]:
        """利用可能なモデルの一覧を取得"""
        return [
            {
                'model_id': model_id,
                'name': info['name'],
                'tier': info['tier'],
                'description': info['description'],
                'status': info['status']
            }
            for model_id, info in self.models.items()
            if info['status'] == 'available'
        ]
    
    def get_model_info(self, model_id: str) -> Optional[Dict[str, Any]]:
        """指定モデルの詳細情報を取得"""
        if model_id not in self.models:
            return None
            
        info = self.models[model_id].copy()
        info['model_id'] = model_id
        return info
    
    def get_model_pricing(self, model_id: str) -> Optional[Dict[str, Any]]:
        """モデルの料金情報を取得"""
        model_info = self.get_model_info(model_id)
        return model_info['pricing'] if model_info else None
    
    def get_recommended_model(self, task_type: str, priority: str = 'balanced') -> str:
        """タスクと優先度に基づいて推奨モデルを取得"""
        if task_type in self.task_recommendations:
            recommendations = self.task_recommendations[task_type]
            return recommendations.get(priority, recommendations['balanced'])
        
        # デフォルト推奨
        defaults = {
            'fast': 'claude-3-haiku-20240307',
            'balanced': 'claude-3-sonnet-20240229', 
            'best': 'claude-3-5-sonnet-20240620'
        }
        return defaults.get(priority, 'claude-3-haiku-20240307')
    
    def compare_models(self, model_ids: List[str]) -> Dict[str, Any]:
        """複数モデルの比較情報を生成"""
        comparison = {
            'models': [],
            'comparison_date': datetime.now().isoformat(),
            'metrics': ['pricing', 'performance', 'capabilities']
        }
        
        for model_id in model_ids:
            model_info = self.get_model_info(model_id)
            if model_info:
                comparison['models'].append({
                    'model_id': model_id,
                    'name': model_info['name'],
                    'tier': model_info['tier'],
                    'input_cost': model_info['pricing']['input_per_1m'],
                    'output_cost': model_info['pricing']['output_per_1m'],
                    'reasoning_level': model_info['capabilities']['reasoning'],
                    'context_window': model_info['context_window'],
                    'recommended_for': model_info['recommended_for']
                })
        
        return comparison
    
    def estimate_task_cost(self, task_type: str, input_tokens: int, 
                          output_tokens: int = 1000, priority: str = 'balanced') -> Dict[str, Any]:
        """タスク実行の推定コストを計算"""
        recommended_model = self.get_recommended_model(task_type, priority)
        pricing = self.get_model_pricing(recommended_model)
        
        if not pricing:
            return {'error': 'Model pricing information not found'}
        
        input_cost = (input_tokens / 1_000_000) * pricing['input_per_1m']
        output_cost = (output_tokens / 1_000_000) * pricing['output_per_1m'] 
        total_cost = input_cost + output_cost
        
        return {
            'task_type': task_type,
            'priority': priority,
            'recommended_model': recommended_model,
            'input_tokens': input_tokens,
            'output_tokens': output_tokens,
            'costs': {
                'input_cost_usd': round(input_cost, 6),
                'output_cost_usd': round(output_cost, 6),
                'total_cost_usd': round(total_cost, 6)
            },
            'pricing_rates': pricing
        }
    
    def get_model_by_tier(self, tier: str) -> List[Dict[str, Any]]:
        """Tier別でモデルを取得"""
        return [
            {
                'model_id': model_id,
                'name': info['name'],
                'description': info['description']
            }
            for model_id, info in self.models.items()
            if info['tier'] == tier and info['status'] == 'available'
        ]
    
    def validate_model_id(self, model_id: str) -> bool:
        """モデルIDの有効性を検証"""
        return model_id in self.models and self.models[model_id]['status'] == 'available'
    
    def get_model_capabilities(self, model_id: str) -> Optional[Dict[str, Any]]:
        """モデルの機能・能力情報を取得"""
        model_info = self.get_model_info(model_id)
        return model_info['capabilities'] if model_info else None
    
    def test_model_availability(self, model_id: str, claude_client=None) -> Dict[str, Any]:
        """モデルの利用可能性をテスト"""
        if not self.validate_model_id(model_id):
            return {
                'success': False,
                'model_id': model_id,
                'error': 'Invalid or unavailable model ID',
                'tested_at': datetime.now().isoformat()
            }
        
        result = {
            'success': True,
            'model_id': model_id,
            'model_info': self.get_model_info(model_id),
            'tested_at': datetime.now().isoformat()
        }
        
        # Claude APIクライアントが提供されている場合は実際にテスト
        if claude_client:
            try:
                api_test = claude_client.test_connection(model_id)
                result['api_test'] = api_test
                result['api_available'] = api_test.get('success', False)
            except Exception as e:
                result['api_test'] = {'error': str(e)}
                result['api_available'] = False
                analysis_logger.log_error('model_availability_test', str(e))
        
        return result
    
    def get_cost_efficient_model(self, task_type: str, max_cost_per_1k_tokens: float) -> Optional[str]:
        """コスト制約内で最適なモデルを選択"""
        recommendations = self.task_recommendations.get(task_type, {})
        
        # 各優先度レベルのモデルをコスト順でチェック
        for priority in ['fast', 'balanced', 'best']:
            if priority in recommendations:
                model_id = recommendations[priority]
                pricing = self.get_model_pricing(model_id)
                
                if pricing:
                    # 1000トークンあたりのコスト（入力+出力）を概算
                    est_cost_per_1k = (pricing['input_per_1m'] + pricing['output_per_1m']) / 1000
                    
                    if est_cost_per_1k <= max_cost_per_1k_tokens:
                        return model_id
        
        return None
    
    def get_model_stats_summary(self) -> Dict[str, Any]:
        """モデル統計サマリーを取得"""
        available_models = self.get_available_models()
        
        pricing_range = {
            'min_input_cost': min(info['pricing']['input_per_1m'] for info in self.models.values()),
            'max_input_cost': max(info['pricing']['input_per_1m'] for info in self.models.values()),
            'min_output_cost': min(info['pricing']['output_per_1m'] for info in self.models.values()),
            'max_output_cost': max(info['pricing']['output_per_1m'] for info in self.models.values())
        }
        
        tiers = list(set(info['tier'] for info in self.models.values()))
        families = list(set(info['family'] for info in self.models.values()))
        
        return {
            'total_models': len(available_models),
            'available_tiers': tiers,
            'model_families': families,
            'pricing_range_usd': pricing_range,
            'task_types_supported': list(self.task_recommendations.keys()),
            'last_updated': datetime.now().isoformat()
        }
