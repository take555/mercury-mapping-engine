"""
Mercury Mapping Engine - AI Package
Claude AI機能の統合パッケージ
"""
from typing import Optional, Dict, Any
import os
from .claude_client import ClaudeClient
from .model_manager import ModelManager
from .prompt_builder import PromptBuilder
from utils.logger import analysis_logger


class AIManager:
    """AI機能の統合管理クラス"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        
        # API キーの取得
        api_key = self.config.get('claude_api_key') or os.getenv('CLAUDE_API_KEY')
        if not api_key:
            raise ValueError("Claude API key is required")
        
        # 各コンポーネントの初期化
        self.claude_client = ClaudeClient(api_key, self.config.get('claude_config', {}))
        self.model_manager = ModelManager()
        self.prompt_builder = PromptBuilder(self.config.get('prompt_config', {}))
        
        analysis_logger.logger.info("AI Manager initialized successfully")
    
    def analyze_field_mapping(self, headers_a, headers_b, sample_data_a, sample_data_b,
                            model: Optional[str] = None, context: Optional[Dict] = None) -> Dict[str, Any]:
        """フィールドマッピング分析を実行"""
        try:
            # 推奨モデルの取得
            if not model:
                model = self.model_manager.get_recommended_model('field_mapping', 'balanced')
            
            # プロンプト生成
            prompt = self.prompt_builder.build_field_mapping_prompt(
                headers_a, headers_b, sample_data_a, sample_data_b, context
            )
            
            # API呼び出し
            result = self.claude_client.call_api(prompt, model)
            
            if result['success']:
                return {
                    'success': True,
                    'analysis': result['content'],
                    'model_used': model,
                    'usage': result['usage'],
                    'cost': result['cost']
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'model_used': model
                }
                
        except Exception as e:
            analysis_logger.log_error('ai_field_mapping', str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    def analyze_csv_structure(self, headers, sample_data, total_rows, 
                            model: Optional[str] = None, file_info: Optional[Dict] = None) -> Dict[str, Any]:
        """CSV構造分析を実行"""
        try:
            if not model:
                model = self.model_manager.get_recommended_model('csv_analysis', 'fast')
            
            prompt = self.prompt_builder.build_csv_analysis_prompt(
                headers, sample_data, total_rows, file_info
            )
            
            result = self.claude_client.call_api(prompt, model)
            
            if result['success']:
                return {
                    'success': True,
                    'analysis': result['content'],
                    'model_used': model,
                    'usage': result['usage'],
                    'cost': result['cost']
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'model_used': model
                }
                
        except Exception as e:
            analysis_logger.log_error('ai_csv_analysis', str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    def validate_mapping_results(self, mapping_results, confidence_threshold: float = 0.8,
                               model: Optional[str] = None) -> Dict[str, Any]:
        """マッピング結果の検証を実行"""
        try:
            if not model:
                model = self.model_manager.get_recommended_model('data_validation', 'balanced')
            
            prompt = self.prompt_builder.build_mapping_validation_prompt(
                mapping_results, confidence_threshold
            )
            
            result = self.claude_client.call_api(prompt, model)
            
            if result['success']:
                return {
                    'success': True,
                    'validation': result['content'],
                    'model_used': model,
                    'usage': result['usage'],
                    'cost': result['cost']
                }
            else:
                return {
                    'success': False,
                    'error': result['error'],
                    'model_used': model
                }
                
        except Exception as e:
            analysis_logger.log_error('ai_mapping_validation', str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_model_info(self, model_id: Optional[str] = None) -> Dict[str, Any]:
        """モデル情報を取得"""
        if model_id:
            return self.model_manager.get_model_info(model_id)
        else:
            return {
                'available_models': self.model_manager.get_available_models(),
                'task_recommendations': self.model_manager.task_recommendations
            }
    
    def estimate_analysis_cost(self, task_type: str, data_size: str = 'medium',
                             priority: str = 'balanced') -> Dict[str, Any]:
        """分析コストを推定"""
        # データサイズ別の推定トークン数
        token_estimates = {
            'small': {'input': 1000, 'output': 500},
            'medium': {'input': 5000, 'output': 1500},
            'large': {'input': 15000, 'output': 3000}
        }
        
        estimate = token_estimates.get(data_size, token_estimates['medium'])
        
        return self.model_manager.estimate_task_cost(
            task_type, 
            estimate['input'], 
            estimate['output'], 
            priority
        )
    
    def test_ai_connection(self) -> Dict[str, Any]:
        """AI接続テストを実行"""
        try:
            # 軽量モデルでテスト
            test_model = 'claude-3-haiku-20240307'
            result = self.claude_client.test_connection(test_model)
            
            return {
                'success': result['success'],
                'model_tested': test_model,
                'response_time_ms': result.get('response_time_ms', 0),
                'api_stats': self.claude_client.get_stats(),
                'available_models': self.model_manager.get_available_models()
            }
            
        except Exception as e:
            analysis_logger.log_error('ai_connection_test', str(e))
            return {
                'success': False,
                'error': str(e)
            }
    
    def get_ai_stats(self) -> Dict[str, Any]:
        """AI使用統計を取得"""
        return {
            'claude_api_stats': self.claude_client.get_stats(),
            'model_summary': self.model_manager.get_model_stats_summary(),
            'prompt_config': {
                'max_sample_rows': self.prompt_builder.max_sample_rows,
                'max_field_count': self.prompt_builder.max_field_count
            }
        }


# パッケージレベルの便利関数
def create_ai_manager(config: Optional[Dict] = None) -> AIManager:
    """AI Manager のファクトリー関数"""
    return AIManager(config)


def get_available_models() -> Dict[str, Any]:
    """利用可能なモデル一覧を取得（API キー不要）"""
    model_manager = ModelManager()
    return {
        'models': model_manager.get_available_models(),
        'task_recommendations': model_manager.task_recommendations,
        'model_summary': model_manager.get_model_stats_summary()
    }


# パッケージ情報
__version__ = "1.0.0"
__author__ = "Mercury Mapping Engine Team"
__description__ = "Claude AI integration for Mercury Mapping Engine"

# 公開API
__all__ = [
    'AIManager',
    'ClaudeClient', 
    'ModelManager',
    'PromptBuilder',
    'create_ai_manager',
    'get_available_models'
]
