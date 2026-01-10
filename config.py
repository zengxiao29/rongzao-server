# -*- coding: utf-8 -*-
import os

class Config:
    """基础配置"""
    SECRET_KEY = os.environ.get('SECRET_KEY', 'rongzao-secret-key-change-in-production')
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 8818  # 默认端口，会在 app.py 中根据环境覆盖
    
    # 数据库配置
    DB_PATH = os.path.join(os.path.dirname(__file__), 'rongzao.db')
    
    # 上传文件配置
    UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    ALLOWED_EXTENSIONS = {'xlsx', 'xls'}
    
    # 日志配置
    LOG_LEVEL = 'INFO'
    LOG_FILE = os.path.join(os.path.dirname(__file__), 'logs', 'app.log')

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    SECRET_KEY = os.environ.get('SECRET_KEY')  # 必须从环境变量获取
    JWT_SECRET = os.environ.get('JWT_SECRET')  # JWT 密钥也必须从环境变量获取

    # 验证环境变量
    if not SECRET_KEY:
        raise ValueError("生产环境必须设置 SECRET_KEY 环境变量")
    if not JWT_SECRET:
        raise ValueError("生产环境必须设置 JWT_SECRET 环境变量")

    # 生产环境特定的配置
    LOG_LEVEL = 'WARNING'

# 根据环境变量选择配置
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}

def get_config(env=None):
    """获取配置"""
    if env is None:
        env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])