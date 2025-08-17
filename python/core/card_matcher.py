"""
Mercury Mapping Engine - Card Matcher
カードマッチングエンジン
"""
import re
from typing import Dict, List, Tuple, Any, Optional
from utils.text_similarity import TextSimilarity
from utils.logger import analysis_logger, performance_logger


class CardMatcher:
    """カードマッチング専用クラス"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.match_threshold = self.config.get('card_match_threshold', 0.75)
        self.name_similarity_threshold = self.config.get('card_name_similarity_threshold', 0.8)
        self.price_similarity_threshold = self.config.get('price_similarity_threshold', 0.9)
        self.text_similarity = TextSimilarity()
    
    def find_matching_cards(self, data_a: List[Dict], data_b: List[Dict], 
                           headers_a: List[str], headers_b: List[str]) -> List[Dict[str, Any]]:
        """2つのデータセットから同じカードを特定"""
        performance_logger.start_timer('card_matching')
        
        matches = []
        
        # カード名候補フィールドを特定
        name_fields_a = self.identify_card_name_fields(headers_a)
        name_fields_b = self.identify_card_name_fields(headers_b)
        
        analysis_logger.logger.info(f"カード名候補 A社: {name_fields_a}")
        analysis_logger.logger.info(f"カード名候補 B社: {name_fields_b}")
        
        # 価格候補フィールドを特定（補助的な判定用）
        price_fields_a = self.identify_price_fields(headers_a)
        price_fields_b = self.identify_price_fields(headers_b)
        
        # マッチング実行
        for i, row_a in enumerate(data_a):
            for j, row_b in enumerate(data_b):
                match_result = self._calculate_match_score(
                    row_a, row_b, 
                    name_fields_a, name_fields_b,
                    price_fields_a, price_fields_b,
                    headers_a, headers_b
                )
                
                # マッチしたと判定する閾値
                if match_result['score'] > self.match_threshold:
                    matches.append({
                        'row_a_index': i,
                        'row_b_index': j,
                        'row_a_data': row_a,
                        'row_b_data': row_b,
                        'match_score': match_result['score'],
                        'match_details': match_result['details']
                    })
        
        # スコア順でソート
        matches.sort(key=lambda x: x['match_score'], reverse=True)
        
        # 重複を除去（一意なマッチングのみ）
        unique_matches = self._remove_duplicate_matches(matches)
        
        analysis_logger.log_card_matching(
            len(data_a), len(data_b), len(unique_matches)
        )
        performance_logger.end_timer('card_matching')
        
        return unique_matches
    
    def identify_card_name_fields(self, headers: List[str]) -> List[str]:
        """カード名と思われるフィールドを特定"""
        name_patterns = [
            'カード名', '名前', '名称', 'name', 'card_name', 'title', 'product_name',
            'item_name', 'カードタイトル', 'アイテム名', 'プロダクト名', 'カード', 'card'
        ]
        
        candidates = []
        for header in headers:
            for pattern in name_patterns:
                if pattern.lower() in header.lower() or header.lower() in pattern.lower():
                    candidates.append(header)
                    break
        
        return candidates if candidates else headers[:3]  # 見つからない場合は最初の3フィールド
    
    def identify_price_fields(self, headers: List[str]) -> List[str]:
        """価格と思われるフィールドを特定"""
        price_patterns = [
            '価格', '値段', 'price', '金額', 'amount', 'cost', 'buy_price', 'sell_price',
            '販売価格', '買取価格', '税込', '税抜', 'yen', '円', '料金'
        ]
        
        candidates = []
        for header in headers:
            for pattern in price_patterns:
                if pattern.lower() in header.lower():
                    candidates.append(header)
                    break
        
        return candidates
    
    def _calculate_match_score(self, row_a: Dict, row_b: Dict,
                              name_fields_a: List[str], name_fields_b: List[str],
                              price_fields_a: List[str], price_fields_b: List[str],
                              headers_a: List[str], headers_b: List[str]) -> Dict[str, Any]:
        """マッチスコアを計算"""
        match_score = 0
        match_details = {}
        
        # 方法1: カード名の類似度
        name_similarity = self._calculate_card_name_similarity(
            row_a, row_b, name_fields_a, name_fields_b
        )
        if name_similarity > self.name_similarity_threshold:
            match_score += name_similarity * 0.7
            match_details['name_match'] = name_similarity
        
        # 方法2: 価格の一致（補助判定）
        price_similarity = self._calculate_price_similarity(
            row_a, row_b, price_fields_a, price_fields_b
        )
        if price_similarity > self.price_similarity_threshold:
            match_score += price_similarity * 0.3
            match_details['price_match'] = price_similarity
        
        # 方法3: 複数フィールドの総合判定
        overall_similarity = self._calculate_overall_similarity(
            row_a, row_b, headers_a, headers_b
        )
        if overall_similarity > 0.6:
            match_score += overall_similarity * 0.2
            match_details['overall_match'] = overall_similarity
        
        return {
            'score': match_score,
            'details': match_details
        }
    
    def _calculate_card_name_similarity(self, row_a: Dict, row_b: Dict,
                                       name_fields_a: List[str], name_fields_b: List[str]) -> float:
        """カード名の類似度を計算"""
        max_similarity = 0
        
        for field_a in name_fields_a:
            value_a = str(row_a.get(field_a, '')).strip()
            if not value_a:
                continue
                
            for field_b in name_fields_b:
                value_b = str(row_b.get(field_b, '')).strip()
                if not value_b:
                    continue
                
                # 複数の類似度計算手法を使用
                similarities = [
                    self.text_similarity.calculate_exact_similarity(value_a, value_b),
                    self.text_similarity.calculate_fuzzy_similarity(value_a, value_b),
                    self.text_similarity.calculate_partial_similarity(value_a, value_b)
                ]
                
                current_similarity = max(similarities)
                max_similarity = max(max_similarity, current_similarity)
        
        return max_similarity
    
    def _calculate_price_similarity(self, row_a: Dict, row_b: Dict,
                                   price_fields_a: List[str], price_fields_b: List[str]) -> float:
        """価格の類似度を計算"""
        for field_a in price_fields_a:
            value_a = self._extract_numeric_value(row_a.get(field_a, ''))
            if value_a is None:
                continue
                
            for field_b in price_fields_b:
                value_b = self._extract_numeric_value(row_b.get(field_b, ''))
                if value_b is None:
                    continue
                
                # 価格が完全一致または非常に近い場合
                if abs(value_a - value_b) < 0.01:
                    return 1.0
                elif value_a > 0 and value_b > 0:
                    diff_ratio = abs(value_a - value_b) / max(value_a, value_b)
                    if diff_ratio < 0.1:  # 10%以内の差
                        return 1.0 - diff_ratio
        
        return 0.0
    
    def _calculate_overall_similarity(self, row_a: Dict, row_b: Dict,
                                     headers_a: List[str], headers_b: List[str]) -> float:
        """全フィールドでの総合的な類似度"""
        similarities = []
        
        for field_a in headers_a[:5]:  # 最初の5フィールドのみチェック
            value_a = str(row_a.get(field_a, '')).strip()
            if not value_a:
                continue
                
            for field_b in headers_b[:5]:
                value_b = str(row_b.get(field_b, '')).strip()
                if not value_b:
                    continue
                
                similarity = self.text_similarity.calculate_fuzzy_similarity(value_a, value_b)
                if similarity > 0.7:
                    similarities.append(similarity)
        
        return sum(similarities) / len(similarities) if similarities else 0.0
    
    def _extract_numeric_value(self, value_str: str) -> Optional[float]:
        """文字列から数値を抽出"""
        if not value_str:
            return None
        
        # 数字とピリオド、カンマのみ抽出
        numeric_str = re.sub(r'[^\d.,]', '', str(value_str))
        numeric_str = numeric_str.replace(',', '')
        
        try:
            return float(numeric_str)
        except ValueError:
            return None
    
    def _remove_duplicate_matches(self, matches: List[Dict]) -> List[Dict]:
        """重複するマッチを除去"""
        used_a = set()
        used_b = set()
        unique_matches = []
        
        for match in matches:
            if match['row_a_index'] not in used_a and match['row_b_index'] not in used_b:
                unique_matches.append(match)
                used_a.add(match['row_a_index'])
                used_b.add(match['row_b_index'])
        
        return unique_matches
    def analyze_match_quality(self, matches):
        """マッチング品質を分析"""
        if not matches:
            return {
                'total_matches': 0,
                'average_score': 0.0,
                'high_quality_matches': 0,
                'medium_quality_matches': 0,
                'low_quality_matches': 0
            }

        # スコアを安全に取得
        scores = []
        for match in matches:
            score = (match.get('match_score') or
                     match.get('similarity') or
                     match.get('score') or
                     0.0)
            try:
                scores.append(float(score))
            except (ValueError, TypeError):
                scores.append(0.0)

        if not scores:
            scores = [0.0]

        avg_score = sum(scores) / len(scores)
        high_quality = len([s for s in scores if s > 0.8])
        medium_quality = len([s for s in scores if 0.6 <= s <= 0.8])
        low_quality = len([s for s in scores if s < 0.6])

        return {
            'total_matches': len(matches),
            'average_score': round(avg_score, 3),
            'high_quality_matches': high_quality,
            'medium_quality_matches': medium_quality,
            'low_quality_matches': low_quality
        }
    