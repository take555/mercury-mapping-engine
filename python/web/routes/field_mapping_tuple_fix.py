# enhanced.py の結果表示部分でタプル問題を修正

def _build_success_analysis_section(enhanced_mappings, card_matches, mapping_summary, validation_result):
    """成功時の分析セクション生成（タプル対応）"""
    
    html = f"""
    <h2>🎯 カードベース分析結果</h2>
    <div class="success">
        <h3>✅ 分析成功</h3>
        <p><strong>マッチしたカード数:</strong> {len(card_matches)}件</p>
        <p><strong>検出されたフィールドマッピング:</strong> {len(enhanced_mappings)}件</p>
    </div>
    """
    
    # マッピング品質統計
    if mapping_summary and 'mapping_quality' in mapping_summary:
        quality = mapping_summary['mapping_quality']
        html += f"""
        <h3>📈 マッピング品質統計</h3>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="metric-value confidence-high">{quality.get('high_confidence_count', 0)}</div>
                <div>高信頼度マッピング</div>
            </div>
            <div class="stat-card">
                <div class="metric-value confidence-medium">{quality.get('medium_confidence_count', 0)}</div>
                <div>中信頼度マッピング</div>
            </div>
            <div class="stat-card">
                <div class="metric-value">{quality.get('average_confidence', 0.0):.3f}</div>
                <div>平均信頼度</div>
            </div>
            <div class="stat-card">
                <div class="metric-value">{quality.get('coverage_ratio_a', 0.0):.1%}</div>
                <div>A社フィールドカバレッジ</div>
            </div>
        </div>
        """
    
    # フィールドマッピング表示（タプル対応）
    if enhanced_mappings:
        html += """
        <h3>🎯 検出されたフィールドマッピング</h3>
        <table>
        <tr>
            <th>フィールドタイプ</th>
            <th>A社フィールド</th>
            <th>B社フィールド</th>
            <th>信頼度</th>
            <th>サンプル数</th>
            <th>品質指標</th>
        </tr>
        """
        
        for mapping in enhanced_mappings[:15]:
            try:
                # タプル形式の場合の安全な処理
                if isinstance(mapping, tuple):
                    # タプルを辞書に変換
                    if len(mapping) >= 2:
                        field_a = str(mapping[0]).replace('\ufeff', '').strip() if mapping[0] else 'unknown'
                        field_b = str(mapping[1]).replace('\ufeff', '').strip() if mapping[1] else 'unknown'
                    else:
                        field_a = field_b = 'unknown'
                    
                    confidence = 0.0
                    sample_count = 'N/A'
                    field_type = 'tuple_data'
                    quality_score = 'N/A'
                    
                elif isinstance(mapping, dict):
                    # 通常の辞書形式
                    field_a = str(mapping.get('company_a_field', mapping.get('field_a', 'unknown'))).replace('\ufeff', '').strip()
                    field_b = str(mapping.get('company_b_field', mapping.get('field_b', 'unknown'))).replace('\ufeff', '').strip()
                    confidence = mapping.get('confidence', 0.0)
                    sample_count = mapping.get('sample_count', 'N/A')
                    field_type = mapping.get('field_type', 'unknown')
                    quality_score = mapping.get('quality_score', 'N/A')
                    
                else:
                    # その他の形式
                    field_a = field_b = 'unknown'
                    confidence = 0.0
                    sample_count = 'N/A'
                    field_type = 'unknown_format'
                    quality_score = 'N/A'
                
                confidence_class = "confidence-high" if confidence > 0.8 else "confidence-medium" if confidence > 0.6 else "confidence-low"

                html += f"""
                <tr>
                    <td>{field_type}</td>
                    <td><strong>{field_a}</strong></td>
                    <td><strong>{field_b}</strong></td>
                    <td class="{confidence_class}">{confidence:.3f}</td>
                    <td>{sample_count}</td>
                    <td>{quality_score}</td>
                </tr>
                """
                
            except Exception as e:
                # エラー時のフォールバック
                html += f"""
                <tr>
                    <td>error</td>
                    <td>parsing_failed</td>
                    <td>parsing_failed</td>
                    <td class="confidence-low">0.000</td>
                    <td>N/A</td>
                    <td>Error: {str(e)[:50]}</td>
                </tr>
                """
        
        html += "</table>"
    
    return html