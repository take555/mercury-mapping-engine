"""
Mercury Mapping Engine - Configuration Settings
アプリケーション設定管理
"""
import os
from datetime import timedelta


class BaseConfig:
    """基本設定"""
    
    # Flask設定
    SECRET_KEY = os.getenv('SECRET_KEY', 'mercury-mapping-engine-secret-key')
    JSON_AS_ASCII = False
    
    # データベース設定
    MYSQL_HOST = os.getenv('MYSQL_HOST', 'mysql')
    MYSQL_USER = os.getenv('MYSQL_USER', 'mercury')
    MYSQL_PASSWORD = os.getenv('MYSQL_PASSWORD', 'mercurypass')
    MYSQL_DATABASE = os.getenv('MYSQL_DATABASE', 'mercury')
    MYSQL_CHARSET = 'utf8mb4'
    
    # Claude API設定
    CLAUDE_API_KEY = os.getenv('CLAUDE_API_KEY')
    CLAUDE_API_VERSION = '2023-06-01'
    CLAUDE_API_BASE_URL = 'https://api.anthropic.com/v1'
    CLAUDE_DEFAULT_MODEL = 'claude-3-haiku-20240307'
    CLAUDE_MAX_TOKENS = 4000
    CLAUDE_TIMEOUT = 60
    
    # ファイル設定
    UPLOAD_FOLDER = '/app/uploads'
    RESULTS_FOLDER = '/app/results'
    LOGS_FOLDER = '/app/logs'
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # CSV解析設定
    CSV_MAX_ROWS = 1000
    CSV_SAMPLE_ROWS = 5
    CSV_ENCODING = 'utf-8'
    
    # カードマッチング設定
    CARD_MATCH_THRESHOLD = 0.75
    CARD_NAME_SIMILARITY_THRESHOLD = 0.8
    PRICE_SIMILARITY_THRESHOLD = 0.9
    FIELD_SIMILARITY_THRESHOLD = 0.7
    FIELD_CONSISTENCY_THRESHOLD = 0.6
    MIN_SAMPLE_COUNT = 3
    
    # ログ設定
    LOG_LEVEL = 'INFO'
    LOG_FORMAT = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    LOG_FILE_MAX_SIZE = 10 * 1024 * 1024  # 10MB
    LOG_FILE_BACKUP_COUNT = 5
    
    @staticmethod
    def init_app(app):
        """アプリケーション初期化時の処理"""
        pass


class DevelopmentConfig(BaseConfig):
    """開発環境設定"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'
    
    # 開発用のより小さい制限
    CSV_MAX_ROWS = 999999  # 実質無制限
    CLAUDE_MAX_TOKENS = 1000
    
    @staticmethod
    def init_app(app):
        BaseConfig.init_app(app)
        print("🔧 Development mode activated")


class ProductionConfig(BaseConfig):
    """本番環境設定"""
    DEBUG = False
    LOG_LEVEL = 'WARNING'
    
    # 本番用のより大きな制限
    CSV_MAX_ROWS = 5000
    CLAUDE_MAX_TOKENS = 8000
    
    @staticmethod
    def init_app(app):
        BaseConfig.init_app(app)
        
        # 本番環境での必須設定チェック
        required_env_vars = [
            'CLAUDE_API_KEY',
            'MYSQL_PASSWORD',
            'SECRET_KEY'
        ]
        
        missing_vars = [var for var in required_env_vars if not os.getenv(var)]
        if missing_vars:
            raise ValueError(f"Missing required environment variables: {missing_vars}")


class TestingConfig(BaseConfig):
    """テスト環境設定"""
    TESTING = True
    DEBUG = True
    LOG_LEVEL = 'ERROR'
    
    # テスト用の小さい制限
    CSV_MAX_ROWS = 10
    CLAUDE_MAX_TOKENS = 100
    
    # テスト用DB（メモリ）
    MYSQL_DATABASE = 'mercury_test'


class Config:
    """設定クラス管理"""
    
    configs = {
        'development': DevelopmentConfig,
        'production': ProductionConfig,
        'testing': TestingConfig,
        'default': DevelopmentConfig
    }
    
    @classmethod
    def get_config(cls, config_name):
        """設定クラスを取得"""
        return cls.configs.get(config_name, cls.configs['default'])
    
    @classmethod
    def get_database_config(cls, config_name='default'):
        """データベース設定を辞書で取得"""
        config_class = cls.get_config(config_name)
        return {
            'host': config_class.MYSQL_HOST,
            'user': config_class.MYSQL_USER,
            'password': config_class.MYSQL_PASSWORD,
            'database': config_class.MYSQL_DATABASE,
            'charset': config_class.MYSQL_CHARSET
        }
    
    @classmethod
    def get_claude_config(cls, config_name='default'):
        """Claude API設定を辞書で取得"""
        config_class = cls.get_config(config_name)
        return {
            'api_key': config_class.CLAUDE_API_KEY,
            'api_version': config_class.CLAUDE_API_VERSION,
            'base_url': config_class.CLAUDE_API_BASE_URL,
            'default_model': config_class.CLAUDE_DEFAULT_MODEL,
            'max_tokens': config_class.CLAUDE_MAX_TOKENS,
            'timeout': config_class.CLAUDE_TIMEOUT
        }
    
    @classmethod
    def get_analysis_config(cls, config_name='default'):
        """分析設定を辞書で取得"""
        config_class = cls.get_config(config_name)
        return {
            'csv_max_rows': config_class.CSV_MAX_ROWS,
            'csv_sample_rows': config_class.CSV_SAMPLE_ROWS,
            'csv_encoding': config_class.CSV_ENCODING,
            'card_match_threshold': config_class.CARD_MATCH_THRESHOLD,
            'card_name_similarity_threshold': config_class.CARD_NAME_SIMILARITY_THRESHOLD,
            'price_similarity_threshold': config_class.PRICE_SIMILARITY_THRESHOLD,
            'field_similarity_threshold': config_class.FIELD_SIMILARITY_THRESHOLD,
            'field_consistency_threshold': config_class.FIELD_CONSISTENCY_THRESHOLD,
            'min_sample_count': config_class.MIN_SAMPLE_COUNT
        }