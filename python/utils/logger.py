"""
Mercury Mapping Engine - Logging Utilities
ログ設定管理
"""
import logging
import logging.handlers
import os
from datetime import datetime


def setup_logging(app):
    """アプリケーションのログ設定"""
    
    # ログレベル設定
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    app.logger.setLevel(log_level)
    
    # ログフォーマット
    formatter = logging.Formatter(
        app.config.get('LOG_FORMAT', 
                      '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )
    
    # コンソールハンドラー
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    
    # ファイルハンドラー（ローテーション付き）
    logs_folder = app.config.get('LOGS_FOLDER', '/app/logs')
    os.makedirs(logs_folder, exist_ok=True)
    
    log_file = os.path.join(logs_folder, 'mercury.log')
    file_handler = logging.handlers.RotatingFileHandler(
        log_file,
        maxBytes=app.config.get('LOG_FILE_MAX_SIZE', 10*1024*1024),
        backupCount=app.config.get('LOG_FILE_BACKUP_COUNT', 5),
        encoding='utf-8'
    )
    file_handler.setLevel(log_level)
    file_handler.setFormatter(formatter)
    
    # ハンドラーをアプリケーションロガーに追加
    app.logger.addHandler(console_handler)
    app.logger.addHandler(file_handler)
    
    # 他のライブラリのログレベルを調整
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('mysql.connector').setLevel(logging.WARNING)
    
    app.logger.info("Logging configuration completed")


class AnalysisLogger:
    """分析処理専用のロガー"""
    
    def __init__(self, name="analysis"):
        self.logger = logging.getLogger(name)
        
    def log_csv_analysis(self, file_path, headers_count, rows_count):
        """CSV分析のログ"""
        self.logger.info(f"CSV Analysis - File: {file_path}, Headers: {headers_count}, Rows: {rows_count}")
    
    def log_card_matching(self, total_cards_a, total_cards_b, matches_found):
        """カードマッチングのログ"""
        self.logger.info(f"Card Matching - A: {total_cards_a}, B: {total_cards_b}, Matches: {matches_found}")
    
    def log_field_mapping(self, mappings_count, high_confidence_count):
        """フィールドマッピングのログ"""
        self.logger.info(f"Field Mapping - Total: {mappings_count}, High Confidence: {high_confidence_count}")
    
    def log_claude_api_call(self, model, input_tokens, cost_estimate):
        """Claude API呼び出しのログ"""
        self.logger.info(f"Claude API - Model: {model}, Tokens: {input_tokens}, Cost: ${cost_estimate:.6f}")
    
    def log_error(self, operation, error_message):
        """エラーログ"""
        self.logger.error(f"Error in {operation}: {error_message}")


class PerformanceLogger:
    """パフォーマンス測定用のロガー"""
    
    def __init__(self):
        self.logger = logging.getLogger("performance")
        self.start_times = {}
    
    def start_timer(self, operation_name):
        """タイマー開始"""
        self.start_times[operation_name] = datetime.now()
        self.logger.debug(f"Started: {operation_name}")
    
    def end_timer(self, operation_name):
        """タイマー終了とログ出力"""
        if operation_name in self.start_times:
            duration = datetime.now() - self.start_times[operation_name]
            duration_ms = duration.total_seconds() * 1000
            self.logger.info(f"Completed: {operation_name} in {duration_ms:.2f}ms")
            del self.start_times[operation_name]
            return duration_ms
        else:
            self.logger.warning(f"Timer not found for operation: {operation_name}")
            return None


# グローバルなロガーインスタンス
analysis_logger = AnalysisLogger()
performance_logger = PerformanceLogger()