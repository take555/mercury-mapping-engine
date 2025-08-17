"""
Mercury Mapping Engine - Enhanced Analysis Web Routes
高精度分析Webページルート
"""
from flask import Blueprint, request, current_app
import os
import traceback
from core import create_mapping_engine
from config.settings import Config
from utils.logger import analysis_logger, performance_logger

# ブループリント作成
enhanced_bp = Blueprint('enhanced', __name__)


@enhanced_bp.route('/test/files/enhanced')
def enhanced_analysis():
    """カードベース分析を使用した拡張ファイル分析"""
    performance_logger.start_timer('enhanced_analysis_page')
    
    selected_model = request.args.get('model', 'claude-3-haiku-20240307')
    
    try:
        # ファイル存在確認
        file_a = '/app/uploads/a.csv'
        file_b = '/app/uploads/b.csv'
        
        if not os.path.exists(file_a):
            return _render_error_page("ファイルエラー", "a.csv が見つかりません")
        
        if not os.path.exists(file_b):
            return _render_error_page("ファイルエラー", "b.csv が見つかりません")
        
        # 新しいMappingEngineを作成
        config = Config.get_analysis_config()
        engine = create_mapping_engine(config)
        
        analysis_logger.logger.info("Enhanced analysis started")
        
        # CSV分析
        csv_result = engine.analyze_csv_files(file_a, file_b, full_analysis=True)

        if 'error' in csv_result:
            return _render_error_page("CSV分析エラー", csv_result['error'])
        
        analysis_a = csv_result['analysis_a']
        analysis_b = csv_result['analysis_b']
        
        # カードベースマッピング分析
        try:
            enhanced_mappings, card_matches = engine.analyze_card_based_mapping(
                analysis_a['headers'], 
                analysis_b['headers'],
                analysis_a['sample_data'],
                analysis_b['sample_data'],
                analysis_a.get('full_data'),
                analysis_b.get('full_data')
            )
            card_analysis_success = True
            analysis_logger.logger.info(f"Card-based analysis completed: {len(card_matches)} matches, {len(enhanced_mappings)} mappings")
            
        except Exception as e:
            current_app.logger.error(f"カードベース分析エラー: {e}")
            enhanced_mappings = []
            card_matches = []
            card_analysis_success = False
            card_analysis_error = str(e)
        
        # マッピングサマリー作成
        if enhanced_mappings:
            mapping_summary = engine.create_mapping_summary(enhanced_mappings, card_matches, analysis_a, analysis_b)
            validation_result = engine.validate_mapping_results(enhanced_mappings, card_matches)
        else:
            mapping_summary = None
            validation_result = None
        
        # HTML生成
        html = _build_enhanced_analysis_html(
            analysis_a, analysis_b, enhanced_mappings, card_matches,
            card_analysis_success, locals().get('card_analysis_error'),
            mapping_summary, validation_result, selected_model
        )
        
        performance_logger.end_timer('enhanced_analysis_page')
        return html
        
    except Exception as e:
        current_app.logger.error(f"システムエラー: {e}")
        return _render_error_page("システムエラー", str(e), traceback.format_exc())


def _build_enhanced_analysis_html(analysis_a, analysis_b, enhanced_mappings, card_matches,
                                card_analysis_success, card_analysis_error, mapping_summary,
                                validation_result, selected_model):
    """拡張分析結果のHTML生成"""
    
    # ヘッダー部分
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎯 カードベース高精度マッピング分析 - Mercury Mapping Engine</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
            .header {{ background: #2196F3; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .success {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 5px solid #4caf50; }}
            .error {{ background: #ffe6e6; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 5px solid #f44336; }}
            .warning {{ background: #fff3e0; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 5px solid #ff9800; }}
            .info {{ background: #e3f2fd; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 5px solid #2196f3; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f0f0f0; font-weight: bold; }}
            .confidence-high {{ color: #4caf50; font-weight: bold; }}
            .confidence-medium {{ color: #ff9800; font-weight: bold; }}
            .confidence-low {{ color: #f44336; font-weight: bold; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
            .metric-value {{ font-size: 2em; font-weight: bold; color: #2196f3; }}
            .nav-links {{ margin: 20px 0; }}
            .nav-links a {{ margin-right: 15px; padding: 8px 16px; background: #2196f3; color: white; text-decoration: none; border-radius: 4px; }}
            .nav-links a:hover {{ background: #1976d2; }}
            details {{ margin: 20px 0; }}
            summary {{ cursor: pointer; font-weight: bold; padding: 10px; background: #f0f0f0; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 カードベース高精度マッピング分析</h1>
            <p>Mercury Mapping Engine v2.0 - 新アーキテクチャ</p>
        </div>
    """
    
    # データ概要
    html += f"""
    <h2>📊 データ概要</h2>
    <div class="stats-grid">
        <div class="stat-card">
            <div class="metric-value">{analysis_a['total_rows']}</div>
            <div>A社レコード数</div>
        </div>
        <div class="stat-card">
            <div class="metric-value">{analysis_b['total_rows']}</div>
            <div>B社レコード数</div>
        </div>
        <div class="stat-card">
            <div class="metric-value">{len(analysis_a['headers'])}</div>
            <div>A社フィールド数</div>
        </div>
        <div class="stat-card">
            <div class="metric-value">{len(analysis_b['headers'])}</div>
            <div>B社フィールド数</div>
        </div>
    </div>
    
    <details>
    <summary>📋 フィールド詳細</summary>
    <h3>A社フィールド</h3>
    <p>{', '.join(analysis_a['headers'])}</p>
    <h3>B社フィールド</h3>
    <p>{', '.join(analysis_b['headers'])}</p>
    </details>
    """
    
    # カードベース分析結果
    if card_analysis_success:
        html += _build_success_analysis_section(enhanced_mappings, card_matches, mapping_summary, validation_result)
    else:
        html += _build_error_analysis_section(card_analysis_error)
    
    # ナビゲーション
    html += f"""
    <div class="nav-links">
        <a href="/">🏠 トップページ</a>
        <a href="/test/files">📊 従来分析との比較</a>
        <a href="/test/models">🤖 Claude モデル一覧</a>
        <a href="/api/health">💚 システム状態確認</a>
    </div>
    
    <footer style="margin-top: 40px; padding: 20px; background: #f0f0f0; text-align: center; border-radius: 8px;">
        <p>Mercury Mapping Engine v2.0 | 使用モデル: {selected_model}</p>
        <p>高精度カードベース分析 | 新アーキテクチャ実装</p>
    </footer>
    
    </body>
    </html>
    """
    
    return html


def _build_success_analysis_section(enhanced_mappings, card_matches, mapping_summary, validation_result):
    """成功時の分析セクション生成"""
    
    html = f"""
    <h2>🎯 カードベース分析結果</h2>
    <div class="success">
        <h3>✅ 分析成功</h3>
        <p><strong>マッチしたカード数:</strong> {len(card_matches)}件</p>
        <p><strong>検出されたフィールドマッピング:</strong> {len(enhanced_mappings)}件</p>
    </div>
    """
    
    # マッピング品質統計
    if mapping_summary:
        quality = mapping_summary['mapping_quality']
        html += f"""
        <h3>📈 マッピング品質統計</h3>
        <div class="stats-grid">
            <div class="stat-card">
                <div class="metric-value confidence-high">{quality['high_confidence_count']}</div>
                <div>高信頼度マッピング</div>
            </div>
            <div class="stat-card">
                <div class="metric-value confidence-medium">{quality['medium_confidence_count']}</div>
                <div>中信頼度マッピング</div>
            </div>
            <div class="stat-card">
                <div class="metric-value">{quality['average_confidence']:.3f}</div>
                <div>平均信頼度</div>
            </div>
            <div class="stat-card">
                <div class="metric-value">{quality['coverage_ratio_a']:.1%}</div>
                <div>A社フィールドカバレッジ</div>
            </div>
        </div>
        """
    
    # 高精度フィールドマッピング
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
        
        for mapping in enhanced_mappings[:15]:  # 上位15件表示
            confidence = mapping.get('confidence', 0.0)
            confidence_class = "confidence-high" if confidence > 0.8 else "confidence-medium" if confidence > 0.6 else "confidence-low"

            html += f"""
            <tr>
                <td>{mapping.get('field_type', 'unknown')}</td>
                <td><strong>{mapping.get('company_a_field', '')}</strong></td>
                <td><strong>{mapping.get('company_b_field', '')}</strong></td>
                <td class="{confidence_class}">{mapping.get('confidence', 0.0):.3f}</td>
                <td>{mapping.get('sample_count', 'N/A')}</td>
                <td>{mapping.get('high_matches', 'N/A')}/{mapping.get('sample_count', 'N/A')}</td>
            </tr>
            """
        
        html += "</table>"
    
    # マッチしたカードサンプル
    if card_matches:
        html += """
        <details>
        <summary>🔍 マッチしたカードサンプル</summary>
        <table>
        <tr>
            <th>A社データ</th>
            <th>B社データ</th>
            <th>マッチスコア</th>
        </tr>
        """
        
        for i, match in enumerate(card_matches[:5]):  # 上位5件表示
            a_preview = ', '.join([f"{k}='{str(v)[:20]}'" for k, v in list(match.get('row_a_data', {}).items())[:3]])
            b_preview = ', '.join([f"{k}='{str(v)[:20]}'" for k, v in list(match.get('row_b_data', {}).items())[:3]])
            
            html += f"""
            <tr>
                <td style="font-size: 12px;">{a_preview}...</td>
                <td style="font-size: 12px;">{b_preview}...</td>
                <td class="confidence-high">{match.get('match_score', 0.0):.3f}</td>
            </tr>
            """
        
        html += "</table></details>"
    
    # 推奨アクション
    if mapping_summary and 'recommended_actions' in mapping_summary:
        html += """
        <h3>💡 推奨アクション</h3>
        <div class="info">
        """
        for action in mapping_summary['recommended_actions']:
            html += f"<p>{action}</p>"
        html += "</div>"
    
    return html


def _build_error_analysis_section(error_message):
    """エラー時の分析セクション生成"""
    return f"""
    <h2>❌ カードベース分析失敗</h2>
    <div class="error">
        <h3>分析エラー</h3>
        <p><strong>エラー内容:</strong> {error_message or '不明なエラー'}</p>
        <p>データの品質を確認して再度お試しください。</p>
    </div>
    
    <div class="warning">
        <h3>🔧 トラブルシューティング</h3>
        <ul>
            <li>カード名フィールドが適切に設定されているか確認</li>
            <li>データ内に同じカードが十分な数存在するか確認</li>
            <li>文字エンコーディングが正しいか確認</li>
            <li>データフォーマットの整合性を確認</li>
        </ul>
    </div>
    """


def _render_error_page(title, message, details=None):
    """エラーページの生成"""
    details_html = f"<details><summary>詳細情報</summary><pre>{details}</pre></details>" if details else ""
    
    return f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title} - Mercury Mapping Engine</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 40px; }}
            .error {{ color: #d32f2f; background: #ffe6e6; padding: 20px; border-radius: 8px; border-left: 5px solid #f44336; }}
            .nav {{ margin: 20px 0; }}
            .nav a {{ padding: 8px 16px; background: #2196f3; color: white; text-decoration: none; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="error">
            <h1>{title}</h1>
            <p>{message}</p>
            {details_html}
        </div>
        <div class="nav">
            <a href="/">← トップページに戻る</a>
        </div>
    </body>
    </html>
    """