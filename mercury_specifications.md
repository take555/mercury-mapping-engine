# Mercury Mapping Engine 完全仕様書

## 📋 プロジェクト概要

### 目的
A社とB社のトレーディングカードCSVデータを高精度でマッピングし、フィールド対応関係を自動検出するシステム

### 革新的アプローチ
**従来**: フィールド名の類似度のみで判定  
**新手法**: 実際のカードデータを比較→同じ商品を特定→フィールド対応を分析

---

## 🏗️ アーキテクチャ

### 現在の状況
- ✅ **リファクタリング完了**: 巨大な app.py (1800行) → モジュール分割
- ✅ **Core Engine実装済み**: CSV解析、カードマッチング、フィールドマッピング
- 🔄 **実装中**: API/Web Routes、動作テスト

### ディレクトリ構造
```
mercury-mapping-engine/
├── app.py                     # ✅ 軽量化メインアプリ（50行）
├── config/                    # ✅ 設定管理
│   ├── __init__.py
│   ├── database.py           # ✅ DB接続・コネクションプール
│   └── settings.py           # ✅ 環境別設定
├── core/                     # ✅ コア分析エンジン
│   ├── __init__.py           # ✅ ファクトリー関数
│   ├── csv_analyzer.py       # ✅ CSV解析エンジン
│   ├── card_matcher.py       # ✅ カードマッチングエンジン
│   ├── field_mapper.py       # ✅ フィールドマッピングエンジン
│   └── mapping_engine.py     # ✅ 統合エンジン
├── ai/                       # 🔄 Claude AI機能
│   ├── claude_client.py      # 🔄 実装予定
│   ├── model_manager.py      # 🔄 実装予定
│   └── prompt_builder.py     # 🔄 実装予定
├── api/routes/               # 🔄 REST API
│   ├── __init__.py           # ✅ ルート登録基盤
│   ├── health.py             # 🔄 実装予定
│   ├── analysis.py           # 🔄 実装予定
│   └── models.py             # 🔄 実装予定
├── web/routes/               # 🔄 Web UI
│   ├── __init__.py           # ✅ Web基盤
│   ├── index.py              # 🔄 実装予定
│   ├── enhanced.py           # 🔄 実装予定
│   └── test_pages.py         # 🔄 実装予定
├── utils/                    # ✅ 共通ユーティリティ
│   ├── __init__.py
│   ├── text_similarity.py    # ✅ テキスト類似度計算
│   └── logger.py             # ✅ ログ設定
└── database/                 # 📋 既存DBスキーマ
    └── init.sql              # ✅ 既存
```

---

## 🧩 Core Engine詳細仕様

### 1. CSVAnalyzer (`core/csv_analyzer.py`)
```python
class CSVAnalyzer:
    def __init__(self, config=None)
    
    # 主要メソッド
    def analyze_file(filepath) -> Dict                    # サンプル分析
    def analyze_file_full(filepath, max_rows=1000)        # 全件分析
    def validate_csv_structure(headers, data)             # 構造検証
    def detect_field_types(headers, data)                 # データ型推定
    def get_statistics(data)                              # 統計情報
```

**出力例**:
```json
{
  "headers": ["カード名", "価格", "シリーズ"],
  "sample_data": [...],
  "full_data": [...],
  "total_rows": 1000,
  "truncated": false
}
```

### 2. CardMatcher (`core/card_matcher.py`)
```python
class CardMatcher:
    def __init__(self, config=None)
    
    # 主要メソッド
    def find_matching_cards(data_a, data_b, headers_a, headers_b)  # カードマッチング
    def identify_card_name_fields(headers)                         # カード名フィールド特定
    def identify_price_fields(headers)                             # 価格フィールド特定
    def analyze_match_quality(matches)                             # マッチング品質分析
```

**アルゴリズム**:
1. カード名候補フィールド自動特定
2. 複数手法での類似度計算（完全一致、あいまい一致、部分一致）
3. 価格による補助判定
4. 重複除去・品質分析

### 3. FieldMapper (`core/field_mapper.py`)
```python
class FieldMapper:
    def __init__(self, config=None)
    
    # 主要メソッド
    def analyze_field_mappings_from_matches(card_matches, headers_a, headers_b)  # カードベース分析
    def calculate_mapping_confidence(field_mappings, card_matches)              # 信頼度計算
    def analyze_traditional_mappings(headers_a, headers_b, sample_data_a, sample_data_b)  # 従来手法
    def create_mapping_rules(confident_mappings, threshold=0.8)                 # ルール生成
```

**信頼度計算**:
```python
confidence = (similarity * 0.4 + consistency * 0.4 + sample_score * 0.2)
```

### 4. MappingEngine (`core/mapping_engine.py`)
```python
class MappingEngine:
    def __init__(self, config=None)
    
    # 統合メソッド
    def analyze_csv_files(filepath_a, filepath_b, full_analysis=True)
    def analyze_card_based_mapping(headers_a, headers_b, sample_data_a, sample_data_b, full_data_a=None, full_data_b=None)
    def create_mapping_summary(enhanced_mappings, card_matches, analysis_a, analysis_b)
    def export_mapping_rules(enhanced_mappings, confidence_threshold=0.8)
    def validate_mapping_results(enhanced_mappings, card_matches)
```

---

## 🤖 AI Integration仕様

### Claude API統合
- **モデル対応**: Haiku, Sonnet, Opus, 3.5 Sonnet
- **コスト計算**: トークン数×料金体系
- **エラーハンドリング**: フォールバック機能

### 既存実装（巨大app.pyから移行予定）
```python
# ai/claude_client.py (予定)
class ClaudeClient:
    def call_api(prompt, model)
    def count_tokens(prompt, model)
    def estimate_cost(model, input_tokens)

# ai/model_manager.py (予定)
class ModelManager:
    def get_available_models()
    def get_model_info(model_id)
    def test_model_availability(model)
```

---

## 🗄️ データベース仕様

### 既存テーブル
```sql
-- カテゴリマスタ
mercury_category2 (id, name, order_display, active, updated_at, created_at)

-- 会社マスタ  
mercury_company (id, company_code, company_name, active, created_at, updated_at)

-- マッピングルール
mercury_common_mapping_rule (
    id, category2_id, company_a_id, company_b_id,
    company_a_field, company_b_field, common_field_name,
    mapping_type, transform_rule, priority, active,
    created_at, updated_at
)

-- 正規化ルール
mercury_normalization_rule (
    id, category2_id, field_name, rule_type, rule_config,
    execution_order, active, created_at, updated_at
)

-- ジョブ管理
mercury_mapping_job (
    id, job_uuid, category2_id, company_a_id, company_b_id,
    file_a_path, file_b_path, result_url, local_result_path,
    mapping_options, status, progress, various_counts,
    log_message, error_message, created_by, timestamps
)
```

### 接続管理
- **コネクションプール**: 5接続
- **設定**: `config/database.py`
- **環境別分離**: 開発/本番/テスト

---

## 🌐 API仕様

### REST API エンドポイント
```
GET  /api/health              # ヘルスチェック
GET  /api/categories          # カテゴリ一覧
GET  /api/models              # 利用可能モデル一覧
GET  /api/models/{model_id}   # モデル詳細
POST /api/tokens/count        # トークン数計算
POST /api/analyze/basic       # 基本分析
POST /api/analyze/enhanced    # 高精度分析
```

### Web UI エンドポイント
```
GET  /                        # メインページ
GET  /test/claude             # Claude接続テスト
GET  /test/models             # モデル一覧
GET  /test/tokens             # トークン計算UI
GET  /test/files              # 従来分析
GET  /test/files/enhanced     # 高精度分析 ⭐推奨
```

---

## ⚙️ 設定管理

### 環境設定 (`config/settings.py`)
```python
class BaseConfig:
    # Claude API
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    CLAUDE_DEFAULT_MODEL = 'claude-3-haiku-20240307'
    
    # 分析設定
    CSV_MAX_ROWS = 1000
    CARD_MATCH_THRESHOLD = 0.75
    FIELD_SIMILARITY_THRESHOLD = 0.7
    
class DevelopmentConfig(BaseConfig):
    DEBUG = True
    CSV_MAX_ROWS = 100  # 開発用制限
    
class ProductionConfig(BaseConfig):
    DEBUG = False
    CSV_MAX_ROWS = 5000  # 本番用拡張
```

### 必須環境変数
```bash
CLAUDE_API_KEY=sk-ant-api03-...
MYSQL_HOST=mysql
MYSQL_USER=mercury
MYSQL_PASSWORD=mercurypass
MYSQL_DATABASE=mercury
```

---

## 🔄 処理フロー

### 高精度分析フロー
1. **CSV読み込み**: `CSVAnalyzer.analyze_file_full()`
2. **カードマッチング**: `CardMatcher.find_matching_cards()`
3. **フィールド分析**: `FieldMapper.analyze_field_mappings_from_matches()`
4. **信頼度計算**: `FieldMapper.calculate_mapping_confidence()`
5. **Claude統合**: AI分析結果との統合
6. **結果検証**: `MappingEngine.validate_mapping_results()`
7. **ルール生成**: `FieldMapper.create_mapping_rules()`

### エラーハンドリング
- **カードマッチ失敗** → 従来手法にフォールバック
- **Claude API失敗** → パターンマッチング使用
- **CSV読み込み失敗** → 詳細エラー情報提供

---

## 📊 品質メトリクス

### マッピング品質指標
- **信頼度**: 0.0-1.0（類似度×一貫性×サンプル数）
- **カバレッジ**: マッピングされたフィールド/全フィールド
- **一貫性**: 高一致サンプル/全サンプル

### 推奨基準
- **高品質**: 信頼度 > 0.8
- **中品質**: 信頼度 0.6-0.8
- **要確認**: 信頼度 < 0.6

---

## 🚧 実装状況

### ✅ 完了済み
- Core Engine全体 (CSV, Card, Field,統合)
- 設定管理・DB接続
- ログ・エラーハンドリング
- テキスト類似度計算

### 🔄 実装中
- API Routes実装
- Web Routes実装  
- 既存機能の新Engine接続

### 📋 TODO
- AI パッケージ分離
- テンプレート化
- テスト作成
- パフォーマンス最適化

---

## 🚀 次回実装タスク

### 優先度A: 動作確認
1. 新しいMappingEngineを既存エンドポイントに接続
2. `/test/files/enhanced` の動作テスト
3. エラーハンドリング確認

### 優先度B: API実装
1. `api/routes/analysis.py` - 分析API
2. `api/routes/health.py` - ヘルスチェック
3. `web/routes/enhanced.py` - 高精度分析ページ

### 優先度C: 最適化
1. Claude API機能の分離
2. HTMLテンプレート化
3. パフォーマンス改善

---

## 💡 重要なポイント

### 設計思想
- **単一責任原則**: 各クラスが明確な役割
- **依存関係の最小化**: 疎結合設計
- **拡張性**: 新機能追加が容易
- **エラー耐性**: フォールバック機能完備

### パフォーマンス
- **コネクションプール**: DB接続効率化
- **行数制限**: 大量データ対応
- **並列処理対応**: 将来拡張可能

### 保守性
- **モジュール分割**: 機能別ファイル
- **設定外部化**: 環境別管理
- **ログ充実**: デバッグ・監視対応

---

## 📞 引き継ぎ時の確認事項

1. **現在のファイル配置状況確認**
2. **Docker環境の動作確認**
3. **エラーログの確認**
4. **優先実装項目の決定**

---

*このドキュメントは Mercury Mapping Engine v2.0 の完全仕様書です。*  
*更新日: 2024年8月16日*