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
    app.run(debug=True, host='0.0.0.0', port=5001)