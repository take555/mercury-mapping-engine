"""
Mercury Mapping Engine - CSV Analyzer
CSV解析エンジン
"""
import csv
import io
from typing import Dict, List, Optional, Any
from utils.logger import analysis_logger, performance_logger


class CSVAnalyzer:
    """CSV解析専用クラス"""
    
    def __init__(self, config=None):
        self.config = config or {}
        self.max_rows = self.config.get('csv_max_rows', 1000)
        self.sample_rows = self.config.get('csv_sample_rows', 5)
        self.encoding = self.config.get('csv_encoding', 'utf-8')

    def analyze_file(self, filepath: str) -> Dict[str, Any]:
        """CSVファイルを分析（BOM対応）"""
        try:
            # BOM対応でファイルを読み込み
            with open(filepath, 'r', encoding='utf-8-sig') as file:  # utf-8-sig でBOM自動除去
                content = file.read()

            # さらに手動でBOM除去（念のため）
            if content.startswith('\ufeff'):
                content = content[1:]

            # 一時ファイルに書き出して pandas で読み込み
            import tempfile
            import os

            with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False, encoding='utf-8') as temp_file:
                temp_file.write(content)
                temp_path = temp_file.name

            try:
                # pandas でクリーンなCSVを読み込み
                import pandas as pd
                df = pd.read_csv(temp_path, encoding='utf-8')

                # ヘッダーの BOM 除去とクリーニング
                clean_headers = []
                for header in df.columns:
                    clean_header = str(header).strip()
                    # BOM文字を除去
                    clean_header = clean_header.replace('\ufeff', '')
                    # 先頭末尾の不要文字除去
                    clean_header = clean_header.strip('\'"` \t\n\r')
                    clean_headers.append(clean_header)

                # データフレームのカラム名を更新
                df.columns = clean_headers

                # データもクリーニング
                for col in df.columns:
                    if df[col].dtype == 'object':  # 文字列カラムのみ
                        df[col] = df[col].astype(str).str.replace('\ufeff', '', regex=False)
                        df[col] = df[col].str.strip()

                # 辞書形式に変換
                data = df.to_dict('records')

                analysis_logger.logger.info(f"CSV analysis completed: {len(clean_headers)} headers, {len(data)} rows")
                analysis_logger.logger.info(f"Headers: {clean_headers[:5]}...")  # 最初の5個を表示

                return {
                    'headers': clean_headers,
                    'sample_data': data[:10],  # サンプル10行
                    'total_rows': len(data),
                    'encoding': 'utf-8-cleaned'
                }

            finally:
                # 一時ファイル削除
                os.unlink(temp_path)

        except Exception as e:
            analysis_logger.log_error('csv_analysis', str(e))
            return {
                'error': f'CSV analysis failed: {str(e)}',
                'encoding': 'unknown'
            }

    def analyze_file_full(self, filepath: str, max_rows: Optional[int] = None) -> Dict[str, Any]:
        """CSV ファイルを全件分析（行数制限付き）"""
        performance_logger.start_timer('csv_full_analysis')
        
        max_rows = max_rows or self.max_rows
        
        try:
            with open(filepath, 'r', encoding=self.encoding) as f:
                content = f.read()
            
            lines = content.strip().split('\n')
            headers = [h.strip().strip('"') for h in lines[0].split(',')]
            
            all_data = []
            sample_data = []
            
            for i, line in enumerate(lines[1:], 1):
                if i > max_rows:  # 最大行数制限
                    break
                    
                if line.strip():
                    # CSVパース改善（ダブルクォート対応）
                    row_data = self.parse_csv_row(line)
                    
                    if len(row_data) == len(headers):
                        row_dict = dict(zip(headers, row_data))
                        all_data.append(row_dict)
                        
                        # サンプルデータ（最初の数行）
                        if len(sample_data) < self.sample_rows:
                            sample_data.append(row_dict)
            
            result = {
                'headers': headers,
                'sample_data': sample_data,
                'full_data': all_data,
                'total_rows': len(all_data),
                'file_total_rows': len(lines) - 1,
                'truncated': len(lines) - 1 > max_rows
            }
            
            analysis_logger.log_csv_analysis(
                filepath, 
                len(headers), 
                len(all_data)
            )
            performance_logger.end_timer('csv_full_analysis')
            
            return result
            
        except Exception as e:
            analysis_logger.log_error('csv_full_analysis', str(e))
            return {'error': str(e)}
    
    def parse_csv_row(self, line: str) -> List[str]:
        """CSV行を適切にパース（ダブルクォート、カンマ対応）"""
        try:
            # csv.readerを使用して適切にパース
            reader = csv.reader(io.StringIO(line))
            row = next(reader)
            return [cell.strip() for cell in row]
        except:
            # フォールバック: 単純分割
            return [cell.strip().strip('"') for cell in line.split(',')]
    
    def validate_csv_structure(self, headers: List[str], data: List[Dict]) -> Dict[str, Any]:
        """CSV構造のバリデーション"""
        validation_result = {
            'is_valid': True,
            'issues': [],
            'stats': {}
        }
        
        # ヘッダー検証
        if not headers:
            validation_result['is_valid'] = False
            validation_result['issues'].append("No headers found")
            return validation_result
        
        # 重複ヘッダーチェック
        duplicate_headers = [h for h in set(headers) if headers.count(h) > 1]
        if duplicate_headers:
            validation_result['issues'].append(f"Duplicate headers: {duplicate_headers}")
        
        # データ整合性チェック
        if data:
            # 空の値の統計
            empty_counts = {}
            for header in headers:
                empty_count = sum(1 for row in data if not str(row.get(header, '')).strip())
                empty_counts[header] = empty_count
            
            validation_result['stats']['empty_values'] = empty_counts
            validation_result['stats']['total_rows'] = len(data)
            validation_result['stats']['completeness'] = {
                header: 1 - (empty_count / len(data))
                for header, empty_count in empty_counts.items()
            }
        
        return validation_result
    
    def detect_field_types(self, headers: List[str], data: List[Dict]) -> Dict[str, str]:
        """フィールドのデータ型を推定"""
        field_types = {}
        
        for header in headers:
            values = [str(row.get(header, '')).strip() for row in data if row.get(header, '').strip()]
            
            if not values:
                field_types[header] = 'empty'
                continue
            
            # 数値型判定
            numeric_count = 0
            for value in values:
                if self._is_numeric(value):
                    numeric_count += 1
            
            numeric_ratio = numeric_count / len(values)
            
            if numeric_ratio >= 0.9:
                field_types[header] = 'numeric'
            elif numeric_ratio >= 0.5:
                field_types[header] = 'mixed'
            else:
                field_types[header] = 'text'
        
        return field_types
    
    def _is_numeric(self, value: str) -> bool:
        """文字列が数値かどうか判定"""
        try:
            # カンマを除去して数値変換を試行
            cleaned_value = value.replace(',', '').replace('¥', '').replace('円', '')
            float(cleaned_value)
            return True
        except ValueError:
            return False
    
    def get_statistics(self, data: List[Dict]) -> Dict[str, Any]:
        """データの統計情報を取得"""
        if not data:
            return {}
        
        stats = {
            'total_rows': len(data),
            'headers': list(data[0].keys()) if data else [],
            'field_count': len(data[0]) if data else 0
        }
        
        # 各フィールドの統計
        field_stats = {}
        for header in stats['headers']:
            values = [str(row.get(header, '')).strip() for row in data]
            non_empty_values = [v for v in values if v]
            
            field_stats[header] = {
                'total_count': len(values),
                'non_empty_count': len(non_empty_values),
                'empty_count': len(values) - len(non_empty_values),
                'unique_count': len(set(non_empty_values)),
                'completeness_ratio': len(non_empty_values) / len(values) if values else 0
            }
            
            # サンプル値（最初の3個）
            if non_empty_values:
                field_stats[header]['sample_values'] = non_empty_values[:3]
        
        stats['field_statistics'] = field_stats
        
        return stats