"""
Mercury Mapping Engine - Database Configuration
データベース接続管理
"""
import mysql.connector
from mysql.connector import pooling
from contextlib import contextmanager
from .settings import Config


class DatabaseManager:
    """データベース接続管理クラス"""
    
    def __init__(self, config_name='default'):
        self.config = Config.get_database_config(config_name)
        self.pool = None
        self._create_connection_pool()
    
    def _create_connection_pool(self):
        """コネクションプールを作成"""
        try:
            pool_config = self.config.copy()
            pool_config.update({
                'pool_name': 'mercury_pool',
                'pool_size': 5,
                'pool_reset_session': True
            })
            
            self.pool = pooling.MySQLConnectionPool(**pool_config)
            print("✅ Database connection pool created")
            
        except Exception as e:
            print(f"❌ Failed to create database connection pool: {e}")
            raise
    
    @contextmanager
    def get_connection(self):
        """コネクションをコンテキストマネージャーで取得"""
        connection = None
        try:
            connection = self.pool.get_connection()
            yield connection
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if connection and connection.is_connected():
                connection.close()
    
    @contextmanager
    def get_cursor(self, dictionary=False):
        """カーソルをコンテキストマネージャーで取得"""
        with self.get_connection() as connection:
            cursor = connection.cursor(dictionary=dictionary)
            try:
                yield cursor, connection
            finally:
                cursor.close()
    
    def test_connection(self):
        """接続テスト"""
        try:
            with self.get_connection() as connection:
                if connection.is_connected():
                    return True
            return False
        except Exception as e:
            print(f"Database connection test failed: {e}")
            return False
    
    def execute_query(self, query, params=None, fetch=False, dictionary=False):
        """クエリ実行ヘルパー"""
        try:
            with self.get_cursor(dictionary=dictionary) as (cursor, connection):
                cursor.execute(query, params or ())
                
                if fetch:
                    if 'SELECT' in query.upper():
                        return cursor.fetchall()
                    else:
                        return cursor.rowcount
                else:
                    connection.commit()
                    return cursor.rowcount
                    
        except Exception as e:
            print(f"Query execution failed: {e}")
            raise
    
    def get_categories(self):
        """カテゴリ一覧を取得"""
        query = "SELECT * FROM mercury_category2 WHERE active = 1"
        return self.execute_query(query, fetch=True, dictionary=True)
    
    def health_check(self):
        """ヘルスチェック用のクエリ実行"""
        try:
            query = "SELECT 1 as status"
            result = self.execute_query(query, fetch=True)
            return len(result) > 0
        except Exception:
            return False


# グローバルなデータベースマネージャーインスタンス
_db_manager = None


def init_db(app):
    """アプリケーション初期化時のDB設定"""
    global _db_manager
    
    config_name = 'production' if not app.config.get('DEBUG') else 'development'
    _db_manager = DatabaseManager(config_name)
    
    # アプリケーションコンテキストにDB管理を追加
    app.db_manager = _db_manager
    
    # 接続テスト
    if _db_manager.test_connection():
        app.logger.info("✅ Database connection established")
    else:
        app.logger.error("❌ Database connection failed")


def get_db_manager():
    """グローバルなDB管理インスタンスを取得"""
    if _db_manager is None:
        raise RuntimeError("Database not initialized. Call init_db() first.")
    return _db_manager


# 便利な関数群
def execute_query(query, params=None, fetch=False, dictionary=False):
    """グローバルなクエリ実行関数"""
    return get_db_manager().execute_query(query, params, fetch, dictionary)


def get_categories():
    """カテゴリ一覧取得"""
    return get_db_manager().get_categories()


def health_check():
    """ヘルスチェック"""
    return get_db_manager().health_check()