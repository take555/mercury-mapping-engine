"""
Mercury Mapping Engine - Prompt Builder
Claude AI用のプロンプト生成と最適化
"""
import json
from typing import Dict, List, Optional, Any, Union
from datetime import datetime
from utils.logger import analysis_logger


class PromptBuilder:
    """Claude AI用プロンプト生成クラス"""
    
    def __init__(self, config: Optional[Dict] = None):
        self.config = config or {}
        self.max_sample_rows = self.config.get('max_sample_rows', 10)
        self.max_field_count = self.config.get('max_field_count', 50)
        
        # プロンプトテンプレート
        self.templates = {
            'field_mapping': self._get_field_mapping_template(),
            'csv_analysis': self._get_csv_analysis_template(), 
            'card_matching': self._get_card_matching_template(),
            'data_validation': self._get_data_validation_template(),
            'mapping_validation': self._get_mapping_validation_template()
        }
    
    def build_field_mapping_prompt(self, headers_a: List[str], headers_b: List[str],
                                 sample_data_a: List[Dict], sample_data_b: List[Dict],
                                 context: Optional[Dict] = None) -> str:
        """フィールドマッピング用プロンプトを生成"""
        
        # サンプルデータを制限
        sample_a = self._limit_sample_data(sample_data_a)
        sample_b = self._limit_sample_data(sample_data_b)
        
        # コンテキスト情報
        context_info = ""
        if context:
            if context.get('category'):
                context_info += f"商品カテゴリ: {context['category']}\n"
            if context.get('companies'):
                context_info += f"対象企業: {' vs '.join(context['companies'])}\n"
        
        prompt_data = {
            'context_info': context_info,
            'headers_a': headers_a[:self.max_field_count],
            'headers_b': headers_b[:self.max_field_count], 
            'sample_count_a': len(sample_a),
            'sample_count_b': len(sample_b),
            'sample_data_a': sample_a,
            'sample_data_b': sample_b,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.templates['field_mapping'].format(**prompt_data)
    
    def build_csv_analysis_prompt(self, headers: List[str], sample_data: List[Dict],
                                total_rows: int, file_info: Optional[Dict] = None) -> str:
        """CSV分析用プロンプトを生成"""
        
        sample_data = self._limit_sample_data(sample_data)
        
        file_context = ""
        if file_info:
            if file_info.get('filename'):
                file_context += f"ファイル名: {file_info['filename']}\n"
            if file_info.get('size'):
                file_context += f"ファイルサイズ: {file_info['size']}\n"
        
        prompt_data = {
            'file_context': file_context,
            'headers': headers[:self.max_field_count],
            'total_headers': len(headers),
            'sample_data': sample_data,
            'sample_count': len(sample_data),
            'total_rows': total_rows,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.templates['csv_analysis'].format(**prompt_data)
    
    def build_card_matching_prompt(self, cards_a: List[Dict], cards_b: List[Dict],
                                 matching_config: Optional[Dict] = None) -> str:
        """カードマッチング用プロンプトを生成"""
        
        # マッチング設定
        config_info = ""
        if matching_config:
            threshold = matching_config.get('threshold', 0.75)
            config_info += f"類似度しきい値: {threshold}\n"
            if matching_config.get('use_price'):
                config_info += "価格情報を補助的に使用\n"
        
        prompt_data = {
            'config_info': config_info,
            'cards_a': self._limit_sample_data(cards_a),
            'cards_b': self._limit_sample_data(cards_b),
            'count_a': len(cards_a),
            'count_b': len(cards_b),
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.templates['card_matching'].format(**prompt_data)
    
    def build_data_validation_prompt(self, data: List[Dict], headers: List[str],
                                   validation_rules: Optional[Dict] = None) -> str:
        """データ検証用プロンプトを生成"""
        
        rules_info = ""
        if validation_rules:
            for field, rules in validation_rules.items():
                rules_info += f"{field}: {', '.join(rules)}\n"
        
        prompt_data = {
            'headers': headers,
            'sample_data': self._limit_sample_data(data),
            'total_records': len(data),
            'validation_rules': rules_info,
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.templates['data_validation'].format(**prompt_data)
    
    def build_mapping_validation_prompt(self, mapping_results: Dict,
                                      confidence_threshold: float = 0.8) -> str:
        """マッピング結果検証用プロンプトを生成"""
        
        # 高信頼度と低信頼度のマッピングを分類
        high_confidence = []
        low_confidence = []
        
        for mapping in mapping_results.get('mappings', []):
            confidence = mapping.get('confidence', 0)
            if confidence >= confidence_threshold:
                high_confidence.append(mapping)
            else:
                low_confidence.append(mapping)
        
        prompt_data = {
            'total_mappings': len(mapping_results.get('mappings', [])),
            'high_confidence_count': len(high_confidence),
            'low_confidence_count': len(low_confidence),
            'confidence_threshold': confidence_threshold,
            'high_confidence_mappings': high_confidence[:10],  # 上位10件
            'low_confidence_mappings': low_confidence[:10],   # 上位10件
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        }
        
        return self.templates['mapping_validation'].format(**prompt_data)
    
    def build_custom_prompt(self, template_name: str, **kwargs) -> str:
        """カスタムプロンプトを生成"""
        if template_name not in self.templates:
            raise ValueError(f"Unknown template: {template_name}")
        
        # タイムスタンプを自動追加
        kwargs['timestamp'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        try:
            return self.templates[template_name].format(**kwargs)
        except KeyError as e:
            analysis_logger.log_error('prompt_build', f"Missing parameter: {e}")
            raise ValueError(f"Missing required parameter: {e}")
    
    def estimate_prompt_tokens(self, prompt: str) -> Dict[str, Any]:
        """プロンプトのトークン数を推定"""
        # 簡易的な推定（4文字 = 1トークン）
        char_count = len(prompt)
        estimated_tokens = char_count // 4
        
        # 日本語と英語を考慮した推定
        import re
        japanese_chars = len(re.findall(r'[あ-ん|ア-ン|一-龯]', prompt))
        english_words = len(re.findall(r'[a-zA-Z]+', prompt))
        
        heuristic_tokens = int(japanese_chars / 2 + english_words * 1.3)
        final_estimate = max(estimated_tokens, heuristic_tokens)
        
        return {
            'character_count': char_count,
            'estimated_tokens': final_estimate,
            'japanese_characters': japanese_chars,
            'english_words': english_words,
            'estimation_method': 'heuristic'
        }
    
    def optimize_prompt_size(self, prompt: str, max_tokens: int = 150000) -> str:
        """プロンプトサイズを最適化"""
        current_estimate = self.estimate_prompt_tokens(prompt)
        
        if current_estimate['estimated_tokens'] <= max_tokens:
            return prompt
        
        # サンプルデータを削減して再生成する必要がある場合の処理
        analysis_logger.logger.warning(f"Prompt too long: {current_estimate['estimated_tokens']} tokens")
        
        # 簡易的な切り詰め（実際は呼び出し元でサンプル数を調整する方が良い）
        reduction_ratio = max_tokens / current_estimate['estimated_tokens']
        target_length = int(len(prompt) * reduction_ratio * 0.9)  # 安全マージン
        
        return prompt[:target_length] + "\n\n[注意: プロンプトが長すぎるため切り詰められました]"
    
    def _limit_sample_data(self, data: List[Dict]) -> List[Dict]:
        """サンプルデータを制限"""
        return data[:self.max_sample_rows]
    
    def _format_sample_data(self, data: List[Dict]) -> str:
        """サンプルデータを読みやすい形式に整形"""
        if not data:
            return "（サンプルデータなし）"
        
        formatted = []
        for i, row in enumerate(data[:self.max_sample_rows], 1):
            formatted.append(f"行{i}: {json.dumps(row, ensure_ascii=False, indent=2)}")
        
        return "\n".join(formatted)
    
    def _get_field_mapping_template(self) -> str:
        """フィールドマッピング用テンプレート"""
        return """# トレーディングカードCSVフィールドマッピング分析

## 分析対象
{context_info}
分析日時: {timestamp}

## CSVファイルA
ヘッダー({sample_count_a}フィールド): {headers_a}

サンプルデータ({sample_count_a}行):
{sample_data_a}

## CSVファイルB  
ヘッダー({sample_count_b}フィールド): {headers_b}

サンプルデータ({sample_count_b}行):
{sample_data_b}

## 分析依頼

以下の観点でフィールドマッピングを分析してください：

1. **フィールド対応分析**
   - ファイルA、Bの各フィールドが何を表すか推測
   - 同じ情報を表すフィールドペアを特定
   - 対応の信頼度を0.0-1.0で評価

2. **データ型・形式分析**
   - 各フィールドのデータ型を推定
   - 数値、文字列、日付などの形式を確認
   - 変換が必要な場合の処理方法を提案

3. **マッピング品質評価**
   - 高信頼度マッピング（0.8以上）
   - 中信頼度マッピング（0.6-0.8）
   - 低信頼度マッピング（0.6未満）

4. **推奨事項**
   - マッピングルールの生成
   - データ正規化の必要性
   - 注意すべきポイント

JSON形式で結果を出力してください。"""
    
    def _get_csv_analysis_template(self) -> str:
        """CSV分析用テンプレート"""
        return """# CSVファイル構造分析

## ファイル情報
{file_context}
分析日時: {timestamp}

## データ構造
ヘッダー数: {total_headers}
ヘッダー: {headers}
サンプル行数: {sample_count}
総行数: {total_rows}

## サンプルデータ
{sample_data}

## 分析依頼

以下の観点でCSVファイルを分析してください：

1. **フィールド分析**
   - 各フィールドの推定される内容
   - データ型（文字列/数値/日付など）
   - トレーディングカードデータとしての分類

2. **データ品質**
   - 欠損値の有無
   - データ形式の一貫性
   - 異常値の可能性

3. **構造的特徴**
   - 主キーと思われるフィールド
   - カテゴリカルデータ
   - 数値データの範囲

4. **トレーディングカード特有の特徴**
   - カード名フィールドの特定
   - 価格情報の特定
   - シリーズ・セット情報

JSON形式で結果を出力してください。"""
    
    def _get_card_matching_template(self) -> str:
        """カードマッチング用テンプレート"""
        return """# トレーディングカードマッチング分析

## マッチング設定
{config_info}
分析日時: {timestamp}

## データセットA
カード数: {count_a}
サンプル:
{cards_a}

## データセットB
カード数: {count_b}
サンプル:
{cards_b}

## 分析依頼

以下の観点でカードマッチングを分析してください：

1. **カード名分析**
   - 同一カードと思われるペアを特定
   - 名称の表記揺れを考慮
   - 省略形や英日表記の違いを考慮

2. **マッチング手法**
   - 完全一致
   - 部分一致
   - あいまい一致（類似度計算）

3. **補助情報活用**
   - 価格による妥当性チェック
   - シリーズ情報の整合性
   - レアリティなどの属性情報

4. **マッチング結果**
   - 高信頼度マッチ
   - 候補マッチ
   - マッチしなかった項目

JSON形式で結果を出力してください。"""
    
    def _get_data_validation_template(self) -> str:
        """データ検証用テンプレート"""
        return """# データ検証分析

## 検証対象
ヘッダー: {headers}
レコード数: {total_records}
分析日時: {timestamp}

## 検証ルール
{validation_rules}

## サンプルデータ
{sample_data}

## 検証依頼

以下の観点でデータを検証してください：

1. **データ品質**
   - 形式エラーの検出
   - 欠損値の分析
   - 重複データの確認

2. **値の妥当性**
   - 数値範囲の確認
   - 文字列パターンの検証
   - 参照整合性の確認

3. **トレーディングカード特有の検証**
   - カード名の妥当性
   - 価格の妥当性
   - カテゴリ情報の整合性

4. **改善提案**
   - データクリーニングの必要箇所
   - 正規化ルールの提案
   - 品質向上の施策

JSON形式で結果を出力してください。"""
    
    def _get_mapping_validation_template(self) -> str:
        """マッピング検証用テンプレート"""
        return """# フィールドマッピング検証

## 検証対象
総マッピング数: {total_mappings}
高信頼度マッピング: {high_confidence_count}
低信頼度マッピング: {low_confidence_count}
信頼度しきい値: {confidence_threshold}
検証日時: {timestamp}

## 高信頼度マッピング
{high_confidence_mappings}

## 低信頼度マッピング
{low_confidence_mappings}

## 検証依頼

以下の観点でマッピング結果を検証してください：

1. **マッピングの正確性**
   - 論理的に正しい対応か
   - データ型の整合性
   - 意味的な対応の妥当性

2. **信頼度の妥当性**
   - 高信頼度マッピングの再確認
   - 低信頼度マッピングの改善可能性
   - 信頼度計算の妥当性

3. **欠損マッピング**
   - 対応付けられていないフィールド
   - 潜在的なマッピング候補
   - 手動確認が必要な項目

4. **最終推奨事項**
   - 自動適用可能なマッピング
   - 手動確認推奨マッピング
   - 追加調査が必要な項目

JSON形式で結果を出力してください。"""