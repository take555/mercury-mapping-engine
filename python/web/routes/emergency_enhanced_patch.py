# enhanced.pyの_handle_enhanced_analysis_post()関数の先頭に以下を追加

import logging
import sys
import time

# 緊急デバッグログ設定
debug_logger = logging.getLogger('enhanced_emergency_debug')
debug_logger.setLevel(logging.INFO)
if not debug_logger.handlers:
    # コンソール出力
    console_handler = logging.StreamHandler(sys.stdout)
    console_formatter = logging.Formatter('%(asctime)s - EMERGENCY - %(message)s')
    console_handler.setFormatter(console_formatter)
    debug_logger.addHandler(console_handler)
    
    # ファイル出力
    try:
        file_handler = logging.FileHandler('/app/logs/emergency_debug.log', encoding='utf-8')
        file_handler.setFormatter(console_formatter)
        debug_logger.addHandler(file_handler)
    except:
        pass

def clean_field_name(field_name):
    """BOM文字とエンコーディング問題を修正"""
    if isinstance(field_name, str):
        return field_name.replace('\ufeff', '').strip()
    elif isinstance(field_name, tuple):
        return tuple(str(item).replace('\ufeff', '').strip() for item in field_name)
    return str(field_name).replace('\ufeff', '').strip()

def log_performance_step(step_name, start_time=None):
    """パフォーマンス計測"""
    current_time = time.time()
    if start_time:
        elapsed = current_time - start_time
        debug_logger.info(f"✅ {step_name} 完了: {elapsed:.2f}秒")
        return current_time
    else:
        debug_logger.info(f"🚀 {step_name} 開始")
        return current_time

# _handle_enhanced_analysis_post()関数内で使用例:

def _handle_enhanced_analysis_post():
    debug_logger.info("=" * 60)
    debug_logger.info("🚀 ENHANCED ANALYSIS START (EMERGENCY DEBUG)")
    debug_logger.info("=" * 60)
    
    total_start = time.time()
    
    try:
        # ステップ1: ファイル処理
        step1_start = log_performance_step("ファイルアップロード処理")
        
        # ... 既存のファイル処理コード ...
        
        step1_end = log_performance_step("ファイルアップロード処理", step1_start)
        
        # ステップ2: Engine初期化
        step2_start = log_performance_step("MappingEngine初期化")
        
        # ... 既存のEngine初期化コード ...
        
        step2_end = log_performance_step("MappingEngine初期化", step2_start)
        
        # ステップ3: CSV分析
        step3_start = log_performance_step("CSV分析")
        
        # ... 既存のCSV分析コード ...
        
        step3_end = log_performance_step("CSV分析", step3_start)
        debug_logger.info(f"CSV分析結果: A社{analysis_a['total_rows']}行, B社{analysis_b['total_rows']}行")
        
        # ステップ4: マッチング
        step4_start = log_performance_step("Brute Force Matching")
        
        # ... 既存のマッチング処理 ...
        
        step4_end = log_performance_step("Brute Force Matching", step4_start)
        debug_logger.info(f"マッチング結果: {len(matches)}件")
        
        # ステップ5: フィールドマッピング分析（ここが遅い可能性大）
        step5_start = log_performance_step("フィールドマッピング分析")
        
        if matches:
            debug_logger.info(f"フィールドマッピング開始: {len(matches)}件のマッチから分析")
            
            # 既存のフィールドマッピング処理
            field_mapping_result = engine.field_mapper.analyze_field_mappings_from_matches(
                matches, analysis_a['headers'], analysis_b['headers']
            )
            
            debug_logger.info(f"フィールドマッピング生データ取得: {type(field_mapping_result)}")
            
            # BOM文字除去とデータクリーニング
            if isinstance(field_mapping_result, list):
                enhanced_mappings = []
                for mapping in field_mapping_result:
                    if isinstance(mapping, dict):
                        cleaned_mapping = {
                            'field_a': clean_field_name(mapping.get('field_a', '')),
                            'field_b': clean_field_name(mapping.get('field_b', '')),
                            'confidence': mapping.get('confidence', 0.0),
                            'sample_count': mapping.get('sample_count', 0),
                            'field_type': mapping.get('field_type', 'unknown')
                        }
                        enhanced_mappings.append(cleaned_mapping)
                    elif isinstance(mapping, tuple):
                        # タプル形式の場合
                        field_a = clean_field_name(mapping[0]) if len(mapping) > 0 else 'unknown'
                        field_b = clean_field_name(mapping[1]) if len(mapping) > 1 else 'unknown'
                        cleaned_mapping = {
                            'field_a': field_a,
                            'field_b': field_b,
                            'confidence': 0.0,
                            'sample_count': 1,
                            'field_type': 'tuple_converted'
                        }
                        enhanced_mappings.append(cleaned_mapping)
            elif isinstance(field_mapping_result, dict):
                enhanced_mappings = []
                for key, value in field_mapping_result.items():
                    if '→' in str(key):
                        parts = str(key).split('→')
                        field_a = clean_field_name(parts[0])
                        field_b = clean_field_name(parts[1]) if len(parts) > 1 else 'unknown'
                    else:
                        field_a = clean_field_name(key)
                        field_b = 'unknown'
                    
                    confidence = value.get('confidence', 0.0) if isinstance(value, dict) else 0.0
                    
                    cleaned_mapping = {
                        'field_a': field_a,
                        'field_b': field_b,
                        'confidence': confidence,
                        'sample_count': value.get('sample_count', 1) if isinstance(value, dict) else 1,
                        'field_type': 'dict_converted'
                    }
                    enhanced_mappings.append(cleaned_mapping)
            else:
                enhanced_mappings = []
            
            debug_logger.info(f"クリーニング後のマッピング: {len(enhanced_mappings)}件")
            
        step5_end = log_performance_step("フィールドマッピング分析", step5_start)
        
        # ステップ6: サマリー作成（ここも遅い可能性）
        step6_start = log_performance_step("マッピングサマリー作成")
        
        # ... 既存のサマリー作成処理 ...
        
        step6_end = log_performance_step("マッピングサマリー作成", step6_start)
        
        # ステップ7: HTML生成（最も遅い可能性）
        step7_start = log_performance_step("HTML生成")
        
        # ... 既存のHTML生成処理 ...
        
        step7_end = log_performance_step("HTML生成", step7_start)
        
        total_time = time.time() - total_start
        debug_logger.info("=" * 60)
        debug_logger.info(f"🏁 TOTAL TIME: {total_time:.2f}秒")
        debug_logger.info("=" * 60)
        
        return html
        
    except Exception as e:
        debug_logger.error(f"💥 CRITICAL ERROR: {e}")
        debug_logger.error(f"ERROR TRACEBACK: {traceback.format_exc()}")
        raise