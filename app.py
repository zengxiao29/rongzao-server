# -*- coding: utf-8 -*-
import os
from flask import Flask
from dotenv import load_dotenv

# 加载 .env 文件中的环境变量
load_dotenv()

from routes import register_routes
from api.dates import register_dates_routes
from api.analyse import register_analyse_routes
from api.upload import register_upload_routes
from api.export import register_export_routes
from api.product_manage import register_product_manage_routes
from api.auth import register_auth_routes
from api.report import register_report_routes
from api.analyse_by_product import register_analyse_by_product_routes
from database import init_user_table

app = Flask(__name__)

# 注册所有路由
register_routes(app)
register_dates_routes(app)
register_analyse_routes(app)
register_upload_routes(app)
register_export_routes(app)
register_product_manage_routes(app)
register_auth_routes(app)
register_report_routes(app)
register_analyse_by_product_routes(app)

if __name__ == '__main__':
    # 初始化用户表
    init_user_table()

    # 检查是否为服务器环境（通过 .ecs 文件判断）
    is_server = os.path.exists('.ecs')

    if is_server:
        # 服务器环境：使用 8818 端口
        port = 8818
        debug = False
        print("运行模式: 服务器环境 (端口 8818)")
    else:
        # 开发环境：使用 8818 端口
        port = 8818
        debug = True
        print("运行模式: 开发环境 (端口 8818)")

    app.run(debug=debug, host='0.0.0.0', port=port)