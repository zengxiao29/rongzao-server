# -*- coding: utf-8 -*-
import json
import os
from flask import jsonify, request


def register_config_routes(app):
    """注册配置相关 API 路由"""

    @app.route('/api/analyse/config', methods=['GET'])
    def get_analyse_config():
        """获取 tab 配置"""
        config_file = os.path.join(os.path.dirname(__file__), '..', 'tab_config.json')
        if os.path.exists(config_file):
            with open(config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            return jsonify(config)
        else:
            return jsonify({'tabs': []})

    @app.route('/api/analyse/config', methods=['POST'])
    def save_analyse_config():
        """保存 tab 配置"""
        config_file = os.path.join(os.path.dirname(__file__), '..', 'tab_config.json')

        try:
            config = request.json
            with open(config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            return jsonify({'success': True})
        except Exception as e:
            return jsonify({'error': str(e)}), 500