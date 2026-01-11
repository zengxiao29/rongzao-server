# -*- coding: utf-8 -*-
import os
from flask import Flask
from dotenv import load_dotenv
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

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

app = Flask(__name__)

# 调试：检查SECRET_KEY是否正确加载
secret_key = os.environ.get('SECRET_KEY')
print(f"DEBUG: SECRET_KEY from environment: {secret_key}")
if secret_key:
    app.config['SECRET_KEY'] = secret_key
else:
    print("WARNING: SECRET_KEY not found in environment variables")
    # 设置一个默认密钥用于开发
    app.config['SECRET_KEY'] = 'dev-secret-key-change-this-in-production'

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
    
    # 检查是否是服务器环境
    if os.path.exists('.ecs'):
        # 服务器环境
        default_port = 8818
        debug = False
        env_name = "服务器环境"
    else:
        # 开发环境
        default_port = 8818
        debug = True
        env_name = "开发环境"
    
    # 确定端口号：命令行参数 > 环境变量 > 默认值
    port = args.port if args.port is not None else default_port
    
    print(f"运行模式: {env_name} (端口 {port})")
    # 添加use_reloader=False以避免在命令行启动时产生多个进程
    app.run(debug=debug, host=args.host, port=port, use_reloader=False)