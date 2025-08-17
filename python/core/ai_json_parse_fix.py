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