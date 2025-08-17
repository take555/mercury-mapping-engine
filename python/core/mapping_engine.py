"""
Mercury Mapping Engine - Main Mapping Engine
統合マッピングエンジン
"""
from typing import Dict, List, Tuple, Any, Optional
from .csv_analyzer import CSVAnalyzer
from .card_matcher import CardMatcher
from .field_mapper import FieldMapper
from utils.logger import analysis_logger, performance_logger


class MappingEngine:
    """統合マッピングエンジン"""
    
    def __init__(self, config=None):
        self.config = config or {}
        
        # 各コンポーネントを初期化
        self.csv_analyzer = CSVAnalyzer(self.config)
        self.card_matcher = CardMatcher(self.config)
        self.field_mapper = FieldMapper(self.config)
        
        analysis_logger.logger.info("MappingEngine initialized with modular components")
    
    def analyze_csv_files(self, filepath_a: str, filepath_b: str, 
                         full_analysis: bool = True) -> Dict[str, Any]:
        """CSV ファイルの分析"""
        performance_logger.start_timer('full_csv_analysis')
        
        try:
            if full_analysis:
                analysis_a = self.csv_analyzer.analyze_file_full(filepath_a)
                analysis_b = self.csv_analyzer.analyze_file_full(filepath_b)
            else:
                analysis_a = self.csv_analyzer.analyze_file(filepath_a)
                analysis_b = self.csv_analyzer.analyze_file(filepath_b)
            
            # エラーチェック
            if 'error' in analysis_a:
                return {'error': f"A社CSVエラー: {analysis_a['error']}"}
            
            if 'error' in analysis_b:
                return {'error': f"B社CSVエラー: {analysis_b['error']}"}
            
            # CSV構造の検証
            validation_a = self.csv_analyzer.validate_csv_structure(
                analysis_a['headers'], analysis_a.get('full_data', analysis_a['sample_data'])
            )
            validation_b = self.csv_analyzer.validate_csv_structure(
                analysis_b['headers'], analysis_b.get('full_data', analysis_b['sample_data'])
            )
            
            result = {
                'analysis_a': analysis_a,
                'analysis_b': analysis_b,
                'validation_a': validation_a,
                'validation_b': validation_b,
                'analysis_type': 'full' if full_analysis else 'sample'
            }
            
            performance_logger.end_timer('full_csv_analysis')
            return result
            
        except Exception as e:
            analysis_logger.log_error('csv_files_analysis', str(e))
            return {'error': str(e)}
    
    def analyze_card_based_mapping(self, headers_a: List[str], headers_b: List[str],
                                  sample_data_a: List[Dict], sample_data_b: List[Dict],
                                  full_data_a: Optional[List[Dict]] = None,
                                  full_data_b: Optional[List[Dict]] = None) -> Tuple[List[Dict], List[Dict]]:
        """カードベースでのフィールドマッピング分析"""
        performance_logger.start_timer('card_based_mapping')
        
        try:
            # データが少ない場合はサンプルデータを使用
            data_a = full_data_a if full_data_a else sample_data_a
            data_b = full_data_b if full_data_b else sample_data_b
            
            analysis_logger.logger.info(f"分析データ数: A社={len(data_a)}, B社={len(data_b)}")
            
            # ステップ1: 同じカードを特定
            card_matches = self.card_matcher.find_matching_cards(data_a, data_b, headers_a, headers_b)
            
            if len(card_matches) < self.config.get('min_sample_count', 3):
                analysis_logger.logger.warning("マッチするカードが少なすぎます。従来の方法にフォールバック")
                return self.field_mapper.analyze_traditional_mappings(headers_a, headers_b, sample_data_a, sample_data_b)
            
            # ステップ2: マッチしたカードからフィールド対応を分析
            field_mappings = self.field_mapper.analyze_field_mappings_from_matches(card_matches, headers_a, headers_b)
            
            # ステップ3: 信頼度を計算
            enhanced_mappings = self.field_mapper.calculate_mapping_confidence(field_mappings, card_matches)
            
            performance_logger.end_timer('card_based_mapping')
            return enhanced_mappings, card_matches
            
        except Exception as e:
            analysis_logger.log_error('card_based_mapping', str(e))
            # エラー時は従来手法にフォールバック
            return self.field_mapper.analyze_traditional_mappings(headers_a, headers_b, sample_data_a, sample_data_b)
    
    def create_mapping_summary(self, enhanced_mappings: List[Dict], card_matches: List[Dict],
                              analysis_a: Dict, analysis_b: Dict) -> Dict[str, Any]:
        """マッピング分析のサマリーを作成"""
        
        # 品質メトリクス
        high_confidence_mappings = [m for m in enhanced_mappings if m.get('confidence', 0.0) > 0.8]
        medium_confidence_mappings = [m for m in enhanced_mappings if 0.6 < m.get('confidence', 0.0) <= 0.8]
        low_confidence_mappings = [m for m in enhanced_mappings if m.get('confidence', 0.0) <= 0.6]
         
        # カードマッチングの品質分析
        match_quality = self.card_matcher.analyze_match_quality(card_matches)
        
        # フィールドタイプ別の統計
        field_types = {}
        for mapping in enhanced_mappings:
            field_type = mapping.get('field_type', 'unknown')
            if field_type not in field_types:
                field_types[field_type] = []
            field_types[field_type].append(mapping)
        
        summary = {
            'analysis_summary': {
                'total_fields_a': len(analysis_a['headers']),
                'total_fields_b': len(analysis_b['headers']),
                'total_records_a': analysis_a.get('total_rows', 0),
                'total_records_b': analysis_b.get('total_rows', 0),
                'card_matches_found': len(card_matches),
                'total_mappings_detected': len(enhanced_mappings)
            },
            'mapping_quality': {
                'high_confidence_count': len(high_confidence_mappings),
                'medium_confidence_count': len(medium_confidence_mappings),
                'low_confidence_count': len(enhanced_mappings) - len(high_confidence_mappings) - len(medium_confidence_mappings),
                'average_confidence': sum(m.get('confidence', 0.0) for m in enhanced_mappings) / len(enhanced_mappings) if enhanced_mappings else 0,
                'coverage_ratio_a': len(set(m.get('company_a_field', '') for m in enhanced_mappings if m.get('company_a_field'))) / len(analysis_a['headers']),
                'coverage_ratio_b': len(set(m.get('company_b_field', '') for m in enhanced_mappings if m.get('company_b_field'))) / len(analysis_b['headers'])
            },
            'card_matching_quality': match_quality,
            'field_type_distribution': {
                field_type: len(mappings) for field_type, mappings in field_types.items()
            },
            'recommended_actions': self._generate_recommendations(enhanced_mappings, card_matches, match_quality)
        }
        
        return summary
    
    def export_mapping_rules(self, enhanced_mappings: List[Dict], 
                           confidence_threshold: float = 0.8) -> Dict[str, Any]:
        """マッピングルールをエクスポート"""
        rules = self.field_mapper.create_mapping_rules(enhanced_mappings, confidence_threshold)
        
        export_data = {
            'version': '1.0',
            'created_at': None,  # 実装時に現在時刻を設定
            'confidence_threshold': confidence_threshold,
            'total_rules': len(rules),
            'rules': rules,
            'metadata': {
                'engine_version': 'Mercury Mapping Engine v2.0',
                'analysis_method': 'card_based_matching',
                'quality_metrics': {
                    'average_confidence': sum(r.get('confidence', 0.0) for r in rules) / len(rules) if rules else 0,
                    'high_quality_rules': len([r for r in rules if r.get('confidence', 0.0) > 0.9])
                }
            }
        }
        
        return export_data
    
    def validate_mapping_results(self, enhanced_mappings: List[Dict], 
                                card_matches: List[Dict]) -> Dict[str, Any]:
        """マッピング結果の検証"""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'warnings': [],
            'statistics': {}
        }
        
        # 基本的な検証
        if not enhanced_mappings:
            validation_result['is_valid'] = False
            validation_result['issues'].append("マッピング結果が見つかりません")
            return validation_result
        
        if not card_matches:
            validation_result['warnings'].append("カードマッチが見つかりません")
        
        # 重複チェック
        a_fields = [m.get('company_a_field', '') for m in enhanced_mappings]
        b_fields = [m.get('company_b_field', '') for m in enhanced_mappings]
        
        duplicate_a = [f for f in set(a_fields) if a_fields.count(f) > 1]
        duplicate_b = [f for f in set(b_fields) if b_fields.count(f) > 1]
        
        if duplicate_a:
            validation_result['warnings'].append(f"A社フィールドの重複: {duplicate_a}")
        
        if duplicate_b:
            validation_result['warnings'].append(f"B社フィールドの重複: {duplicate_b}")
        
        # 信頼度の分布チェック
        confidences = [m.get('confidence', 0.0) for m in enhanced_mappings]
        low_confidence_count = len([c for c in confidences if c < 0.5])
        
        if low_confidence_count > len(enhanced_mappings) * 0.5:
            validation_result['warnings'].append("低信頼度のマッピングが全体の50%を超えています")
        
        validation_result['statistics'] = {
            'total_mappings': len(enhanced_mappings),
            'unique_a_fields': len(set(a_fields)),
            'unique_b_fields': len(set(b_fields)),
            'average_confidence': sum(confidences) / len(confidences),
            'low_confidence_count': low_confidence_count
        }
        
        return validation_result
    
    def _generate_recommendations(self, enhanced_mappings: List[Dict], 
                                card_matches: List[Dict], match_quality: Dict) -> List[str]:
        """推奨アクションを生成"""
        recommendations = []
        
        if not enhanced_mappings:
            recommendations.append("データクリーニングを実施して再分析することを推奨します")
            return recommendations
        
        high_confidence_count = len([m for m in enhanced_mappings if m.get('confidence', 0.0) > 0.8])
        total_mappings = len(enhanced_mappings)
        
        if high_confidence_count / total_mappings > 0.8:
            recommendations.append("✅ 高品質なマッピングが検出されました。このルールセットの使用を推奨します")
        elif high_confidence_count / total_mappings > 0.5:
            recommendations.append("⚠️ 中程度の品質です。高信頼度のマッピングのみ使用することを推奨します")
        else:
            recommendations.append("❌ 低品質なマッピングです。データの見直しや手動での確認を推奨します")
        
        if len(card_matches) < 10:
            recommendations.append("🔍 カードマッチ数が少ないです。より多くのデータでの再分析を推奨します")
        
        if match_quality.get('average_score', 0) < 0.8:
            recommendations.append("📝 カード名の正規化やデータクリーニングを実施することを推奨します")
        
        return recommendations
