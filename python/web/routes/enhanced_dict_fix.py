# enhanced.py の _handle_enhanced_analysis_post 内の該当箇所を修正

# フィールドマッピング分析（dict/tuple対応）
if matches:
    try:
        field_mapping_result = engine.field_mapper.analyze_field_mappings_from_matches(
            matches, analysis_a['headers'], analysis_b['headers']
        )
        
        # 返り値の型に応じて適切に処理
        if isinstance(field_mapping_result, tuple):
            enhanced_mappings = field_mapping_result[0] if field_mapping_result else []
            analysis_logger.logger.info(f"Field mapping returned tuple, extracted mappings: {len(enhanced_mappings)}")
        elif isinstance(field_mapping_result, dict):
            # dictの場合、キーから推測して処理
            if 'mappings' in field_mapping_result:
                enhanced_mappings = field_mapping_result['mappings']
            elif 'enhanced_mappings' in field_mapping_result:
                enhanced_mappings = field_mapping_result['enhanced_mappings']
            else:
                # dictをリストに変換（各キーを個別のマッピングとして扱う）
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
            analysis_logger.logger.info(f"Field mapping returned dict, converted to list: {len(enhanced_mappings)} mappings")
        elif isinstance(field_mapping_result, list):
            enhanced_mappings = field_mapping_result
        else:
            analysis_logger.logger.warning(f"Unexpected field mapping result type: {type(field_mapping_result)}")
            enhanced_mappings = []
            
        # enhanced_mappingsが確実にlistであることを保証
        if not isinstance(enhanced_mappings, list):
            analysis_logger.logger.warning(f"Converting enhanced_mappings to list from {type(enhanced_mappings)}")
            enhanced_mappings = []
            
    except Exception as e:
        analysis_logger.logger.error(f"Field mapping analysis error: {e}")
        enhanced_mappings = []
        
else:
    enhanced_mappings = []