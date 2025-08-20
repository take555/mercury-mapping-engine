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
        """カード間のマッチスコア計算（カード名最優先）"""
        score = 0.0
        matches = []
        
        # カード名を最優先でチェック（A社・B社入れ替わり対応）
        name_matched = False
        fields_a_name = key_fields.get('a', {}).get('name', [])
        fields_b_name = key_fields.get('b', {}).get('name', [])
        
        for field_a in fields_a_name:
            for field_b in fields_b_name:
                val_a = normalize_value(card_a.get(field_a), 'name')
                val_b = normalize_value(card_b.get(field_b), 'name')
                
                if val_a and val_b and val_a == val_b:
                    score += 1.0  # 名前一致は100点（最重要）
                    name_matched = True
                    matches.append({
                        'type': 'name',
                        'field_a': field_a,
                        'field_b': field_b,
                        'value': val_a
                    })
                    break
            if name_matched:
                break
        
        # 名前が一致した場合のみ、日付をボーナスとして追加
        # 注意: IDフィールドは判定結果として決定されるため、マッチング判定には使用しない
        if name_matched:
            for key_type in ['date']:
                fields_a = key_fields.get('a', {}).get(key_type, [])
                fields_b = key_fields.get('b', {}).get(key_type, [])
                
                for field_a in fields_a:
                    for field_b in fields_b:
                        val_a = normalize_value(card_a.get(field_a), key_type)
                        val_b = normalize_value(card_b.get(field_b), key_type)
                        
                        if val_a and val_b and val_a == val_b:
                            # ボーナス点を追加
                            if key_type == 'date':
                                score += 0.1   # 日付ボーナス: 10点
                            
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
            
            # スコア1.0以上を同一カードとして判定（カード名必須）
            if score >= 1.0:
                identical_pairs.append({
                    'card_a': card_a,
                    'card_b': card_b,
                    'match_score': round(score, 3),
                    'match_details': match_details
                })
    
    logger.info(f"同一カード特定完了: {len(identical_pairs)}組")
    
    # データ管理粒度の違いに対応：同一カードの統合
    consolidated_pairs = consolidate_identical_cards(identical_pairs, logger)
    logger.info(f"カード統合後: {len(consolidated_pairs)}組")
    
    return consolidated_pairs

def consolidate_identical_cards(identical_pairs, logger):
    """同一カードの統合（データ管理粒度の違いに対応）"""
    from collections import defaultdict
    
    # カード名でグループ化
    card_groups = defaultdict(list)
    
    for pair in identical_pairs:
        # カード名を取得（A社・B社のどちらからでも）
        card_a = pair['card_a']
        card_b = pair['card_b']
        
        # カード名の候補フィールドを試行
        name_candidates_a = ['カード名', 'name', '商品名', 'title', 'product']
        name_candidates_b = ['name', 'name_short', 'カード名', '商品名', 'title']
        
        card_name = None
        for field in name_candidates_a:
            if field in card_a and card_a[field]:
                card_name = str(card_a[field]).strip()
                break
        
        if not card_name:
            for field in name_candidates_b:
                if field in card_b and card_b[field]:
                    card_name = str(card_b[field]).strip()
                    break
        
        if card_name:
            # 正規化したカード名でグループ化
            normalized_name = normalize_value(card_name, 'name')
            card_groups[normalized_name].append(pair)
    
    consolidated_pairs = []
    
    for normalized_name, group in card_groups.items():
        if len(group) == 1:
            # グループに1つだけの場合はそのまま追加
            consolidated_pairs.append(group[0])
        else:
            # 複数ある場合は最も高いスコアのペアを代表として選択
            best_pair = max(group, key=lambda x: x['match_score'])
            logger.info(f"カード '{normalized_name}' の{len(group)}件を統合 → 最高スコア{best_pair['match_score']}")
            consolidated_pairs.append(best_pair)
    
    return consolidated_pairs

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
                
                # IDフィールドかどうかを判定
                field_a_clean = field_a.replace('\ufeff', '').strip()
                field_b_clean = field_b.replace('\ufeff', '').strip()
                is_id_field = is_id_field_mapping(field_a_clean, field_b_clean)
                
                field_mappings.append({
                    'field_a': field_a_clean,
                    'field_b': field_b_clean,
                    'confidence': round(confidence, 3),
                    'sample_count': stats['exact_matches'],
                    'total_comparisons': stats['total_comparisons'],
                    'field_type': 'id_mapping' if is_id_field else 'learned_from_identical_cards',
                    'quality_score': 'ID_Field' if is_id_field else ('High' if confidence > 0.8 else 'Medium'),
                    'sample_values': stats['sample_values'],
                    'is_id_field': is_id_field
                })
    
    # 信頼度でソート
    field_mappings.sort(key=lambda x: x['confidence'], reverse=True)
    
    logger.info(f"フィールドマッピング学習完了: {len(field_mappings)}件")
    
    # 共起パターン分析を追加実行（テスト）
    cooccurrence_mappings = analyze_cooccurrence_patterns(identical_pairs, headers_a, headers_b, logger)
    
    # 既存マッピングと共起マッピングを統合
    enhanced_mappings = merge_mappings(field_mappings, cooccurrence_mappings, logger)
    
    return enhanced_mappings

def is_id_field_mapping(field_a, field_b):
    """IDフィールドマッピングかどうかを判定"""
    id_patterns = [
        'id', 'ID', 'Id',
        'serial', 'Serial', 'SERIAL',
        '型番', '棚番', 'コード', 'code', 'Code', 'CODE',
        'number', 'Number', 'NUMBER', 'No', 'no', 'NO',
        'jan', 'JAN', 'sku', 'SKU',
        'product_id', 'item_id', 'card_id',
        'product_code', 'item_code', 'card_code'
    ]
    
    # フィールド名にIDパターンが含まれているかチェック
    field_a_lower = field_a.lower()
    field_b_lower = field_b.lower()
    
    for pattern in id_patterns:
        pattern_lower = pattern.lower()
        if pattern_lower in field_a_lower or pattern_lower in field_b_lower:
            return True
    
    return False

def analyze_cooccurrence_patterns(identical_pairs, headers_a, headers_b, logger):
    """同一カードペア間での値共起パターン分析"""
    import math
    from collections import defaultdict, Counter
    
    logger.info("🔍 共起パターン分析開始...")
    
    cooccurrence_stats = {}
    
    for field_a in headers_a:
        for field_b in headers_b:
            # 値ペアを収集
            value_pairs = []
            valid_pairs = 0
            
            for pair in identical_pairs:
                val_a = str(pair['card_a'].get(field_a, '')).strip()
                val_b = str(pair['card_b'].get(field_b, '')).strip()
                
                # 空でない値のペアのみ収集
                if val_a and val_b and val_a != 'N/A' and val_b != 'N/A':
                    value_pairs.append((val_a, val_b))
                    valid_pairs += 1
            
            # サンプルがある場合のみ分析（テスト用に閾値を1に）
            if valid_pairs >= 1:
                mutual_info = calculate_mutual_information(value_pairs)
                unique_patterns = len(set(value_pairs))
                
                cooccurrence_stats[f"{field_a}→{field_b}"] = {
                    'field_a': field_a,
                    'field_b': field_b,
                    'mutual_information': mutual_info,
                    'sample_count': valid_pairs,
                    'unique_patterns': unique_patterns,
                    'pattern_diversity': unique_patterns / valid_pairs,
                    'top_patterns': Counter(value_pairs).most_common(3)
                }
    
    # 相互情報量でソートして上位を取得
    sorted_stats = sorted(cooccurrence_stats.items(), 
                         key=lambda x: x[1]['mutual_information'], reverse=True)
    
    cooccurrence_mappings = []
    for field_pair, stats in sorted_stats[:20]:  # 上位20件
        # 相互情報量を信頼度に変換（0-1スケール）
        confidence = min(stats['mutual_information'] / 2.0, 1.0)
        
        if confidence > 0.3:  # 閾値0.3以上のみ採用
            cooccurrence_mappings.append({
                'field_a': stats['field_a'],
                'field_b': stats['field_b'],
                'confidence': round(confidence, 3),
                'sample_count': stats['sample_count'],
                'total_comparisons': stats['sample_count'],
                'field_type': 'cooccurrence_pattern',
                'quality_score': 'Cooccurrence',
                'mutual_information': round(stats['mutual_information'], 3),
                'pattern_diversity': round(stats['pattern_diversity'], 3),
                'top_patterns': stats['top_patterns']
            })
    
    logger.info(f"✅ 共起パターン分析完了: {len(cooccurrence_mappings)}件検出")
    return cooccurrence_mappings

def calculate_mutual_information(value_pairs):
    """相互情報量を計算"""
    if not value_pairs:
        return 0.0
    
    from collections import Counter
    import math
    
    # 値ペアの頻度カウント
    pair_counts = Counter(value_pairs)
    total_pairs = len(value_pairs)
    
    # 個別値の頻度カウント
    values_a = [pair[0] for pair in value_pairs]
    values_b = [pair[1] for pair in value_pairs]
    counts_a = Counter(values_a)
    counts_b = Counter(values_b)
    
    # 相互情報量計算
    mutual_info = 0.0
    for (val_a, val_b), joint_count in pair_counts.items():
        p_joint = joint_count / total_pairs
        p_a = counts_a[val_a] / total_pairs
        p_b = counts_b[val_b] / total_pairs
        
        if p_joint > 0:
            mutual_info += p_joint * math.log2(p_joint / (p_a * p_b))
    
    return max(0.0, mutual_info)

def merge_mappings(field_mappings, cooccurrence_mappings, logger):
    """既存マッピングと共起マッピングを統合"""
    existing_pairs = set(f"{m['field_a']}→{m['field_b']}" for m in field_mappings)
    
    # 新しく発見された共起パターン
    new_mappings = []
    for mapping in cooccurrence_mappings:
        pair_key = f"{mapping['field_a']}→{mapping['field_b']}"
        if pair_key not in existing_pairs:
            new_mappings.append(mapping)
            logger.info(f"🆕 新発見: {mapping['field_a']} ↔ {mapping['field_b']} "
                       f"(信頼度: {mapping['confidence']}, 相互情報量: {mapping['mutual_information']})")
    
    # 統合してソート
    all_mappings = field_mappings + new_mappings
    all_mappings.sort(key=lambda x: x['confidence'], reverse=True)
    
    return all_mappings

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