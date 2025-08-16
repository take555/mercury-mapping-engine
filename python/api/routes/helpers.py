"""
Mercury Mapping Engine - API Helpers
API routes共通のヘルパー関数
"""
from flask import jsonify
from typing import Dict, Any, Optional
import traceback
from datetime import datetime


def create_success_response(data: Any = None, message: str = "Success", 
                          status_code: int = 200) -> tuple:
    """成功レスポンスを作成"""
    response_data = {
        "success": True,
        "message": message,
        "timestamp": datetime.now().isoformat(),
        "data": data
    }
    return jsonify(response_data), status_code


def create_error_response(error: str, status_code: int = 400, 
                         details: Optional[Dict] = None) -> tuple:
    """エラーレスポンスを作成"""
    response_data = {
        "success": False,
        "error": error,
        "timestamp": datetime.now().isoformat()
    }
    
    if details:
        response_data["details"] = details
    
    return jsonify(response_data), status_code


def create_validation_error_response(errors: Dict[str, str]) -> tuple:
    """バリデーションエラーレスポンスを作成"""
    return create_error_response(
        error="Validation failed",
        status_code=422,
        details={"validation_errors": errors}
    )


def handle_exception(e: Exception, context: str = "") -> tuple:
    """例外を適切なレスポンスに変換"""
    error_message = f"{context}: {str(e)}" if context else str(e)
    
    # デバッグ情報（開発環境のみ）
    details = {
        "type": type(e).__name__,
        "traceback": traceback.format_exc()
    }
    
    return create_error_response(
        error=error_message,
        status_code=500,
        details=details
    )


def validate_required_fields(data: Dict, required_fields: list) -> Optional[Dict[str, str]]:
    """必須フィールドのバリデーション"""
    errors = {}
    
    for field in required_fields:
        if field not in data or data[field] is None:
            errors[field] = f"Field '{field}' is required"
        elif isinstance(data[field], str) and not data[field].strip():
            errors[field] = f"Field '{field}' cannot be empty"
    
    return errors if errors else None


def paginate_response(data: list, page: int = 1, per_page: int = 20) -> Dict[str, Any]:
    """ページネーション付きレスポンスを作成"""
    total = len(data)
    start = (page - 1) * per_page
    end = start + per_page
    
    return {
        "items": data[start:end],
        "pagination": {
            "page": page,
            "per_page": per_page,
            "total": total,
            "pages": (total + per_page - 1) // per_page,
            "has_prev": page > 1,
            "has_next": end < total
        }
    }
