"""
Mercury Mapping Engine - Analysis API Routes
分析APIルート
"""
from flask import Blueprint, request, current_app
import os
import json
from core import create_mapping_engine
from config.settings import Config
from utils.logger import analysis_logger, performance_logger
from .helpers import create_success_response, create_error_response

# ブループリント作成
analysis_bp = Blueprint('analysis', __name__)


@analysis_bp.route('/analyze/basic', methods=['POST'])
def analyze_basic():
    """基本的なCSV分析API"""
    try:
        data = request.get_json()
        
        # パラメータ検証
        if not data:
            return create_error_response("Request body is required", 400)
        
        file_a_path = data.get('file_a_path', '/app/uploads/a.csv')
        file_b_path = data.get('file_b_path', '/app/uploads/b.csv')
        
        # ファイル存在確認
        if not os.path.exists(file_a_path):
            return create_error_response(f"File A not found: {file_a_path}", 404)
        
        if not os.path.exists(file_b_path):
            return create_error_response(f"File B not found: {file_b_path}", 404)
        
        # エンジン初期化
        config = Config.get_analysis_config()
        engine = create_mapping_engine(config)
        
        analysis_logger.logger.info(f"Basic analysis started: {file_a_path}, {file_b_path}")
        
        # CSV分析実行
        csv_result = engine.analyze_csv_files(file_a_path, file_b_path, full_analysis=False)
        
        if 'error' in csv_result:
            return create_error_response(f"CSV analysis failed: {csv_result['error']}", 400)
        
        # 従来手法でのフィールドマッピング
        analysis_a = csv_result['analysis_a']
        analysis_b = csv_result['analysis_b']
        
        a_to_b_mappings, b_to_a_mappings = engine.field_mapper.analyze_traditional_mappings(
            analysis_a['headers'], 
            analysis_b['headers'],
            analysis_a['sample_data'],
            analysis_b['sample_data']
        )
        
        # レスポンス構築
        response_data = {
            'analysis_type': 'basic',
            'file_a': {
                'path': file_a_path,
                'headers': analysis_a['headers'],
                'total_rows': analysis_a['total_rows'],
                'sample_rows': len(analysis_a['sample_data'])
            },
            'file_b': {
                'path': file_b_path,
                'headers': analysis_b['headers'],
                'total_rows': analysis_b['total_rows'],
                'sample_rows': len(analysis_b['sample_data'])
            },
            'field_mappings': {
                'a_to_b': a_to_b_mappings,
                'b_to_a': b_to_a_mappings
            },
            'validation': {
                'file_a': csv_result.get('validation_a', {}),
                'file_b': csv_result.get('validation_b', {})
            }
        }
        
        analysis_logger.logger.info("Basic analysis completed successfully")
        return create_success_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Basic analysis error: {e}")
        return create_error_response(f"Analysis failed: {str(e)}", 500)


@analysis_bp.route('/analyze/enhanced', methods=['POST'])
def analyze_enhanced():
    """高精度カードベース分析API"""
    performance_logger.start_timer('enhanced_analysis_api')
    
    try:
        data = request.get_json()
        
        # パラメータ検証
        if not data:
            return create_error_response("Request body is required", 400)
        
        file_a_path = data.get('file_a_path', '/app/uploads/a.csv')
        file_b_path = data.get('file_b_path', '/app/uploads/b.csv')
        confidence_threshold = data.get('confidence_threshold', 0.8)
        max_rows = data.get('max_rows', 1000)
        
        # ファイル存在確認
        if not os.path.exists(file_a_path):
            return create_error_response(f"File A not found: {file_a_path}", 404)
        
        if not os.path.exists(file_b_path):
            return create_error_response(f"File B not found: {file_b_path}", 404)
        
        # エンジン初期化
        config = Config.get_analysis_config()
        config['csv_max_rows'] = max_rows
        engine = create_mapping_engine(config)
        
        analysis_logger.logger.info(f"Enhanced analysis started: {file_a_path}, {file_b_path}")
        
        # CSV分析実行
        csv_result = engine.analyze_csv_files(file_a_path, file_b_path, full_analysis=True)
        
        if 'error' in csv_result:
            return create_error_response(f"CSV analysis failed: {csv_result['error']}", 400)
        
        analysis_a = csv_result['analysis_a']
        analysis_b = csv_result['analysis_b']
        
        # カードベース分析実行
        enhanced_mappings, card_matches = engine.analyze_card_based_mapping(
            analysis_a['headers'], 
            analysis_b['headers'],
            analysis_a['sample_data'],
            analysis_b['sample_data'],
            analysis_a.get('full_data'),
            analysis_b.get('full_data')
        )
        
        # マッピングサマリー作成
        mapping_summary = engine.create_mapping_summary(enhanced_mappings, card_matches, analysis_a, analysis_b)
        
        # 結果検証
        validation_result = engine.validate_mapping_results(enhanced_mappings, card_matches)
        
        # マッピングルール生成
        mapping_rules = engine.export_mapping_rules(enhanced_mappings, confidence_threshold)
        
        # レスポンス構築
        response_data = {
            'analysis_type': 'enhanced',
            'parameters': {
                'confidence_threshold': confidence_threshold,
                'max_rows': max_rows
            },
            'file_analysis': {
                'file_a': {
                    'path': file_a_path,
                    'headers': analysis_a['headers'],
                    'total_rows': analysis_a['total_rows'],
                    'processed_rows': len(analysis_a.get('full_data', [])),
                    'truncated': analysis_a.get('truncated', False)
                },
                'file_b': {
                    'path': file_b_path,
                    'headers': analysis_b['headers'],
                    'total_rows': analysis_b['total_rows'],
                    'processed_rows': len(analysis_b.get('full_data', [])),
                    'truncated': analysis_b.get('truncated', False)
                }
            },
            'card_matching': {
                'total_matches': len(card_matches),
                'match_quality': engine.card_matcher.analyze_match_quality(card_matches),
                'sample_matches': card_matches[:5]  # 上位5件のみ
            },
            'field_mappings': {
                'total_mappings': len(enhanced_mappings),
                'high_confidence_mappings': [m for m in enhanced_mappings if m['confidence'] >= confidence_threshold],
                'all_mappings': enhanced_mappings
            },
            'mapping_summary': mapping_summary,
            'validation': validation_result,
            'generated_rules': mapping_rules
        }
        
        analysis_logger.logger.info(f"Enhanced analysis completed: {len(card_matches)} matches, {len(enhanced_mappings)} mappings")
        performance_logger.end_timer('enhanced_analysis_api')
        
        return create_success_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Enhanced analysis error: {e}")
        return create_error_response(f"Enhanced analysis failed: {str(e)}", 500)


@analysis_bp.route('/analyze/compare', methods=['POST'])
def analyze_compare():
    """従来手法と新手法の比較分析API"""
    try:
        data = request.get_json()
        
        # パラメータ検証
        if not data:
            return create_error_response("Request body is required", 400)
        
        file_a_path = data.get('file_a_path', '/app/uploads/a.csv')
        file_b_path = data.get('file_b_path', '/app/uploads/b.csv')
        
        # ファイル存在確認
        if not os.path.exists(file_a_path):
            return create_error_response(f"File A not found: {file_a_path}", 404)
        
        if not os.path.exists(file_b_path):
            return create_error_response(f"File B not found: {file_b_path}", 404)
        
        # エンジン初期化
        config = Config.get_analysis_config()
        engine = create_mapping_engine(config)
        
        analysis_logger.logger.info("Comparison analysis started")
        
        # CSV分析
        csv_result = engine.analyze_csv_files(file_a_path, file_b_path, full_analysis=True)
        
        if 'error' in csv_result:
            return create_error_response(f"CSV analysis failed: {csv_result['error']}", 400)
        
        analysis_a = csv_result['analysis_a']
        analysis_b = csv_result['analysis_b']
        
        # 従来手法
        traditional_a_to_b, traditional_b_to_a = engine.field_mapper.analyze_traditional_mappings(
            analysis_a['headers'], 
            analysis_b['headers'],
            analysis_a['sample_data'],
            analysis_b['sample_data']
        )
        
        # 新手法（カードベース）
        enhanced_mappings, card_matches = engine.analyze_card_based_mapping(
            analysis_a['headers'], 
            analysis_b['headers'],
            analysis_a['sample_data'],
            analysis_b['sample_data'],
            analysis_a.get('full_data'),
            analysis_b.get('full_data')
        )
        
        # 比較分析
        comparison_result = _compare_analysis_methods(traditional_a_to_b, enhanced_mappings)
        
        # レスポンス構築
        response_data = {
            'analysis_type': 'comparison',
            'traditional_method': {
                'a_to_b_mappings': traditional_a_to_b,
                'b_to_a_mappings': traditional_b_to_a,
                'total_field_pairs': len(analysis_a['headers']) * len(analysis_b['headers'])
            },
            'enhanced_method': {
                'card_matches': len(card_matches),
                'field_mappings': enhanced_mappings,
                'match_quality': engine.card_matcher.analyze_match_quality(card_matches)
            },
            'comparison': comparison_result,
            'recommendations': _generate_method_recommendations(comparison_result)
        }
        
        analysis_logger.logger.info("Comparison analysis completed")
        return create_success_response(response_data)
        
    except Exception as e:
        current_app.logger.error(f"Comparison analysis error: {e}")
        return create_error_response(f"Comparison analysis failed: {str(e)}", 500)


@analysis_bp.route('/analyze/validate/<job_id>', methods=['GET'])
def validate_analysis(job_id):
    """分析結果の検証API"""
    try:
        # 実装予定: データベースから結果を取得して検証
        # 現在はサンプルレスポンス
        
        validation_result = {
            'job_id': job_id,
            'validation_status': 'completed',
            'quality_score': 0.85,
            'issues_found': [],
            'recommendations': [
                "高信頼度のマッピングが85%を占めており、品質は良好です",
                "カードマッチング精度が高く、信頼性の高い結果です"
            ]
        }
        
        return create_success_response(validation_result)
        
    except Exception as e:
        current_app.logger.error(f"Validation error: {e}")
        return create_error_response(f"Validation failed: {str(e)}", 500)


def _compare_analysis_methods(traditional_mappings, enhanced_mappings):
    """従来手法と新手法の比較分析"""
    
    # 従来手法の統計
    traditional_high_confidence = []
    for mapping in traditional_mappings:
        if mapping['matches']:
            best_match = mapping['matches'][0]
            if best_match['similarity'] > 0.8:
                traditional_high_confidence.append({
                    'source_field': mapping['source_field'],
                    'target_field': best_match['target_field'],
                    'confidence': best_match['similarity']
                })
    
    # 新手法の統計
    enhanced_high_confidence = [m for m in enhanced_mappings if m['confidence'] > 0.8]
    
    # 比較結果
    comparison = {
        'traditional_method': {
            'total_candidates': len(traditional_mappings),
            'high_confidence_count': len(traditional_high_confidence),
            'average_confidence': sum(m['confidence'] for m in traditional_high_confidence) / len(traditional_high_confidence) if traditional_high_confidence else 0
        },
        'enhanced_method': {
            'total_mappings': len(enhanced_mappings),
            'high_confidence_count': len(enhanced_high_confidence),
            'average_confidence': sum(m['confidence'] for m in enhanced_high_confidence) / len(enhanced_high_confidence) if enhanced_high_confidence else 0
        },
        'improvement': {
            'confidence_improvement': 0,
            'precision_improvement': 0,
            'method_recommendation': 'enhanced'
        }
    }
    
    # 改善度計算
    if comparison['traditional_method']['average_confidence'] > 0:
        confidence_improvement = (comparison['enhanced_method']['average_confidence'] - comparison['traditional_method']['average_confidence']) / comparison['traditional_method']['average_confidence']
        comparison['improvement']['confidence_improvement'] = confidence_improvement
    
    return comparison


def _generate_method_recommendations(comparison_result):
    """手法推奨の生成"""
    recommendations = []
    
    enhanced_confidence = comparison_result['enhanced_method']['average_confidence']
    traditional_confidence = comparison_result['traditional_method']['average_confidence']
    
    if enhanced_confidence > traditional_confidence * 1.2:
        recommendations.append("新手法（カードベース）の使用を強く推奨します")
        recommendations.append(f"信頼度が従来手法より{((enhanced_confidence - traditional_confidence) / traditional_confidence * 100):.1f}%向上しています")
    elif enhanced_confidence > traditional_confidence:
        recommendations.append("新手法の使用を推奨します")
    else:
        recommendations.append("データの特性により従来手法が適している可能性があります")
    
    return recommendations
