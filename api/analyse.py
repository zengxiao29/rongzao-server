# -*- coding: utf-8 -*-
import json
import os
import pandas as pd
from flask import jsonify, request
from dbpy.database import get_db_connection
from utils.auth import token_required


def register_analyse_routes(app):
    """注册数据分析相关 API 路由"""

    @app.route('/api/analyse/data', methods=['GET', 'POST'])
    @token_required
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
                sql = 'SELECT * FROM OrderDetails WHERE 付款时间 IS NOT NULL AND 付款时间 != "NaT"'
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

                print("开始处理数据...")
                for idx, row in df_filtered.iterrows():
                    product_name = row['商品名称']

                    # 查找商品映射
                    product_info = product_full_mapping.get(product_name)

                    if product_info is None or product_info['mapped_title'] is None:
                        # 未找到映射，记录下来
                        if idx < 30:  # 只打印前30条未匹配的
                            print(f"未找到映射: {product_name}")
                        unmatched_products.add(product_name)
                        continue

                    mapped_title = product_info['mapped_title']
                    category_id = product_info['category']

                    # 计算有效订购数
                    valid_orders = row['订购数'] if pd.notna(row['订购数']) else 0

                    # 计算让利后金额
                    discount_amount = row['让利后金额'] if pd.notna(row['让利后金额']) else 0

                    # 获取店铺类型
                    shop_type = str(row['店铺类型']) if pd.notna(row['店铺类型']) else ''

                    # 调试：打印所有舰载熊猫系列的商品
                    if '舰载熊猫' in product_name:
                        print(f"舰载熊猫商品: {product_name}, 映射: {mapped_title}, 店铺类型: '{shop_type}', 订购数: {valid_orders}")

                    if mapped_title not in mapped_title_stats:
                        mapped_title_stats[mapped_title] = {
                            'category': category_id,
                            'valid_orders': 0,
                            'discount_amount': 0,
                            'douyin_orders': 0,
                            'douyin_amount': 0,
                            'tmall_orders': 0,
                            'tmall_amount': 0,
                            'youzan_orders': 0,
                            'youzan_amount': 0,
                            'jd_orders': 0,
                            'jd_amount': 0
                        }

                    # 累加总数
                    mapped_title_stats[mapped_title]['valid_orders'] += valid_orders
                    mapped_title_stats[mapped_title]['discount_amount'] += discount_amount

                    # 按店铺类型统计（只统计这四个渠道的）
                    if shop_type:
                        if '抖音' in shop_type or '今日头条' in shop_type or '鲁班' in shop_type:
                            mapped_title_stats[mapped_title]['douyin_orders'] += valid_orders
                            mapped_title_stats[mapped_title]['douyin_amount'] += discount_amount
                            if '舰载熊猫' in product_name:
                                print(f"  -> 匹配到抖音列，累计: {mapped_title_stats[mapped_title]['douyin_orders']}")
                        elif '天猫' in shop_type:
                            mapped_title_stats[mapped_title]['tmall_orders'] += valid_orders
                            mapped_title_stats[mapped_title]['tmall_amount'] += discount_amount
                            if '舰载熊猫' in product_name:
                                print(f"  -> 匹配到天猫列，累计: {mapped_title_stats[mapped_title]['tmall_orders']}")
                        elif '有赞' in shop_type:
                            mapped_title_stats[mapped_title]['youzan_orders'] += valid_orders
                            mapped_title_stats[mapped_title]['youzan_amount'] += discount_amount
                            if '舰载熊猫' in product_name:
                                print(f"  -> 匹配到有赞列，累计: {mapped_title_stats[mapped_title]['youzan_orders']}")
                        elif '京东' in shop_type:
                            mapped_title_stats[mapped_title]['jd_orders'] += valid_orders
                            mapped_title_stats[mapped_title]['jd_amount'] += discount_amount
                            if '舰载熊猫' in product_name:
                                print(f"  -> 匹配到京东列，累计: {mapped_title_stats[mapped_title]['jd_orders']}")

                # 按category分组组织数据
                tabs_data = []
                for category in categories:
                    category_id = category['id']
                    category_name = category['name']

                    # 找出属于该category的所有mapped_title（从ProductInfo中获取）
                    category_mapped_titles = {}
                    for name, info in product_full_mapping.items():
                        if info['category'] == category_id and info['mapped_title']:
                            mapped_title = info['mapped_title']
                            if mapped_title not in category_mapped_titles:
                                category_mapped_titles[mapped_title] = True

                    # 为每个mapped_title准备统计数据，默认为0
                    type_stats = {}
                    for mapped_title in category_mapped_titles.keys():
                        if mapped_title in mapped_title_stats:
                            stats = mapped_title_stats[mapped_title]
                            type_stats[mapped_title] = {
                                'valid_orders': stats['valid_orders'],
                                'discount_amount': stats['discount_amount'],
                                'douyin_orders': stats['douyin_orders'],
                                'douyin_amount': stats['douyin_amount'],
                                'tmall_orders': stats['tmall_orders'],
                                'tmall_amount': stats['tmall_amount'],
                                'youzan_orders': stats['youzan_orders'],
                                'youzan_amount': stats['youzan_amount'],
                                'jd_orders': stats['jd_orders'],
                                'jd_amount': stats['jd_amount']
                            }
                        else:
                            # 没有数据，设置为0
                            type_stats[mapped_title] = {
                                'valid_orders': 0,
                                'discount_amount': 0.0,
                                'douyin_orders': 0,
                                'douyin_amount': 0.0,
                                'tmall_orders': 0,
                                'tmall_amount': 0.0,
                                'youzan_orders': 0,
                                'youzan_amount': 0.0,
                                'jd_orders': 0,
                                'jd_amount': 0.0
                            }

                    # 转换为列表格式
                    tab_data = {
                        'name': category_name,
                        'data': [
                            {
                                'product_type': product_type,
                                'valid_orders': int(stats.get('valid_orders', 0)),
                                'discount_amount': float(stats.get('discount_amount', 0)),
                                'douyin_orders': int(stats.get('douyin_orders', 0)),
                                'douyin_amount': float(stats.get('douyin_amount', 0)),
                                'tmall_orders': int(stats.get('tmall_orders', 0)),
                                'tmall_amount': float(stats.get('tmall_amount', 0)),
                                'youzan_orders': int(stats.get('youzan_orders', 0)),
                                'youzan_amount': float(stats.get('youzan_amount', 0)),
                                'jd_orders': int(stats.get('jd_orders', 0)),
                                'jd_amount': float(stats.get('jd_amount', 0))
                            }
                            for product_type, stats in type_stats.items()
                        ]
                    }

                    # 排序：包含"其它"或"其他"的商品类型放在最后
                    def sort_key(item):
                        product_type = item['product_type']
                        # 如果包含"其它"或"其他"，返回1，否则返回0
                        return 1 if '其它' in product_type or '其他' in product_type else 0

                    tab_data['data'].sort(key=sort_key)

                    # 调试信息：打印统计结果
                    print(f'分类 {category_name} 统计结果:')
                    for item in tab_data['data']:
                        print(f"  {item['product_type']}: 总数={item['valid_orders']}, 抖音={item['douyin_orders']}, 天猫={item['tmall_orders']}, 有赞={item['youzan_orders']}")

                    tabs_data.append(tab_data)

                return jsonify({
                    'tabs': tabs_data,
                    'unmatched_products': list(unmatched_products)
                })

            finally:
                conn.close()

        except Exception as e:
            print(f'处理数据时出错: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500