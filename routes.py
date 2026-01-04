# -*- coding: utf-8 -*-
from flask import render_template, send_from_directory


def register_routes(app):
    """注册所有页面路由"""

    @app.route('/')
    def index():
        """首页"""
        return render_template('index.html')

    @app.route('/data-analysis')
    def data_analysis():
        """数据分析页面"""
        return render_template('data_analysis.html')

    @app.route('/test')
    def test():
        """测试页面"""
        return render_template('test.html')

    @app.route('/project-management')
    def project_management():
        """项目管理页面"""
        return render_template('project_management.html')

    @app.route('/production-management')
    def production_management():
        """生产管理页面"""
        return render_template('production_management.html')

    @app.route('/analyse')
    def analyse():
        """数据分析页面"""
        return render_template('analyse.html')

    @app.route('/mobile-analyse')
    def mobile_analyse():
        """移动端数据分析页面"""
        return render_template('mobile_analyse.html')

    @app.route('/<path:filename>')
    def serve_static_file(filename):
        """提供静态文件服务"""
        return send_from_directory('.', filename)