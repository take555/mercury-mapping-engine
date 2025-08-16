"""
Mercury Mapping Engine - Field Mapper
フィールドマッピングエンジン
"""
from typing import Dict, List, Tuple, Any, Optional
from utils.text_similarity import TextSimilarity
from utils.logger import analysis_logger, performance_logger


class FieldMapper:
    """フィールドマッピング専用クラス"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.field_similarity_threshold = self.config.get('field_similarity_threshold', 0.7)
        self.field_consistency_threshold = self.config.get('field_consistency_threshold', 0.6)
        self.min_sample_count = self.config.get('min_sample_count', 3)
        self.text_similarity = TextSimilarity()
    
    def analyze_field_mappings_from_matches(self, card_matches: List[Dict], 
                                          headers_a: List[str], headers_b: List[str]) -> Dict[Tuple[str, str], Dict[str, Any]]:
        """マッチしたカードからフィールド対応を分析"""
        performance_logger.start_timer('field_mapping_analysis')
        
        field_mappings = {}
        
        # 各フィールドペアの対応度を計算
        for field_a in headers_a:
            for field_b in headers_b:
                similarities = []
                
                for match in card_matches:
                    value_a = str(match['row_a_data'].get(field_a, '')).strip()
                    value_b = str(match['row_b_data'].get(field_b, '')).strip()
                    
                    if value_a and value_b:
                        # 複数の類似度計算手法を使用
                        similarity_result = self.text_similarity.calculate_comprehensive_similarity(value_a, value_b)
                        similarities.append(similarity_result['comprehensive_score'])
                
                if similarities:
                    avg_similarity = sum(similarities) / len(similarities)
                    consistency = len([s for s in similarities if s > 0.8]) / len(similarities)
                    
                    field_mappings[(field_a, field_b)] = {
                        'similarity': avg_similarity,
                        'consistency': consistency,
                        'sample_count': len(similarities),
                        'high_matches': len([s for s in similarities if s > 0.8]),
                        'similarity_details': similarities
                    }
        
        performance_logger.end_timer('field_mapping_analysis')
        return field_mappings
    
    def calculate_mapping_confidence(self, field_mappings: Dict[Tuple[str, str], Dict[str, Any]], 
                                   card_matches: List[Dict]) -> List[Dict[str, Any]]:
        """フィールドマッピングの信頼度を計算"""
        performance_logger.start_timer('mapping_confidence_calculation')
        
        confident_mappings = []
        min_samples = max(self.min_sample_count, len(card_matches) * 0.3)
        
        for (field_a, field_b), stats in field_mappings.items():
            # 総合スコア計算
            confidence = self._calculate_confidence_score(stats, min_samples)
            
            if (stats['similarity'] >= self.field_similarity_threshold and 
                stats['consistency'] >= self.field_consistency_threshold and
                stats['sample_count'] >= min_samples):
                
                # フィールドタイプを推定
                field_type = self.estimate_field_type(field_a, field_b, stats)
                
                confident_mappings.append({
                    'field_type': field_type,
                    'company_a_field': field_a,
                    'company_b_field': field_b,
                    'confidence': confidence,
                    'similarity': stats['similarity'],
                    'consistency': stats['consistency'],
                    'sample_count': stats['sample_count'],
                    'high_matches': stats['high_matches'],
                    'reasoning': f'カードベース分析: {stats["sample_count"]}件中{stats["high_matches"]}件が高一致',
                    'quality_metrics': self._calculate_quality_metrics(stats)
                })
        
        # 信頼度順でソート
        confident_mappings.sort(key=lambda x: x['confidence'], reverse=True)
        
        analysis_logger.log_field_mapping(
            len(confident_mappings),
            len([m for m in confident_mappings if m['confidence'] > 0.8])
        )
        performance_logger.end_timer('mapping_confidence_calculation')
        
        return confident_mappings
    
    def estimate_field_type(self, field_a: str, field_b: str, stats: Dict[str, Any]) -> str:
        """フィールドタイプを推定"""
        field_patterns = {
            'card_name': ['カード名', '名前', '名称', 'name', 'title', 'card', 'product'],
            'price': ['価格', '値段', 'price', '金額', 'amount', 'cost', '円', 'yen'],
            'series': ['シリーズ', 'series', 'set', 'セット', 'edition'],
            'rarity': ['レアリティ', 'rarity', '希少度', 'レア', 'rare'],
            'condition': ['状態', 'condition', 'コンディション', '品質', 'quality'],
            'stock': ['在庫', 'stock', '数量', 'quantity', 'count'],
            'id': ['id', 'ID', 'コード', 'code', 'jan', 'sku'],
            'category': ['カテゴリ', 'category', '分類', 'type', 'class'],
            'manufacturer': ['メーカー', 'manufacturer', 'maker', '発売元', 'publisher'],
            'language': ['言語', 'language', 'lang', '版', 'ver'],
            'description': ['説明', 'description', 'desc', 'テキスト', 'text', '詳細'],
            'date': ['日付', 'date', '発売日', 'release', '登録日']
        }
        
        field_combination = f"{field_a} {field_b}".lower()
        
        # パターンマッチングで最適なタイプを検索
        for field_type, patterns in field_patterns.items():
            for pattern in patterns:
                if pattern.lower() in field_combination:
                    return field_type
        
        # パターンマッチしない場合は類似度と一貫性で判定
        if stats['similarity'] > 0.9 and stats['consistency'] > 0.8:
            return 'high_confidence_unknown'
        elif stats['similarity'] > 0.7:
            return 'medium_confidence_unknown'
        else:
            return 'unknown'
    
    def analyze_traditional_mappings(self, headers_a: List[str], headers_b: List[str], 
                                   sample_data_a: List[Dict], sample_data_b: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """従来手法でのフィールドマッピング分析（比較用）"""
        performance_logger.start_timer('traditional_mapping_analysis')
        
        # A社基準：各A社フィールドに対するB社フィールドのマッピング度
        a_to_b_mappings = []
        for field_a in headers_a:
            best_matches = []
            for field_b in headers_b:
                similarity = self._calculate_traditional_field_similarity(
                    field_a, field_b, sample_data_a, sample_data_b
                )
                if similarity > 0.1:  # 10%以上の類似度
                    best_matches.append({
                        'target_field': field_b,
                        'similarity': similarity,
                        'reasoning': self._get_similarity_reason(field_a, field_b)
                    })
            
            # 類似度順でソート
            best_matches.sort(key=lambda x: x['similarity'], reverse=True)
            a_to_b_mappings.append({
                'source_field': field_a,
                'matches': best_matches[:3]  # 上位3件
            })
        
        # B社基準：各B社フィールドに対するA社フィールドのマッピング度
        b_to_a_mappings = []
        for field_b in headers_b:
            best_matches = []
            for field_a in headers_a:
                similarity = self._calculate_traditional_field_similarity(
                    field_b, field_a, sample_data_b, sample_data_a
                )
                if similarity > 0.1:  # 10%以上の類似度
                    best_matches.append({
                        'target_field': field_a,
                        'similarity': similarity,
                        'reasoning': self._get_similarity_reason(field_b, field_a)
                    })
            
            # 類似度順でソート
            best_matches.sort(key=lambda x: x['similarity'], reverse=True)
            b_to_a_mappings.append({
                'source_field': field_b,
                'matches': best_matches[:3]  # 上位3件
            })
        
        performance_logger.end_timer('traditional_mapping_analysis')
        return a_to_b_mappings, b_to_a_mappings
    
    def create_mapping_rules(self, confident_mappings: List[Dict[str, Any]], 
                           confidence_threshold: float = 0.8) -> List[Dict[str, Any]]:
        """マッピングルールを作成"""
        rules = []
        
        for mapping in confident_mappings:
            if mapping['confidence'] >= confidence_threshold:
                rule = {
                    'rule_id': f"rule_{len(rules) + 1}",
                    'field_type': mapping['field_type'],
                    'source_field': mapping['company_a_field'],
                    'target_field': mapping['company_b_field'],
                    'mapping_type': 'direct',  # direct, transform, extract
                    'confidence': mapping['confidence'],
                    'validation_metrics': {
                        'similarity': mapping['similarity'],
                        'consistency': mapping['consistency'],
                        'sample_count': mapping['sample_count']
                    },
                    'transform_rule': None,  # 将来的な変換ルール用
                    'active': True
                }
                rules.append(rule)
        
        return rules
    
    def _calculate_confidence_score(self, stats: Dict[str, Any], min_samples: int) -> float:
        """信頼度スコアを計算"""
        similarity_score = stats['similarity']
        consistency_score = stats['consistency']
        sample_score = min(1.0, stats['sample_count'] / min_samples)
        
        # 重み付け平均
        confidence = (similarity_score * 0.4 + consistency_score * 0.4 + sample_score * 0.2)
        
        return round(confidence, 3)
    
    def _calculate_quality_metrics(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """品質メトリクスを計算"""
        similarities = stats.get('similarity_details', [])
        
        if not similarities:
            return {}
        
        return {
            'min_similarity': min(similarities),
            'max_similarity': max(similarities),
            'std_deviation': self._calculate_std_deviation(similarities),
            'median_similarity': self._calculate_median(similarities),
            'consistency_ratio': stats['consistency']
        }
    
    def _calculate_traditional_field_similarity(self, field1: str, field2: str, 
                                              sample_data1: List[Dict], sample_data2: List[Dict]) -> float:
        """従来手法でのフィールド間の類似度を計算"""
        # 1. フィールド名の類似度 (40%)
        name_similarity = self.text_similarity.calculate_comprehensive_similarity(field1, field2)['comprehensive_score']
        
        # 2. データ型の類似度 (30%)
        type_similarity = self._calculate_data_type_similarity(field1, field2, sample_data1, sample_data2)
        
        # 3. データ内容の類似度 (30%)
        content_similarity = self._calculate_content_similarity(field1, field2, sample_data1, sample_data2)
        
        # 重み付け平均
        total_similarity = (name_similarity * 0.4) + (type_similarity * 0.3) + (content_similarity * 0.3)
        
        return round(total_similarity, 3)
    
    def _calculate_data_type_similarity(self, field1: str, field2: str, 
                                      sample_data1: List[Dict], sample_data2: List[Dict]) -> float:
        """データ型の類似度を計算"""
        def get_data_type(field, sample_data):
            values = [str(row.get(field, '')).strip() for row in sample_data if row.get(field, '').strip()]
            if not values:
                return 'empty'
            
            numeric_count = 0
            for value in values:
                try:
                    float(value.replace(',', '').replace('¥', '').replace('円', ''))
                    numeric_count += 1
                except ValueError:
                    pass
            
            if numeric_count == len(values):
                return 'numeric'
            elif numeric_count > len(values) * 0.7:
                return 'mostly_numeric'
            else:
                return 'text'
        
        type1 = get_data_type(field1, sample_data1)
        type2 = get_data_type(field2, sample_data2)
        
        if type1 == type2:
            return 1.0
        elif (type1 == 'numeric' and type2 == 'mostly_numeric') or (type1 == 'mostly_numeric' and type2 == 'numeric'):
            return 0.8
        elif type1 == 'text' and type2 == 'text':
            return 1.0
        else:
            return 0.2
    
    def _calculate_content_similarity(self, field1: str, field2: str, 
                                    sample_data1: List[Dict], sample_data2: List[Dict]) -> float:
        """データ内容の類似度を計算"""
        values1 = [str(row.get(field1, '')).strip().lower() for row in sample_data1 if row.get(field1, '').strip()]
        values2 = [str(row.get(field2, '')).strip().lower() for row in sample_data2 if row.get(field2, '').strip()]
        
        if not values1 or not values2:
            return 0.0
        
        # 共通値の比率
        set1 = set(values1)
        set2 = set(values2)
        
        if not set1 or not set2:
            return 0.0
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def _get_similarity_reason(self, field1: str, field2: str) -> str:
        """類似度の根拠を説明"""
        field1_lower = field1.lower()
        field2_lower = field2.lower()
        
        if field1_lower == field2_lower:
            return "完全一致"
        elif field1_lower in field2_lower or field2_lower in field1_lower:
            return "部分一致"
        else:
            # 共通文字を確認
            common_chars = set(field1_lower) & set(field2_lower)
            if len(common_chars) > 2:
                return f"文字類似度: {len(common_chars)}文字共通"
            else:
                return "データ内容類似"
    
    def _calculate_std_deviation(self, values: List[float]) -> float:
        """標準偏差を計算"""
        if len(values) < 2:
            return 0.0
        
        mean = sum(values) / len(values)
        variance = sum((x - mean) ** 2 for x in values) / len(values)
        return variance ** 0.5
    
    def _calculate_median(self, values: List[float]) -> float:
        """中央値を計算"""
        if not values:
            return 0.0
        
        sorted_values = sorted(values)
        n = len(sorted_values)
        
        if n % 2 == 0:
            return (sorted_values[n // 2 - 1] + sorted_values[n // 2]) / 2
        else:
            return sorted_values[n // 2]