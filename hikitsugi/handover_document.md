# Mercury Mapping Engine - 性能改善プロジェクト引き継ぎ

## 📋 プロジェクト概要

**プロジェクト名**: Mercury Mapping Engine v2.0  
**目的**: A社・B社のトレーディングカードCSVデータの高精度フィールドマッピング  
**問題**: `/test/files/enhanced`の処理が異常に遅い（数分〜数十分）  
**緊急度**: 高（本日中に解決必要）

## 🔍 現在の問題

### 症状
- Web画面での分析処理が数分以上かかる
- 結果として952件の無意味なマッピングが生成される
- 全ての信頼度が0.000となっている
- HTMLテーブルが崩れて表示されている

### 原因分析
```
A社フィールド数: 42
B社フィールド数: 57
総組み合わせ: 42 × 57 = 2,394通り

現在の処理:
100行 × 100行 × 2,394フィールド組み合わせ = 約24,000,000回の比較
↓
結果: 無意味な952件のマッピング（信頼度0.000）
```

## 🎯 解決すべき課題

### 処理時間の問題
- **現在**: 数分〜数十分
- **目標**: 10秒以内

### 結果品質の問題
- **現在**: 952件の無意味なマッピング
- **目標**: 10-20件の高品質マッピング

### 信頼度の問題
- **現在**: 全て0.000
- **目標**: 0.8-1.0の高信頼度

## 📁 ファイル構造

```
mercury-mapping-engine/
├── python/
│   └── web/
│       └── routes/
│           └── enhanced.py          # 🔥 修正対象メインファイル
├── logs/
│   └── mercury.log                  # ログファイル
└── テストデータ/
    ├── Youyadatasample.csv         # A社サンプル
    └── Tay2datasample.csv          # B社サンプル
```

## 📊 サンプルデータ構造

### A社データ (Youyadatasample.csv)
```csv
name,serial,releace_date,attribute,rarity,series
江戸川コナン,PR001,2024/1/24,青,プロモ,プロモカード
服部平次＆怪盗キッド,PR003,2024/3/1,緑,プロモ,プロモカード
```

### B社データ (Tay2datasample.csv)
```csv
カード名,型番,発売日,色,種類,シリーズ
江戸川コナン,PR001,20240124,青,パートナー,プロモカード
服部平次＆怪盗キッド,PR003,20240301,緑,パートナー,プロモカード
```

### 期待される同一カード例
| A社 | B社 | 判定根拠 |
|-----|-----|----------|
| name="江戸川コナン" | カード名="江戸川コナン" | 名前完全一致 |
| serial="PR001" | 型番="PR001" | ID一致 |
| releace_date="2024/1/24" | 発売日="20240124" | 日付一致(正規化後) |

## 🔧 実装すべき解決策

### 2段階マッチングシステム

#### Stage 1: 同一カード特定
```python
# 重要フィールドのみで高速マッチング
key_fields = {
    'name': ['name', 'カード名', '商品名'],
    'id': ['serial', '型番', 'id'],
    'date': ['releace_date', '発売日']
}

# 同一カードペア特定
identical_pairs = find_identical_cards(data_a, data_b, key_fields)
```

#### Stage 2: フィールドマッピング学習
```python
# 同一カードペアからフィールド対応関係を学習
field_mappings = analyze_field_mappings_from_pairs(identical_pairs)

# 期待される結果例:
# name ↔ カード名 (信頼度: 1.0)
# serial ↔ 型番 (信頼度: 1.0)
# releace_date ↔ 発売日 (信頼度: 1.0)
```

## 🎯 修正対象コード

### ファイル: `python/web/routes/enhanced.py`

#### 修正箇所1: Step 4 - Brute Force Matching
```python
# 現在のコード (遅い)
matches = card_matcher.brute_force_matching(
    data_a, data_b, 
    analysis_a['headers'], analysis_b['headers'],
    max_sample_size=max_sample_size
)

# 修正後 (高速)
matches, enhanced_mappings = two_stage_matching_system(
    data_a, data_b,
    analysis_a['headers'], analysis_b['headers']
)
```

#### 修正箇所2: Step 5 - フィールドマッピング分析
```python
# 現在のコード (重い処理)
field_mapping_result = engine.field_mapper.analyze_field_mappings_from_matches(
    matches, analysis_a['headers'], analysis_b['headers']
)

# 修正後 (Stage 2で既に完了)
# enhanced_mappings は既に Stage 1 で生成済み
```

#### 修正箇所3: Step 7 - HTML生成
```python
# 表示件数制限を追加
display_mappings = enhanced_mappings[:20]  # 最大20件に制限
```

## 📈 期待される改善効果

| 項目 | 修正前 | 修正後 | 改善率 |
|------|--------|--------|--------|
| 処理時間 | 数分 | 数秒 | 95%以上削減 |
| マッピング件数 | 952件 | 10-20件 | 95%削減 |
| 信頼度 | 0.000 | 0.8-1.0 | 大幅改善 |
| 実用性 | 無意味 | 実用的 | 完全改善 |

## 🧪 テスト手順

### 1. 現状確認
```bash
# 現在の処理時間を計測
time curl -X POST http://localhost:5000/test/files/enhanced \
  -F "file_a=@Youyadatasample.csv" \
  -F "file_b=@Tay2datasample.csv"
```

### 2. 修正実装
- 2段階マッチングシステムを実装
- enhanced.py の該当部分を修正

### 3. 性能テスト
```bash
# 修正後の処理時間を計測
time curl -X POST http://localhost:5000/test/files/enhanced \
  -F "file_a=@Youyadatasample.csv" \
  -F "file_b=@Tay2datasample.csv"
```

### 4. 結果検証
- 同一カードが正しく特定されているか
- フィールドマッピングの信頼度が適切か
- 処理時間が目標値以内か

## ✅ 成功判定基準

### 必須条件
- [ ] 処理時間が10秒以内
- [ ] フィールドマッピング件数が50件以下
- [ ] 信頼度0.8以上のマッピングが5件以上存在

### 推奨条件
- [ ] 同一カード「江戸川コナン」が正しく特定される
- [ ] name ↔ カード名 のマッピングが検出される
- [ ] serial ↔ 型番 のマッピングが検出される
- [ ] HTMLテーブルが正常に表示される

## 🚨 注意事項

### 重要な制約
1. **既存機能を壊さない**: 他のページ・APIは正常動作を維持
2. **ログ出力**: 処理時間と結果を詳細にログ出力
3. **エラーハンドリング**: 異常データでもクラッシュしない

### トラブルシューティング
```bash
# ログ確認
tail -f logs/mercury.log

# Docker再起動
docker-compose restart

# 依存関係確認
pip list | grep pandas
```

## 📞 引き継ぎ後の連絡

### 実装完了時
- 処理時間の改善結果
- フィールドマッピングの件数・信頼度
- 発見された課題や追加改善点

### 問題発生時
- エラーメッセージの詳細
- 再現手順
- ログファイルの該当部分

---

## 🎯 最重要ポイント

**現在**: 42×57の全フィールド総当り → 24,000,000回比較 → 数分  
**改善**: 重要フィールドのみ → 同一カード特定 → フィールド学習 → 数秒

**この根本的なアプローチ変更により、劇的な性能改善と品質向上を実現する**