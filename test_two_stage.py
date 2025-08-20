#!/usr/bin/env python3
"""
2段階マッチングシステムのテストスクリプト
"""

import sys
import csv
import logging
import time
from pathlib import Path

# プロジェクトのパスを追加
sys.path.insert(0, '/home/aktk/Projects/docker-projects/mercury-mapping-engine/python')

# ロガー設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# 2段階マッチングをインポート
from core.two_stage_matching import enhanced_two_stage_matching

def load_csv(filepath):
    """CSVファイルを読み込む"""
    data = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            data.append(row)
    return headers, data

def main():
    print("=" * 60)
    print("🚀 2段階マッチングシステム テスト開始")
    print("=" * 60)
    
    # テストデータのパス
    file_a = '/home/aktk/Projects/docker-projects/mercury-mapping-engine/hikitsugi/Youyadatasample.csv'
    file_b = '/home/aktk/Projects/docker-projects/mercury-mapping-engine/hikitsugi/Tay2datasample.csv'
    
    # CSVデータ読み込み
    print("\n📁 CSVファイル読み込み中...")
    headers_a, data_a = load_csv(file_a)
    headers_b, data_b = load_csv(file_b)
    
    print(f"✅ A社データ: {len(headers_a)}フィールド, {len(data_a)}行")
    print(f"   ヘッダー: {headers_a[:5]}...")
    print(f"✅ B社データ: {len(headers_b)}フィールド, {len(data_b)}行")
    print(f"   ヘッダー: {headers_b[:5]}...")
    
    # サンプルデータ表示
    if data_a:
        print(f"\n📊 A社サンプルデータ (1行目):")
        for key, value in list(data_a[0].items())[:5]:
            print(f"   {key}: {value}")
    
    if data_b:
        print(f"\n📊 B社サンプルデータ (1行目):")
        for key, value in list(data_b[0].items())[:5]:
            print(f"   {key}: {value}")
    
    # 2段階マッチング実行
    print("\n" + "=" * 60)
    print("🎯 2段階マッチングシステム実行")
    print("=" * 60)
    
    start_time = time.time()
    
    # 最大100行に制限してテスト
    matches, field_mappings = enhanced_two_stage_matching(
        data_a[:100], 
        data_b[:100], 
        headers_a, 
        headers_b,
        max_sample_size=100
    )
    
    elapsed_time = time.time() - start_time
    
    # 結果表示
    print("\n" + "=" * 60)
    print("📊 実行結果")
    print("=" * 60)
    print(f"⏱️  実行時間: {elapsed_time:.2f}秒")
    print(f"🎯 同一カード: {len(matches)}組")
    print(f"🔗 フィールドマッピング: {len(field_mappings)}件")
    
    # 同一カードの例を表示
    if matches:
        print("\n🎯 同一カードの例（上位3件）:")
        for i, match in enumerate(matches[:3], 1):
            card_a = match['card_a']
            card_b = match['card_b']
            score = match['overall_similarity']
            
            name_a = card_a.get('name', card_a.get('serial', 'Unknown'))
            name_b = card_b.get('カード名', card_b.get('型番', 'Unknown'))
            
            print(f"\n  {i}. マッチスコア: {score:.3f}")
            print(f"     A社: {name_a}")
            print(f"     B社: {name_b}")
    
    # フィールドマッピングの例を表示
    if field_mappings:
        print("\n🔗 フィールドマッピング（上位5件）:")
        for i, mapping in enumerate(field_mappings[:5], 1):
            print(f"\n  {i}. {mapping['field_a']} → {mapping['field_b']}")
            print(f"     信頼度: {mapping['confidence']:.3f}")
            print(f"     品質: {mapping.get('quality_score', 'N/A')}")
            print(f"     サンプル数: {mapping.get('sample_count', 0)}")
    
    # 性能改善の確認
    print("\n" + "=" * 60)
    print("✅ 性能改善の確認")
    print("=" * 60)
    
    # 従来手法での予想時間
    old_comparisons = len(data_a) * len(data_b) * len(headers_a) * len(headers_b)
    old_estimated_time = old_comparisons / 1000000 * 2  # 100万比較で約2秒と仮定
    
    print(f"📊 従来手法（総当たり）:")
    print(f"   予想比較回数: {old_comparisons:,}")
    print(f"   予想実行時間: {old_estimated_time:.1f}秒")
    
    print(f"\n📊 新手法（2段階マッチング）:")
    print(f"   実際の実行時間: {elapsed_time:.2f}秒")
    print(f"   性能改善率: {(1 - elapsed_time/old_estimated_time) * 100:.1f}%")
    
    # 品質チェック
    high_confidence = [m for m in field_mappings if m.get('confidence', 0) > 0.8]
    print(f"\n📊 マッピング品質:")
    print(f"   高信頼度マッピング（>0.8）: {len(high_confidence)}件")
    print(f"   総マッピング数: {len(field_mappings)}件")
    
    if elapsed_time < 10:
        print("\n🎉 成功: 処理時間が10秒以内です！")
    else:
        print("\n⚠️ 警告: 処理時間が10秒を超えています")
    
    if len(high_confidence) >= 5:
        print("🎉 成功: 高信頼度マッピングが5件以上あります！")
    else:
        print("⚠️ 警告: 高信頼度マッピングが5件未満です")

if __name__ == "__main__":
    main()