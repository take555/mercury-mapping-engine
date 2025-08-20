import re
from datetime import datetime
import logging

def smart_card_matching(data_a, data_b, headers_a, headers_b):
    """賢いカードマッチングロジック"""
    logger = logging.getLogger('smart_matching')
    
    # キーフィールドマッピング定義
    key_field_mappings = {
        'name_fields': {
            'a': ['name', 'name_short', 'pos_en_name'],
            'b': ['カード名', 'カード名カナ']
        },
        'id_fields': {
            'a': ['serial', 'id'],
            'b': ['型番', '自社型番']
        },
        'date_fields': {
            'a': ['releace_date'],
            'b': ['発売日']
        },
        'series_fields': {
            'a': ['series'],
            'b': ['シリーズ']
        }
    }
    
    def normalize_date(date_str):
        """日付を正規化"""
        if not date_str:
            return ""
        
        date_str = str(date_str).strip()
        
        # YYYY/M/D → YYYYMMDD
        if '/' in date_str:
            try:
                parts = date_str.split('/')
                if len(parts) == 3:
                    year, month, day = parts
                    return f"{year.zfill(4)}{month.zfill(2)}{day.zfill(2)}"
            except:
                pass
        
        # YYYYMMDD形式はそのまま
        if re.match(r'^\d{8}$', date_str):
            return date_str
        
        return date_str
    
    def normalize_text(text):
        """テキストを正規化"""
        if not text:
            return ""
        
        text = str(text).strip()
        # 全角・半角統一
        text = text.replace('＆', '&').replace('　', ' ')
        # 特殊文字除去
        text = re.sub(r'[^\w\s&・]', '', text)
        return text.lower()
    
    def extract_field_value(card, field_list):
        """カードから指定フィールドの値を抽出"""
        for field in field_list:
            if field in card and card[field]:
                return str(card[field]).strip()
        return ""
    
    def calculate_card_similarity(card_a, card_b):
        """カード間の類似度を計算"""
        similarity_score = 0.0
        matches = []
        
        # 1. 名前の比較（最重要）
        name_a = extract_field_value(card_a, key_field_mappings['name_fields']['a'])
        name_b = extract_field_value(card_b, key_field_mappings['name_fields']['b'])
        
        if name_a and name_b:
            name_a_norm = normalize_text(name_a)
            name_b_norm = normalize_text(name_b)
            
            if name_a_norm == name_b_norm:
                similarity_score += 0.4  # 40点
                matches.append(('name_exact', name_a, name_b, 1.0))
            elif name_a_norm in name_b_norm or name_b_norm in name_a_norm:
                similarity_score += 0.3  # 30点
                matches.append(('name_partial', name_a, name_b, 0.75))
        
        # 2. ID/型番の比較（最重要）
        id_a = extract_field_value(card_a, key_field_mappings['id_fields']['a'])
        id_b = extract_field_value(card_b, key_field_mappings['id_fields']['b'])
        
        if id_a and id_b:
            if id_a == id_b:
                similarity_score += 0.4  # 40点
                matches.append(('id_exact', id_a, id_b, 1.0))
            elif id_a in id_b or id_b in id_a:
                similarity_score += 0.2  # 20点
                matches.append(('id_partial', id_a, id_b, 0.5))
        
        # 3. 発売日の比較
        date_a = extract_field_value(card_a, key_field_mappings['date_fields']['a'])
        date_b = extract_field_value(card_b, key_field_mappings['date_fields']['b'])
        
        if date_a and date_b:
            date_a_norm = normalize_date(date_a)
            date_b_norm = normalize_date(date_b)
            
            if date_a_norm == date_b_norm:
                similarity_score += 0.15  # 15点
                matches.append(('date_exact', date_a, date_b, 1.0))
        
        # 4. シリーズの比較
        series_a = extract_field_value(card_a, key_field_mappings['series_fields']['a'])
        series_b = extract_field_value(card_b, key_field_mappings['series_fields']['b'])
        
        if series_a and series_b:
            series_a_norm = normalize_text(series_a)
            series_b_norm = normalize_text(series_b)
            
            if series_a_norm == series_b_norm:
                similarity_score += 0.05  # 5点
                matches.append(('series_exact', series_a, series_b, 1.0))
        
        return similarity_score, matches
    
    # 実際のマッチング実行
    logger.info(f"🎯 賢いカードマッチング開始: {len(data_a)}×{len(data_b)}行")
    
    card_matches = []
    field_mappings = {}
    
    for i, card_a in enumerate(data_a):
        for j, card_b in enumerate(data_b):
            similarity_score, match_details = calculate_card_similarity(card_a, card_b)
            
            # 類似度が60%以上の場合にマッチとして記録
            if similarity_score >= 0.6:
                match = {
                    'card_a': card_a,
                    'card_b': card_b,
                    'overall_similarity': round(similarity_score, 3),
                    'match_details': match_details,
                    'confidence': 'high' if similarity_score >= 0.8 else 'medium'
                }
                card_matches.append(match)
                
                # フィールドマッピングを記録
                for match_type, val_a, val_b, field_sim in match_details:
                    if match_type == 'name_exact' or match_type == 'name_partial':
                        field_mappings['name→カード名'] = field_mappings.get('name→カード名', 0) + field_sim
                    elif match_type == 'id_exact' or match_type == 'id_partial':
                        field_mappings['serial→型番'] = field_mappings.get('serial→型番', 0) + field_sim
                    elif match_type == 'date_exact':
                        field_mappings['releace_date→発売日'] = field_mappings.get('releace_date→発売日', 0) + field_sim
                    elif match_type == 'series_exact':
                        field_mappings['series→シリーズ'] = field_mappings.get('series→シリーズ', 0) + field_sim
    
    # フィールドマッピングの信頼度を計算
    enhanced_mappings = []
    for field_pair, total_sim in field_mappings.items():
        field_a, field_b = field_pair.split('→')
        confidence = min(1.0, total_sim / len(card_matches)) if card_matches else 0.0
        
        enhanced_mappings.append({
            'field_a': field_a,
            'field_b': field_b,
            'confidence': round(confidence, 3),
            'sample_count': len([m for m in card_matches if any(
                field_pair in f"{detail[0]}" for detail in m['match_details']
            )]),
            'field_type': 'smart_detected',
            'quality_score': 'High' if confidence > 0.8 else 'Medium' if confidence > 0.5 else 'Low'
        })
    
    logger.info(f"✅ 賢いマッチング完了: {len(card_matches)}件のカードマッチ, {len(enhanced_mappings)}件のフィールドマッピング")
    
    # 結果の詳細ログ
    for i, match in enumerate(card_matches[:5]):  # 上位5件を表示
        logger.info(f"   マッチ{i+1}: {match['overall_similarity']:.3f} - {match['confidence']}")
        name_a = extract_field_value(match['card_a'], key_field_mappings['name_fields']['a'])
        name_b = extract_field_value(match['card_b'], key_field_mappings['name_fields']['b'])
        logger.info(f"     A社: {name_a} | B社: {name_b}")
    
    return card_matches, enhanced_mappings

def apply_smart_matching_to_enhanced():
    """enhanced.pyに賢いマッチングを適用するコード例"""
    
    # enhanced.pyのStep 4部分を以下に置き換え
    replacement_code = '''
    # Step 4: 賢いカードマッチング実行
    emergency_logger.info("🧠 Step 4: 賢いカードマッチング開始")
    step4_start = time.time()
    
    try:
        data_a = analysis_a.get('full_data', analysis_a['sample_data'])
        data_b = analysis_b.get('full_data', analysis_b['sample_data'])
        
        # サンプルサイズ制限
        if len(data_a) > max_sample_size:
            data_a = data_a[:max_sample_size]
        if len(data_b) > max_sample_size:
            data_b = data_b[:max_sample_size]
        
        emergency_logger.info(f"   - 実際の処理データ: A社{len(data_a)}行, B社{len(data_b)}行")
        
        # 賢いマッチング実行
        matches, enhanced_mappings = smart_card_matching(
            data_a, data_b, 
            analysis_a['headers'], analysis_b['headers']
        )
        
        step4_time = time.time() - step4_start
        emergency_logger.info(f"✅ 賢いカードマッチング完了 ({step4_time:.2f}秒)")
        emergency_logger.info(f"🎯 結果: {len(matches)}件のマッチ, {len(enhanced_mappings)}件のマッピング")
        
        card_analysis_success = True
        
    except Exception as e:
        emergency_logger.error(f"❌ 賢いマッチングエラー: {e}")
        matches = []
        enhanced_mappings = []
        card_analysis_success = False
        card_analysis_error = str(e)
    '''
    
    return replacement_code