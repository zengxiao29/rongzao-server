# -*- coding: utf-8 -*-
from flask import jsonify
from database import get_db_connection


def register_stats_routes(app):
    """注册统计相关 API 路由"""

    @app.route('/api/db/stats', methods=['GET'])
    def get_database_stats():
        """获取数据库统计信息"""
        try:
            conn = get_db_connection()
            cursor = conn.cursor()

            # 获取总记录数
            cursor.execute('SELECT COUNT(*) as total FROM OrderDetails')
            total = cursor.fetchone()['total']

            # 获取去重后的单据编号数
            cursor.execute('SELECT COUNT(DISTINCT 单据编号) as unique_orders FROM OrderDetails')
            unique_orders = cursor.fetchone()['unique_orders']

            # 获取去重后的商品代码数
            cursor.execute('SELECT COUNT(DISTINCT 商品代码) as unique_products FROM OrderDetails')
            unique_products = cursor.fetchone()['unique_products']

            # 获取退款订单数
            cursor.execute('SELECT COUNT(*) as refunded FROM OrderDetails WHERE 是否退款 = "退款成功"')
            refunded = cursor.fetchone()['refunded']

            # 获取有效订单数
            cursor.execute('SELECT COUNT(*) as valid FROM OrderDetails WHERE 是否退款 != "退款成功" OR 是否退款 IS NULL')
            valid = cursor.fetchone()['valid']

            # 获取总订购数（有效订单）
            cursor.execute('SELECT SUM(订购数) as total_orders FROM OrderDetails WHERE 是否退款 != "退款成功" OR 是否退款 IS NULL')
            total_orders = cursor.fetchone()['total_orders'] or 0

            # 获取总让利后金额（有效订单）
            cursor.execute('SELECT SUM(让利后金额) as total_amount FROM OrderDetails WHERE 是否退款 != "退款成功" OR 是否退款 IS NULL')
            total_amount = cursor.fetchone()['total_amount'] or 0

            conn.close()

            return jsonify({
                'success': True,
                'stats': {
                    'total_records': total,
                    'unique_orders': unique_orders,
                    'unique_products': unique_products,
                    'refunded_orders': refunded,
                    'valid_orders': valid,
                    'total_order_quantity': int(total_orders),
                    'total_discount_amount': float(total_amount)
                }
            })

        except Exception as e:
            print(f'获取统计信息时出错: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500