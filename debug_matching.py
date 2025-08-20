#!/usr/bin/env python3
"""
2段階マッチングシステムのデバッグスクリプト
なぜマッチ数が2件しかないのかを調査
"""

import sys
import csv
import logging
from pathlib import Path

# プロジェクトのパスを追加
sys.path.insert(0, '/home/aktk/Projects/docker-projects/mercury-mapping-engine/python')

# ロガー設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from core.two_stage_matching import identify_key_fields, find_identical_cards, normalize_value

def load_csv_debug(filepath):
    """CSVファイルを読み込んでデバッグ情報を表示"""
    data = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            data.append(row)
    return headers, data

def debug_matching():
    print("=" * 80)
    print("🔍 2段階マッチングシステム デバッグ開始")
    print("=" * 80)
    
    # テストデータ読み込み
    file_a = '/home/aktk/Projects/docker-projects/mercury-mapping-engine/hikitsugi/Youyadatasample.csv'
    file_b = '/home/aktk/Projects/docker-projects/mercury-mapping-engine/hikitsugi/Tay2datasample.csv'
    
    headers_a, data_a = load_csv_debug(file_a)
    headers_b, data_b = load_csv_debug(file_b)
    
    print(f"📊 データ概要:")
    print(f"   A社: {len(headers_a)}フィールド, {len(data_a)}行")
    print(f"   B社: {len(headers_b)}フィールド, {len(data_b)}行")
    
    # 500件に制限（Web設定と同じ）
    data_a_limited = data_a[:500]
    data_b_limited = data_b[:500]
    
    print(f"📊 制限後データ:")
    print(f"   A社: {len(data_a_limited)}行")
    print(f"   B社: {len(data_b_limited)}行")
    
    # キーフィールド特定
    print(f"\n🔍 Step 1: キーフィールド特定")
    key_fields = identify_key_fields(headers_a, headers_b)
    
    print(f"   A社キーフィールド: {key_fields.get('a', {})}")
    print(f"   B社キーフィールド: {key_fields.get('b', {})}")
    
    # 手動で名前フィールドの内容確認
    print(f"\n🔍 Step 2: 名前フィールドの内容確認")
    
    # A社の名前フィールド候補
    name_fields_a = key_fields.get('a', {}).get('name', [])
    if name_fields_a:
        sample_names_a = []
        for i, row in enumerate(data_a_limited[:10]):
            for field in name_fields_a:
                if field in row and row[field]:
                    sample_names_a.append(f"行{i+1}: {field}='{row[field]}'")
                    break
        print(f"   A社名前サンプル: {sample_names_a[:5]}")
    
    # B社の名前フィールド候補  
    name_fields_b = key_fields.get('b', {}).get('name', [])
    if name_fields_b:
        sample_names_b = []
        for i, row in enumerate(data_b_limited[:10]):
            for field in name_fields_b:
                if field in row and row[field]:
                    sample_names_b.append(f"行{i+1}: {field}='{row[field]}'")
                    break
        print(f"   B社名前サンプル: {sample_names_b[:5]}")
    
    # 実際のマッチング実行（デバッグ版）
    print(f"\n🔍 Step 3: マッチングデバッグ実行")
    
    def debug_matching_process(data_a, data_b, key_fields):
        """デバッグ版マッチング処理"""
        matches = []
        debug_info = []
        
        for i, card_a in enumerate(data_a[:20]):  # 最初の20件のみデバッグ
            for j, card_b in enumerate(data_b[:20]):
                score = 0.0
                match_details = []
                
                # 名前での比較
                for key_type in ['name', 'id', 'date']:
                    fields_a = key_fields.get('a', {}).get(key_type, [])
                    fields_b = key_fields.get('b', {}).get(key_type, [])
                    
                    for field_a in fields_a:
                        for field_b in fields_b:
                            val_a = normalize_value(card_a.get(field_a), key_type)
                            val_b = normalize_value(card_b.get(field_b), key_type)
                            
                            if val_a and val_b and val_a == val_b:
                                if key_type == 'name':
                                    score += 0.5
                                elif key_type == 'id':
                                    score += 0.4
                                elif key_type == 'date':
                                    score += 0.1
                                
                                match_details.append({
                                    'type': key_type,
                                    'field_a': field_a,
                                    'field_b': field_b,
                                    'value_a': val_a,
                                    'value_b': val_b
                                })
                                break
                
                # デバッグ情報記録
                if score > 0:  # 何らかのマッチがある場合
                    debug_info.append({
                        'i': i, 'j': j,
                        'score': score,
                        'details': match_details,
                        'card_a_sample': {k: v for k, v in list(card_a.items())[:3]},
                        'card_b_sample': {k: v for k, v in list(card_b.items())[:3]}
                    })
                
                if score >= 0.8:
                    matches.append({
                        'card_a': card_a,
                        'card_b': card_b,
                        'match_score': round(score, 3),
                        'match_details': match_details
                    })
        
        return matches, debug_info
    
    matches, debug_info = debug_matching_process(data_a_limited, data_b_limited, key_fields)
    
    print(f"\n📊 デバッグ結果:")
    print(f"   最終マッチ数: {len(matches)}件 (閾値0.8以上)")
    print(f"   部分マッチ数: {len(debug_info)}件 (スコア>0)")
    
    # デバッグ情報の詳細表示
    if debug_info:
        print(f"\n🔍 部分マッチの詳細 (上位10件):")
        for i, info in enumerate(debug_info[:10], 1):
            print(f"   {i}. スコア:{info['score']:.3f} A行{info['i']+1}×B行{info['j']+1}")
            print(f"      マッチ詳細: {info['details']}")
            if info['score'] >= 0.8:
                print(f"      → ✅ 最終マッチに含まれる")
            else:
                print(f"      → ❌ 閾値0.8未満のため除外")
    
    # 最終マッチの詳細
    if matches:
        print(f"\n✅ 最終マッチの詳細:")
        for i, match in enumerate(matches, 1):
            print(f"   {i}. スコア: {match['match_score']}")
            print(f"      マッチ詳細: {match['match_details']}")
    
    # 名前での単純マッチング確認
    print(f"\n🔍 Step 4: 名前での単純マッチング確認")
    simple_name_matches = 0
    
    if name_fields_a and name_fields_b:
        for card_a in data_a_limited[:50]:
            for card_b in data_b_limited[:50]:
                for field_a in name_fields_a[:1]:  # 最初の名前フィールドのみ
                    for field_b in name_fields_b[:1]:
                        name_a = normalize_value(card_a.get(field_a), 'name')
                        name_b = normalize_value(card_b.get(field_b), 'name')
                        
                        if name_a and name_b and name_a == name_b:
                            simple_name_matches += 1
                            if simple_name_matches <= 5:
                                print(f"   名前マッチ{simple_name_matches}: '{name_a}' = '{name_b}'")
    
    print(f"   単純名前マッチ総数: {simple_name_matches}件")
    
    print("=" * 80)
    print("🏁 デバッグ完了")
    print("=" * 80)

if __name__ == "__main__":
    debug_matching()