# -*- coding: utf-8 -*-
import os
from flask import Flask
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# 加载 .env 文件中的环境变量
load_dotenv()

# 导入配置
from config import get_config

from routes import register_routes
from api.dates import register_dates_routes
from api.analyse import register_analyse_routes
from api.upload import register_upload_routes
from api.export import register_export_routes
from api.product_manage import register_product_manage_routes
from api.auth import register_auth_routes
from api.report import register_report_routes
from api.analyse_by_product import register_analyse_by_product_routes

app = Flask(__name__)

# 获取配置（根据 FLASK_ENV 环境变量自动选择）
config = get_config()

# 应用配置到 Flask 应用
app.config.from_object(config)

# 调试：显示当前配置
print(f"DEBUG: 当前环境: {os.environ.get('FLASK_ENV', 'development')}")
print(f"DEBUG: SECRET_KEY: {app.config.get('SECRET_KEY')[:20]}..." if app.config.get('SECRET_KEY') else "DEBUG: SECRET_KEY: None")

# 启用CSRF保护
csrf = CSRFProtect(app)

# 配置速率限制
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["1 per second"]  # 默认限制：每秒1个请求
)
limiter.init_app(app)

# 将limiter附加到app对象，以便在路由中使用
app.limiter = limiter

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
    import argparse
    
    # 解析命令行参数
    parser = argparse.ArgumentParser(description='启动Flask应用')
    parser.add_argument('--port', type=int, default=None, help='服务器端口号')
    parser.add_argument('--host', type=str, default='0.0.0.0', help='服务器主机地址')
    args = parser.parse_args()
    
    # 根据配置获取环境信息
    debug = config.DEBUG
    env_name = os.environ.get('FLASK_ENV', 'development')
    
    # 确定端口号：命令行参数 > 配置文件 > 默认值
    port = args.port if args.port is not None else getattr(config, 'PORT', 8818)
    
    print(f"运行模式: {env_name} (端口 {port}, DEBUG={debug})")
    # 添加use_reloader=False以避免在命令行启动时产生多个进程
    app.run(debug=debug, host=args.host, port=port, use_reloader=False)