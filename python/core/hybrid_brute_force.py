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
                            'best_field_match': max(field_match_results, key=lambda x: x['similarity']) if field_match_results else None
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
        """AI類似度分析用プロンプト構築"""
        pairs_text = ""
        for i, pair in enumerate(field_pairs[:20]):  # 最大20ペアずつ処理
            pairs_text += f"""
{i}: フィールド名 "{pair['field_a']}" vs "{pair['field_b']}"
    値の例: "{pair['value_a']}" vs "{pair['value_b']}"
"""
        
        prompt = f"""
以下のフィールドペアについて、類似度を分析してください。

【分析対象】
{pairs_text}

【判定基準】
1. 意味的類似性（フィールド名の意味）
2. データ形式の一致度
3. ビジネスロジックの整合性
4. 値の内容の類似性

【回答形式】
JSON形式で各ペアの分析結果を返してください：
{{
  "0": {{
    "similarity": 0.85,
    "reasoning": "attackとAPは両方とも攻撃力を表し、数値も一致",
    "match_type": "semantic_match",
    "confidence": 0.9
  }},
  "1": {{ ... }}
}}

類似度は0.0-1.0で評価し、0.7以上を高類似度として判定してください。
"""
        return prompt

    def _parse_ai_similarity_response(self, content: str) -> Dict:
        """AI応答のJSONパース"""
        try:
            # JSONブロックを抽出
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                import json
                return json.loads(json_match.group())
            else:
                analysis_logger.logger.warning("AI response does not contain valid JSON")
                return {}
        except Exception as e:
            analysis_logger.logger.error(f"Failed to parse AI response: {e}")
            return {}

    # 既存の_calculate_comprehensive_similarity等のメソッドはそのまま保持