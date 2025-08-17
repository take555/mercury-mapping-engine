# enhanced.py の _handle_enhanced_analysis_post に詳細ログを追加

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
        ai_model = request.form.get('ai_model', 'claude-3-haiku-20240307')
        
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
        
        # 🔥 Brute Force Matching実行（詳細ログ付き）
        analysis_logger.logger.info("💪 Step 4: Brute Force Matching開始")
        start_time = time.time()
        
        try:
            card_matcher = engine.card_matcher
            
            data_a = analysis_a.get('full_data', analysis_a['sample_data'])
            data_b = analysis_b.get('full_data', analysis_b['sample_data'])
            
            analysis_logger.logger.info(f"📊 マッチング対象データ:")
            analysis_logger.logger.info(f"   - A社データ: {len(data_a)}行")
            analysis_logger.logger.info(f"   - B社データ: {len(data_b)}行")
            analysis_logger.logger.info(f"   - 予想比較回数: {len(data_a)} × {len(data_b)} = {len(data_a) * len(data_b)}")
            
            matches = card_matcher.brute_force_matching(
                data_a,
                data_b,
                analysis_a['headers'],
                analysis_b['headers'],
                max_sample_size=max_sample_size,
                similarity_mode=similarity_mode,
                ai_manager=ai_manager
            )
            
            matching_time = time.time() - start_time
            analysis_logger.logger.info(f"✅ Brute Force Matching完了 ({matching_time:.2f}秒)")
            analysis_logger.logger.info(f"🎯 マッチング結果: {len(matches)}件")
            
            # フィールドマッピング分析（詳細ログ付き）
            analysis_logger.logger.info("🔗 Step 5: フィールドマッピング分析開始")
            start_time = time.time()
            
            if matches:
                try:
                    analysis_logger.logger.info(f"   - 入力マッチ数: {len(matches)}")
                    
                    field_mapping_result = engine.field_mapper.analyze_field_mappings_from_matches(
                        matches, analysis_a['headers'], analysis_b['headers']
                    )
                    
                    analysis_logger.logger.info(f"   - マッピング結果タイプ: {type(field_mapping_result)}")
                    
                    # 返り値の型に応じて適切に処理（詳細ログ付き）
                    if isinstance(field_mapping_result, tuple):
                        enhanced_mappings = field_mapping_result[0] if field_mapping_result else []
                        analysis_logger.logger.info(f"   - Tuple形式: 要素数={len(field_mapping_result)}, 第1要素={len(enhanced_mappings)}件")
                    elif isinstance(field_mapping_result, dict):
                        analysis_logger.logger.info(f"   - Dict形式: キー={list(field_mapping_result.keys())[:5]}")
                        
                        if 'mappings' in field_mapping_result:
                            enhanced_mappings = field_mapping_result['mappings']
                            analysis_logger.logger.info(f"   - 'mappings'キーから取得: {len(enhanced_mappings)}件")
                        elif 'enhanced_mappings' in field_mapping_result:
                            enhanced_mappings = field_mapping_result['enhanced_mappings']
                            analysis_logger.logger.info(f"   - 'enhanced_mappings'キーから取得: {len(enhanced_mappings)}件")
                        else:
                            # dictをリストに変換
                            enhanced_mappings = [
                                {
                                    'field_a': k.split('→')[0] if '→' in k else k,
                                    'field_b': k.split('→')[1] if '→' in k else 'unknown',
                                    'confidence': v.get('confidence', v.get('avg_similarity', 0.0)) if isinstance(v, dict) else 0.0,
                                    'sample_count': v.get('count', v.get('sample_count', 1)) if isinstance(v, dict) else 1,
                                    'field_type': v.get('field_type', 'unknown') if isinstance(v, dict) else 'unknown'
                                }
                                for k, v in field_mapping_result.items()
                            ]
                            analysis_logger.logger.info(f"   - Dict変換: {len(enhanced_mappings)}件のマッピング")
                    elif isinstance(field_mapping_result, list):
                        enhanced_mappings = field_mapping_result
                        analysis_logger.logger.info(f"   - List形式: {len(enhanced_mappings)}件")
                    else:
                        analysis_logger.logger.warning(f"   - 未知の形式: {type(field_mapping_result)}")
                        enhanced_mappings = []
                        
                except Exception as e:
                    analysis_logger.logger.error(f"❌ フィールドマッピング分析エラー: {e}")
                    analysis_logger.logger.error(f"   - エラー詳細: {traceback.format_exc()}")
                    enhanced_mappings = []
                    
            else:
                enhanced_mappings = []
                analysis_logger.logger.info("   - マッチなし: フィールドマッピングスキップ")
            
            mapping_time = time.time() - start_time
            analysis_logger.logger.info(f"✅ フィールドマッピング分析完了 ({mapping_time:.2f}秒)")
            
            card_analysis_success = True
            
        except Exception as e:
            analysis_logger.logger.error(f"❌ Brute Force分析エラー: {e}")
            analysis_logger.logger.error(f"   - エラー詳細: {traceback.format_exc()}")
            enhanced_mappings = []
            matches = []
            card_analysis_success = False
            card_analysis_error = str(e)
        
        # マッピングサマリー作成（詳細ログ付き）
        analysis_logger.logger.info("📋 Step 6: マッピングサマリー作成開始")
        start_time = time.time()
        
        if enhanced_mappings:
            try:
                analysis_logger.logger.info(f"   - enhanced_mappings: {len(enhanced_mappings)}件")
                analysis_logger.logger.info(f"   - matches: {len(matches)}件")
                
                mapping_summary = engine.create_mapping_summary(enhanced_mappings, matches, analysis_a, analysis_b)
                validation_result = engine.validate_mapping_results(enhanced_mappings, matches)
                
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

