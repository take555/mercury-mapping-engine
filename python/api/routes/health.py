"""
Mercury Mapping Engine - Health Check API Routes
ヘルスチェックAPIルート
"""
from flask import Blueprint, current_app
import os
from datetime import datetime
from config.database import get_db_manager
from core import create_mapping_engine
from .helpers import create_success_response, create_error_response

# ブループリント作成
health_bp = Blueprint('health', __name__)


@health_bp.route('/health')
def health_check():
    """システム全体のヘルスチェック"""
    try:
        health_status = {
            'status': 'healthy',
            'timestamp': datetime.utcnow().isoformat(),
            'version': '2.0.0',
            'components': {}
        }
        
        # データベース接続チェック
        try:
            db_manager = get_db_manager()
            if db_manager.health_check():
                health_status['components']['database'] = {
                    'status': 'healthy',
                    'response_time_ms': _measure_db_response_time()
                }
            else:
                health_status['components']['database'] = {
                    'status': 'unhealthy',
                    'error': 'Connection failed'
                }
                health_status['status'] = 'degraded'
        except Exception as e:
            health_status['components']['database'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'degraded'
        
        # Claude API設定チェック
        claude_api_key = os.getenv('CLAUDE_API_KEY')
        if claude_api_key and claude_api_key != 'your-api-key-here':
            health_status['components']['claude_api'] = {
                'status': 'configured',
                'key_length': len(claude_api_key)
            }
        else:
            health_status['components']['claude_api'] = {
                'status': 'not_configured',
                'warning': 'Claude API key not set'
            }
        
        # ファイルシステムチェック
        upload_folder = '/app/uploads'
        if os.path.exists(upload_folder) and os.access(upload_folder, os.R_OK | os.W_OK):
            health_status['components']['file_system'] = {
                'status': 'healthy',
                'upload_folder': upload_folder,
                'writable': True
            }
        else:
            health_status['components']['file_system'] = {
                'status': 'unhealthy',
                'upload_folder': upload_folder,
                'writable': False
            }
            health_status['status'] = 'degraded'
        
        # Core Engine初期化チェック
        try:
            engine = create_mapping_engine()
            health_status['components']['core_engine'] = {
                'status': 'healthy',
                'components_loaded': True
            }
        except Exception as e:
            health_status['components']['core_engine'] = {
                'status': 'unhealthy',
                'error': str(e)
            }
            health_status['status'] = 'degraded'
        
        # 全体ステータスの決定
        component_statuses = [comp['status'] for comp in health_status['components'].values()]
        if any(status == 'unhealthy' for status in component_statuses):
            health_status['status'] = 'unhealthy'
            status_code = 503
        elif any(status == 'degraded' for status in component_statuses):
            health_status['status'] = 'degraded'
            status_code = 200
        else:
            status_code = 200
        
        return create_success_response(health_status), status_code
        
    except Exception as e:
        return create_error_response(f"Health check failed: {str(e)}", 500)


@health_bp.route('/health/database')
def database_health():
    """データベース専用ヘルスチェック"""
    try:
        db_manager = get_db_manager()
        
        # 接続テスト
        connection_ok = db_manager.test_connection()
        
        # クエリ実行テスト
        response_time = _measure_db_response_time()
        
        # カテゴリテーブルのカウント
        try:
            categories = db_manager.get_categories()
            category_count = len(categories)
        except Exception as e:
            category_count = None
            categories_error = str(e)
        
        db_status = {
            'connection': 'healthy' if connection_ok else 'unhealthy',
            'response_time_ms': response_time,
            'categories_count': category_count,
            'test_timestamp': datetime.utcnow().isoformat()
        }
        
        if not connection_ok:
            db_status['error'] = 'Database connection failed'
            return create_error_response("Database unhealthy", 503, db_status)
        
        if 'categories_error' in locals():
            db_status['categories_error'] = categories_error
        
        return create_success_response(db_status)
        
    except Exception as e:
        return create_error_response(f"Database health check failed: {str(e)}", 500)


@health_bp.route('/health/engine')
def engine_health():
    """Core Engine専用ヘルスチェック"""
    try:
        # Core Engineの初期化テスト
        engine = create_mapping_engine()
        
        engine_status = {
            'status': 'healthy',
            'components': {
                'csv_analyzer': engine.csv_analyzer is not None,
                'card_matcher': engine.card_matcher is not None,
                'field_mapper': engine.field_mapper is not None
            },
            'config_loaded': engine.config is not None,
            'test_timestamp': datetime.utcnow().isoformat()
        }
        
        # 簡単な機能テスト
        try:
            # テストデータでのCSV解析テスト
            test_result = _test_engine_functionality(engine)
            engine_status['functionality_test'] = test_result
        except Exception as e:
            engine_status['functionality_test'] = {
                'status': 'failed',
                'error': str(e)
            }
        
        return create_success_response(engine_status)
        
    except Exception as e:
        return create_error_response(f"Engine health check failed: {str(e)}", 500)


@health_bp.route('/health/files')
def files_health():
    """ファイルシステムとテストデータのヘルスチェック"""
    try:
        file_status = {
            'upload_folder': '/app/uploads',
            'test_files': {},
            'permissions': {},
            'test_timestamp': datetime.utcnow().isoformat()
        }
        
        # アップロードフォルダの確認
        upload_folder = '/app/uploads'
        file_status['upload_folder_exists'] = os.path.exists(upload_folder)
        file_status['permissions']['readable'] = os.access(upload_folder, os.R_OK) if os.path.exists(upload_folder) else False
        file_status['permissions']['writable'] = os.access(upload_folder, os.W_OK) if os.path.exists(upload_folder) else False
        
        # テストファイルの確認
        test_files = ['a.csv', 'b.csv']
        for filename in test_files:
            filepath = os.path.join(upload_folder, filename)
            if os.path.exists(filepath):
                stat = os.stat(filepath)
                file_status['test_files'][filename] = {
                    'exists': True,
                    'size_bytes': stat.st_size,
                    'modified': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'readable': os.access(filepath, os.R_OK)
                }
            else:
                file_status['test_files'][filename] = {
                    'exists': False,
                    'error': 'File not found'
                }
        
        # 全体ステータス判定
        all_files_exist = all(info['exists'] for info in file_status['test_files'].values())
        permissions_ok = file_status['permissions']['readable'] and file_status['permissions']['writable']
        
        if all_files_exist and permissions_ok:
            file_status['status'] = 'healthy'
            return create_success_response(file_status)
        else:
            file_status['status'] = 'degraded'
            return create_success_response(file_status), 200
        
    except Exception as e:
        return create_error_response(f"File system health check failed: {str(e)}", 500)


def _measure_db_response_time():
    """データベースレスポンス時間を測定"""
    import time
    try:
        start_time = time.time()
        db_manager = get_db_manager()
        db_manager.health_check()
        end_time = time.time()
        return round((end_time - start_time) * 1000, 2)  # ミリ秒
    except:
        return None


def _test_engine_functionality(engine):
    """Core Engineの基本機能テスト"""
    try:
        # テストデータ
        test_headers_a = ['name', 'price', 'series']
        test_headers_b = ['card_name', 'cost', 'set']
        test_data_a = [{'name': 'テストカード', 'price': '100', 'series': 'テスト'}]
        test_data_b = [{'card_name': 'テストカード', 'cost': '100', 'set': 'テスト'}]
        
        # カードマッチングテスト
        card_matches = engine.card_matcher.find_matching_cards(
            test_data_a, test_data_b, test_headers_a, test_headers_b
        )
        
        return {
            'status': 'passed',
            'card_matches_found': len(card_matches),
            'basic_functionality': 'working'
        }
        
    except Exception as e:
        return {
            'status': 'failed',
            'error': str(e)
        }
