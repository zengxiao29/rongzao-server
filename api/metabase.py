# -*- coding: utf-8 -*-
import jwt
import time
from flask import jsonify, request
from functools import wraps

# Metabase 配置
METABASE_SITE_URL = "http://localhost:3000"
METABASE_SECRET_KEY = "463a666a7fe9ba08e92efba2626cf68e95e5fb63fa4ffbb00c8c877f84ad0132"


def generate_metabase_token(dashboard_id):
    """
    生成 Metabase 嵌入 token

    Args:
        dashboard_id: 仪表板 ID

    Returns:
        JWT token 字符串
    """
    payload = {
        "resource": {"dashboard": dashboard_id},
        "params": {},
        "exp": round(time.time()) + (60 * 10)  # 10 minute expiration
    }

    token = jwt.encode(payload, METABASE_SECRET_KEY, algorithm="HS256")

    # 处理不同版本的 PyJWT 返回类型
    if isinstance(token, bytes):
        token = token.decode('utf-8')

    return token


def generate_metabase_embed_url(dashboard_id):
    """
    生成 Metabase 嵌入 URL

    Args:
        dashboard_id: 仪表板 ID

    Returns:
        完整的嵌入 URL 字符串
    """
    token = generate_metabase_token(dashboard_id)
    iframeUrl = METABASE_SITE_URL + "/embed/dashboard/" + token + "#bordered=true&titled=true"
    return iframeUrl


def register_metabase_routes(app):
    """注册 Metabase 相关 API 路由"""

    @app.route('/metabase-test')
    def metabase_test():
        """Metabase 测试页面"""
        from flask import render_template
        return render_template('metabase_test.html')

    @app.route('/api/metabase/token', methods=['POST'])
    def get_metabase_token():
        """获取 Metabase 嵌入 token"""
        try:
            data = request.json
            dashboard_id = data.get('dashboard_id')

            if not dashboard_id:
                return jsonify({'error': '缺少 dashboard_id 参数'}), 400

            # 生成 token
            token = generate_metabase_token(dashboard_id)

            # 生成完整的嵌入 URL
            iframe_url = generate_metabase_embed_url(dashboard_id)

            return jsonify({
                'token': token,
                'url': iframe_url
            })

        except Exception as e:
            print(f'生成 Metabase token 失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500