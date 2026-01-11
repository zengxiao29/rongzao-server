# -*- coding: utf-8 -*-
"""
错误处理工具模块
用于统一处理API错误，防止敏感信息泄露
"""

import os
import traceback
from flask import jsonify


def handle_api_error(e, context="API"):
    """
    统一处理API错误，防止敏感信息泄露
    
    Args:
        e: 异常对象
        context: 错误上下文，如API名称等
    
    Returns:
        Flask响应对象
    """
    # 记录详细错误日志（仅在服务器环境记录）
    error_msg = str(e)
    print(f'{context}发生错误: {error_msg}')
    
    # 始终记录堆栈跟踪到日志
    traceback.print_exc()
    
    # 检查是否为生产环境
    is_production = os.path.exists('.ecs')
    
    if is_production:
        # 生产环境：返回通用错误消息
        return jsonify({
            'error': '服务器内部错误，请稍后重试或联系管理员'
        }), 500
    else:
        # 开发环境：返回详细错误信息（便于调试）
        return jsonify({
            'error': f'{context}发生错误: {error_msg}',
            'detail': str(e),
            'type': type(e).__name__
        }), 500