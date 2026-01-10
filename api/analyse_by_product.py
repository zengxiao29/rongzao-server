# -*- coding: utf-8 -*-
"""
按商品分析 API
提供单个商品的详细销售数据
"""

import sqlite3
import pandas as pd
from flask import jsonify, request
from dbpy.database import get_db_connection
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

            # 计算聚合级别
            import datetime
            start_dt = datetime.datetime.strptime(start_date, '%Y-%m-%d')
            end_dt = datetime.datetime.strptime(end_date, '%Y-%m-%d')
            days_diff = (end_dt - start_dt).days
            
            # 确定聚合级别
            def determine_aggregation_level(days):
                if days <= 30:      # 1个月内：按天显示
                    return 'day'
                elif days <= 90:    # 1-3个月：按周显示
                    return 'week'
                elif days <= 912:   # 两年半以内：按月显示
                    return 'month'
                elif days <= 1825:  # 两年半到五年：按季度显示
                    return 'quarter'
                else:               # 五年以上：按年显示
                    return 'year'
            
            aggregation_level = determine_aggregation_level(days_diff)
            print(f'日期范围: {days_diff}天, 聚合级别: {aggregation_level}')

            # 连接数据库
            conn = get_db_connection()
            cursor = conn.cursor()

            # 先查询 ProductInfo 表，获取所有映射到该 mapped_title 的商品名称
            cursor.execute('SELECT name FROM ProductInfo WHERE mapped_title = ?', (product_type,))
            product_names = [row['name'] for row in cursor.fetchall()]

            if not product_names:
                conn.close()
                return jsonify({
                    'success': True,
                    'product_type': product_type,
                    'aggregation_level': aggregation_level,
                    'sales_curve': {
                        'dates': [],
                        'overall': {'quantities': [], 'amounts': [], 'average_prices': []},
                        'channels': {
                            '抖音': {'quantities': [], 'amounts': [], 'average_prices': []},
                            '天猫': {'quantities': [], 'amounts': [], 'average_prices': []},
                            '有赞': {'quantities': [], 'amounts': [], 'average_prices': []},
                            '京东': {'quantities': [], 'amounts': [], 'average_prices': []}
                        }
                    },
                    'average_order_value': 0,
                    'channel_sales': {'抖音': 0, '天猫': 0, '有赞': 0, '京东': 0}
                })

            print(f'找到 {len(product_names)} 个商品名称映射到 {product_type}: {product_names}')

            # 查询该商品在指定日期范围内的数据
            # 使用 IN 子句查询所有映射的商品名称
            placeholders = ','.join(['?' for _ in product_names])
            query = f'''
                SELECT
                    付款时间,
                    订购数,
                    是否退款,
                    让利后金额,
                    店铺类型
                FROM OrderDetails
                WHERE 商品名称 IN ({placeholders})
                  AND 付款时间 >= ?
                  AND 付款时间 <= ?
                ORDER BY 付款时间
            '''

            # 构建日期范围（包含完整的日期时间）
            start_datetime = f'{start_date} 00:00:00'
            end_datetime = f'{end_date} 23:59:59'

            cursor.execute(query, product_names + [start_datetime, end_datetime])
            rows = cursor.fetchall()

            conn.close()

            # 转换为 DataFrame
            df = pd.DataFrame([dict(row) for row in rows])

            if len(df) == 0:
                return jsonify({
                    'success': True,
                    'product_type': product_type,
                    'aggregation_level': aggregation_level,
                    'sales_curve': {
                        'dates': [],
                        'overall': {'quantities': [], 'amounts': [], 'average_prices': []},
                        'channels': {
                            '抖音': {'quantities': [], 'amounts': [], 'average_prices': []},
                            '天猫': {'quantities': [], 'amounts': [], 'average_prices': []},
                            '有赞': {'quantities': [], 'amounts': [], 'average_prices': []},
                            '京东': {'quantities': [], 'amounts': [], 'average_prices': []}
                        }
                    },
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
            
            # 识别渠道
            def identify_channel(shop_type):
                shop_type_str = str(shop_type) if pd.notna(shop_type) else ''
                if '抖音' in shop_type_str or '今日头条' in shop_type_str or '鲁班' in shop_type_str:
                    return '抖音'
                elif '天猫' in shop_type_str:
                    return '天猫'
                elif '有赞' in shop_type_str:
                    return '有赞'
                elif '京东' in shop_type_str:
                    return '京东'
                else:
                    return '其他'
            
            df['channel'] = df['店铺类型'].apply(identify_channel)

            # 根据聚合级别生成日期标签和映射函数
            def get_aggregation_functions(level):
                """返回聚合级别对应的标签生成器和日期映射函数"""
                if level == 'day':
                    # 按天：YYYY-MM-DD
                    def generate_labels(start, end):
                        labels = []
                        current = start
                        while current <= end:
                            labels.append(current.strftime('%Y-%m-%d'))
                            current += datetime.timedelta(days=1)
                        return labels
                    
                    def map_date(date_str):
                        return date_str  # 直接返回日期字符串
                    
                    return generate_labels, map_date
                
                elif level == 'week':
                    # 按周：YYYY-WWW (如2024-W01)
                    def generate_labels(start, end):
                        labels = []
                        current = start
                        # 找到第一个周一的日期
                        while current.weekday() != 0:  # 0代表周一
                            current -= datetime.timedelta(days=1)
                        
                        while current <= end:
                            year = current.year
                            week_num = current.isocalendar()[1]
                            labels.append(f'{year}-W{week_num:02d}')
                            current += datetime.timedelta(weeks=1)
                        return labels
                    
                    def map_date(date_str):
                        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                        year = date_obj.year
                        week_num = date_obj.isocalendar()[1]
                        return f'{year}-W{week_num:02d}'
                    
                    return generate_labels, map_date
                
                elif level == 'month':
                    # 按月：YYYY-MM
                    def generate_labels(start, end):
                        labels = []
                        current = datetime.datetime(start.year, start.month, 1)
                        while current <= end:
                            labels.append(current.strftime('%Y-%m'))
                            # 下个月
                            if current.month == 12:
                                current = datetime.datetime(current.year + 1, 1, 1)
                            else:
                                current = datetime.datetime(current.year, current.month + 1, 1)
                        return labels
                    
                    def map_date(date_str):
                        return date_str[:7]  # 取前7位 YYYY-MM
                    
                    return generate_labels, map_date
                
                elif level == 'quarter':
                    # 按季度：YYYY-Q1 (季度1-4)
                    def generate_labels(start, end):
                        labels = []
                        current = datetime.datetime(start.year, ((start.month - 1) // 3) * 3 + 1, 1)
                        while current <= end:
                            quarter = (current.month - 1) // 3 + 1
                            labels.append(f'{current.year}-Q{quarter}')
                            # 下个季度
                            if current.month in [10, 11, 12]:  # 第四季度
                                current = datetime.datetime(current.year + 1, 1, 1)
                            else:
                                current = datetime.datetime(current.year, current.month + 3, 1)
                        return labels
                    
                    def map_date(date_str):
                        date_obj = datetime.datetime.strptime(date_str, '%Y-%m-%d')
                        quarter = (date_obj.month - 1) // 3 + 1
                        return f'{date_obj.year}-Q{quarter}'
                    
                    return generate_labels, map_date
                
                else:  # 'year'
                    # 按年：YYYY
                    def generate_labels(start, end):
                        labels = []
                        for year in range(start.year, end.year + 1):
                            labels.append(str(year))
                        return labels
                    
                    def map_date(date_str):
                        return date_str[:4]  # 取前4位 YYYY
                    
                    return generate_labels, map_date
            
            # 生成聚合标签
            generate_labels, map_date = get_aggregation_functions(aggregation_level)
            aggregation_labels = generate_labels(start_dt, end_dt)
            
            # 初始化销售曲线数据结构
            sales_curve_data = {
                'dates': aggregation_labels,  # 使用聚合标签
                'overall': {
                    'quantities': [0] * len(aggregation_labels),
                    'amounts': [0.0] * len(aggregation_labels),
                    'average_prices': [0] * len(aggregation_labels)
                },
                'channels': {
                    '抖音': {'quantities': [0] * len(aggregation_labels), 'amounts': [0.0] * len(aggregation_labels), 'average_prices': [0] * len(aggregation_labels)},
                    '天猫': {'quantities': [0] * len(aggregation_labels), 'amounts': [0.0] * len(aggregation_labels), 'average_prices': [0] * len(aggregation_labels)},
                    '有赞': {'quantities': [0] * len(aggregation_labels), 'amounts': [0.0] * len(aggregation_labels), 'average_prices': [0] * len(aggregation_labels)},
                    '京东': {'quantities': [0] * len(aggregation_labels), 'amounts': [0.0] * len(aggregation_labels), 'average_prices': [0] * len(aggregation_labels)}
                }
            }
            
            # 创建标签到索引的映射
            label_to_index = {label: idx for idx, label in enumerate(aggregation_labels)}

            # 使用新的聚合逻辑填充数据
            # 遍历DataFrame的每一行，将数据累加到对应的聚合标签
            for _, row in df.iterrows():
                date_str = row['date']
                quantity = row['valid_quantity']
                amount = row['valid_amount']
                channel = row['channel']
                
                # 将日期映射到聚合标签
                aggregation_label = map_date(date_str)
                
                # 检查标签是否在映射中（可能在边界情况）
                if aggregation_label in label_to_index:
                    idx = label_to_index[aggregation_label]
                    
                    # 整体数据累加
                    sales_curve_data['overall']['quantities'][idx] += quantity
                    sales_curve_data['overall']['amounts'][idx] += amount
                    
                    # 渠道数据累加
                    if channel in ['抖音', '天猫', '有赞', '京东']:
                        sales_curve_data['channels'][channel]['quantities'][idx] += quantity
                        sales_curve_data['channels'][channel]['amounts'][idx] += amount
            
            # 计算客单价（每个聚合区间）
            for idx in range(len(aggregation_labels)):
                # 整体客单价
                overall_quantity = sales_curve_data['overall']['quantities'][idx]
                overall_amount = sales_curve_data['overall']['amounts'][idx]
                if overall_quantity > 0:
                    sales_curve_data['overall']['average_prices'][idx] = round(overall_amount / overall_quantity)
                else:
                    sales_curve_data['overall']['average_prices'][idx] = 0
                
                # 各渠道客单价
                for channel in ['抖音', '天猫', '有赞', '京东']:
                    channel_quantity = sales_curve_data['channels'][channel]['quantities'][idx]
                    channel_amount = sales_curve_data['channels'][channel]['amounts'][idx]
                    if channel_quantity > 0:
                        sales_curve_data['channels'][channel]['average_prices'][idx] = round(channel_amount / channel_quantity)
                    else:
                        sales_curve_data['channels'][channel]['average_prices'][idx] = 0

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
                'aggregation_level': aggregation_level,
                'sales_curve': sales_curve_data,
                'average_order_value': round(average_order_value, 2),
                'channel_sales': channel_sales
            })

        except Exception as e:
            print(f'获取商品详情失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
