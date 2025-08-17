# enhanced.py の _handle_enhanced_analysis_post 内の該当箇所を修正

# 🔥 Brute Force Matching実行（モード切り替え対応）
try:
    analysis_logger.logger.info(f"Starting brute force matching in {similarity_mode} mode")
    
    # CardMatcherのbrute_force_matching呼び出し
    card_matcher = engine.card_matcher
    
    matches = card_matcher.brute_force_matching(
        analysis_a.get('full_data', analysis_a['sample_data']),
        analysis_b.get('full_data', analysis_b['sample_data']),
        analysis_a['headers'],
        analysis_b['headers'],
        max_sample_size=max_sample_size,
        similarity_mode=similarity_mode,
        ai_manager=ai_manager
    )
    
    # フィールドマッピング分析（tuple対応）
    if matches:
        field_mapping_result = engine.field_mapper.analyze_field_mappings_from_matches(
            matches, analysis_a['headers'], analysis_b['headers']
        )
        
        # tupleかどうかチェックして適切に処理
        if isinstance(field_mapping_result, tuple):
            enhanced_mappings = field_mapping_result[0] if field_mapping_result else []
            analysis_logger.logger.info(f"Field mapping returned tuple, extracted mappings: {len(enhanced_mappings)}")
        else:
            enhanced_mappings = field_mapping_result or []
            
        # enhanced_mappingsがNoneやtupleでないことを確認
        if not isinstance(enhanced_mappings, list):
            analysis_logger.logger.warning(f"Enhanced mappings is not a list: {type(enhanced_mappings)}")
            enhanced_mappings = []
            
    else:
        enhanced_mappings = []
    
    card_analysis_success = True
    analysis_logger.logger.info(f"✅ Brute force analysis completed: {len(matches)} matches, {len(enhanced_mappings)} mappings")
    
except Exception as e:
    current_app.logger.error(f"Brute force分析エラー: {e}")
    enhanced_mappings = []
    matches = []
    card_analysis_success = False
    card_analysis_error = str(e)