# -*- coding: utf-8 -*-
from flask import jsonify
from dbpy.database import get_db_connection
from utils.auth import token_required


def register_dates_routes(app):
    """注册日期相关 API 路由"""

    @app.route('/api/analyse/dates', methods=['GET'])
    @token_required
    def get_available_dates():
        """获取数据库中所有可用的付款时间日期"""
        print('收到获取可用日期请求')

        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                # 获取所有付款时间不为空的记录
                cursor.execute('SELECT DISTINCT 付款时间 FROM OrderDetails WHERE 付款时间 IS NOT NULL AND 付款时间 != "" ORDER BY 付款时间')
                rows = cursor.fetchall()

                # 提取日期部分（YYYY-MM-DD）
                dates = set()
                for row in rows:
                    if row['付款时间']:
                        try:
                            # 处理日期字符串，提取日期部分
                            date_str = str(row['付款时间'])
                            if ' ' in date_str:
                                date_part = date_str.split(' ')[0]  # 提取日期部分
                                dates.add(date_part)
                        except:
                            continue

                # 转换为排序后的列表
                sorted_dates = sorted(list(dates))

                return jsonify({
                    'success': True,
                    'dates': sorted_dates,
                    'count': len(sorted_dates)
                })

            finally:
                conn.close()

        except Exception as e:
            print(f'获取可用日期时出错: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500