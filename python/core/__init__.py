"""
Mercury Mapping Engine - Core Package
コア分析エンジンパッケージ
"""

from .csv_analyzer import CSVAnalyzer
from .card_matcher import CardMatcher
from .field_mapper import FieldMapper
from .mapping_engine import MappingEngine

__all__ = [
    'CSVAnalyzer',
    'CardMatcher', 
    'FieldMapper',
    'MappingEngine'
]

# バージョン情報
__version__ = '2.0.0'
__author__ = 'Mercury Mapping Engine Team'

# 設定のデフォルト値
DEFAULT_CONFIG = {
    # CSV設定
    'csv_max_rows': 1000,
    'csv_sample_rows': 5,
    'csv_encoding': 'utf-8',
    
    # カードマッチング設定
    'card_match_threshold': 0.75,
    'card_name_similarity_threshold': 0.8,
    'price_similarity_threshold': 0.9,
    
    # フィールドマッピング設定
    'field_similarity_threshold': 0.7,
    'field_consistency_threshold': 0.6,
    'min_sample_count': 3
}

def create_mapping_engine(config=None):
    """ファクトリー関数: 設定付きでMappingEngineを作成"""
    final_config = DEFAULT_CONFIG.copy()
    if config:
        final_config.update(config)
    
    return MappingEngine(final_config)