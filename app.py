# -*- coding: utf-8 -*-
import os
from flask import Flask
from routes import register_routes
from api.dates import register_dates_routes
from api.analyse import register_analyse_routes
from api.upload import register_upload_routes
from api.export import register_export_routes
from api.product_manage import register_product_manage_routes

app = Flask(__name__)

# 注册所有路由
register_routes(app)
register_dates_routes(app)
register_analyse_routes(app)
register_upload_routes(app)
register_export_routes(app)
register_product_manage_routes(app)

if __name__ == '__main__':
    # 检查是否为服务器环境（通过 .ecs 文件判断）
    is_server = os.path.exists('.ecs')
    
    if is_server:
        # 服务器环境：使用 80 端口
        port = 80
        debug = False
        print("运行模式: 服务器环境 (端口 80)")
    else:
        # 开发环境：使用 5001 端口
        port = 5001
        debug = True
        print("运行模式: 开发环境 (端口 5001)")
    
    app.run(debug=debug, host='0.0.0.0', port=port)