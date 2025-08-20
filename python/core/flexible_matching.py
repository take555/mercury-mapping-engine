#!/usr/bin/env python3
"""
Flexible Matching System - AI/String Similarity Based
汎用的なデータマッチングシステム（固定フィールドパターンに依存しない）
"""

import re
import unicodedata
from difflib import SequenceMatcher
from typing import List, Dict, Any, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class FlexibleMatcher:
    """柔軟なデータマッチングシステム"""
    
    def __init__(self, similarity_threshold: float = 0.8):
        self.similarity_threshold = similarity_threshold
        self.field_weight_cache = {}
        self.field_types = {}  # AIベースのフィールドタイプ情報を保存
        
    def normalize_text(self, text: str) -> str:
        """テキストの正規化"""
        if not text:
            return ""
        
        # Unicode正規化
        text = unicodedata.normalize('NFKC', text)
        
        # 全角英数を半角に変換
        text = text.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        text = text.translate(str.maketrans('ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ', 
                                          'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'))
        
        # 記号・空白の統一
        text = re.sub(r'[　\s]+', ' ', text)  # 全角・半角スペースを統一
        text = re.sub(r'[‐－−‒–—―]', '-', text)  # ハイフンを統一
        text = re.sub(r'[～〜]', '~', text)  # チルダを統一
        
        return text.strip()
    
    def calculate_string_similarity(self, str1: str, str2: str) -> float:
        """2つの文字列の類似度を計算"""
        if not str1 or not str2:
            return 0.0
        
        norm1 = self.normalize_text(str1)
        norm2 = self.normalize_text(str2)
        
        if norm1 == norm2:
            return 1.0
        
        # SequenceMatcherで類似度計算
        similarity = SequenceMatcher(None, norm1, norm2).ratio()
        return similarity
    
    def analyze_field_importance(self, headers: List[str], data: List[Dict]) -> Dict[str, float]:
        """フィールドの重要度を動的に分析"""
        if not data:
            return {}
        
        field_scores = {}
        field_types = {}
        total_rows = len(data)
        
        for field in headers:
            # 非空データの割合
            non_empty_count = sum(1 for row in data if str(row.get(field, '')).strip())
            coverage = non_empty_count / total_rows if total_rows > 0 else 0
            
            # データの多様性（ユニーク値の割合）
            if non_empty_count > 0:
                unique_values = set(str(row.get(field, '')).strip() for row in data if str(row.get(field, '')).strip())
                diversity = len(unique_values) / non_empty_count
            else:
                diversity = 0
            
            # AIベースのフィールドタイプ判別
            field_type = self._classify_field_type_ai(field, data, field)
            field_types[field] = field_type
            
            # フィールドタイプに基づく重要度
            type_importance = self._get_importance_by_type(field_type)
            
            # フィールド名からの推測重要度（バックアップ）
            name_importance = self._estimate_field_importance_by_name(field)
            
            # 総合スコア（AIタイプ判別を優先）
            importance = max(type_importance, name_importance)
            field_scores[field] = (coverage * 0.4) + (diversity * 0.3) + (importance * 0.3)
        
        self.field_types = field_types  # デバッグ用に保存
        return field_scores
    
    def _estimate_field_importance_by_name(self, field_name: str) -> float:
        """フィールド名から重要度を推定"""
        name_lower = field_name.lower()
        
        # 名前系フィールド
        if any(keyword in name_lower for keyword in ['name', 'title', 'カード名', '名前', 'タイトル', '商品名']):
            return 0.9
        
        # ID系フィールド
        if any(keyword in name_lower for keyword in ['id', 'code', 'number', '番号', 'コード', '識別']):
            return 0.8
        
        # レアリティ系フィールド
        if any(keyword in name_lower for keyword in ['rarity', 'rare', 'レアリティ', 'レア', '希少度', 'rareza']):
            return 0.8
        
        # シリアル系フィールド
        if any(keyword in name_lower for keyword in ['serial', 'シリアル', 'number', '番号', 'no.', '型番']):
            return 0.8
        
        # 日付系フィールド
        if any(keyword in name_lower for keyword in ['date', 'time', '日付', '時間', '発売', 'release']):
            return 0.7
        
        # 分類・カテゴリ系フィールド
        if any(keyword in name_lower for keyword in ['category', 'type', 'class', '分類', 'カテゴリ', 'タイプ']):
            return 0.6
        
        # その他
        return 0.5
    
    def _classify_field_type_ai(self, field_name: str, data: List[Dict], field_key: str) -> str:
        """AIベースでフィールドタイプを分類"""
        if not field_name or not data:
            return 'unknown'
        
        # サンプルデータを収集
        sample_values = []
        for row in data[:10]:  # 最初の10行をサンプリング
            value = str(row.get(field_key, '')).strip()
            if value and value != 'nan':
                sample_values.append(value)
        
        if not sample_values:
            return 'unknown'
        
        # フィールド名とデータパターンの分析
        field_lower = field_name.lower()
        sample_str = ', '.join(sample_values[:5])  # 最初の5つの値
        
        # レアリティ判定
        if self._is_rarity_field_ai(field_lower, sample_values):
            return 'rarity'
        
        # シリアル/ID判定
        if self._is_serial_field_ai(field_lower, sample_values):
            return 'serial'
        
        # 名前判定
        if self._is_name_field_ai(field_lower, sample_values):
            return 'name'
        
        # 日付判定
        if self._is_date_field_ai(field_lower, sample_values):
            return 'date'
        
        # 価格判定
        if self._is_price_field_ai(field_lower, sample_values):
            return 'price'
        
        return 'other'
    
    def _is_rarity_field_ai(self, field_name: str, sample_values: List[str]) -> bool:
        """AIベースでレアリティフィールドかどうか判定"""
        # フィールド名パターン
        name_patterns = ['rarity', 'rare', 'レア', '希少', 'star', 'grade', 'rank', 'tier']
        if any(pattern in field_name for pattern in name_patterns):
            return True
        
        # データパターン分析
        rarity_patterns = ['SR', 'SSR', 'R', 'N', 'UR', 'レア', '★', '☆', 'rare', 'common', 'super']
        for value in sample_values:
            if any(pattern in value.upper() for pattern in rarity_patterns):
                return True
        
        # 短い文字列で統一されたパターン（レアリティの特徴）
        if all(len(v) <= 5 for v in sample_values) and len(set(sample_values)) <= 10:
            return any(pattern in field_name for pattern in ['star', '星', 'level', 'grade'])
        
        return False
    
    def _is_serial_field_ai(self, field_name: str, sample_values: List[str]) -> bool:
        """AIベースでシリアル/IDフィールドかどうか判定（ネット検索照合機能付き）"""
        # フィールド名パターン
        name_patterns = ['serial', 'id', 'code', 'number', 'シリアル', '型番', '番号', 'sku', 'jan']
        name_match = any(pattern in field_name for pattern in name_patterns)
        if name_match:
            # 名前系フィールドは除外
            if not any(exclude in field_name for exclude in ['name', '名前', 'title', 'カード名']):
                return True
        
        # データパターン分析
        # 英数字の組み合わせが多い
        alphanumeric_count = sum(1 for v in sample_values if self._is_alphanumeric_serial_pattern(v))
        alphanumeric_ratio = alphanumeric_count / len(sample_values) if sample_values else 0
        
        # 統一されたフォーマット（PK001, D01001等）
        format_consistent = len(set(len(v) for v in sample_values)) <= 2 if sample_values else False
        
        # 基本的なパターンマッチング
        if alphanumeric_ratio > 0.7 or format_consistent:
            return True
        
        # カード名との照合による高度な判定（サンプルが小さく不確実な場合）
        if alphanumeric_ratio > 0.3 and hasattr(self, 'field_types') and self.field_types:  
            return self._verify_serial_with_card_name_matching(sample_values)
        
        return False
    
    def _is_alphanumeric_serial_pattern(self, value: str) -> bool:
        """文字列がシリアルっぽい英数字パターンかどうか判定"""
        if not value or len(value) < 2:
            return False
        
        # 英字と数字の両方を含む
        has_alpha = any(c.isalpha() for c in value)
        has_digit = any(c.isdigit() for c in value)
        
        # 特殊文字は少なめ
        special_chars = sum(1 for c in value if not c.isalnum() and c not in ['-', '_'])
        
        return has_alpha and has_digit and special_chars <= 2
    
    def _verify_serial_with_card_name_matching(self, sample_serials: List[str]) -> bool:
        """カード名とシリアルの照合による検証（簡易版）"""
        # 実装を簡素化：将来的にはWeb検索APIを統合
        # 今回はパターン分析に集中
        
        # シリアルっぽいパターンの追加検証
        if not sample_serials:
            return False
        
        # より厳格なシリアルパターンチェック
        serial_like_count = 0
        for serial in sample_serials:
            # 典型的なシリアルパターン
            if any([
                # PRxxx, SSRxxx, URxxxパターン
                len(serial) >= 3 and serial[:2].isalpha() and serial[2:].isdigit(),
                # Dxxxxx, Pxxxxxパターン  
                len(serial) >= 4 and serial[0].isalpha() and serial[1:].isdigit(),
                # PR001, SR123のようなパターン
                len(serial) >= 4 and serial[:2].isalpha() and serial[2:].isdigit() and len(serial) <= 8
            ]):
                serial_like_count += 1
        
        return serial_like_count > len(sample_serials) * 0.6
    
    def _is_name_field_ai(self, field_name: str, sample_values: List[str]) -> bool:
        """AIベースで名前フィールドかどうか判定"""
        name_patterns = ['name', 'title', '名前', 'カード名', 'タイトル', '商品名']
        return any(pattern in field_name for pattern in name_patterns)
    
    def _is_date_field_ai(self, field_name: str, sample_values: List[str]) -> bool:
        """AIベースで日付フィールドかどうか判定"""
        name_patterns = ['date', 'time', '日付', '時間', '発売', 'release']
        if any(pattern in field_name for pattern in name_patterns):
            return True
        
        # 日付フォーマットの検出
        import re
        date_patterns = [r'\d{4}/\d{1,2}/\d{1,2}', r'\d{8}', r'\d{4}-\d{1,2}-\d{1,2}']
        for value in sample_values:
            if any(re.match(pattern, value) for pattern in date_patterns):
                return True
        
        return False
    
    def _is_price_field_ai(self, field_name: str, sample_values: List[str]) -> bool:
        """AIベースで価格フィールドかどうか判定"""
        name_patterns = ['price', 'cost', '価格', '値段', '金額', 'yen', 'dollar']
        if any(pattern in field_name for pattern in name_patterns):
            return True
        
        # 数値のパターン
        numeric_count = sum(1 for v in sample_values if v.replace(',', '').replace('.', '').isdigit())
        return numeric_count > len(sample_values) * 0.8
    
    def _get_importance_by_type(self, field_type: str) -> float:
        """フィールドタイプに基づく重要度を返す"""
        type_importance = {
            'name': 0.9,
            'serial': 0.8,
            'rarity': 0.8,
            'date': 0.7,
            'price': 0.6,
            'other': 0.5,
            'unknown': 0.3
        }
        return type_importance.get(field_type, 0.5)
    
    def find_best_field_matches(self, headers_a: List[str], headers_b: List[str], 
                               data_a: List[Dict], data_b: List[Dict]) -> List[Tuple[str, str, float]]:
        """最適なフィールドマッチングを見つける"""
        
        # 各データセットのフィールド重要度を分析
        importance_a = self.analyze_field_importance(headers_a, data_a)
        importance_b = self.analyze_field_importance(headers_b, data_b)
        
        field_matches = []
        
        # 全フィールドペアの類似度を計算
        for field_a in headers_a:
            for field_b in headers_b:
                # フィールド名の類似度
                name_similarity = self.calculate_string_similarity(field_a, field_b)
                
                # データ内容の類似度をサンプルで確認
                content_similarity = self._calculate_content_similarity(
                    field_a, field_b, data_a, data_b
                )
                
                # 重要度を考慮した総合スコア
                importance_factor = (importance_a.get(field_a, 0.5) + importance_b.get(field_b, 0.5)) / 2
                total_score = (name_similarity * 0.4) + (content_similarity * 0.4) + (importance_factor * 0.2)
                
                if total_score > 0.3:  # 閾値以上のもののみ保持
                    field_matches.append((field_a, field_b, total_score))
        
        # スコア順でソート
        field_matches.sort(key=lambda x: x[2], reverse=True)
        
        return field_matches
    
    def _calculate_content_similarity(self, field_a: str, field_b: str, 
                                     data_a: List[Dict], data_b: List[Dict], sample_size: int = 20) -> float:
        """フィールド内容の類似度を計算"""
        
        # サンプルデータを取得
        sample_a = [row.get(field_a, '') for row in data_a[:sample_size] if str(row.get(field_a, '')).strip()]
        sample_b = [row.get(field_b, '') for row in data_b[:sample_size] if str(row.get(field_b, '')).strip()]
        
        if not sample_a or not sample_b:
            return 0.0
        
        # 各サンプル間の類似度を計算
        similarities = []
        for val_a in sample_a[:10]:  # 最大10件まで
            for val_b in sample_b[:10]:
                sim = self.calculate_string_similarity(str(val_a), str(val_b))
                if sim > 0.1:  # 極端に低い類似度は除外
                    similarities.append(sim)
        
        if similarities:
            return sum(similarities) / len(similarities)
        else:
            return 0.0
    
    def flexible_card_matching(self, data_a: List[Dict], data_b: List[Dict], 
                              headers_a: List[str], headers_b: List[str], 
                              max_comparisons: int = 10000) -> List[Dict]:
        """柔軟なカードマッチング"""
        
        logger.info(f"Starting flexible matching: A={len(data_a)}, B={len(data_b)}")
        
        # フィールドマッチングを分析
        field_matches = self.find_best_field_matches(headers_a, headers_b, data_a, data_b)
        
        logger.info(f"Found {len(field_matches)} potential field matches")
        
        # 上位のフィールドマッチングを使用
        top_field_matches = field_matches[:5]  # 上位5個まで
        
        matches = []
        comparison_count = 0
        
        # 全カードペアを比較（制限付き）
        for i, card_a in enumerate(data_a):
            if comparison_count >= max_comparisons:
                break
                
            for j, card_b in enumerate(data_b):
                if comparison_count >= max_comparisons:
                    break
                    
                comparison_count += 1
                
                # カード類似度を計算
                card_similarity = self._calculate_card_similarity(
                    card_a, card_b, top_field_matches
                )
                
                if card_similarity >= self.similarity_threshold:
                    matches.append({
                        'card_a': card_a,
                        'card_b': card_b,
                        'card_a_row': i + 2,  # CSV行番号（ヘッダー行を除いて+2）
                        'card_b_row': j + 2,  # CSV行番号（ヘッダー行を除いて+2）
                        'overall_similarity': round(card_similarity, 3),
                        'field_matches_used': top_field_matches[:3],  # 使用したフィールドマッチング
                        'similarity_details': self._build_similarity_details(
                            card_a, card_b, top_field_matches
                        )
                    })
        
        logger.info(f"Flexible matching completed: {len(matches)} matches found, {comparison_count} comparisons")
        
        return matches
    
    def _calculate_card_similarity(self, card_a: Dict, card_b: Dict, 
                                  field_matches: List[Tuple[str, str, float]]) -> float:
        """2つのカード間の類似度を計算"""
        
        total_score = 0.0
        weight_sum = 0.0
        
        for field_a, field_b, field_weight in field_matches:
            val_a = str(card_a.get(field_a, '')).strip()
            val_b = str(card_b.get(field_b, '')).strip()
            
            if val_a and val_b:
                field_similarity = self.calculate_string_similarity(val_a, val_b)
                total_score += field_similarity * field_weight
                weight_sum += field_weight
        
        if weight_sum > 0:
            return total_score / weight_sum
        else:
            return 0.0
    
    def _build_similarity_details(self, card_a: Dict, card_b: Dict, 
                                 field_matches: List[Tuple[str, str, float]]) -> List[Dict]:
        """類似度の詳細情報を構築"""
        
        details = []
        
        for field_a, field_b, field_weight in field_matches[:3]:  # 上位3個まで
            val_a = str(card_a.get(field_a, '')).strip()
            val_b = str(card_b.get(field_b, '')).strip()
            
            if val_a and val_b:
                similarity = self.calculate_string_similarity(val_a, val_b)
                details.append({
                    'field_a': field_a,
                    'field_b': field_b,
                    'value_a': val_a,
                    'value_b': val_b,
                    'similarity': round(similarity, 3),
                    'weight': round(field_weight, 3)
                })
        
        return details


def flexible_enhanced_matching(data_a: List[Dict], data_b: List[Dict], 
                             headers_a: List[str], headers_b: List[str], 
                             max_sample_size: int = 100) -> Tuple[List[Dict], Dict]:
    """
    柔軟な拡張マッチング - enhanced.pyとの互換性を保持
    """
    
    # サンプルサイズでデータを制限
    if len(data_a) > max_sample_size:
        data_a = data_a[:max_sample_size]
    if len(data_b) > max_sample_size:
        data_b = data_b[:max_sample_size]
    
    matcher = FlexibleMatcher(similarity_threshold=0.7)  # 少し閾値を下げる
    
    # 柔軟マッチングを実行
    matches = matcher.flexible_card_matching(data_a, data_b, headers_a, headers_b)
    
    # フィールドマッピング情報を生成
    field_matches = matcher.find_best_field_matches(headers_a, headers_b, data_a, data_b)
    
    enhanced_mappings = {
        'flexible_field_mappings': field_matches[:10],  # 上位10個
        'matching_strategy': 'flexible_similarity',
        'similarity_threshold': matcher.similarity_threshold,
        'total_comparisons': len(data_a) * len(data_b),
        'match_count': len(matches)
    }
    
    return matches, enhanced_mappings