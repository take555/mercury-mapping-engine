#!/usr/bin/env python3
"""
柔軟マッチングシステムのテストスクリプト
"""

import sys
import csv
import time
from pathlib import Path

# プロジェクトのパスを追加
sys.path.insert(0, '/home/aktk/Projects/docker-projects/mercury-mapping-engine/python')

from core.flexible_matching import flexible_enhanced_matching

def load_csv_data(filepath):
    """CSVファイルを読み込み"""
    data = []
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        for row in reader:
            data.append(row)
    return headers, data

def test_flexible_matching():
    print("=" * 80)
    print("🧪 柔軟マッチングシステム テスト開始")
    print("=" * 80)
    
    # テストデータ読み込み
    file_a = '/home/aktk/Projects/docker-projects/mercury-mapping-engine/hikitsugi/Youyadatasample.csv'
    file_b = '/home/aktk/Projects/docker-projects/mercury-mapping-engine/hikitsugi/Tay2datasample.csv'
    
    print("📂 データファイル読み込み中...")
    headers_a, data_a = load_csv_data(file_a)
    headers_b, data_b = load_csv_data(file_b)
    
    print(f"   A社: {len(headers_a)}フィールド, {len(data_a)}行")
    print(f"   B社: {len(headers_b)}フィールド, {len(data_b)}行")
    
    # フィールド一覧表示
    print(f"\n🏷️  A社フィールド: {headers_a[:5]}...")
    print(f"🏷️  B社フィールド: {headers_b[:5]}...")
    
    # 柔軟マッチングテスト
    print(f"\n🚀 柔軟マッチング実行中...")
    start_time = time.time()
    
    try:
        matches, enhanced_mappings = flexible_enhanced_matching(
            data_a,
            data_b, 
            headers_a,
            headers_b,
            max_sample_size=100
        )
        
        execution_time = time.time() - start_time
        
        print(f"✅ 柔軟マッチング完了 ({execution_time:.3f}秒)")
        print(f"🎯 結果:")
        print(f"   - マッチしたカード: {len(matches)}件")
        print(f"   - 戦略: {enhanced_mappings.get('matching_strategy', 'unknown')}")
        print(f"   - 類似度閾値: {enhanced_mappings.get('similarity_threshold', 0.0)}")
        print(f"   - 総比較回数: {enhanced_mappings.get('total_comparisons', 0):,}回")
        
        # フィールドマッピング結果
        field_mappings = enhanced_mappings.get('flexible_field_mappings', [])
        print(f"\n🔗 フィールドマッピング結果 ({len(field_mappings)}件):")
        for i, mapping in enumerate(field_mappings[:10], 1):
            if isinstance(mapping, tuple) and len(mapping) >= 3:
                field_a, field_b, score = mapping[0], mapping[1], mapping[2]
                print(f"   {i:2d}. {field_a:<20} ↔ {field_b:<20} (類似度: {score:.3f})")
        
        # マッチ結果のサンプル
        print(f"\n📋 カードマッチ結果サンプル:")
        for i, match in enumerate(matches[:5], 1):
            similarity = match.get('overall_similarity', 0.0)
            details = match.get('similarity_details', [])
            print(f"   {i}. 総合類似度: {similarity:.3f}")
            
            # 詳細表示
            for detail in details[:2]:
                field_a = detail.get('field_a', '')
                field_b = detail.get('field_b', '')
                val_a = detail.get('value_a', '')
                val_b = detail.get('value_b', '')
                sim = detail.get('similarity', 0.0)
                print(f"      {field_a} [{val_a}] ↔ {field_b} [{val_b}] = {sim:.3f}")
        
        print(f"\n📊 パフォーマンス比較:")
        comparisons_per_sec = enhanced_mappings.get('total_comparisons', 0) / execution_time if execution_time > 0 else 0
        print(f"   - 実行時間: {execution_time:.3f}秒")
        print(f"   - 比較速度: {comparisons_per_sec:,.0f}回/秒")
        print(f"   - マッチ率: {len(matches) / enhanced_mappings.get('total_comparisons', 1) * 100:.3f}%")
        
    except Exception as e:
        print(f"❌ テストエラー: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)
    print("🏁 テスト完了")
    print("=" * 80)

if __name__ == "__main__":
    test_flexible_matching()