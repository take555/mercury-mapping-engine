"""
Mercury Mapping Engine - Enhanced Analysis Web Routes
高精度分析Webページルート
"""
from flask import Blueprint, request, current_app
from typing import List, Dict
import os
import time
import traceback
import csv
import json
import requests
from core import create_mapping_engine
from core.flexible_matching import flexible_enhanced_matching
from config.settings import Config
from utils.logger import analysis_logger, performance_logger

# ブループリント作成
enhanced_bp = Blueprint('enhanced', __name__)


@enhanced_bp.route('/test/files/enhanced', methods=['GET', 'POST'])
def enhanced_analysis():
    """カードベース分析フォーム表示と分析実行"""
    from flask import current_app
    current_app.logger.info("🔥 高精度CSV分析ページ アクセス")
    current_app.logger.info(f"   - リクエストメソッド: {request.method}")
    current_app.logger.info(f"   - アクセス元IP: {request.remote_addr}")
    current_app.logger.info(f"   - User-Agent: {request.headers.get('User-Agent', 'Unknown')[:100]}...")
    
    if request.method == 'GET':
        # GET: フォーム表示
        current_app.logger.info("   - フォーム表示モード")
        return _build_enhanced_analysis_form()
    else:
        # POST: 分析実行
        current_app.logger.info("   - 分析実行モード")
        return _handle_enhanced_analysis_post()


def _handle_enhanced_analysis_post():
    """POST処理 - 詳細ログ付きファイルアップロードと分析実行"""
    performance_logger.start_timer('enhanced_analysis_page')

    try:
        analysis_logger.logger.info("=" * 60)
        analysis_logger.logger.info("🚀 ENHANCED ANALYSIS START")
        analysis_logger.logger.info("=" * 60)

        # フォームデータ取得
        similarity_mode = request.form.get('similarity_mode', 'library')
        max_sample_size = int(request.form.get('max_sample_size', 100))
        full_analysis = request.form.get('full_analysis') == 'on'
        # デフォルトモデルを動的に取得（最初のモデル）
        available_models = _get_available_claude_models()
        default_model = available_models[0]['id'] if available_models else 'claude-sonnet-4-20250514'
        ai_model = request.form.get('ai_model', default_model)

        analysis_logger.logger.info(f"📋 設定情報:")
        analysis_logger.logger.info(f"   - 分析モード: {similarity_mode}")
        analysis_logger.logger.info(f"   - サンプルサイズ: {max_sample_size}")
        analysis_logger.logger.info(f"   - フル分析: {full_analysis}")
        analysis_logger.logger.info(f"   - AIモデル: {ai_model}")

        # ファイルアップロード処理
        analysis_logger.logger.info("📁 Step 1: ファイルアップロード処理開始")
        file_a = request.files.get('file_a')
        file_b = request.files.get('file_b')

        if not file_a or not file_b:
            analysis_logger.logger.error("❌ ファイルアップロードエラー: 両方のファイルが必要")
            return _render_error_page("ファイルエラー", "両方のCSVファイルを選択してください")

        analysis_logger.logger.info(f"   - ファイルA: {file_a.filename} ({file_a.content_length} bytes)")
        analysis_logger.logger.info(f"   - ファイルB: {file_b.filename} ({file_b.content_length} bytes)")

        # ファイル保存
        upload_dir = '/app/uploads'
        os.makedirs(upload_dir, exist_ok=True)

        file_a_path = os.path.join(upload_dir, f'uploaded_a_{int(time.time())}.csv')
        file_b_path = os.path.join(upload_dir, f'uploaded_b_{int(time.time())}.csv')

        file_a.save(file_a_path)
        file_b.save(file_b_path)
        analysis_logger.logger.info("✅ ファイル保存完了")

        # 新しいMappingEngineを作成
        analysis_logger.logger.info("🔧 Step 2: MappingEngine初期化開始")
        config = Config.get_analysis_config()
        engine = create_mapping_engine(config)
        analysis_logger.logger.info("✅ MappingEngine初期化完了")

        # AI Manager初期化（AI modeの場合）
        ai_manager = None
        if similarity_mode == 'ai':
            analysis_logger.logger.info("🤖 Step 2.1: AI Manager初期化開始")
            try:
                from ai import create_ai_manager
                ai_config = {
                    'claude_config': {
                        'default_model': ai_model
                    }
                }
                ai_manager = create_ai_manager(ai_config)
                analysis_logger.logger.info(f"✅ AI Manager初期化完了: {ai_model}")
            except Exception as e:
                analysis_logger.logger.error(f"❌ AI Manager初期化失敗: {e}")
                return _render_error_page("AI設定エラー", f"Claude AI の初期化に失敗しました: {str(e)}")

        # CSV分析
        analysis_logger.logger.info("📊 Step 3: CSV分析開始")
        start_time = time.time()

        csv_result = engine.analyze_csv_files(file_a_path, file_b_path, full_analysis=full_analysis)

        csv_time = time.time() - start_time
        analysis_logger.logger.info(f"✅ CSV分析完了 ({csv_time:.2f}秒)")

        if 'error' in csv_result:
            analysis_logger.logger.error(f"❌ CSV分析エラー: {csv_result['error']}")
            return _render_error_page("CSV分析エラー", csv_result['error'])

        analysis_a = csv_result['analysis_a']
        analysis_b = csv_result['analysis_b']

        analysis_logger.logger.info(f"📋 CSV分析結果:")
        analysis_logger.logger.info(f"   - A社: {len(analysis_a['headers'])}フィールド, {analysis_a['total_rows']}行")
        analysis_logger.logger.info(f"   - B社: {len(analysis_b['headers'])}フィールド, {analysis_b['total_rows']}行")
        analysis_logger.logger.info(f"   - A社ヘッダー: {analysis_a['headers'][:5]}...")
        analysis_logger.logger.info(f"   - B社ヘッダー: {analysis_b['headers'][:5]}...")

        # 🚀 2段階マッチングシステム実行（高速化版）
        analysis_logger.logger.info("🚀 Step 4: 2段階マッチングシステム開始")
        start_time = time.time()

        try:
            data_a = analysis_a.get('full_data', analysis_a['sample_data'])
            data_b = analysis_b.get('full_data', analysis_b['sample_data'])

            analysis_logger.logger.info(f"📊 マッチング対象データ:")
            analysis_logger.logger.info(f"   - A社データ: {len(data_a)}行")
            analysis_logger.logger.info(f"   - B社データ: {len(data_b)}行")
            analysis_logger.logger.info(f"   - 新手法: AI/文字列類似度による柔軟なデータマッチング")

            # Claude Mapping Modeの場合は先にフィールドマッピングを取得
            if similarity_mode == 'claude_mapping':
                analysis_logger.logger.info("🧠 Claude APIフィールドマッピング分析開始")
                claude_mappings = _claude_field_mapping_analysis(
                    analysis_a['headers'], 
                    analysis_b['headers'], 
                    data_a[:10],  # サンプルデータ
                    data_b[:10],
                    ai_model  # 選択されたモデルを渡す
                )
                
                if claude_mappings:
                    analysis_logger.logger.info(f"✅ Claude マッピング取得: {len(claude_mappings)}件")
                    # Claudeマッピングを使って同一カード特定
                    matches = _match_cards_with_claude_mappings(
                        data_a, data_b, claude_mappings, max_sample_size
                    )
                    # enhanced_mappingsを辞書形式で作成
                    enhanced_mappings = {
                        'flexible_field_mappings': claude_mappings,
                        'matching_strategy': 'claude_mapping',
                        'similarity_threshold': 0.8,
                        'total_comparisons': len(data_a) * len(data_b),
                        'match_count': len(matches)
                    }
                else:
                    analysis_logger.logger.warning("⚠️ Claude マッピング失敗、従来手法にフォールバック")
                    # フォールバック: 柔軟マッチング実行
                    matches, enhanced_mappings = flexible_enhanced_matching(
                        data_a, data_b, analysis_a['headers'], analysis_b['headers'], max_sample_size
                    )
            else:
                # 柔軟マッチング実行 (AI/文字列類似度ベース)
                matches, enhanced_mappings = flexible_enhanced_matching(
                    data_a,
                    data_b,
                    analysis_a['headers'],
                    analysis_b['headers'],
                    max_sample_size=max_sample_size
                )

            matching_time = time.time() - start_time
            analysis_logger.logger.info(f"✅ 柔軟マッチング完了 ({matching_time:.2f}秒)")
            # enhanced_mappingsは辞書形式で返される
            field_mappings = enhanced_mappings.get('flexible_field_mappings', [])
            analysis_logger.logger.info(f"🎯 結果: {len(matches)}件の同一カード, {len(field_mappings)}件のフィールドマッピング")

            # フィールドマッピングは柔軟マッチングで既に完了
            analysis_logger.logger.info("✅ Step 5: フィールドマッピング分析は柔軟マッチングで完了済み")
            analysis_logger.logger.info(f"   - 戦略: {enhanced_mappings.get('matching_strategy', 'unknown')}")
            analysis_logger.logger.info(f"   - 類似度閾値: {enhanced_mappings.get('similarity_threshold', 0.0)}")
            analysis_logger.logger.info(f"   - 総比較回数: {enhanced_mappings.get('total_comparisons', 0):,}回")

            # CSV出力機能を追加
            try:
                _export_matches_to_csv(matches, enhanced_mappings, analysis_a['headers'], analysis_b['headers'], data_a, data_b)
                analysis_logger.logger.info("✅ マッチングデータをresults/test.csvに出力しました")
            except Exception as e:
                analysis_logger.logger.error(f"❌ CSV出力エラー: {e}")

            card_analysis_success = True

        except Exception as e:
            analysis_logger.logger.error(f"❌ Brute Force分析エラー: {e}")
            analysis_logger.logger.error(f"   - エラー詳細: {traceback.format_exc()}")
            enhanced_mappings = {'flexible_field_mappings': [], 'matching_strategy': 'error', 'match_count': 0}
            matches = []
            card_analysis_success = False
            card_analysis_error = str(e)

        # マッピングサマリー作成（詳細ログ付き）
        analysis_logger.logger.info("📋 Step 6: マッピングサマリー作成開始")
        start_time = time.time()

        if enhanced_mappings and isinstance(enhanced_mappings, dict):
            try:
                field_mappings = enhanced_mappings.get('flexible_field_mappings', [])
                analysis_logger.logger.info(f"   - enhanced_mappings: {len(field_mappings)}件")
                analysis_logger.logger.info(f"   - matches: {len(matches)}件")

                # 柔軟マッチングの結果をマッピングエンジンに渡すため形式変換
                field_mappings = enhanced_mappings.get('flexible_field_mappings', [])
                mapping_list = []
                for mapping in field_mappings:
                    # タプル形式と辞書形式の両方に対応
                    if isinstance(mapping, (list, tuple)) and len(mapping) >= 3:
                        # タプル形式: (field_a, field_b, score)
                        mapping_list.append({
                            'field_a': mapping[0],
                            'field_b': mapping[1],
                            'confidence': mapping[2],
                            'field_type': 'flexible',
                            'sample_count': 'auto'
                        })
                    elif isinstance(mapping, dict):
                        # 辞書形式（Claude APIから）
                        mapping_list.append({
                            'field_a': mapping.get('field_a', ''),
                            'field_b': mapping.get('field_b', ''),
                            'confidence': mapping.get('confidence', 0),
                            'field_type': mapping.get('field_type', 'claude_api_analysis'),
                            'sample_count': mapping.get('sample_count', 'auto')
                        })
                
                mapping_summary = engine.create_mapping_summary(mapping_list, matches, analysis_a, analysis_b)
                validation_result = engine.validate_mapping_results(mapping_list, matches)

                analysis_logger.logger.info("✅ マッピングサマリー作成完了")
            except Exception as e:
                analysis_logger.logger.error(f"❌ マッピングサマリー作成エラー: {e}")
                analysis_logger.logger.error(f"   - エラー詳細: {traceback.format_exc()}")
                mapping_summary = None
                validation_result = None
        else:
            mapping_summary = None
            validation_result = None
            analysis_logger.logger.info("   - マッピングなし: サマリー作成スキップ")

        summary_time = time.time() - start_time
        analysis_logger.logger.info(f"✅ マッピングサマリー完了 ({summary_time:.2f}秒)")

        # HTML生成（詳細ログ付き）
        analysis_logger.logger.info("🎨 Step 7: HTML生成開始")
        start_time = time.time()

        try:
            html = _build_enhanced_analysis_html(
                analysis_a, analysis_b, enhanced_mappings, matches,
                card_analysis_success, locals().get('card_analysis_error'),
                mapping_summary, validation_result, ai_model, similarity_mode
            )

            html_time = time.time() - start_time
            analysis_logger.logger.info(f"✅ HTML生成完了 ({html_time:.2f}秒)")

        except Exception as e:
            analysis_logger.logger.error(f"❌ HTML生成エラー: {e}")
            analysis_logger.logger.error(f"   - エラー詳細: {traceback.format_exc()}")
            return _render_error_page("HTML生成エラー", str(e))

        total_time = performance_logger.end_timer('enhanced_analysis_page')
        analysis_logger.logger.info("=" * 60)
        analysis_logger.logger.info(f"🏁 ENHANCED ANALYSIS COMPLETE - 総実行時間: {total_time:.2f}秒")
        analysis_logger.logger.info("=" * 60)

        return html

    except Exception as e:
        analysis_logger.logger.error("=" * 60)
        analysis_logger.logger.error(f"💥 CRITICAL ERROR: {e}")
        analysis_logger.logger.error(f"エラー詳細: {traceback.format_exc()}")
        analysis_logger.logger.error("=" * 60)
        current_app.logger.error(f"システムエラー: {e}")
        return _render_error_page("システムエラー", str(e), traceback.format_exc())


def _get_available_claude_models():
    """Claude API Models APIから利用可能なモデル一覧を取得"""
    try:
        api_key = os.environ.get('CLAUDE_API_KEY')
        if not api_key:
            # フォールバック: 静的リスト
            return [
                {'id': 'claude-sonnet-4-20250514', 'display_name': 'Claude 4 Sonnet (最新・最高性能)'},
                {'id': 'claude-3-5-sonnet-20241022', 'display_name': 'Claude 3.5 Sonnet (高性能・推奨)'},
                {'id': 'claude-3-5-haiku-20241022', 'display_name': 'Claude 3.5 Haiku (超高速・低コスト)'},
            ]
        
        headers = {
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        }
        
        from flask import current_app
        current_app.logger.info("🔍 Claude Models API でモデル一覧を取得中...")
        
        response = requests.get('https://api.anthropic.com/v1/models', headers=headers, timeout=10)
        
        if response.status_code == 200:
            data = response.json()
            models = []
            
            # モデルを新しい順にソート（created_atが新しい順）
            sorted_models = sorted(data.get('data', []), key=lambda x: x.get('created_at', ''), reverse=True)
            
            for model in sorted_models:
                model_id = model.get('id', '')
                display_name = model.get('display_name', model_id)
                
                # 説明を追加
                description = ""
                if 'sonnet-4' in model_id.lower():
                    description = " (最新・最高性能)"
                elif '3.5-sonnet' in model_id.lower():
                    description = " (高性能・推奨)"  
                elif '3.5-haiku' in model_id.lower():
                    description = " (超高速・低コスト)"
                elif 'opus' in model_id.lower():
                    description = " (旧最高性能)"
                elif 'sonnet' in model_id.lower() and '3-sonnet' in model_id.lower():
                    description = " (旧版)"
                elif 'haiku' in model_id.lower() and '3-haiku' in model_id.lower():
                    description = " (旧版)"
                
                models.append({
                    'id': model_id,
                    'display_name': f"{display_name}{description}"
                })
            
            current_app.logger.info(f"✅ {len(models)}個のモデルを取得")
            return models
        else:
            current_app.logger.warning(f"⚠️ Models API失敗: {response.status_code}, フォールバック使用")
            # フォールバック: 静的リスト
            return [
                {'id': 'claude-sonnet-4-20250514', 'display_name': 'Claude 4 Sonnet (最新・最高性能)'},
                {'id': 'claude-3-5-sonnet-20241022', 'display_name': 'Claude 3.5 Sonnet (高性能・推奨)'},
                {'id': 'claude-3-5-haiku-20241022', 'display_name': 'Claude 3.5 Haiku (超高速・低コスト)'},
            ]
            
    except Exception as e:
        from flask import current_app
        current_app.logger.error(f"❌ Models API エラー: {e}")
        # フォールバック: 静的リスト
        return [
            {'id': 'claude-sonnet-4-20250514', 'display_name': 'Claude 4 Sonnet (最新・最高性能)'},
            {'id': 'claude-3-5-sonnet-20241022', 'display_name': 'Claude 3.5 Sonnet (高性能・推奨)'},
            {'id': 'claude-3-5-haiku-20241022', 'display_name': 'Claude 3.5 Haiku (超高速・低コスト)'},
        ]

def _build_enhanced_analysis_form() -> str:
    """高精度分析フォーム（プログレス表示付き）"""
    # 利用可能なモデルを動的に取得
    available_models = _get_available_claude_models()
    model_options = ""
    
    for i, model in enumerate(available_models):
        selected = 'selected' if i == 0 else ''  # 最初のモデル（最新）をデフォルト選択
        model_options += f'                                <option value="{model["id"]}" {selected}>{model["display_name"]}</option>\n'
    
    # HTMLテンプレートを取得してモデル部分を置換
    html_template = _get_html_template()
    return html_template.replace("{{MODEL_OPTIONS}}", model_options)

def _get_html_template():
    """HTMLテンプレートを返す（raw string使用）"""
    return r"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🔥 高精度CSV分析 - Mercury Mapping Engine</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; background: #f5f5f5; }
            .container { max-width: 800px; margin: 0 auto; background: white; padding: 30px; border-radius: 12px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
            .header { background: linear-gradient(135deg, #2196F3, #1976D2); color: white; padding: 25px; border-radius: 8px; margin-bottom: 30px; text-align: center; }
            .header h1 { margin: 0; font-size: 2em; }
            .header p { margin: 10px 0 0 0; opacity: 0.9; }

            .file-inputs { margin: 25px 0; }
            .file-group { margin: 15px 0; }
            .file-group label { display: block; margin-bottom: 8px; font-weight: 500; color: #333; }
            .file-group input[type="file"] { width: 100%; padding: 12px; border: 2px dashed #ccc; border-radius: 6px; background: #fafafa; transition: border-color 0.3s; }
            .file-group input[type="file"]:hover { border-color: #2196F3; }

            .analysis-mode-section { margin: 25px 0; padding: 20px; background: #f8f9fa; border-radius: 8px; }
            .mode-options { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; margin-top: 20px; }
            .mode-option { position: relative; }
            .mode-option input[type="radio"] { position: absolute; opacity: 0; width: 0; height: 0; }

            .mode-label { display: block; padding: 20px; border: 2px solid #e0e0e0; border-radius: 10px; cursor: pointer; transition: all 0.3s ease; background: white; }
            .mode-option input[type="radio"]:checked + .mode-label { border-color: #2196F3; background: #f0f8ff; box-shadow: 0 4px 12px rgba(33,150,243,0.15); }

            .mode-header { display: flex; align-items: center; gap: 10px; margin-bottom: 12px; }
            .mode-icon { font-size: 1.4em; }
            .mode-badge { padding: 4px 10px; border-radius: 15px; font-size: 0.8em; font-weight: bold; margin-left: auto; }
            .mode-badge.free { background: #d4edda; color: #155724; }
            .mode-badge.premium { background: #fff3cd; color: #856404; }

            .mode-description ul { margin: 10px 0; padding-left: 20px; font-size: 0.9em; color: #555; }
            .mode-description li { margin: 5px 0; }

            .advanced-settings { margin: 25px 0; padding: 20px; background: #ffffff; border: 1px solid #e0e0e0; border-radius: 8px; }
            .settings-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 20px; margin-top: 15px; }
            .setting-item label { display: block; margin-bottom: 8px; font-weight: 500; color: #333; }
            .setting-item select, .setting-item input { width: 100%; padding: 10px; border: 1px solid #ccc; border-radius: 6px; }

            .ai-only { opacity: 0.5; transition: opacity 0.3s ease; }

            .submit-section { text-align: center; margin-top: 35px; position: relative; }
            .btn-analyze { 
                background: linear-gradient(135deg, #2196F3, #1976D2); 
                color: white; border: none; padding: 15px 40px; border-radius: 8px; 
                font-size: 1.2em; cursor: pointer; display: inline-flex; 
                align-items: center; gap: 10px; transition: all 0.3s ease; 
                box-shadow: 0 4px 12px rgba(33,150,243,0.3);
                position: relative;
            }
            .btn-analyze:hover:not(:disabled) { 
                background: linear-gradient(135deg, #1976D2, #1565C0); 
                transform: translateY(-2px); 
                box-shadow: 0 6px 16px rgba(33,150,243,0.4); 
            }
            .btn-analyze:disabled {
                background: #ccc;
                cursor: not-allowed;
                transform: none;
                box-shadow: none;
            }

            /* ローディング表示 */
            .loading-overlay {
                display: none;
                position: fixed;
                top: 0; left: 0; right: 0; bottom: 0;
                background: rgba(0,0,0,0.7);
                z-index: 9999;
                align-items: center;
                justify-content: center;
            }

            .loading-container {
                background: white;
                padding: 40px;
                border-radius: 12px;
                text-align: center;
                max-width: 500px;
                box-shadow: 0 8px 32px rgba(0,0,0,0.3);
            }

            .loading-spinner {
                width: 60px;
                height: 60px;
                border: 4px solid #e0e0e0;
                border-left: 4px solid #2196F3;
                border-radius: 50%;
                animation: spin 1s linear infinite;
                margin: 0 auto 20px;
            }

            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }

            .progress-container {
                margin: 20px 0;
            }

            .progress-bar {
                width: 100%;
                height: 8px;
                background: #e0e0e0;
                border-radius: 4px;
                overflow: hidden;
            }

            .progress-fill {
                height: 100%;
                background: linear-gradient(90deg, #2196F3, #21CBF3);
                width: 0%;
                transition: width 0.3s ease;
                animation: progress-shimmer 2s infinite;
            }

            @keyframes progress-shimmer {
                0% { background-position: -200px 0; }
                100% { background-position: 200px 0; }
            }

            .loading-steps {
                text-align: left;
                margin: 20px 0;
            }

            .loading-step {
                padding: 8px 0;
                display: flex;
                align-items: center;
                gap: 10px;
                opacity: 0.5;
                transition: opacity 0.3s ease;
            }

            .loading-step.active {
                opacity: 1;
                color: #2196F3;
                font-weight: 500;
            }

            .loading-step.completed {
                opacity: 0.7;
                color: #4CAF50;
            }

            .step-icon {
                width: 20px;
                height: 20px;
                border-radius: 50%;
                background: #e0e0e0;
                display: flex;
                align-items: center;
                justify-content: center;
                font-size: 12px;
                font-weight: bold;
            }

            .loading-step.active .step-icon {
                background: #2196F3;
                color: white;
                animation: pulse 1.5s infinite;
            }

            .loading-step.completed .step-icon {
                background: #4CAF50;
                color: white;
            }

            @keyframes pulse {
                0% { transform: scale(1); }
                50% { transform: scale(1.1); }
                100% { transform: scale(1); }
            }

            .estimated-time {
                margin: 15px 0;
                padding: 12px;
                background: #f0f8ff;
                border-radius: 6px;
                font-size: 0.9em;
                color: #1976D2;
            }

            .cancel-btn {
                background: #f44336;
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                cursor: pointer;
                margin-top: 15px;
            }

            .analysis-info { margin-top: 20px; color: #666; font-size: 0.9em; }
            .nav-links { margin-top: 30px; text-align: center; }
            .nav-links a { margin: 0 10px; padding: 8px 16px; background: #6c757d; color: white; text-decoration: none; border-radius: 4px; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔥 高精度CSV分析</h1>
                <p>Mercury Mapping Engine v2.0 - Brute Force Matching</p>
            </div>

            <form method="post" enctype="multipart/form-data" class="analysis-form" id="analysisForm">
                <div class="file-inputs">
                    <div class="file-group">
                        <label for="file_a">📄 A社CSVファイル:</label>
                        <input type="file" id="file_a" name="file_a" accept=".csv" required>
                    </div>

                    <div class="file-group">
                        <label for="file_b">📄 B社CSVファイル:</label>
                        <input type="file" id="file_b" name="file_b" accept=".csv" required>
                    </div>
                </div>

                <div class="analysis-mode-section">
                    <h3>⚙️ 分析モード選択</h3>
                    <div class="mode-options">
                        <div class="mode-option">
                            <input type="radio" id="mode_library" name="similarity_mode" value="library" checked>
                            <label for="mode_library" class="mode-label">
                                <div class="mode-header">
                                    <span class="mode-icon">🐍</span>
                                    <strong>Library Mode</strong>
                                    <span class="mode-badge free">無料</span>
                                </div>
                                <div class="mode-description">
                                    <p>Python ライブラリベースの高速分析</p>
                                    <ul>
                                        <li>✅ 高速処理（数秒〜数分）</li>
                                        <li>✅ 無制限使用</li>
                                        <li>✅ 文字列・数値類似度</li>
                                        <li>⚡ おすすめ: 初回分析・大量処理</li>
                                    </ul>
                                </div>
                            </label>
                        </div>

                        <div class="mode-option">
                            <input type="radio" id="mode_ai" name="similarity_mode" value="ai">
                            <label for="mode_ai" class="mode-label">
                                <div class="mode-header">
                                    <span class="mode-icon">🤖</span>
                                    <strong>AI Mode</strong>
                                    <span class="mode-badge premium">Premium</span>
                                </div>
                                <div class="mode-description">
                                    <p>Claude AI による意味理解分析</p>
                                    <ul>
                                        <li>✅ 意味的類似度判定</li>
                                        <li>✅ 文脈・ビジネスロジック理解</li>
                                        <li>✅ 多言語対応（英⇔日）</li>
                                        <li>💰 API使用料: ~$0.01-0.05</li>
                                        <li>🎯 おすすめ: 高精度が必要な場合</li>
                                    </ul>
                                </div>
                            </label>
                        </div>

                        <div class="mode-option">
                            <input type="radio" id="mode_claude_mapping" name="similarity_mode" value="claude_mapping">
                            <label for="mode_claude_mapping" class="mode-label">
                                <div class="mode-header">
                                    <span class="mode-icon">🧠</span>
                                    <strong>Claude Mapping Mode</strong>
                                    <span class="mode-badge new">New</span>
                                </div>
                                <div class="mode-description">
                                    <p>Claude AIによる直感的フィールドマッピング</p>
                                    <ul>
                                        <li>✅ 人間的な判断でフィールド対応を決定</li>
                                        <li>✅ 概念的・意味的関連性を理解</li>
                                        <li>✅ 信頼度付きマッピング結果</li>
                                        <li>💰 API使用料: ~$0.005-0.02</li>
                                        <li>🎯 おすすめ: 新しいCSVペアの分析</li>
                                    </ul>
                                </div>
                            </label>
                        </div>
                    </div>
                </div>

                <div class="advanced-settings">
                    <h3>🔧 詳細設定</h3>
                    <div class="settings-grid">
                        <div class="setting-item">
                            <label for="sample_size">同一カードデータ取得数:</label>
                            <select id="sample_size" name="max_sample_size">
                                <option value="100" selected>100件 (高速)</option>
                                <option value="200">200件</option>
                                <option value="300">300件</option>
                                <option value="400">400件</option>
                                <option value="500">500件 (推奨)</option>
                                <option value="600">600件</option>
                                <option value="700">700件</option>
                                <option value="800">800件</option>
                                <option value="900">900件</option>
                                <option value="1000">1000件 (最大)</option>
                            </select>
                        </div>

                        <div class="setting-item">
                            <label>
                                <input type="checkbox" id="full_analysis" name="full_analysis" checked>
                                フル分析実行
                            </label>
                        </div>

                        <div class="setting-item ai-only" style="display: none;">
                            <label for="ai_model">AIモデル:</label>
                            <select id="ai_model" name="ai_model">
{{MODEL_OPTIONS}}                            </select>
                        </div>
                    </div>
                </div>

                <div class="submit-section">
                    <button type="submit" class="btn-analyze" id="analyzeBtn">
                        <span class="btn-icon">🚀</span>
                        <span class="btn-text">分析開始</span>
                    </button>
                    <div class="analysis-info">
                        <p class="info-text">選択されたモードで高精度分析を実行します</p>
                    </div>
                </div>
            </form>

            <div class="nav-links">
                <a href="/">🏠 トップページ</a>
                <a href="/test/claude">🤖 Claude接続テスト</a>
                <a href="/test/models">📊 モデル一覧</a>
                <a href="/api/health">💚 システム状態</a>
            </div>
        </div>

        <!-- ローディングオーバーレイ -->
        <div class="loading-overlay" id="loadingOverlay">
            <div class="loading-container">
                <div class="loading-spinner"></div>
                <h3 id="loadingTitle">🔥 分析実行中...</h3>

                <div class="progress-container">
                    <div class="progress-bar">
                        <div class="progress-fill" id="progressFill"></div>
                    </div>
                </div>

                <div class="estimated-time" id="estimatedTime">
                    推定残り時間: 計算中...
                </div>

                <div class="loading-steps">
                    <div class="loading-step active" id="step1">
                        <div class="step-icon">1</div>
                        <span>ファイルアップロード</span>
                    </div>
                    <div class="loading-step" id="step2">
                        <div class="step-icon">2</div>
                        <span>CSV構造解析</span>
                    </div>
                    <div class="loading-step" id="step3">
                        <div class="step-icon">3</div>
                        <span id="step3Text">力技マッチング実行</span>
                    </div>
                    <div class="loading-step" id="step4">
                        <div class="step-icon">4</div>
                        <span>フィールドマッピング分析</span>
                    </div>
                    <div class="loading-step" id="step5">
                        <div class="step-icon">5</div>
                        <span>結果統合・表示</span>
                    </div>
                </div>

                <div style="margin-top: 20px; font-size: 0.9em; color: #666;">
                    <p id="processingNote">データを分析中です。しばらくお待ちください...</p>
                </div>
            </div>
        </div>

        <script>
        document.addEventListener('DOMContentLoaded', function() {
            const libraryMode = document.getElementById('mode_library');
            const aiMode = document.getElementById('mode_ai');
            const claudeMappingMode = document.getElementById('mode_claude_mapping');
            const aiOnlySettings = document.querySelectorAll('.ai-only');
            const analysisInfo = document.querySelector('.info-text');
            const form = document.getElementById('analysisForm');
            const analyzeBtn = document.getElementById('analyzeBtn');
            const loadingOverlay = document.getElementById('loadingOverlay');

            let currentStep = 1;
            let startTime;

            function updateUI() {
                if (aiMode.checked || claudeMappingMode.checked) {
                    aiOnlySettings.forEach(el => {
                        el.style.display = 'block';
                        el.style.opacity = '1';
                    });
                    if (claudeMappingMode.checked) {
                        analysisInfo.textContent = 'Claude AIによる直感的フィールドマッピングを実行します（API使用料が発生します）';
                        document.getElementById('step3Text').textContent = 'Claude フィールドマッピング';
                    } else {
                        analysisInfo.textContent = 'Claude AIによる高精度意味解析を実行します（API使用料が発生します）';
                        document.getElementById('step3Text').textContent = 'AI意味解析実行';
                    }
                } else {
                    aiOnlySettings.forEach(el => {
                        el.style.display = 'none';
                        el.style.opacity = '0.5';
                    });
                    analysisInfo.textContent = 'Pythonライブラリによる高速分析を実行します（無料）';
                    document.getElementById('step3Text').textContent = '力技マッチング実行';
                }
            }

            function showLoading() {
                loadingOverlay.style.display = 'flex';
                analyzeBtn.disabled = true;
                startTime = Date.now();

                // プログレス更新開始
                simulateProgress();

                // ステップ更新開始
                setTimeout(() => updateStep(2), 1000);
                setTimeout(() => updateStep(3), 3000);
                setTimeout(() => updateStep(4), aiMode.checked ? 15000 : 8000);
                setTimeout(() => updateStep(5), aiMode.checked ? 25000 : 12000);
            }

            function updateStep(step) {
                // 前のステップを完了状態に
                if (currentStep > 1) {
                    const prevStep = document.getElementById(`step${currentStep}`);
                    prevStep.classList.remove('active');
                    prevStep.classList.add('completed');
                    prevStep.querySelector('.step-icon').textContent = '✓';
                }

                // 現在のステップをアクティブに
                if (step <= 5) {
                    const currentStepEl = document.getElementById(`step${step}`);
                    currentStepEl.classList.add('active');
                    currentStep = step;
                }
            }

            function simulateProgress() {
                const progressFill = document.getElementById('progressFill');
                const estimatedTime = document.getElementById('estimatedTime');
                const processingNote = document.getElementById('processingNote');

                let progress = 0;
                const isAI = aiMode.checked;
                const totalTime = isAI ? 30000 : 15000; // AIモード: 30秒, ライブラリモード: 15秒
                const interval = 200;

                const progressInterval = setInterval(() => {
                    const elapsed = Date.now() - startTime;
                    progress = Math.min((elapsed / totalTime) * 100, 95); // 95%まで

                    progressFill.style.width = progress + '%';

                    const remainingTime = Math.max(0, totalTime - elapsed);
                    const remainingSeconds = Math.ceil(remainingTime / 1000);

                    if (remainingSeconds > 0) {
                        estimatedTime.textContent = `推定残り時間: ${remainingSeconds}秒`;
                    } else {
                        estimatedTime.textContent = '最終処理中...';
                    }

                    // ステップ別メッセージ
                    const messages = [
                        'ファイルをアップロード中...',
                        'CSVファイルを解析中...',
                        isAI ? 'Claude AIで意味解析中...' : '力技マッチング実行中...',
                        'フィールドマッピングを生成中...',
                        '結果を統合中...'
                    ];

                    if (currentStep <= messages.length) {
                        processingNote.textContent = messages[currentStep - 1];
                    }

                    if (progress >= 95) {
                        clearInterval(progressInterval);
                    }
                }, interval);
            }

            // フォーム送信時にローディング表示
            form.addEventListener('submit', function(e) {
                // バリデーション
                const fileA = document.getElementById('file_a').files[0];
                const fileB = document.getElementById('file_b').files[0];

                if (!fileA || !fileB) {
                    alert('両方のCSVファイルを選択してください');
                    e.preventDefault();
                    return;
                }

                // ローディング表示
                showLoading();

                // AIモードの場合は警告
                if (aiMode.checked) {
                    document.getElementById('loadingTitle').textContent = '🤖 AI分析実行中...';
                    document.getElementById('processingNote').textContent = 'Claude AIが意味解析を実行中です。高精度な結果をお待ちください...';
                } else {
                    document.getElementById('loadingTitle').textContent = '🐍 高速分析実行中...';
                }
            });

            libraryMode.addEventListener('change', updateUI);
            aiMode.addEventListener('change', updateUI);
            claudeMappingMode.addEventListener('change', updateUI);
            updateUI();
        });
        </script>
    </body>
    </html>
    """


def _build_enhanced_analysis_html(analysis_a, analysis_b, enhanced_mappings, card_matches,
                                  card_analysis_success, card_analysis_error, mapping_summary,
                                  validation_result, selected_model, similarity_mode='library'):
    """拡張分析結果のHTML生成（モード情報追加）"""

    mode_info = {
        'library': '🐍 Python Library Mode',
        'ai': f'🤖 Claude AI Mode ({selected_model})'
    }
    
    # ヘッダー部分（省略：既存のHTMLスタイル）
    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>🎯 分析結果 - Mercury Mapping Engine</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; line-height: 1.6; }}
            .header {{ background: linear-gradient(135deg, #4CAF50, #45a049); color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }}
            .mode-badge {{ display: inline-block; padding: 5px 12px; background: rgba(255,255,255,0.2); border-radius: 20px; margin-left: 10px; font-size: 0.9em; }}
            .success {{ background: #e8f5e8; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 5px solid #4caf50; }}
            .error {{ background: #ffe6e6; padding: 15px; border-radius: 5px; margin: 10px 0; border-left: 5px solid #f44336; }}
            .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 15px; margin: 20px 0; }}
            .stat-card {{ background: #f8f9fa; padding: 15px; border-radius: 8px; text-align: center; }}
            .metric-value {{ font-size: 2em; font-weight: bold; color: #4CAF50; }}
            table {{ border-collapse: collapse; width: 100%; margin: 15px 0; }}
            th, td {{ border: 1px solid #ddd; padding: 12px; text-align: left; }}
            th {{ background-color: #f0f0f0; font-weight: bold; }}
            .confidence-high {{ color: #4caf50; font-weight: bold; }}
            .confidence-medium {{ color: #ff9800; font-weight: bold; }}
            .confidence-low {{ color: #f44336; font-weight: bold; }}
            .row-number {{ color: #666; font-size: 0.8em; background: #f0f0f0; padding: 2px 6px; border-radius: 3px; }}
            .nav-links {{ margin: 20px 0; }}
            .nav-links a {{ margin-right: 15px; padding: 8px 16px; background: #2196f3; color: white; text-decoration: none; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>🎯 高精度分析結果</h1>
            <p>Mercury Mapping Engine v2.0 - Brute Force Matching
            <span class="mode-badge">{mode_info.get(similarity_mode, similarity_mode)}</span>
            </p>
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
    """
    
    # 分析結果表示
    if card_analysis_success:
        html += _build_success_analysis_section(enhanced_mappings, card_matches, mapping_summary, validation_result)
    else:
        html += _build_error_analysis_section(card_analysis_error)

    # ナビゲーション
    html += f"""
    <div class="nav-links">
        <a href="/test/files/enhanced">🔄 新しい分析</a>
        <a href="/">🏠 トップページ</a>
        <a href="/api/health">💚 システム状態</a>
    </div>

    <footer style="margin-top: 40px; padding: 20px; background: #f0f0f0; text-align: center; border-radius: 8px;">
        <p>Mercury Mapping Engine v2.0 | 分析モード: {mode_info.get(similarity_mode, similarity_mode)}</p>
        <p>🔥 Brute Force Matching | 革命的精度向上</p>
    </footer>
    </body>
    </html>
    """

    return html


def _is_rarity_field(field_name: str, data_sample: List[Dict] = None) -> bool:
    """AIベースでレアリティフィールドかどうか判定"""
    if not field_name:
        return False
    
    # フィールド名パターン
    name_lower = str(field_name).lower()
    name_patterns = ['rarity', 'rare', 'レア', '希少', 'star', 'grade', 'rank', 'tier', '等級', 'グレード', 'ランク']
    if any(pattern in name_lower for pattern in name_patterns):
        return True
    
    # データパターン分析（サンプルがある場合）
    if data_sample:
        sample_values = []
        for row in data_sample[:10]:
            value = str(row.get(field_name, '')).strip()
            if value and value != 'nan':
                sample_values.append(value)
        
        if sample_values:
            # レアリティ特有のパターン
            rarity_patterns = ['SR', 'SSR', 'R', 'N', 'UR', 'レア', '★', '☆', 'rare', 'common', 'super']
            for value in sample_values:
                if any(pattern in value.upper() for pattern in rarity_patterns):
                    return True
            
            # 短い文字列で統一されたパターン（レアリティの特徴）
            if all(len(v) <= 5 for v in sample_values) and len(set(sample_values)) <= 10:
                return any(pattern in name_lower for pattern in ['star', '星', 'level', 'grade'])
    
    return False


def _is_serial_field(field_name: str, data_sample: List[Dict] = None) -> bool:
    """AIベースでシリアルフィールドかどうか判定"""
    if not field_name:
        return False
    
    # フィールド名パターン
    name_lower = str(field_name).lower()
    name_patterns = ['serial', 'id', 'code', 'number', 'シリアル', '型番', '番号', 'sku', 'jan', '品番']
    if any(pattern in name_lower for pattern in name_patterns):
        # 名前系フィールドは除外
        if not any(exclude in name_lower for exclude in ['name', '名前', 'title', 'カード名']):
            return True
    
    # データパターン分析（サンプルがある場合）
    if data_sample:
        sample_values = []
        for row in data_sample[:10]:
            value = str(row.get(field_name, '')).strip()
            if value and value != 'nan':
                sample_values.append(value)
        
        if sample_values:
            # 英数字の組み合わせが多い
            alphanumeric_count = sum(1 for v in sample_values if any(c.isalnum() for c in v) and any(c.isdigit() for c in v))
            if alphanumeric_count > len(sample_values) * 0.7:
                return True
            
            # 統一されたフォーマット（PK001, D01001等）
            if len(set(len(v) for v in sample_values)) <= 2:  # 長さが統一されている
                return True
    
    return False


def _export_matches_to_csv(matches, enhanced_mappings, headers_a, headers_b, data_a=None, data_b=None):
    """マッチングデータをCSVファイルに出力（データ数が多い方を基準に全レコード出力）"""
    
    # 出力ディレクトリを作成
    output_dir = '/app/results'
    os.makedirs(output_dir, exist_ok=True)
    
    output_file = os.path.join(output_dir, 'test.csv')
    
    # データ数を確認して、多い方を基準にする
    len_a = len(data_a) if data_a else 0
    len_b = len(data_b) if data_b else 0
    use_a_as_base = len_a >= len_b
    
    # マッチ情報を辞書化（高速検索用）
    match_dict_a_to_b = {}  # A社カードID -> B社カード
    match_dict_b_to_a = {}  # B社カードID -> A社カード
    match_scores = {}  # ペアのマッチスコア
    
    for match in matches:
        card_a = match.get('card_a', {})
        card_b = match.get('card_b', {})
        similarity = match.get('overall_similarity', 0.0)
        
        # ユニークキーを生成（最初の非空フィールドの値を使用）
        key_a = _get_record_key(card_a, headers_a)
        key_b = _get_record_key(card_b, headers_b)
        
        if key_a and key_b:
            match_dict_a_to_b[key_a] = card_b
            match_dict_b_to_a[key_b] = card_a
            match_scores[(key_a, key_b)] = similarity
    
    # CSVヘッダーを構築：A社全フィールド + 区切り + B社全フィールド + マッチスコア
    csv_headers = []
    
    # A社全フィールドを追加
    for header in headers_a:
        csv_headers.append(f"A社_{header}")
    
    # 区切り文字列
    csv_headers.append("____####____")
    
    # B社全フィールドを追加  
    for header in headers_b:
        csv_headers.append(f"B社_{header}")
    
    # マッチスコアを追加
    csv_headers.append("マッチスコア")
    
    # CSVファイルに書き込み
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as csvfile:
        writer = csv.writer(csvfile)
        
        # ヘッダー行を書き込み
        writer.writerow(csv_headers)
        
        # データ数が多い方を基準にして全レコードを出力
        if use_a_as_base and data_a:
            # A社データを基準
            for record_a in data_a:
                row = []
                key_a = _get_record_key(record_a, headers_a)
                
                # A社全フィールドのデータを追加
                for header in headers_a:
                    value_a = str(record_a.get(header, '')).strip() or 'N/A'
                    row.append(value_a)
                
                # 区切り文字列を追加
                row.append("____####____")
                
                # マッチするB社データがあるか確認
                if key_a in match_dict_a_to_b:
                    card_b = match_dict_a_to_b[key_a]
                    key_b = _get_record_key(card_b, headers_b)
                    
                    # B社全フィールドのデータを追加
                    for header in headers_b:
                        value_b = str(card_b.get(header, '')).strip() or 'N/A'
                        row.append(value_b)
                    
                    # マッチスコアを追加
                    score = match_scores.get((key_a, key_b), 0.0)
                    row.append(f"{score:.3f}")
                else:
                    # マッチなし - B社フィールドは空
                    for header in headers_b:
                        row.append('')
                    row.append('0.000')  # マッチスコア0
                
                writer.writerow(row)
                
        elif data_b:
            # B社データを基準
            for record_b in data_b:
                row = []
                key_b = _get_record_key(record_b, headers_b)
                
                # マッチするA社データがあるか確認
                if key_b in match_dict_b_to_a:
                    card_a = match_dict_b_to_a[key_b]
                    key_a = _get_record_key(card_a, headers_a)
                    
                    # A社全フィールドのデータを追加
                    for header in headers_a:
                        value_a = str(card_a.get(header, '')).strip() or 'N/A'
                        row.append(value_a)
                else:
                    # マッチなし - A社フィールドは空
                    for header in headers_a:
                        row.append('')
                
                # 区切り文字列を追加
                row.append("____####____")
                
                # B社全フィールドのデータを追加
                for header in headers_b:
                    value_b = str(record_b.get(header, '')).strip() or 'N/A'
                    row.append(value_b)
                
                # マッチスコアを追加
                if key_b in match_dict_b_to_a:
                    key_a = _get_record_key(match_dict_b_to_a[key_b], headers_a)
                    score = match_scores.get((key_a, key_b), 0.0)
                    row.append(f"{score:.3f}")
                else:
                    row.append('0.000')
                
                writer.writerow(row)
    
    # ログ出力
    analysis_logger.logger.info(f"📊 CSV出力完了:")
    analysis_logger.logger.info(f"   - 基準データ: {'A社' if use_a_as_base else 'B社'} ({len_a if use_a_as_base else len_b}件)")
    analysis_logger.logger.info(f"   - マッチ件数: {len(matches)}件")
    analysis_logger.logger.info(f"   - アンマッチ件数: {(len_a if use_a_as_base else len_b) - len(matches)}件")
    
    return output_file


def _get_record_key(record, headers):
    """レコードのユニークキーを生成（複数フィールドの組み合わせ）"""
    if not record:
        return None
    
    # 最初の3つの非空フィールドを結合してキーとする
    key_parts = []
    for header in headers[:10]:  # 最初の10フィールドから探す
        value = str(record.get(header, '')).strip()
        if value and value != 'N/A':
            key_parts.append(value)
            if len(key_parts) >= 3:
                break
    
    return '|||'.join(key_parts) if key_parts else None

def _claude_field_mapping_analysis(headers_a, headers_b, sample_data_a, sample_data_b, model_name='claude-sonnet-4-20250514'):
    """Claude APIを使ってフィールドマッピングを分析"""
    try:
        # Claude API設定
        api_key = os.environ.get('CLAUDE_API_KEY')
        if not api_key:
            analysis_logger.logger.error("CLAUDE_API_KEY環境変数が設定されていません")
            return []
        
        # CSVサンプルデータを準備
        csv_sample_a = _format_csv_sample(headers_a, sample_data_a[:5])
        csv_sample_b = _format_csv_sample(headers_b, sample_data_b[:5])
        
        # Claude APIプロンプト
        prompt = f"""この2つのCSVファイルを比較して、A社とB社の対応するフィールドペアを特定してください。信頼度も含めて教えてください。

A社のCSV:
```
{csv_sample_a}
```

B社のCSV:
```
{csv_sample_b}
```

以下のJSON形式で回答してください：
{{
    "field_mappings": [
        {{
            "field_a": "A社フィールド名",
            "field_b": "B社フィールド名", 
            "confidence": 0.95,
            "reasoning": "判断理由"
        }}
    ]
}}

完全一致、概念的一致、形式的一致を含めて判断してください。"""

        # Claude API呼び出し
        headers = {
            'Content-Type': 'application/json',
            'x-api-key': api_key,
            'anthropic-version': '2023-06-01'
        }
        
        data = {
            'model': model_name,
            'max_tokens': 4000,
            'messages': [
                {
                    'role': 'user',
                    'content': prompt
                }
            ]
        }
        
        from flask import current_app
        current_app.logger.info("🤖 Claude APIでフィールドマッピング分析開始...")
        current_app.logger.info(f"   - リクエストURL: https://api.anthropic.com/v1/messages")
        current_app.logger.info(f"   - モデル: {data['model']}")
        current_app.logger.info(f"   - プロンプト長: {len(prompt)}文字")
        current_app.logger.info("   - リクエストデータ:")
        current_app.logger.info(f"     プロンプト: {prompt[:200]}...")
        
        import time
        
        # リトライ機能付きでClaude API呼び出し
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = requests.post(
                    'https://api.anthropic.com/v1/messages',
                    headers=headers,
                    json=data,
                    timeout=60
                )
                
                current_app.logger.info(f"   - レスポンス状態: {response.status_code} (試行 {attempt + 1}/{max_retries})")
                
                if response.status_code == 200:
                    break
                elif response.status_code == 529:  # Overloaded
                    current_app.logger.warning(f"   - Claude API過負荷、{5 * (attempt + 1)}秒後にリトライ...")
                    if attempt < max_retries - 1:
                        time.sleep(5 * (attempt + 1))  # 指数バックオフ
                        continue
                else:
                    break
                    
            except requests.exceptions.Timeout:
                current_app.logger.error(f"   - タイムアウトエラー (試行 {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    time.sleep(5 * (attempt + 1))
                    continue
                else:
                    break
        
        if response.status_code == 200:
            result = response.json()
            content = result['content'][0]['text']
            
            current_app.logger.info("   - Claude APIレスポンス受信成功")
            current_app.logger.info(f"     レスポンス長: {len(content)}文字")
            current_app.logger.info(f"     レスポンス内容: {content[:500]}...")
            
            # JSONを抽出・パース
            import re
            json_match = re.search(r'\{.*\}', content, re.DOTALL)
            if json_match:
                current_app.logger.info(f"     JSON抽出成功: {len(json_match.group())}文字")
                mapping_data = json.loads(json_match.group())
                field_mappings = mapping_data.get('field_mappings', [])
                
                current_app.logger.info(f"✅ Claude APIマッピング完了: {len(field_mappings)}件")
                for i, mapping in enumerate(field_mappings):
                    current_app.logger.info(f"     マッピング{i+1}: {mapping['field_a']} -> {mapping['field_b']} (信頼度: {mapping['confidence']})")
                
                # enhanced.py形式に変換
                enhanced_mappings = []
                for mapping in field_mappings:
                    enhanced_mappings.append({
                        'field_a': mapping['field_a'],
                        'field_b': mapping['field_b'], 
                        'confidence': mapping['confidence'],
                        'sample_count': len(sample_data_a),
                        'total_comparisons': len(sample_data_a),
                        'field_type': 'claude_api_analysis',
                        'quality_score': 'Claude_AI',
                        'reasoning': mapping.get('reasoning', '')
                    })
                
                return enhanced_mappings
            else:
                current_app.logger.error("Claude APIレスポンスからJSONを抽出できませんでした")
                current_app.logger.error(f"     レスポンス全文: {content}")
                return []
        else:
            current_app.logger.error(f"Claude API呼び出し失敗: {response.status_code}")
            current_app.logger.error(f"     エラーレスポンス: {response.text}")
            
            # 高コストモデルで過負荷の場合、軽量モデルでリトライ
            if response.status_code == 529 and model_name in ['claude-sonnet-4-20250514', 'claude-3-5-sonnet-20241022', 'claude-3-opus-20240229']:
                current_app.logger.info("   - 軽量モデル(Haiku)でフォールバック試行...")
                return _claude_field_mapping_analysis(headers_a, headers_b, sample_data_a, sample_data_b, 'claude-3-5-haiku-20241022')
            
            return []
            
    except Exception as e:
        current_app.logger.error(f"Claude APIマッピング分析エラー: {str(e)}")
        return []

def _format_csv_sample(headers, sample_data):
    """CSVサンプルデータを文字列形式にフォーマット"""
    lines = [','.join(headers)]
    for row in sample_data:
        values = [str(row.get(header, '')).replace(',', ';') for header in headers]
        lines.append(','.join(values))
    return '\n'.join(lines)

def _match_cards_with_claude_mappings(data_a, data_b, claude_mappings, max_sample_size):
    """Claudeマッピングを使って同一カード特定"""
    import time
    start_time = time.time()
    
    # データサイズ制限
    if len(data_a) > max_sample_size:
        data_a = data_a[:max_sample_size]
    if len(data_b) > max_sample_size:
        data_b = data_b[:max_sample_size]
    
    analysis_logger.logger.info(f"🔍 Claudeマッピングベースカード特定開始: {len(data_a)}×{len(data_b)}行")
    
    # 高信頼度マッピングのみを使用（confidence > 0.8）
    reliable_mappings = {}
    for mapping in claude_mappings:
        if mapping.get('confidence', 0) > 0.8:
            reliable_mappings[mapping['field_a']] = mapping['field_b']
    
    analysis_logger.logger.info(f"📝 使用する高信頼度マッピング: {len(reliable_mappings)}件")
    
    matches = []
    for card_a in data_a:
        best_match = None
        best_score = 0.0
        
        for card_b in data_b:
            score = 0.0
            matched_fields = 0
            
            # 高信頼度マッピングでスコア計算
            for field_a, field_b in reliable_mappings.items():
                val_a = str(card_a.get(field_a, '')).strip().lower()
                val_b = str(card_b.get(field_b, '')).strip().lower()
                
                if val_a and val_b and val_a != 'n/a':
                    matched_fields += 1
                    if val_a == val_b:
                        score += 1.0  # 完全一致
                    elif val_a in val_b or val_b in val_a:
                        score += 0.7  # 部分一致
            
            # 正規化スコア
            if matched_fields > 0:
                normalized_score = score / matched_fields
                if normalized_score > best_score and normalized_score >= 0.7:  # 70%以上の一致
                    best_score = normalized_score
                    best_match = card_b
        
        if best_match:
            matches.append({
                'card_a': card_a,
                'card_b': best_match,
                'overall_similarity': round(best_score, 3),
                'similarity_details': {}
            })
    
    elapsed_time = time.time() - start_time
    analysis_logger.logger.info(f"✅ Claudeマッピングベース特定完了: {len(matches)}組 ({elapsed_time:.2f}秒)")
    
    return matches

def _build_success_analysis_section(enhanced_mappings, card_matches, mapping_summary, validation_result):
    """成功時の分析セクション生成（タプル対応）"""

    html = f"""
    <h2>🎯 カードベース分析結果</h2>
    <div class="success">
        <h3>✅ 分析成功</h3>
        <p><strong>マッチしたカード数:</strong> {len(card_matches)}件</p>
        <p><strong>検出されたフィールドマッピング:</strong> {len(enhanced_mappings.get('flexible_field_mappings', []))}件</p>
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

    # 同一カード対応テーブル
    if card_matches:
        html += f"""
        <h3>🎯 同一カード対応表（{len(card_matches)}件）</h3>
        <table>
        <tr>
            <th>No.</th>
            <th>A社カードデータ (行数)</th>
            <th>B社カードデータ (行数)</th>
            <th>マッチスコア</th>
        </tr>
        """
        
        # フィールドマッピングから高信頼度のもののみを取得（表示用）
        display_fields = []
        rarity_fields = {'a': None, 'b': None}
        serial_fields = {'a': None, 'b': None}
        
        # AIベース判定のためのサンプルデータを準備
        sample_data_a = [match.get('card_a', {}) for match in card_matches[:10]]
        sample_data_b = [match.get('card_b', {}) for match in card_matches[:10]]
        
        if enhanced_mappings and isinstance(enhanced_mappings, dict):
            field_mappings = enhanced_mappings.get('flexible_field_mappings', [])
            
            # 名前、レアリティ、シリアル等の重要フィールドを優先的に取得
            for mapping in field_mappings:
                if isinstance(mapping, tuple) and len(mapping) >= 3:
                    field_a, field_b, score = mapping[0], mapping[1], mapping[2]
                    
                    # AIベースでレアリティフィールドを特定
                    if not rarity_fields['a'] and _is_rarity_field(field_a, sample_data_a):
                        rarity_fields['a'] = field_a
                        rarity_fields['b'] = field_b
                    
                    # AIベースでシリアルフィールドを特定
                    elif not serial_fields['a'] and _is_serial_field(field_a, sample_data_a):
                        serial_fields['a'] = field_a
                        serial_fields['b'] = field_b
                    
                    # 高信頼度フィールドマッピング
                    elif score > 0.7:
                        display_fields.append((field_a, field_b))
            
            # 上位5つまでに制限
            display_fields = display_fields[:5]
        
        # 同一カード表示（全件表示）
        for idx, match in enumerate(card_matches, 1):
            try:
                card_a = match.get('card_a', {})
                card_b = match.get('card_b', {})
                card_a_row = match.get('card_a_row', '不明')
                card_b_row = match.get('card_b_row', '不明')
                similarity = match.get('overall_similarity', 0.0)
                
                # A社データの表示
                a_data_items = []
                
                # レアリティ情報を追加
                if rarity_fields['a']:
                    rarity_value = str(card_a.get(rarity_fields['a'], '')).strip()
                    if rarity_value and rarity_value != 'nan':
                        a_data_items.append(f"<strong style='color:#ff9800;'>🌟レアリティ:</strong> <span style='background:#fff3e0;padding:2px 6px;border-radius:3px;'>{rarity_value}</span>")
                
                # シリアル情報を追加
                if serial_fields['a']:
                    serial_value = str(card_a.get(serial_fields['a'], '')).strip()
                    if serial_value and serial_value != 'nan':
                        a_data_items.append(f"<strong style='color:#2196f3;'>🏷️シリアル:</strong> <span style='background:#e3f2fd;padding:2px 6px;border-radius:3px;'>{serial_value}</span>")
                
                # その他の表示フィールド
                for field_a, field_b in display_fields:
                    value_a = str(card_a.get(field_a, '')).strip()
                    if value_a and value_a != 'nan':
                        a_data_items.append(f"<strong>{field_a}:</strong> {value_a}")
                
                # 表示フィールドがない場合は代表的なフィールドを使用
                if not a_data_items:
                    for key in ['name', 'カード名', 'serial', '型番', 'id', 'rarity', 'レアリティ']:
                        if key in card_a and str(card_a[key]).strip() and str(card_a[key]) != 'nan':
                            a_data_items.append(f"<strong>{key}:</strong> {card_a[key]}")
                            if len(a_data_items) >= 3:  # 最大3つまで
                                break
                
                a_display = "<br>".join(a_data_items) if a_data_items else "データなし"
                a_display_with_row = f"<div><small class='row-number'>CSV行: {card_a_row}</small><br>{a_display}</div>"
                
                # B社データの表示
                b_data_items = []
                
                # レアリティ情報を追加
                if rarity_fields['b']:
                    rarity_value = str(card_b.get(rarity_fields['b'], '')).strip()
                    if rarity_value and rarity_value != 'nan':
                        b_data_items.append(f"<strong style='color:#ff9800;'>🌟レアリティ:</strong> <span style='background:#fff3e0;padding:2px 6px;border-radius:3px;'>{rarity_value}</span>")
                
                # シリアル情報を追加
                if serial_fields['b']:
                    serial_value = str(card_b.get(serial_fields['b'], '')).strip()
                    if serial_value and serial_value != 'nan':
                        b_data_items.append(f"<strong style='color:#2196f3;'>🏷️シリアル:</strong> <span style='background:#e3f2fd;padding:2px 6px;border-radius:3px;'>{serial_value}</span>")
                
                # その他の表示フィールド
                for field_a, field_b in display_fields:
                    value_b = str(card_b.get(field_b, '')).strip()
                    if value_b and value_b != 'nan':
                        b_data_items.append(f"<strong>{field_b}:</strong> {value_b}")
                
                # 表示フィールドがない場合は代表的なフィールドを使用
                if not b_data_items:
                    for key in ['name', 'カード名', 'serial', '型番', 'id', 'rarity', 'レアリティ']:
                        if key in card_b and str(card_b[key]).strip() and str(card_b[key]) != 'nan':
                            b_data_items.append(f"<strong>{key}:</strong> {card_b[key]}")
                            if len(b_data_items) >= 3:  # 最大3つまで
                                break
                
                b_display = "<br>".join(b_data_items) if b_data_items else "データなし"
                b_display_with_row = f"<div><small class='row-number'>CSV行: {card_b_row}</small><br>{b_display}</div>"
                
                # スコアに応じた色分け
                score_class = "confidence-high" if similarity > 0.9 else "confidence-medium" if similarity > 0.7 else "confidence-low"
                
                html += f"""
                <tr>
                    <td>{idx}</td>
                    <td style="max-width: 300px; word-wrap: break-word;">{a_display_with_row}</td>
                    <td style="max-width: 300px; word-wrap: break-word;">{b_display_with_row}</td>
                    <td class="{score_class}">{similarity:.3f}</td>
                </tr>
                """
            except Exception as e:
                html += f"""
                <tr>
                    <td>{idx}</td>
                    <td colspan="3">データ表示エラー: {str(e)[:100]}</td>
                </tr>
                """
        
        html += "</table>"

    # フィールドマッピング表示（柔軟マッチング対応）
    if enhanced_mappings and isinstance(enhanced_mappings, dict):
        field_mappings = enhanced_mappings.get('flexible_field_mappings', [])
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

        for mapping in field_mappings[:15]:
            try:
                # 柔軟マッチングのタプル形式: (field_a, field_b, similarity_score)
                if isinstance(mapping, tuple):
                    if len(mapping) >= 3:
                        field_a = str(mapping[0]).replace('\ufeff', '').strip() if mapping[0] else 'unknown'
                        field_b = str(mapping[1]).replace('\ufeff', '').strip() if mapping[1] else 'unknown'
                        confidence = float(mapping[2]) if mapping[2] else 0.0
                    else:
                        field_a = field_b = 'unknown'
                        confidence = 0.0

                    sample_count = 'Auto'
                    field_type = 'flexible'
                    quality_score = f'{confidence:.3f}'

                elif isinstance(mapping, dict):
                    # 通常の辞書形式
                    field_a = str(mapping.get('company_a_field', mapping.get('field_a', 'unknown'))).replace('\ufeff',
                                                                                                             '').strip()
                    field_b = str(mapping.get('company_b_field', mapping.get('field_b', 'unknown'))).replace('\ufeff',
                                                                                                             '').strip()
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


def _build_error_analysis_section(error_message):
    """エラー時の分析セクション生成"""
    return f"""
    <h2>❌ 分析エラー</h2>
    <div class="error">
        <h3>分析に失敗しました</h3>
        <p><strong>エラー内容:</strong> {error_message or '不明なエラー'}</p>
        <p>データの品質を確認して再度お試しください。</p>
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
            <a href="/test/files/enhanced">← 戻る</a>
            <a href="/">🏠 トップページ</a>
        </div>
    </body>
    </html>
    """