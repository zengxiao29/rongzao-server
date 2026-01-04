# -*- coding: utf-8 -*-
from flask import Flask
from routes import register_routes
from api.dates import register_dates_routes
from api.config import register_config_routes
from api.analyse import register_analyse_routes
from api.upload import register_upload_routes
from api.stats import register_stats_routes
from api.export import register_export_routes
from api.metabase import register_metabase_routes

app = Flask(__name__)

# 注册所有路由
register_routes(app)
register_dates_routes(app)
register_config_routes(app)
register_analyse_routes(app)
register_upload_routes(app)
register_stats_routes(app)
register_export_routes(app)
register_metabase_routes(app)

if __name__ == '__main__':
    # 从环境变量获取配置，默认为开发环境
    env = os.environ.get('FLASK_ENV', 'development')
    
    # 根据环境选择配置
    if env == 'production':
        # 生产环境：使用 80 端口
        port = 80
        debug = False
        print("运行模式: 生产环境 (端口 80)")
    else:
        # 开发环境：使用 5001 端口
        port = 5001
        debug = True
        print("运行模式: 开发环境 (端口 5001)")
    
    app.run(debug=debug, host='0.0.0.0', port=port)