# -*- coding: utf-8 -*-
"""
按商品分析 API
提供单个商品的详细销售数据
"""

import sqlite3
import pandas as pd
from flask import jsonify, request
from database import get_db_connection
from utils.auth import token_required


def register_analyse_by_product_routes(app):
    """注册按商品分析相关的 API 路由"""

    @app.route('/api/analyse/product-details', methods=['GET'])
    @token_required
    def get_product_details():
        """获取商品详情数据"""
        try:
            # 获取参数
            product_type = request.args.get('product_type', '')
            start_date = request.args.get('start_date', '')
            end_date = request.args.get('end_date', '')
            data_type = request.args.get('data_type', 'quantity')  # quantity 或 amount

            if not product_type:
                return jsonify({'error': '缺少商品类型参数'}), 400

            if not start_date or not end_date:
                return jsonify({'error': '缺少日期参数'}), 400

            print(f'获取商品详情: {product_type}, 日期范围: {start_date} ~ {end_date}, 数据类型: {data_type}')

            # 连接数据库
            conn = get_db_connection()
            cursor = conn.cursor()

            # 查询该商品在指定日期范围内的数据
            query = '''
                SELECT 
                    付款时间,
                    订购数,
                    是否退款,
                    让利后金额,
                    店铺类型
                FROM OrderDetails
                WHERE 商品名称 = ?
                  AND 付款时间 LIKE ?
                ORDER BY 付款时间
            '''

            # 构建日期匹配模式（匹配日期部分）
            date_pattern = f'{start_date}%'
            
            cursor.execute(query, (product_type, date_pattern))
            rows = cursor.fetchall()

            conn.close()

            # 转换为 DataFrame
            df = pd.DataFrame([dict(row) for row in rows])

            if len(df) == 0:
                return jsonify({
                    'success': True,
                    'product_type': product_type,
                    'sales_curve': {'dates': [], 'quantities': [], 'amounts': []},
                    'average_order_value': 0,
                    'channel_sales': {'抖音': 0, '天猫': 0, '有赞': 0, '京东': 0}
                })

            # 1. 计算销售曲线数据（按天汇总）
            # 提取日期部分
            df['date'] = df['付款时间'].apply(lambda x: x.split(' ')[0] if x else '')
            
            # 计算有效订购数（排除退款成功的）
            df['valid_quantity'] = df.apply(
                lambda row: 0 if row['是否退款'] == '退款成功' else row['订购数'], 
                axis=1
            )
            
            # 处理让利后金额
            df['valid_amount'] = pd.to_numeric(df['让利后金额'], errors='coerce').fillna(0)

            # 按日期分组汇总
            daily_stats = df.groupby('date').agg({
                'valid_quantity': 'sum',
                'valid_amount': 'sum'
            }).reset_index()

            # 生成完整的日期范围
            import datetime
            start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            
            date_range = []
            current_dt = start_dt
            while current_dt <= end_dt:
                date_range.append(current_dt.strftime('%Y-%m-%d'))
                current_dt += datetime.timedelta(days=1)

            # 填充缺失的日期
            sales_curve_data = {'dates': date_range, 'quantities': [], 'amounts': []}
            
            for date in date_range:
                day_data = daily_stats[daily_stats['date'] == date]
                if len(day_data) > 0:
                    sales_curve_data['quantities'].append(int(day_data['valid_quantity'].values[0]))
                    sales_curve_data['amounts'].append(float(day_data['valid_amount'].values[0]))
                else:
                    sales_curve_data['quantities'].append(0)
                    sales_curve_data['amounts'].append(0.0)

            # 2. 计算客单价
            total_quantity = df['valid_quantity'].sum()
            total_amount = df['valid_amount'].sum()
            average_order_value = total_amount / total_quantity if total_quantity > 0 else 0

            # 3. 计算渠道销售分布
            channel_sales = {'抖音': 0, '天猫': 0, '有赞': 0, '京东': 0}
            
            for _, row in df.iterrows():
                shop_type = str(row['店铺类型']) if pd.notna(row['店铺类型']) else ''
                quantity = row['valid_quantity']
                
                if '抖音' in shop_type or '今日头条' in shop_type or '鲁班' in shop_type:
                    channel_sales['抖音'] += quantity
                elif '天猫' in shop_type:
                    channel_sales['天猫'] += quantity
                elif '有赞' in shop_type:
                    channel_sales['有赞'] += quantity
                elif '京东' in shop_type:
                    channel_sales['京东'] += quantity

            return jsonify({
                'success': True,
                'product_type': product_type,
                'sales_curve': sales_curve_data,
                'average_order_value': round(average_order_value, 2),
                'channel_sales': channel_sales
            })

        except Exception as e:
            print(f'获取商品详情失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
