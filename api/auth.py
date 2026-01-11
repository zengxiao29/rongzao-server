# -*- coding: utf-8 -*-
from flask import jsonify, request, g
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import bcrypt
from dbpy.database import get_db_connection
from utils.auth import generate_token, verify_token, token_required
from utils.operation_logger import log_operation

def register_auth_routes(app):
    """注册认证相关 API 路由"""

    @app.route('/api/auth/login', methods=['POST'])
    @app.limiter.limit("10 per hour")  # 同一个IP 10次/小时
    def auth_login():
        """
        用户登录

        Request body:
            {
                "username": "用户名",
                "password": "密码",
                "remember_me": true/false  // 可选，默认false
            }

        Response:
            {
                "success": true,
                "token": "JWT token",
                "user": {
                    "id": 用户ID,
                    "username": "用户名",
                    "role": "角色"
                }
            }
        """
        try:
            data = request.json
            username = data.get('username', '').strip()
            password = data.get('password', '')
            remember_me = data.get('remember_me', False)

            if not username or not password:
                return jsonify({'error': '用户名和密码不能为空'}), 400

            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                # 查询用户
                cursor.execute('SELECT id, username, password_hash, role FROM users WHERE username = ?', (username,))
                user = cursor.fetchone()

                if not user:
                    return jsonify({'error': '用户名或密码错误'}), 401

                # 验证密码
                password_hash = user['password_hash']
                if not bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8')):
                    return jsonify({'error': '用户名或密码错误'}), 401

                # 生成 token
                token = generate_token(user['id'], user['username'], user['role'], remember_me)

                # 记录登录日志
                log_operation(
                    username=user['username'],
                    role=user['role'],
                    operation_type='login',
                    result='success'
                )

                return jsonify({
                    'success': True,
                    'token': token,
                    'user': {
                        'id': user['id'],
                        'username': user['username'],
                        'role': user['role']
                    }
                })

            finally:
                conn.close()

        except Exception as e:
            print(f'登录失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500

    @app.route('/api/auth/verify', methods=['GET'])
    @token_required
    def verify():
        """
        验证 token 是否有效

        Response:
            {
                "success": true,
                "user": {
                    "id": 用户ID,
                    "username": "用户名",
                    "role": "角色"
                }
            }
        """
        try:
            return jsonify({
                'success': True,
                'user': g.current_user
            })
        except Exception as e:
            print(f'验证失败: {str(e)}')
            return jsonify({'error': str(e)}), 500

    @app.route('/api/auth/logout', methods=['POST'])
    @token_required
    def logout():
        """
        用户登出

        注意：JWT 是无状态的，服务端无法主动使 token 失效
        客户端需要删除保存的 token
        """
        try:
            # 记录退出日志
            log_operation(
                username=g.current_user['username'],
                role=g.current_user['role'],
                operation_type='logout',
                result='success'
            )

            return jsonify({
                'success': True,
                'message': '登出成功'
            })
        except Exception as e:
            print(f'登出失败: {str(e)}')
            return jsonify({'error': str(e)}), 500