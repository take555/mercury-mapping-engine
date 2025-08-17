"""
Mercury Mapping Engine - Card Matcher
カードマッチングエンジン
"""
import re
from typing import Dict, List, Tuple, Any, Optional
from utils.text_similarity import TextSimilarity
from utils.logger import analysis_logger, performance_logger


class CardMatcher:
    """カードマッチング専用クラス"""

    def __init__(self, config=None):
        self.config = config or {}
        self.match_threshold = self.config.get('card_match_threshold', 0.75)
        self.name_similarity_threshold = self.config.get('card_name_similarity_threshold', 0.8)
        self.price_similarity_threshold = self.config.get('price_similarity_threshold', 0.9)
        self.text_similarity = TextSimilarity()

    def find_matching_cards(self, data_a, data_b, headers_a, headers_b):
        """新生代マッチング - 力技のみ"""
        return self.brute_force_matching(data_a, data_b, headers_a, headers_b)

    def identify_card_name_fields(self, headers: List[str]) -> List[str]:
        """カード名と思われるフィールドを特定"""
        name_patterns = [
            'カード名', '名前', '名称', 'name', 'card_name', 'title', 'product_name',
            'item_name', 'カードタイトル', 'アイテム名', 'プロダクト名', 'カード', 'card'
        ]

        candidates = []
        for header in headers:
            for pattern in name_patterns:
                if pattern.lower() in header.lower() or header.lower() in pattern.lower():
                    candidates.append(header)
                    break

        return candidates if candidates else headers[:3]  # 見つからない場合は最初の3フィールド

    def identify_price_fields(self, headers: List[str]) -> List[str]:
        """価格と思われるフィールドを特定"""
        price_patterns = [
            '価格', '値段', 'price', '金額', 'amount', 'cost', 'buy_price', 'sell_price',
            '販売価格', '買取価格', '税込', '税抜', 'yen', '円', '料金'
        ]

        candidates = []
        for header in headers:
            for pattern in price_patterns:
                if pattern.lower() in header.lower():
                    candidates.append(header)
                    break

        return candidates

    def _calculate_match_score(self, row_a: Dict, row_b: Dict,
                               name_fields_a: List[str], name_fields_b: List[str],
                               price_fields_a: List[str], price_fields_b: List[str],
                               headers_a: List[str], headers_b: List[str]) -> Dict[str, Any]:
        """マッチスコアを計算"""
        match_score = 0
        match_details = {}

        # 方法1: カード名の類似度
        name_similarity = self._calculate_card_name_similarity(
            row_a, row_b, name_fields_a, name_fields_b
        )
        if name_similarity > self.name_similarity_threshold:
            match_score += name_similarity * 0.7
            match_details['name_match'] = name_similarity

        # 方法2: 価格の一致（補助判定）
        price_similarity = self._calculate_price_similarity(
            row_a, row_b, price_fields_a, price_fields_b
        )
        if price_similarity > self.price_similarity_threshold:
            match_score += price_similarity * 0.3
            match_details['price_match'] = price_similarity

        # 方法3: 複数フィールドの総合判定
        overall_similarity = self._calculate_overall_similarity(
            row_a, row_b, headers_a, headers_b
        )
        if overall_similarity > 0.6:
            match_score += overall_similarity * 0.2
            match_details['overall_match'] = overall_similarity

        return {
            'score': match_score,
            'details': match_details
        }

    def _calculate_card_name_similarity(self, row_a: Dict, row_b: Dict,
                                        name_fields_a: List[str], name_fields_b: List[str]) -> float:
        """カード名の類似度を計算"""
        max_similarity = 0

        for field_a in name_fields_a:
            value_a = str(row_a.get(field_a, '')).strip()
            if not value_a:
                continue

            for field_b in name_fields_b:
                value_b = str(row_b.get(field_b, '')).strip()
                if not value_b:
                    continue

                # 複数の類似度計算手法を使用
                similarities = [
                    self.text_similarity.calculate_exact_similarity(value_a, value_b),
                    self.text_similarity.calculate_fuzzy_similarity(value_a, value_b),
                    self.text_similarity.calculate_partial_similarity(value_a, value_b)
                ]

                current_similarity = max(similarities)
                max_similarity = max(max_similarity, current_similarity)

        return max_similarity

    def _calculate_price_similarity(self, row_a: Dict, row_b: Dict,
                                    price_fields_a: List[str], price_fields_b: List[str]) -> float:
        """価格の類似度を計算"""
        for field_a in price_fields_a:
            value_a = self._extract_numeric_value(row_a.get(field_a, ''))
            if value_a is None:
                continue

            for field_b in price_fields_b:
                value_b = self._extract_numeric_value(row_b.get(field_b, ''))
                if value_b is None:
                    continue

                # 価格が完全一致または非常に近い場合
                if abs(value_a - value_b) < 0.01:
                    return 1.0
                elif value_a > 0 and value_b > 0:
                    diff_ratio = abs(value_a - value_b) / max(value_a, value_b)
                    if diff_ratio < 0.1:  # 10%以内の差
                        return 1.0 - diff_ratio

        return 0.0

    def _calculate_overall_similarity(self, row_a: Dict, row_b: Dict,
                                      headers_a: List[str], headers_b: List[str]) -> float:
        """全フィールドでの総合的な類似度"""
        similarities = []

        for field_a in headers_a[:5]:  # 最初の5フィールドのみチェック
            value_a = str(row_a.get(field_a, '')).strip()
            if not value_a:
                continue

            for field_b in headers_b[:5]:
                value_b = str(row_b.get(field_b, '')).strip()
                if not value_b:
                    continue

                similarity = self.text_similarity.calculate_fuzzy_similarity(value_a, value_b)
                if similarity > 0.7:
                    similarities.append(similarity)

        return sum(similarities) / len(similarities) if similarities else 0.0

    def _extract_numeric_value(self, value_str: str) -> Optional[float]:
        """文字列から数値を抽出"""
        if not value_str:
            return None

        # 数字とピリオド、カンマのみ抽出
        numeric_str = re.sub(r'[^\d.,]', '', str(value_str))
        numeric_str = numeric_str.replace(',', '')

        try:
            return float(numeric_str)
        except ValueError:
            return None

    def _remove_duplicate_matches(self, matches: List[Dict]) -> List[Dict]:
        """重複するマッチを除去"""
        used_a = set()
        used_b = set()
        unique_matches = []

        for match in matches:
            if match['row_a_index'] not in used_a and match['row_b_index'] not in used_b:
                unique_matches.append(match)
                used_a.add(match['row_a_index'])
                used_b.add(match['row_b_index'])

        return unique_matches

    def analyze_match_quality(self, matches: List[Dict[str, Any]]) -> Dict[str, Any]:
        """マッチング品質を分析"""
        if not matches:
            return {
                'total_matches': 0,
                'average_score': 0.0,
                'high_quality_matches': 0,
                'medium_quality_matches': 0,
                'low_quality_matches': 0
            }

        # スコアを安全に取得
        scores = []
        for match in matches:
            score = (match.get('match_score') or
                     match.get('similarity') or
                     match.get('score') or
                     0.0)
            try:
                scores.append(float(score))
            except (ValueError, TypeError):
                scores.append(0.0)

        if not scores:
            scores = [0.0]

        avg_score = sum(scores) / len(scores)
        high_quality = len([s for s in scores if s > 0.8])
        medium_quality = len([s for s in scores if 0.6 <= s <= 0.8])
        low_quality = len([s for s in scores if s < 0.6])

        return {
            'total_matches': len(matches),
            'average_score': round(avg_score, 3),
            'high_quality_matches': high_quality,
            'medium_quality_matches': medium_quality,
            'low_quality_matches': low_quality
        }

    def brute_force_matching(self, data_a: List[Dict], data_b: List[Dict],
                             headers_a: List[str], headers_b: List[str],
                             max_sample_size: int = 100,
                             similarity_mode: str = 'library',  # 'library' or 'ai'
                             ai_manager=None) -> List[Dict[str, Any]]:
        """
        ハイブリッド力技マッチング: ライブラリ vs AI で類似度計算を切り替え

        Args:
            data_a: A社データ
            data_b: B社データ
            headers_a: A社ヘッダー
            headers_b: B社ヘッダー
            max_sample_size: 最大サンプルサイズ
            similarity_mode: 'library' (Python libs) or 'ai' (Claude API)
            ai_manager: AI Manager instance (similarity_mode='ai'時に必要)

        Returns:
            高精度マッチング結果
        """
        performance_logger.start_timer('brute_force_matching')

        mode_info = {
            'library': '🐍 Python Library Mode - 高速・安価',
            'ai': '🤖 Claude AI Mode - 高精度・意味理解'
        }

        analysis_logger.logger.info(f"🔥 Brute Force Matching 開始 - {mode_info.get(similarity_mode, similarity_mode)}")

        # サンプリング
        sample_a = data_a[:max_sample_size]
        sample_b = data_b[:max_sample_size]

        matches = []
        field_correlation_matrix = {}

        analysis_logger.logger.info(f"📊 サンプルサイズ: A社{len(sample_a)}行 × B社{len(sample_b)}行")
        analysis_logger.logger.info(f"⚙️ 類似度計算モード: {similarity_mode}")

        for i, row_a in enumerate(sample_a):
            best_matches = []

            for j, row_b in enumerate(sample_b):
                # モード別フィールド比較
                if similarity_mode == 'library':
                    field_match_results = self._compare_all_fields_library(
                        row_a, row_b, headers_a, headers_b
                    )
                elif similarity_mode == 'ai':
                    field_match_results = self._compare_all_fields_ai(
                        row_a, row_b, headers_a, headers_b, ai_manager
                    )
                else:
                    raise ValueError(f"Unknown similarity_mode: {similarity_mode}")

                # フィールド対応マトリクス更新
                self._update_field_correlation_matrix(
                    field_correlation_matrix, field_match_results
                )

                # 行全体のマッチスコア計算
                total_score = self._calculate_brute_force_score(field_match_results)

                if total_score > 0.6:
                    best_matches.append({
                        'row_a_index': i,
                        'row_b_index': j,
                        'row_a_data': row_a,
                        'row_b_data': row_b,
                        'match_score': total_score,
                        'field_matches': field_match_results,
                        'similarity_mode': similarity_mode,
                        'match_details': {
                            'matched_fields_count': len([fm for fm in field_match_results if fm['similarity'] > 0.7]),
                            'total_fields_compared': len(field_match_results),
                            'best_field_match': max(field_match_results,
                                                    key=lambda x: x['similarity']) if field_match_results else None
                        }
                    })

            # 各A社行に対して最良のマッチのみ保持
            if best_matches:
                best_match = max(best_matches, key=lambda x: x['match_score'])
                matches.append(best_match)

        # 重複除去
        unique_matches = self._remove_duplicate_matches_brute_force(matches)

        # フィールド対応統計
        field_mapping_stats = self._analyze_field_correlations(field_correlation_matrix)

        analysis_logger.logger.info(f"🎯 Brute Force結果: {len(unique_matches)}件のマッチ")
        analysis_logger.logger.info(f"📈 発見されたフィールド対応: {len(field_mapping_stats)}組")

        # 結果にモード情報とフィールドマッピング情報を追加
        for match in unique_matches:
            match['discovered_field_mappings'] = field_mapping_stats
            match['analysis_mode'] = similarity_mode

        performance_logger.end_timer('brute_force_matching')
        return unique_matches

    def _compare_all_fields_library(self, row_a: Dict, row_b: Dict,
                                    headers_a: List[str], headers_b: List[str]) -> List[Dict]:
        """🐍 Pythonライブラリベースの全フィールド比較"""
        field_matches = []

        for field_a in headers_a:
            value_a = str(row_a.get(field_a, '')).strip()
            if not value_a or len(value_a) < 2:
                continue

            for field_b in headers_b:
                value_b = str(row_b.get(field_b, '')).strip()
                if not value_b or len(value_b) < 2:
                    continue

                # 複数手法で徹底比較
                similarities = self._calculate_comprehensive_similarity(value_a, value_b)
                max_similarity = max(similarities.values())

                if max_similarity > 0.5:
                    field_matches.append({
                        'field_a': field_a,
                        'field_b': field_b,
                        'value_a': value_a,
                        'value_b': value_b,
                        'similarity': max_similarity,
                        'similarity_details': similarities,
                        'match_type': self._classify_match_type(value_a, value_b, similarities),
                        'calculation_method': 'library'
                    })

        return field_matches

    def _compare_all_fields_ai(self, row_a: Dict, row_b: Dict,
                               headers_a: List[str], headers_b: List[str],
                               ai_manager) -> List[Dict]:
        """🤖 Claude AIベースの全フィールド比較"""
        if not ai_manager:
            analysis_logger.logger.warning("AI Manager not provided, falling back to library mode")
            return self._compare_all_fields_library(row_a, row_b, headers_a, headers_b)

        field_matches = []

        # バッチ処理でAI分析（効率化）
        field_pairs = []
        for field_a in headers_a:
            value_a = str(row_a.get(field_a, '')).strip()
            if not value_a or len(value_a) < 2:
                continue

            for field_b in headers_b:
                value_b = str(row_b.get(field_b, '')).strip()
                if not value_b or len(value_b) < 2:
                    continue

                field_pairs.append({
                    'field_a': field_a,
                    'field_b': field_b,
                    'value_a': value_a,
                    'value_b': value_b
                })

        # AI分析実行
        if field_pairs:
            ai_results = self._batch_ai_similarity_analysis(field_pairs, ai_manager)

            for i, pair in enumerate(field_pairs):
                ai_result = ai_results.get(i, {})
                similarity = ai_result.get('similarity', 0.0)

                if similarity > 0.5:
                    field_matches.append({
                        'field_a': pair['field_a'],
                        'field_b': pair['field_b'],
                        'value_a': pair['value_a'],
                        'value_b': pair['value_b'],
                        'similarity': similarity,
                        'ai_reasoning': ai_result.get('reasoning', ''),
                        'match_type': ai_result.get('match_type', 'ai_determined'),
                        'calculation_method': 'ai',
                        'ai_confidence': ai_result.get('confidence', similarity)
                    })

        return field_matches

    def _batch_ai_similarity_analysis(self, field_pairs: List[Dict], ai_manager) -> Dict:
        """バッチでAI類似度分析実行"""
        try:
            # プロンプト構築
            prompt = self._build_similarity_analysis_prompt(field_pairs)

            # Claude API呼び出し
            result = ai_manager.claude_client.call_api(
                prompt,
                model='claude-3-haiku-20240307'  # 高速モデルで効率化
            )

            if result['success']:
                # JSONレスポンスをパース
                return self._parse_ai_similarity_response(result['content'])
            else:
                analysis_logger.logger.error(f"AI similarity analysis failed: {result.get('error')}")
                return {}

        except Exception as e:
            analysis_logger.logger.error(f"AI similarity analysis error: {e}")
            return {}

    def _build_similarity_analysis_prompt(self, field_pairs: List[Dict]) -> str:
            """AI類似度分析用プロンプト構築（JSON形式改善）"""
            pairs_text = ""
            for i, pair in enumerate(field_pairs[:10]):  # 10ペアに制限してJSONエラーを減らす
                pairs_text += f"""
    {i}: "{pair['field_a']}" vs "{pair['field_b']}"
        値: "{pair['value_a']}" vs "{pair['value_b']}"
    """

            prompt = f"""
    以下のフィールドペアについて、類似度を分析してJSON形式で回答してください。

    【分析対象】
    {pairs_text}

    【重要】以下のJSON形式で正確に回答してください：
    {{
      "0": {{"similarity": 0.85, "reasoning": "説明", "match_type": "semantic_match", "confidence": 0.9}},
      "1": {{"similarity": 0.65, "reasoning": "説明", "match_type": "fuzzy_match", "confidence": 0.7}}
    }}

    ・similarity: 0.0-1.0の数値
    ・reasoning: 簡潔な理由
    ・match_type: exact_match, semantic_match, fuzzy_match, weak_match のいずれか
    ・confidence: 0.0-1.0の数値

    有効なJSONのみ回答してください。
    """
            return prompt

    def _parse_ai_similarity_response(self, content: str) -> Dict:
        """AI応答のJSONパース（堅牢版）"""
        try:
            import json
            import re

            # まず完全なJSONブロックを探す
            json_patterns = [
                r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # ネストしたJSONに対応
                r'\{.*?\}',  # シンプルなJSON
            ]

            for pattern in json_patterns:
                matches = re.findall(pattern, content, re.DOTALL)
                for match in matches:
                    try:
                        parsed = json.loads(match)
                        if isinstance(parsed, dict) and parsed:
                            analysis_logger.logger.info(f"Successfully parsed AI JSON: {len(parsed)} items")
                            return parsed
                    except json.JSONDecodeError:
                        continue

            # JSONが見つからない場合、行ごとに解析を試行
            analysis_logger.logger.warning("Failed to parse complete JSON, attempting line-by-line parsing")

            # フォールバック: 手動パース
            result = {}
            lines = content.split('\n')
            current_index = None

            for line in lines:
                line = line.strip()

                # インデックス行を探す
                index_match = re.match(r'"(\d+)":\s*\{', line)
                if index_match:
                    current_index = index_match.group(1)
                    continue

                # similarity値を探す
                if current_index and 'similarity' in line:
                    similarity_match = re.search(r'"similarity":\s*([\d.]+)', line)
                    if similarity_match:
                        similarity = float(similarity_match.group(1))
                        result[current_index] = {
                            'similarity': similarity,
                            'reasoning': 'Parsed from partial response',
                            'match_type': 'ai_fallback',
                            'confidence': similarity
                        }

            if result:
                analysis_logger.logger.info(f"Fallback parsing successful: {len(result)} items")
                return result
            else:
                analysis_logger.logger.error("All parsing attempts failed")
                return {}

        except Exception as e:
            analysis_logger.logger.error(f"Critical error in AI response parsing: {e}")
            return {}

    # 既存の_calculate_comprehensive_similarity等のメソッドはそのまま保持

    def _calculate_comprehensive_similarity(self, value_a: str, value_b: str) -> Dict[str, float]:
        """包括的類似度計算 - あらゆる手法で比較"""
        similarities = {}

        try:
            # 1. 基本文字列類似度
            similarities['exact'] = 1.0 if value_a == value_b else 0.0
            similarities['fuzzy'] = self.text_similarity.calculate_fuzzy_similarity(value_a, value_b)
            similarities['partial'] = self.text_similarity.calculate_partial_similarity(value_a, value_b)

            # 2. 数値比較（数値の場合）
            num_a = self._extract_numeric_value(value_a)
            num_b = self._extract_numeric_value(value_b)
            if num_a is not None and num_b is not None:
                if num_a == num_b:
                    similarities['numeric_exact'] = 1.0
                elif num_a > 0 and num_b > 0:
                    diff_ratio = abs(num_a - num_b) / max(num_a, num_b)
                    similarities['numeric_close'] = max(0, 1.0 - diff_ratio)

            # 3. 正規化類似度（大文字小文字、記号無視）
            normalized_a = re.sub(r'[^\w]', '', value_a.lower())
            normalized_b = re.sub(r'[^\w]', '', value_b.lower())
            if normalized_a and normalized_b:
                similarities['normalized'] = self.text_similarity.calculate_fuzzy_similarity(
                    normalized_a, normalized_b
                )

            # 4. 部分文字列マッチ
            if len(value_a) >= 3 and len(value_b) >= 3:
                if value_a in value_b or value_b in value_a:
                    similarities['substring'] = 0.8

            # 5. 単語レベル類似度
            words_a = value_a.split()
            words_b = value_b.split()
            if words_a and words_b:
                word_matches = 0
                for word_a in words_a:
                    for word_b in words_b:
                        if self.text_similarity.calculate_fuzzy_similarity(word_a, word_b) > 0.8:
                            word_matches += 1
                            break
                similarities['word_level'] = word_matches / max(len(words_a), len(words_b))

        except Exception as e:
            analysis_logger.logger.warning(f"類似度計算エラー: {e}")
            similarities['fuzzy'] = 0.0

        return similarities

    def _classify_match_type(self, value_a: str, value_b: str, similarities: Dict[str, float]) -> str:
        """マッチタイプを分類"""
        if similarities.get('exact', 0) == 1.0:
            return 'exact_match'
        elif similarities.get('numeric_exact', 0) == 1.0:
            return 'numeric_match'
        elif similarities.get('normalized', 0) > 0.9:
            return 'normalized_match'
        elif similarities.get('substring', 0) > 0.7:
            return 'substring_match'
        elif similarities.get('word_level', 0) > 0.8:
            return 'word_match'
        elif max(similarities.values()) > 0.7:
            return 'fuzzy_match'
        else:
            return 'weak_match'

    def _calculate_brute_force_score(self, field_matches: List[Dict]) -> float:
        """力技スコア計算 - 複数のフィールドマッチから総合判定"""
        if not field_matches:
            return 0.0

        # 重み付きスコア計算
        total_score = 0.0
        weights = {
            'exact_match': 1.0,
            'numeric_match': 0.95,
            'normalized_match': 0.9,
            'substring_match': 0.8,
            'word_match': 0.85,
            'fuzzy_match': 0.7,
            'weak_match': 0.5
        }

        high_confidence_matches = 0
        total_weighted_score = 0.0

        for match in field_matches:
            similarity = match['similarity']
            match_type = match['match_type']
            weight = weights.get(match_type, 0.5)

            weighted_score = similarity * weight
            total_weighted_score += weighted_score

            if weighted_score > 0.8:
                high_confidence_matches += 1

        # 複数高信頼度マッチがある場合は大幅ボーナス
        if high_confidence_matches >= 2:
            total_score = min(0.95, total_weighted_score / len(field_matches) + 0.2)
        elif high_confidence_matches >= 1:
            total_score = min(0.85, total_weighted_score / len(field_matches) + 0.1)
        else:
            total_score = total_weighted_score / len(field_matches)

        return total_score

    def _update_field_correlation_matrix(self, matrix: Dict, field_matches: List[Dict]):
        """フィールド対応マトリクスを更新"""
        for match in field_matches:
            if match['similarity'] > 0.7:  # 高類似度のみ
                key = f"{match['field_a']}→{match['field_b']}"
                if key not in matrix:
                    matrix[key] = {'count': 0, 'total_similarity': 0.0, 'samples': []}

                matrix[key]['count'] += 1
                matrix[key]['total_similarity'] += match['similarity']
                matrix[key]['samples'].append({
                    'value_a': match['value_a'],
                    'value_b': match['value_b'],
                    'similarity': match['similarity']
                })

    def _analyze_field_correlations(self, matrix: Dict) -> List[Dict]:
        """フィールド対応統計分析"""
        correlations = []

        for field_pair, stats in matrix.items():
            if stats['count'] >= 2:  # 2回以上マッチした組み合わせのみ
                avg_similarity = stats['total_similarity'] / stats['count']
                field_a, field_b = field_pair.split('→')

                correlations.append({
                    'field_a': field_a,
                    'field_b': field_b,
                    'confidence': avg_similarity,
                    'sample_count': stats['count'],
                    'field_type': self._infer_field_type(stats['samples']),
                    'quality_score': min(1.0, avg_similarity * (stats['count'] / 10))
                })

        # 信頼度順でソート
        correlations.sort(key=lambda x: x['confidence'], reverse=True)
        return correlations

    def _infer_field_type(self, samples: List[Dict]) -> str:
        """サンプルからフィールドタイプを推測"""
        numeric_count = 0
        text_count = 0

        for sample in samples[:5]:  # 最初の5サンプルで判定
            value_a = sample['value_a']
            value_b = sample['value_b']

            if (self._extract_numeric_value(value_a) is not None and
                    self._extract_numeric_value(value_b) is not None):
                numeric_count += 1
            else:
                text_count += 1

        if numeric_count > text_count:
            return 'numeric'
        elif any('名' in str(s['value_a']) + str(s['value_b']) for s in samples[:3]):
            return 'name'
        elif any('価格' in str(s['value_a']) + str(s['value_b']) or
                 'price' in str(s['value_a']) + str(s['value_b']).lower() for s in samples[:3]):
            return 'price'
        else:
            return 'text'

    def _remove_duplicate_matches_brute_force(self, matches: List[Dict]) -> List[Dict]:
        """力技重複除去 - より高精度"""
        # スコア順でソート
        matches.sort(key=lambda x: x['match_score'], reverse=True)

        used_a = set()
        used_b = set()
        unique_matches = []

        for match in matches:
            row_a_idx = match['row_a_index']
            row_b_idx = match['row_b_index']

            if row_a_idx not in used_a and row_b_idx not in used_b:
                unique_matches.append(match)
                used_a.add(row_a_idx)
                used_b.add(row_b_idx)

        return unique_matches
