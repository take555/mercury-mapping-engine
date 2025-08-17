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