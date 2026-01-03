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

            # 读取 tab 配置
            config_file = os.path.join(os.path.dirname(__file__), '..', 'tab_config.json')
            tabs_config = []
            if os.path.exists(config_file):
                with open(config_file, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    tabs_config = config.get('tabs', [])

            print(f'读取到 {len(tabs_config)} 个 tab 配置')

            # 从数据库读取数据
            conn = get_db_connection()
            cursor = conn.cursor()

            # 构建SQL查询
            sql = 'SELECT * FROM OrderDetails WHERE 1=1'
            params = []

            if start_date:
                sql += ' AND 付款时间 >= ?'
                params.append(start_date)

            if end_date:
                sql += ' AND 付款时间 <= ?'
                params.append(end_date)

            sql += ' ORDER BY 付款时间'

            cursor.execute(sql, params)
            columns = [description[0] for description in cursor.description]
            rows = cursor.fetchall()

            # 转换为DataFrame
            df = pd.DataFrame(rows, columns=columns)
            conn.close()

            print(f'从数据库读取到 {len(df)} 条记录')

            # 过滤掉退款的订单
            df_filtered = df[df['是否退款'] != '退款成功'].copy()

            print(f'过滤退款后剩余 {len(df_filtered)} 行数据')

            # 为每个 tab 生成数据
            tabs_data = []

            for tab in tabs_config:
                tab_name = tab['name']
                mappings = tab['mappings']  # [{'product': '商品名称', 'type': '商品类型'}]

                # 统计该 tab 下的商品类型数据
                type_stats = {}

                # 为每行商品标记是否已匹配
                df_filtered['已匹配'] = False

                for mapping in mappings:
                    original_product = mapping['product']
                    mapped_type = mapping['type']

                    # 查找匹配的商品行（子串匹配，只匹配未匹配的行）
                    mask = ~df_filtered['已匹配'] & df_filtered['商品名称'].str.contains(original_product, na=False)
                    matching_rows = df_filtered[mask]

                    print(f'匹配 "{original_product}": 找到 {len(matching_rows)} 行')

                    if len(matching_rows) > 0:
                        # 标记这些行为已匹配
                        df_filtered.loc[matching_rows.index, '已匹配'] = True

                        # 计算有效订购数
                        valid_orders = matching_rows['订购数'].sum()

                        # 计算让利后金额（如果有此列）
                        discount_amount = 0
                        if '让利后金额' in df_filtered.columns:
                            discount_amount = matching_rows['让利后金额'].sum()

                        if mapped_type not in type_stats:
                            type_stats[mapped_type] = {
                                'valid_orders': 0,
                                'discount_amount': 0
                            }

                        type_stats[mapped_type]['valid_orders'] += valid_orders
                        type_stats[mapped_type]['discount_amount'] += discount_amount

                # 转换为列表格式
                tab_data = {
                    'name': tab_name,
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
                'tabs': tabs_data
            }
        except Exception as e:
            print(f'处理数据时出错: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500