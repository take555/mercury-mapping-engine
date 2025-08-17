# csv_analyzer.py の analyze_file メソッドに BOM 除去機能を追加

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