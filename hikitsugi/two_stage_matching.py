"""
2段階マッチングシステム
Stage 1: 同一カード特定
Stage 2: フィールドマッピング分析
"""

import logging
from collections import defaultdict

def two_stage_matching_system(data_a, data_b, headers_a, headers_b):
    """効率的な2段階マッチングシステム"""
    logger = logging.getLogger('two_stage_matching')
    
    # ========================================
    # Stage 1: 同一カード特定
    # ========================================
    logger.info("🎯 Stage 1: 同一カード特定開始")
    
    # キーフィールドを特定
    key_fields = identify_key_fields(headers_a, headers_b)
    logger.info(f"特定されたキーフィールド: {key_fields}")
    
    # 同一カードペアを特定
    identical_card_pairs = find_identical_cards(data_a, data_b, key_fields)
    logger.info(f"✅ Stage 1完了: {len(identical_card_pairs)}組の同一カードを特定")
    
    # ========================================
    # Stage 2: フィールドマッピング分析
    # ========================================
    logger.info("🔗 Stage 2: フィールドマッピング分析開始")
    
    if not identical_card_pairs:
        logger.warning("同一カードが見つからないため、フィールドマッピングをスキップ")
        return [], []
    
    # 同一カードペアからフィールドマッピングを学習
    field_mappings = analyze_field_mappings_from_pairs(identical_card_pairs, headers_a, headers_b)
    logger.info(f"✅ Stage 2完了: {len(field_mappings)}件のフィールドマッピングを検出")
    
    return identical_card_pairs, field_mappings

def identify_key_fields(headers_a, headers_b):
    """重要フィールドを特定"""
    
    # 重要度の高いキーワード
    key_patterns = {
        'name': ['name', '名前', 'カード名', '商品名', 'title'],
        'id': ['id', 'serial', '型番', 'code', 'number', 'jan'],
        'date': ['date', '日付', '発売日', 'release', 'publish']
    }
    
    key_fields = {'a': {}, 'b': {}}
    
    # A社のキーフィールド特定
    for header in headers_a:
        header_lower = header.lower()
        for key_type, patterns in key_patterns.items():
            if any(pattern in header_lower for pattern in patterns):
                if key_type not in key_fields['a']:
                    key_fields['a'][key_type] = []
                key_fields['a'][key_type].append(header)
    
    # B社のキーフィールド特定
    for header in headers_b:
        header_lower = header.lower()
        for key_type, patterns in key_patterns.items():
            if any(pattern in header_lower for pattern in patterns):
                if key_type not in key_fields['b']:
                    key_fields['b'][key_type] = []
                key_fields['b'][key_type].append(header)
    
    return key_fields

def find_identical_cards(data_a, data_b, key_fields):
    """同一カードペアを特定"""
    
    def normalize_value(value, field_type):
        """値の正規化"""
        if not value:
            return ""
        
        value = str(value).strip().replace('\ufeff', '')
        
        if field_type == 'date':
            # 日付の正規化: 2024/1/24 → 20240124
            if '/' in value:
                parts = value.split('/')
                if len(parts) == 3:
                    year, month, day = parts
                    return f"{year.zfill(4)}{month.zfill(2)}{day.zfill(2)}"
            return value.replace('-', '').replace('/', '')
        
        elif field_type == 'name':
            # 名前の正規化
            return value.replace('＆', '&').replace('　', ' ').lower().strip()
        
        elif field_type == 'id':
            # IDの正規化
            return value.upper().strip()
        
        return value.lower().strip()
    
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
                            'value_a': val_a,
                            'value_b': val_b
                        })
        
        return score, matches
    
    # 実際のマッチング実行
    identical_pairs = []
    
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
    
    return identical_pairs

def analyze_field_mappings_from_pairs(identical_pairs, headers_a, headers_b):
    """同一カードペアからフィールドマッピングを分析"""
    
    # フィールド値の一致パターンを集計
    field_match_stats = defaultdict(lambda: {
        'exact_matches': 0,
        'total_comparisons': 0,
        'sample_pairs': []
    })
    
    for pair in identical_pairs:
        card_a = pair['card_a']
        card_b = pair['card_b']
        
        # 全フィールド組み合わせをチェック（同一カードなので効率的）
        for field_a in headers_a:
            for field_b in headers_b:
                val_a = str(card_a.get(field_a, '')).strip()
                val_b = str(card_b.get(field_b, '')).strip()
                
                field_pair = f"{field_a}→{field_b}"
                stats = field_match_stats[field_pair]
                
                stats['total_comparisons'] += 1
                
                # 値が一致するかチェック
                if val_a and val_b and normalize_for_comparison(val_a) == normalize_for_comparison(val_b):
                    stats['exact_matches'] += 1
                    
                    # サンプルペアを保存
                    if len(stats['sample_pairs']) < 3:
                        stats['sample_pairs'].append({
                            'value_a': val_a,
                            'value_b': val_b,
                            'card_a_key': card_a.get('name', ''),
                            'card_b_key': card_b.get('カード名', '')
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
                    'field_a': field_a,
                    'field_b': field_b,
                    'confidence': round(confidence, 3),
                    'sample_count': stats['exact_matches'],
                    'total_comparisons': stats['total_comparisons'],
                    'field_type': 'learned_from_identical_cards',
                    'quality_score': 'High' if confidence > 0.8 else 'Medium',
                    'sample_pairs': stats['sample_pairs']
                })
    
    # 信頼度でソート
    field_mappings.sort(key=lambda x: x['confidence'], reverse=True)
    
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

def format_results_for_display(identical_pairs, field_mappings):
    """結果を表示用にフォーマット"""
    
    # 同一カードペアのサマリー
    card_summary = []
    for i, pair in enumerate(identical_pairs[:10]):  # 上位10件
        card_a = pair['card_a']
        card_b = pair['card_b']
        
        name_a = card_a.get('name', card_a.get('serial', 'Unknown'))
        name_b = card_b.get('カード名', card_b.get('型番', 'Unknown'))
        
        card_summary.append({
            'index': i + 1,
            'name_a': name_a,
            'name_b': name_b,
            'match_score': pair['match_score'],
            'match_types': [detail['type'] for detail in pair['match_details']]
        })
    
    # フィールドマッピングのサマリー
    mapping_summary = []
    for mapping in field_mappings[:20]:  # 上位20件
        mapping_summary.append({
            'field_a': mapping['field_a'],
            'field_b': mapping['field_b'],
            'confidence': mapping['confidence'],
            'sample_count': mapping['sample_count'],
            'quality': mapping['quality_score']
        })
    
    return {
        'identical_cards': card_summary,
        'field_mappings': mapping_summary,
        'statistics': {
            'total_identical_cards': len(identical_pairs),
            'total_field_mappings': len(field_mappings),
            'high_confidence_mappings': len([m for m in field_mappings if m['confidence'] > 0.8])
        }
    }

# enhanced.pyに統合するためのラッパー関数
def enhanced_two_stage_matching(data_a, data_b, headers_a, headers_b):
    """enhanced.py用の2段階マッチング"""
    
    # 2段階マッチング実行
    identical_pairs, field_mappings = two_stage_matching_system(
        data_a, data_b, headers_a, headers_b
    )
    
    # enhanced.pyの既存形式に合わせて結果を変換
    matches = []
    for pair in identical_pairs:
        matches.append({
            'card_a': pair['card_a'],
            'card_b': pair['card_b'],
            'overall_similarity': pair['match_score'],
            'similarity_details': {
                f"{detail['field_a']}→{detail['field_b']}": 1.0
                for detail in pair['match_details']
            }
        })
    
    return matches, field_mappings