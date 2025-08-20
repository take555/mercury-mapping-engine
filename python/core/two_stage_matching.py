"""
2段階マッチングシステム
Stage 1: 同一カード特定
Stage 2: フィールドマッピング分析
"""

import time
import logging
from collections import defaultdict
import re

# ===============================================
# Stage 1: 同一カード特定システム
# ===============================================

def identify_key_fields(headers_a, headers_b):
    """重要フィールドを自動特定"""
    key_patterns = {
        'name': ['name', '名前', 'カード名', '商品名', 'title', 'product'],
        'id': ['id', 'serial', '型番', 'code', 'number', 'jan', 'sku'],
        'date': ['date', '日付', '発売日', 'release', 'publish', 'launch']
    }
    
    key_fields = {'a': {}, 'b': {}}
    
    for header in headers_a:
        header_lower = header.lower()
        for key_type, patterns in key_patterns.items():
            if any(pattern in header_lower for pattern in patterns):
                if key_type not in key_fields['a']:
                    key_fields['a'][key_type] = []
                key_fields['a'][key_type].append(header)
    
    for header in headers_b:
        header_lower = header.lower()
        for key_type, patterns in key_patterns.items():
            if any(pattern in header_lower for pattern in patterns):
                if key_type not in key_fields['b']:
                    key_fields['b'][key_type] = []
                key_fields['b'][key_type].append(header)
    
    return key_fields

def normalize_value(value, field_type):
    """値の正規化処理"""
    if not value:
        return ""
    
    value = str(value).strip().replace('\ufeff', '')
    
    if field_type == 'date':
        # 日付の正規化: 2024/1/24 → 20240124
        if '/' in value:
            parts = value.split('/')
            if len(parts) == 3 and all(p.isdigit() for p in parts):
                year, month, day = parts
                return f"{year.zfill(4)}{month.zfill(2)}{day.zfill(2)}"
        return value.replace('-', '').replace('/', '').replace(' ', '')
    
    elif field_type == 'name':
        # 名前の正規化: 記号統一、大小文字統一
        return value.replace('＆', '&').replace('　', ' ').lower().strip()
    
    elif field_type == 'id':
        # IDの正規化: 大文字統一、空白除去
        return value.upper().strip().replace(' ', '')
    
    return value.lower().strip()

def find_identical_cards(data_a, data_b, key_fields):
    """同一カードペアを特定"""
    logger = logging.getLogger('identical_cards')
    
    def calculate_match_score(card_a, card_b):
        """カード間のマッチスコア計算"""
        score = 0.0
        matches = []
        
        # 各キータイプでのマッチング確認
        for key_type in ['name', 'id', 'date']:
            fields_a = key_fields.get('a', {}).get(key_type, [])
            fields_b = key_fields.get('b', {}).get(key_type, [])
            
            for field_a in fields_a:
                for field_b in fields_b:
                    val_a = normalize_value(card_a.get(field_a), key_type)
                    val_b = normalize_value(card_b.get(field_b), key_type)
                    
                    if val_a and val_b and val_a == val_b:
                        # 重要度に応じてスコア加算
                        if key_type == 'name':
                            score += 0.5  # 名前は50点
                        elif key_type == 'id':
                            score += 0.4   # IDは40点
                        elif key_type == 'date':
                            score += 0.1   # 日付は10点
                        
                        matches.append({
                            'type': key_type,
                            'field_a': field_a,
                            'field_b': field_b,
                            'value': val_a
                        })
                        break  # 同タイプで複数マッチしても1回のみカウント
        
        return score, matches
    
    # 実際のマッチング実行
    identical_pairs = []
    logger.info(f"同一カード特定開始: {len(data_a)}×{len(data_b)}行")
    
    for card_a in data_a:
        for card_b in data_b:
            score, match_details = calculate_match_score(card_a, card_b)
            
            # スコア0.8以上を同一カードとして判定
            if score >= 0.8:
                identical_pairs.append({
                    'card_a': card_a,
                    'card_b': card_b,
                    'match_score': round(score, 3),
                    'match_details': match_details
                })
    
    logger.info(f"同一カード特定完了: {len(identical_pairs)}組")
    return identical_pairs

# ===============================================
# Stage 2: フィールドマッピング学習システム
# ===============================================

def analyze_field_mappings_from_pairs(identical_pairs, headers_a, headers_b):
    """同一カードペアからフィールドマッピングを学習"""
    logger = logging.getLogger('field_mapping')
    
    # フィールド値の一致パターンを集計
    field_match_stats = defaultdict(lambda: {
        'exact_matches': 0,
        'total_comparisons': 0,
        'sample_values': []
    })
    
    logger.info(f"フィールドマッピング学習開始: {len(identical_pairs)}組のペア")
    
    for pair in identical_pairs:
        card_a = pair['card_a']
        card_b = pair['card_b']
        
        # 全フィールド組み合わせをチェック（同一カードペアなので効率的）
        for field_a in headers_a:
            for field_b in headers_b:
                val_a = str(card_a.get(field_a, '')).strip()
                val_b = str(card_b.get(field_b, '')).strip()
                
                field_pair = f"{field_a}→{field_b}"
                stats = field_match_stats[field_pair]
                
                stats['total_comparisons'] += 1
                
                # 値が一致するかチェック（正規化後）
                if val_a and val_b:
                    val_a_norm = normalize_for_comparison(val_a)
                    val_b_norm = normalize_for_comparison(val_b)
                    
                    if val_a_norm == val_b_norm:
                        stats['exact_matches'] += 1
                        
                        # サンプル値を保存
                        if len(stats['sample_values']) < 3:
                            stats['sample_values'].append({
                                'original_a': val_a,
                                'original_b': val_b,
                                'normalized': val_a_norm
                            })
    
    # 信頼度の高いマッピングのみを抽出
    field_mappings = []
    
    for field_pair, stats in field_match_stats.items():
        if stats['total_comparisons'] > 0:
            confidence = stats['exact_matches'] / stats['total_comparisons']
            
            # 信頼度50%以上のマッピングのみ採用
            if confidence >= 0.5:
                field_a, field_b = field_pair.split('→')
                
                field_mappings.append({
                    'field_a': field_a.replace('\ufeff', '').strip(),
                    'field_b': field_b.replace('\ufeff', '').strip(),
                    'confidence': round(confidence, 3),
                    'sample_count': stats['exact_matches'],
                    'total_comparisons': stats['total_comparisons'],
                    'field_type': 'learned_from_identical_cards',
                    'quality_score': 'High' if confidence > 0.8 else 'Medium',
                    'sample_values': stats['sample_values']
                })
    
    # 信頼度でソート
    field_mappings.sort(key=lambda x: x['confidence'], reverse=True)
    
    logger.info(f"フィールドマッピング学習完了: {len(field_mappings)}件")
    return field_mappings

def normalize_for_comparison(value):
    """比較用の値正規化"""
    if not value:
        return ""
    
    value = str(value).strip().replace('\ufeff', '')
    
    # 日付正規化
    if '/' in value and len(value.split('/')) == 3:
        parts = value.split('/')
        if len(parts) == 3 and all(p.isdigit() for p in parts):
            year, month, day = parts
            return f"{year.zfill(4)}{month.zfill(2)}{day.zfill(2)}"
    
    # 一般的な正規化
    return value.replace('＆', '&').replace('　', ' ').lower().strip()

# ===============================================
# メイン処理：2段階マッチングシステム
# ===============================================

def two_stage_matching_system(data_a, data_b, headers_a, headers_b):
    """効率的な2段階マッチングシステム"""
    logger = logging.getLogger('two_stage_matching')
    start_time = time.time()
    
    logger.info("=" * 50)
    logger.info("🚀 2段階マッチングシステム開始")
    logger.info("=" * 50)
    
    # Stage 1: 同一カード特定
    logger.info("🎯 Stage 1: 同一カード特定")
    stage1_start = time.time()
    
    key_fields = identify_key_fields(headers_a, headers_b)
    logger.info(f"特定されたキーフィールド: {key_fields}")
    
    identical_pairs = find_identical_cards(data_a, data_b, key_fields)
    
    stage1_time = time.time() - stage1_start
    logger.info(f"✅ Stage 1完了: {len(identical_pairs)}組 ({stage1_time:.2f}秒)")
    
    if not identical_pairs:
        logger.warning("同一カードが見つからないため、従来の処理にフォールバック")
        return [], []
    
    # Stage 2: フィールドマッピング分析
    logger.info("🔗 Stage 2: フィールドマッピング分析")
    stage2_start = time.time()
    
    field_mappings = analyze_field_mappings_from_pairs(identical_pairs, headers_a, headers_b)
    
    stage2_time = time.time() - stage2_start
    logger.info(f"✅ Stage 2完了: {len(field_mappings)}件 ({stage2_time:.2f}秒)")
    
    # 結果サマリー
    total_time = time.time() - start_time
    logger.info("=" * 50)
    logger.info(f"🏁 2段階マッチング完了: {total_time:.2f}秒")
    logger.info(f"📊 結果サマリー:")
    logger.info(f"   - 同一カード: {len(identical_pairs)}組")
    logger.info(f"   - フィールドマッピング: {len(field_mappings)}件")
    logger.info(f"   - 高信頼度マッピング: {len([m for m in field_mappings if m['confidence'] > 0.8])}件")
    logger.info("=" * 50)
    
    return identical_pairs, field_mappings

# ===============================================
# enhanced.py統合用ラッパー関数
# ===============================================

def enhanced_two_stage_matching(data_a, data_b, headers_a, headers_b, max_sample_size=100):
    """enhanced.py用の2段階マッチング"""
    logger = logging.getLogger('enhanced_matching')
    
    # データサイズ制限
    if len(data_a) > max_sample_size:
        data_a = data_a[:max_sample_size]
        logger.info(f"A社データを{max_sample_size}件に制限")
    
    if len(data_b) > max_sample_size:
        data_b = data_b[:max_sample_size]
        logger.info(f"B社データを{max_sample_size}件に制限")
    
    # 2段階マッチング実行
    identical_pairs, field_mappings = two_stage_matching_system(
        data_a, data_b, headers_a, headers_b
    )
    
    # enhanced.pyの既存形式に合わせて結果を変換
    matches = []
    for pair in identical_pairs:
        similarity_details = {}
        for detail in pair['match_details']:
            field_pair = f"{detail['field_a']}→{detail['field_b']}"
            similarity_details[field_pair] = 1.0
        
        matches.append({
            'card_a': pair['card_a'],
            'card_b': pair['card_b'],
            'overall_similarity': pair['match_score'],
            'similarity_details': similarity_details
        })
    
    return matches, field_mappings