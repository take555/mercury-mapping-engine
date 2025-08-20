#!/usr/bin/env python3
"""
2段階マッチングシステムのWebアプリ風テストスクリプト
"""

import sys
import csv
import time
import logging
from pathlib import Path
import json

# プロジェクトのパスを追加
sys.path.insert(0, '/home/aktk/Projects/docker-projects/mercury-mapping-engine/python')

# ロガー設定（Webアプリのログをシミュレーション）
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logger = logging.getLogger('enhanced_web_test')

def simulate_enhanced_analysis():
    """enhanced.pyのWebエンドポイントをシミュレート"""
    
    logger.info("=" * 60)
    logger.info("🚀 ENHANCED ANALYSIS WEB TEST START")
    logger.info("=" * 60)
    
    # Step 1: ファイルアップロード処理をシミュレート
    logger.info("📁 Step 1: ファイルアップロード処理開始")
    
    file_a_path = '/home/aktk/Projects/docker-projects/mercury-mapping-engine/hikitsugi/Youyadatasample.csv'
    file_b_path = '/home/aktk/Projects/docker-projects/mercury-mapping-engine/hikitsugi/Tay2datasample.csv'
    
    logger.info(f"   - ファイルA: Youyadatasample.csv")
    logger.info(f"   - ファイルB: Tay2datasample.csv")
    logger.info("✅ ファイル処理完了")
    
    # Step 2: CSV分析をシミュレート
    logger.info("📊 Step 3: CSV分析開始")
    start_time = time.time()
    
    # CSVデータ読み込み
    with open(file_a_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers_a = reader.fieldnames
        data_a = list(reader)
    
    with open(file_b_path, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        headers_b = reader.fieldnames
        data_b = list(reader)
    
    csv_time = time.time() - start_time
    logger.info(f"✅ CSV分析完了 ({csv_time:.2f}秒)")
    logger.info(f"📋 CSV分析結果:")
    logger.info(f"   - A社: {len(headers_a)}フィールド, {len(data_a)}行")
    logger.info(f"   - B社: {len(headers_b)}フィールド, {len(data_b)}行")
    
    # Step 4: 2段階マッチングシステム実行
    logger.info("🚀 Step 4: 2段階マッチングシステム開始")
    start_time = time.time()
    
    # 2段階マッチングをインポートして実行
    from core.two_stage_matching import enhanced_two_stage_matching
    
    # サンプルサイズを100に制限（Webアプリの設定をシミュレート）
    max_sample_size = 100
    
    logger.info(f"📊 マッチング対象データ:")
    logger.info(f"   - A社データ: {min(len(data_a), max_sample_size)}行")
    logger.info(f"   - B社データ: {min(len(data_b), max_sample_size)}行")
    logger.info(f"   - 新手法: 重要フィールドのみで同一カード特定 → フィールドマッピング学習")
    
    # 2段階マッチング実行
    matches, enhanced_mappings = enhanced_two_stage_matching(
        data_a[:max_sample_size],
        data_b[:max_sample_size],
        headers_a,
        headers_b,
        max_sample_size=max_sample_size
    )
    
    matching_time = time.time() - start_time
    logger.info(f"✅ 2段階マッチング完了 ({matching_time:.2f}秒)")
    logger.info(f"🎯 結果: {len(matches)}件の同一カード, {len(enhanced_mappings)}件のフィールドマッピング")
    
    # Step 5: フィールドマッピングは既に完了
    logger.info("✅ Step 5: フィールドマッピング分析は2段階マッチングで完了済み")
    logger.info(f"   - 高信頼度マッピング: {len([m for m in enhanced_mappings if m.get('confidence', 0) > 0.8])}件")
    logger.info(f"   - 中信頼度マッピング: {len([m for m in enhanced_mappings if 0.5 <= m.get('confidence', 0) <= 0.8])}件")
    
    # Step 6: マッピングサマリー
    logger.info("📋 Step 6: マッピングサマリー作成開始")
    logger.info(f"   - enhanced_mappings: {len(enhanced_mappings)}件")
    logger.info(f"   - matches: {len(matches)}件")
    logger.info("✅ マッピングサマリー作成完了")
    
    # Step 7: 結果表示
    logger.info("🎨 Step 7: 結果表示生成開始")
    start_time = time.time()
    
    # パフォーマンス比較データ
    old_comparisons = len(data_a) * len(data_b) * len(headers_a) * len(headers_b)
    old_estimated_time = old_comparisons / 1000000 * 2  # 100万比較で約2秒と仮定
    
    html_time = time.time() - start_time
    logger.info(f"✅ 結果表示生成完了 ({html_time:.2f}秒)")
    
    # 総実行時間
    total_time = csv_time + matching_time + html_time
    logger.info("=" * 60)
    logger.info(f"🏁 ENHANCED ANALYSIS WEB TEST COMPLETE - 総実行時間: {total_time:.2f}秒")
    logger.info("=" * 60)
    
    # 結果サマリー
    print("\n" + "=" * 80)
    print("📊 WEBアプリ性能テスト結果")
    print("=" * 80)
    
    print(f"⏱️  総実行時間: {total_time:.2f}秒")
    print(f"🎯 同一カード: {len(matches)}組")
    print(f"🔗 フィールドマッピング: {len(enhanced_mappings)}件")
    
    # 高品質マッピングを表示
    high_conf_mappings = [m for m in enhanced_mappings if m.get('confidence', 0) > 0.8]
    print(f"✅ 高信頼度マッピング（>0.8）: {len(high_conf_mappings)}件")
    
    if high_conf_mappings:
        print("\n🔗 高信頼度フィールドマッピング:")
        for i, mapping in enumerate(high_conf_mappings[:5], 1):
            print(f"  {i}. {mapping['field_a']} → {mapping['field_b']} (信頼度: {mapping['confidence']:.3f})")
    
    # パフォーマンス改善
    print(f"\n📈 性能改善:")
    print(f"   従来手法予想時間: {old_estimated_time:.1f}秒")
    print(f"   新手法実行時間: {total_time:.2f}秒")
    print(f"   改善率: {(1 - total_time/old_estimated_time) * 100:.1f}%")
    
    # 成功判定
    print(f"\n✅ 成功判定:")
    
    success_criteria = []
    if total_time < 10:
        success_criteria.append("✅ 処理時間10秒以内")
    else:
        success_criteria.append("❌ 処理時間10秒を超過")
    
    if len(enhanced_mappings) <= 50:
        success_criteria.append("✅ マッピング件数50件以下")
    else:
        success_criteria.append("❌ マッピング件数50件超過")
    
    if len(high_conf_mappings) >= 5:
        success_criteria.append("✅ 高信頼度マッピング5件以上")
    else:
        success_criteria.append("❌ 高信頼度マッピング5件未満")
    
    for criteria in success_criteria:
        print(f"   {criteria}")
    
    # 同一カードの例
    if matches:
        print(f"\n🎯 同一カードの例（上位3件）:")
        for i, match in enumerate(matches[:3], 1):
            card_a = match['card_a']
            card_b = match['card_b']
            score = match['overall_similarity']
            
            name_a = card_a.get('name', card_a.get('serial', 'Unknown'))
            name_b = card_b.get('カード名', card_b.get('型番', 'Unknown'))
            
            print(f"  {i}. スコア: {score:.3f} | A社: {name_a} | B社: {name_b}")
    
    print("=" * 80)
    
    # JSON結果も出力（Web APIのレスポンスをシミュレート）
    result = {
        "status": "success",
        "execution_time": total_time,
        "identical_cards": len(matches),
        "field_mappings": len(enhanced_mappings),
        "high_confidence_mappings": len(high_conf_mappings),
        "performance_improvement": f"{(1 - total_time/old_estimated_time) * 100:.1f}%",
        "success_criteria": {
            "time_under_10s": total_time < 10,
            "mappings_under_50": len(enhanced_mappings) <= 50,
            "high_conf_over_5": len(high_conf_mappings) >= 5
        }
    }
    
    print(f"\n📋 JSON Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    simulate_enhanced_analysis()