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

                # 构建SQL查询 - 只选择必要字段，在数据库端过滤退款订单
                sql = '''
                    SELECT 
                        商品名称,
                        付款时间,
                        订购数,
                        让利后金额,
                        店铺类型,
                        是否退款
                    FROM OrderDetails 
                    WHERE 付款时间 IS NOT NULL AND 付款时间 != "NaT"
                      AND ((是否退款 != '退款成功' AND 是否退款 != '退款中') OR 是否退款 IS NULL)
                '''
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
                df_filtered = pd.DataFrame(rows, columns=columns)

                print(f'从数据库读取到 {len(df_filtered)} 条有效记录（已过滤退款）')

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

                # 使用SQL GROUP BY进行聚合统计，提升性能
                print("开始SQL聚合统计...")
                
                # 构建SQL聚合查询
                aggregation_sql = '''
                    SELECT 
                        p.mapped_title,
                        p.category,
                        COALESCE(SUM(o.订购数), 0) as valid_orders,
                        COALESCE(SUM(o.让利后金额), 0) as discount_amount,
                        -- 抖音渠道统计
                        COALESCE(SUM(CASE 
                            WHEN (o.店铺类型 LIKE '%抖音%' OR o.店铺类型 LIKE '%今日头条%' OR o.店铺类型 LIKE '%鲁班%')
                            THEN o.订购数 ELSE 0 
                        END), 0) as douyin_orders,
                        COALESCE(SUM(CASE 
                            WHEN (o.店铺类型 LIKE '%抖音%' OR o.店铺类型 LIKE '%今日头条%' OR o.店铺类型 LIKE '%鲁班%')
                            THEN o.让利后金额 ELSE 0 
                        END), 0) as douyin_amount,
                        -- 天猫渠道统计
                        COALESCE(SUM(CASE 
                            WHEN o.店铺类型 LIKE '%天猫%'
                            THEN o.订购数 ELSE 0 
                        END), 0) as tmall_orders,
                        COALESCE(SUM(CASE 
                            WHEN o.店铺类型 LIKE '%天猫%'
                            THEN o.让利后金额 ELSE 0 
                        END), 0) as tmall_amount,
                        -- 有赞渠道统计
                        COALESCE(SUM(CASE 
                            WHEN o.店铺类型 LIKE '%有赞%'
                            THEN o.订购数 ELSE 0 
                        END), 0) as youzan_orders,
                        COALESCE(SUM(CASE 
                            WHEN o.店铺类型 LIKE '%有赞%'
                            THEN o.让利后金额 ELSE 0 
                        END), 0) as youzan_amount,
                        -- 京东渠道统计
                        COALESCE(SUM(CASE 
                            WHEN o.店铺类型 LIKE '%京东%'
                            THEN o.订购数 ELSE 0 
                        END), 0) as jd_orders,
                        COALESCE(SUM(CASE 
                            WHEN o.店铺类型 LIKE '%京东%'
                            THEN o.让利后金额 ELSE 0 
                        END), 0) as jd_amount
                    FROM OrderDetails o
                    LEFT JOIN ProductInfo p ON o.商品名称 = p.name
                    WHERE o.付款时间 IS NOT NULL AND o.付款时间 != "NaT"
                      AND ((o.是否退款 != '退款成功' AND o.是否退款 != '退款中') OR o.是否退款 IS NULL)
                '''
                
                # 为聚合查询创建独立的参数列表
                aggregation_params = []
                
                # 添加日期范围条件
                if start_date:
                    aggregation_sql += ' AND o.付款时间 >= ?'
                    aggregation_params.append(start_date)
                
                if end_date:
                    aggregation_sql += ' AND o.付款时间 <= ?'
                    aggregation_params.append(f'{end_date} 23:59:59')
                
                aggregation_sql += '''
                    GROUP BY p.mapped_title, p.category
                    HAVING p.mapped_title IS NOT NULL AND p.mapped_title != ""
                    ORDER BY p.category, p.mapped_title
                '''
                
                # 执行聚合查询
                cursor.execute(aggregation_sql, aggregation_params)
                aggregation_results = cursor.fetchall()
                
                # 构建mapped_title_stats字典（与原有结构兼容）
                mapped_title_stats = {}
                for row in aggregation_results:
                    mapped_title = row['mapped_title']
                    category_id = row['category']
                    
                    mapped_title_stats[mapped_title] = {
                        'category': category_id,
                        'valid_orders': row['valid_orders'],
                        'discount_amount': row['discount_amount'],
                        'douyin_orders': row['douyin_orders'],
                        'douyin_amount': row['douyin_amount'],
                        'tmall_orders': row['tmall_orders'],
                        'tmall_amount': row['tmall_amount'],
                        'youzan_orders': row['youzan_orders'],
                        'youzan_amount': row['youzan_amount'],
                        'jd_orders': row['jd_orders'],
                        'jd_amount': row['jd_amount']
                    }
                
                # 统计未匹配的商品名称（通过对比原始数据）
                # 获取所有有映射的商品名称
                mapped_product_names = set(product_full_mapping.keys())
                
                # 检查df_filtered中的商品名称哪些没有映射
                for idx, row in df_filtered.iterrows():
                    product_name = row['商品名称']
                    if product_name not in mapped_product_names:
                        if idx < 30:  # 只打印前30条未匹配的
                            print(f"未找到映射: {product_name}")
                        unmatched_products.add(product_name)
                
                print(f"SQL聚合完成，统计到 {len(mapped_title_stats)} 个商品类型")

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