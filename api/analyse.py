# -*- coding: utf-8 -*-
import json
import os
import pandas as pd
from flask import jsonify, request
from database import get_db_connection


def register_analyse_routes(app):
    """注册数据分析相关 API 路由"""

    @app.route('/api/analyse/data', methods=['GET', 'POST'])
    def get_analyse_data():
        """从数据库获取分析数据"""
        print('收到数据分析请求')

        try:
            # 获取筛选参数
            start_date = None
            end_date = None

            if request.method == 'POST':
                data = request.json
                start_date = data.get('startDate')
                end_date = data.get('endDate')

            print(f'筛选参数: 开始日期={start_date}, 结束日期={end_date}')

            # 从数据库读取数据
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                # 读取 CategoryInfo 表（作为 tab）
                cursor.execute('SELECT id, name FROM CategoryInfo ORDER BY id')
                categories = cursor.fetchall()
                print(f'读取到 {len(categories)} 个大类')

                # 读取 ProductInfo 表（用于商品映射）
                cursor.execute('SELECT name, mapped_title FROM ProductInfo WHERE mapped_title IS NOT NULL AND mapped_title != ""')
                product_mapping = {row['name']: row['mapped_title'] for row in cursor.fetchall()}
                print(f'读取到 {len(product_mapping)} 条商品映射规则')

                # 构建SQL查询
                sql = 'SELECT * FROM OrderDetails WHERE 1=1'
                params = []

                if start_date:
                    sql += ' AND 付款时间 >= ?'
                    params.append(start_date)

                if end_date:
                    sql += ' AND 付款时间 <= ?'
                    params.append(f'{end_date} 23:59:59')

                sql += ' ORDER BY 付款时间'

                cursor.execute(sql, params)
                columns = [description[0] for description in cursor.description]
                rows = cursor.fetchall()

                # 转换为DataFrame
                df = pd.DataFrame(rows, columns=columns)

                print(f'从数据库读取到 {len(df)} 条记录')

                # 过滤掉退款的订单（与PDF导出保持一致的逻辑）
                df_filtered = df[(df['是否退款'] != '退款成功') & (df['是否退款'] != '退款中') | (df['是否退款'].isna())].copy()
                print(f'过滤退款后剩余 {len(df_filtered)} 行数据')

                # 记录未匹配的商品名称
                unmatched_products = set()

                # 为每个 category 生成数据
                # 先读取ProductInfo的category映射
                cursor.execute('SELECT name, mapped_title, category FROM ProductInfo WHERE mapped_title IS NOT NULL AND mapped_title != ""')
                product_full_mapping = {}
                for row in cursor.fetchall():
                    product_full_mapping[row['name']] = {
                        'mapped_title': row['mapped_title'],
                        'category': row['category']
                    }

                # 按mapped_title分组统计
                mapped_title_stats = {}

                for idx, row in df_filtered.iterrows():
                    product_name = row['商品名称']

                    # 查找商品映射
                    product_info = product_full_mapping.get(product_name)

                    if product_info is None or product_info['mapped_title'] is None:
                        # 未找到映射，记录下来
                        unmatched_products.add(product_name)
                        continue

                    mapped_title = product_info['mapped_title']
                    category_id = product_info['category']

                    # 计算有效订购数
                    valid_orders = row['订购数'] if pd.notna(row['订购数']) else 0

                    # 计算让利后金额
                    discount_amount = row['让利后金额'] if pd.notna(row['让利后金额']) else 0

                    if mapped_title not in mapped_title_stats:
                        mapped_title_stats[mapped_title] = {
                            'category': category_id,
                            'valid_orders': 0,
                            'discount_amount': 0
                        }

                    mapped_title_stats[mapped_title]['valid_orders'] += valid_orders
                    mapped_title_stats[mapped_title]['discount_amount'] += discount_amount

                # 按category分组组织数据
                tabs_data = []
                for category in categories:
                    category_id = category['id']
                    category_name = category['name']

                    # 找出属于该category的所有mapped_title
                    type_stats = {}
                    for mapped_title, stats in mapped_title_stats.items():
                        if stats['category'] == category_id:
                            type_stats[mapped_title] = {
                                'valid_orders': stats['valid_orders'],
                                'discount_amount': stats['discount_amount']
                            }

                    # 转换为列表格式
                    tab_data = {
                        'name': category_name,
                        'data': [
                            {
                                'product_type': product_type,
                                'valid_orders': int(stats['valid_orders']),
                                'discount_amount': float(stats['discount_amount'])
                            }
                            for product_type, stats in type_stats.items()
                        ]
                    }

                    tabs_data.append(tab_data)

                return {
                    'tabs': tabs_data,
                    'unmatched_products': list(unmatched_products)
                }

            finally:
                conn.close()

        except Exception as e:
            print(f'处理数据时出错: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500