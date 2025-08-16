"""
Mercury Mapping Engine - Text Similarity Utilities
テキスト類似度計算ユーティリティ
"""
import re
from typing import List, Set


class TextSimilarity:
    """テキスト類似度計算クラス"""
    
    def __init__(self):
        pass
    
    def calculate_exact_similarity(self, str1: str, str2: str) -> float:
        """完全一致・部分一致の類似度"""
        str1_clean = self.clean_text(str1)
        str2_clean = self.clean_text(str2)
        
        if not str1_clean or not str2_clean:
            return 0.0
        
        if str1_clean == str2_clean:
            return 1.0
        elif str1_clean in str2_clean or str2_clean in str1_clean:
            return 0.9
        else:
            return 0.0
    
    def calculate_fuzzy_similarity(self, str1: str, str2: str) -> float:
        """あいまい一致の類似度（レーベンシュタイン距離ベース）"""
        str1_clean = self.clean_text(str1)
        str2_clean = self.clean_text(str2)
        
        if not str1_clean or not str2_clean:
            return 0.0
        
        if str1_clean == str2_clean:
            return 1.0
        
        # レーベンシュタイン距離計算
        distance = self.levenshtein_distance(str1_clean, str2_clean)
        max_len = max(len(str1_clean), len(str2_clean))
        
        if max_len == 0:
            return 1.0
        
        similarity = 1 - (distance / max_len)
        return max(0, similarity)
    
    def calculate_partial_similarity(self, str1: str, str2: str) -> float:
        """部分的な類似度（単語レベル）"""
        words1 = self.extract_words(str1)
        words2 = self.extract_words(str2)
        
        if not words1 or not words2:
            return 0.0
        
        set1 = set(words1)
        set2 = set(words2)
        
        intersection = len(set1 & set2)
        union = len(set1 | set2)
        
        return intersection / union if union > 0 else 0.0
    
    def calculate_jaccard_similarity(self, str1: str, str2: str) -> float:
        """Jaccard類似度（文字n-gramベース）"""
        ngrams1 = self.get_character_ngrams(str1, n=2)
        ngrams2 = self.get_character_ngrams(str2, n=2)
        
        if not ngrams1 or not ngrams2:
            return 0.0
        
        intersection = len(ngrams1 & ngrams2)
        union = len(ngrams1 | ngrams2)
        
        return intersection / union if union > 0 else 0.0
    
    def clean_text(self, text: str) -> str:
        """テキストをクリーニング"""
        if not text:
            return ""
        
        # 不要な文字を除去
        cleaned = re.sub(r'[^\w\s]', '', str(text).lower())
        # 余分な空白を除去
        cleaned = re.sub(r'\s+', ' ', cleaned).strip()
        return cleaned
    
    def extract_words(self, text: str) -> List[str]:
        """テキストから意味のある単語を抽出"""
        if not text:
            return []
        
        # 日本語と英数字の単語を抽出
        words = re.findall(r'[ぁ-ゟ]+|[ァ-ヿ]+|[一-龯]+|[a-zA-Z0-9]+', str(text))
        # 2文字以上の単語のみ
        return [w for w in words if len(w) >= 2]
    
    def get_character_ngrams(self, text: str, n: int = 2) -> Set[str]:
        """文字n-gramを生成"""
        if not text or len(text) < n:
            return set()
        
        cleaned_text = self.clean_text(text)
        if len(cleaned_text) < n:
            return set()
        
        ngrams = set()
        for i in range(len(cleaned_text) - n + 1):
            ngrams.add(cleaned_text[i:i + n])
        
        return ngrams
    
    def levenshtein_distance(self, s1: str, s2: str) -> int:
        """レーベンシュタイン距離を計算"""
        if len(s1) < len(s2):
            return self.levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = list(range(len(s2) + 1))
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def calculate_comprehensive_similarity(self, str1: str, str2: str) -> dict:
        """包括的な類似度計算（複数手法の結果を返す）"""
        results = {
            'exact_similarity': self.calculate_exact_similarity(str1, str2),
            'fuzzy_similarity': self.calculate_fuzzy_similarity(str1, str2),
            'partial_similarity': self.calculate_partial_similarity(str1, str2),
            'jaccard_similarity': self.calculate_jaccard_similarity(str1, str2)
        }
        
        # 総合スコア（重み付け平均）
        weights = {
            'exact_similarity': 0.4,
            'fuzzy_similarity': 0.3,
            'partial_similarity': 0.2,
            'jaccard_similarity': 0.1
        }
        
        comprehensive_score = sum(
            results[method] * weight 
            for method, weight in weights.items()
        )
        
        results['comprehensive_score'] = comprehensive_score
        results['max_score'] = max(results[method] for method in weights.keys())
        
        return results
    
    def find_best_match(self, target: str, candidates: List[str], 
                       threshold: float = 0.5) -> dict:
        """候補の中から最も類似度の高いものを検索"""
        if not candidates:
            return {'match': None, 'score': 0.0, 'index': -1}
        
        best_match = None
        best_score = 0.0
        best_index = -1
        
        for i, candidate in enumerate(candidates):
            similarity = self.calculate_comprehensive_similarity(target, candidate)
            score = similarity['comprehensive_score']
            
            if score > best_score and score >= threshold:
                best_score = score
                best_match = candidate
                best_index = i
        
        return {
            'match': best_match,
            'score': best_score,
            'index': best_index
        }