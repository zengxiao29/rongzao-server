# -*- coding: utf-8 -*-
import jwt
import os
import warnings
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify, g

# JWT 配置
JWT_SECRET = os.environ.get('JWT_SECRET', 'dev-secret-key-change-in-production')

# 验证是否使用了默认密钥
if JWT_SECRET == 'dev-secret-key-change-in-production' or JWT_SECRET == 'your-secret-key-change-this-in-production':
    warnings.warn(
        "JWT_SECRET 使用了默认值，请设置环境变量！\n"
        "生产环境必须设置强随机密钥，否则存在严重安全风险。\n"
        "设置方法: export JWT_SECRET='your-secret-key'"
    )

JWT_ALGORITHM = 'HS256'

# Token 过期时间
ACCESS_TOKEN_EXPIRE_DAYS = 14  # 2周


def generate_token(user_id, username, role, remember_me=False):
    """
    生成 JWT token

    Args:
        user_id: 用户ID
        username: 用户名
        role: 用户角色
        remember_me: 是否记住我（如果为True，使用更长的过期时间）

    Returns:
        JWT token 字符串
    """
    payload = {
        'user_id': user_id,
        'username': username,
        'role': role,
        'exp': datetime.utcnow() + timedelta(days=ACCESS_TOKEN_EXPIRE_DAYS),
        'iat': datetime.utcnow()
    }

    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token


def verify_token(token):
    """
    验证 JWT token

    Args:
        token: JWT token 字符串

    Returns:
        如果验证成功，返回 payload 字典
        如果验证失败，返回 None
    """
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        # Token 过期
        return None
    except jwt.InvalidTokenError:
        # Token 无效
        return None


def token_required(f):
    """
    JWT 认证装饰器，用于保护需要登录的 API

    Usage:
        @app.route('/api/protected')
        @token_required
        def protected_route():
            return jsonify({'message': 'This is a protected route'})
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None

        # 从请求头中获取 token
        auth_header = request.headers.get('Authorization')
        if auth_header and auth_header.startswith('Bearer '):
            token = auth_header.split(' ')[1]

        if not token:
            return jsonify({'error': '未提供认证令牌', 'code': 'NO_TOKEN'}), 401

        # 验证 token
        payload = verify_token(token)
        if not payload:
            return jsonify({'error': '认证令牌无效或已过期', 'code': 'INVALID_TOKEN'}), 401

        # 将用户信息保存到 g 对象中，供后续使用
        g.current_user = {
            'user_id': payload['user_id'],
            'username': payload['username'],
            'role': payload['role']
        }

        return f(*args, **kwargs)

    return decorated


def role_required(required_role):
    """
    角色权限装饰器，用于检查用户是否具有指定角色

    Args:
        required_role: 需要的角色（admin 或 user）

    Usage:
        @app.route('/api/admin-only')
        @token_required
        @role_required('admin')
        def admin_only_route():
            return jsonify({'message': 'This is an admin only route'})
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            # 检查是否有用户信息（需要先使用 token_required 装饰器）
            if not hasattr(g, 'current_user'):
                return jsonify({'error': '未认证', 'code': 'NOT_AUTHENTICATED'}), 401

            # 检查角色
            if g.current_user['role'] != required_role:
                return jsonify({'error': '权限不足', 'code': 'INSUFFICIENT_PERMISSIONS'}), 403

            return f(*args, **kwargs)

        return decorated
    return decorator


def admin_required(f):
    """
    管理员权限装饰器，用于检查用户是否为管理员

    Usage:
        @app.route('/admin/page')
        @admin_required
        def admin_page():
            return render_template('admin.html')
    """
    @wraps(f)
    def decorated(*args, **kwargs):
        # 从 cookie 中获取 token
        token = request.cookies.get('token')

        if not token:
            # 如果没有 token，重定向到首页
            from flask import redirect, url_for
            return redirect(url_for('index'))

        # 验证 token
        payload = verify_token(token)
        if not payload:
            # Token 无效，重定向到首页
            from flask import redirect, url_for
            return redirect(url_for('index'))

        # 检查角色
        if payload.get('role') != 'admin':
            # 不是管理员，重定向到首页
            from flask import redirect, url_for
            return redirect(url_for('index'))

        return f(*args, **kwargs)

    return decorated