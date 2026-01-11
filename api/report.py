# -*- coding: utf-8 -*-
import json
import pandas as pd
from datetime import datetime, timedelta
from flask import jsonify, request, g
from dbpy.database import get_db_connection
from utils.auth import token_required
from utils.operation_logger import log_operation

def register_report_routes(app):
    """注册报表相关 API 路由"""

    @app.route('/api/analyse/generate-report', methods=['POST'])
    @token_required
    def generate_report():
        """生成报表数据（网页版）"""
        try:
            data = request.json
            start_date = data.get('startDate')
            end_date = data.get('endDate')

            if not start_date or not end_date:
                return jsonify({'error': '缺少日期参数'}), 400

            print(f'生成报表: {start_date} 到 {end_date}')

            # 获取数据
            conn = get_db_connection()
            cursor = conn.cursor()

            try:
                # 读取CategoryInfo表（作为tab）
                cursor.execute('SELECT id, name FROM CategoryInfo ORDER BY id')
                categories = cursor.fetchall()

                # 读取ProductInfo表（用于商品映射）
                cursor.execute('SELECT name, mapped_title, category FROM ProductInfo WHERE mapped_title IS NOT NULL AND mapped_title != ""')
                product_full_mapping = {}
                for row in cursor.fetchall():
                    product_full_mapping[row['name']] = {
                        'mapped_title': row['mapped_title'],
                        'category': row['category']
                    }

                # 查询指定日期范围内的数据
                sql = '''
                    SELECT
                        商品名称,
                        付款时间,
                        订购数 as 支付数量,
                        让利后金额 as 金额
                    FROM OrderDetails
                    WHERE 付款时间 >= ? AND 付款时间 <= ?
                    AND (是否退款 != "退款成功" AND 是否退款 != "退款中" OR 是否退款 IS NULL)
                    ORDER BY 付款时间
                '''
                # 将结束日期加上时间部分，以包含当天的所有数据
                end_date_with_time = f"{end_date} 23:59:59"
                cursor.execute(sql, (start_date, end_date_with_time))
                rows = cursor.fetchall()

                if not rows:
                    return jsonify({'success': True, 'data': []})

                # 转换为DataFrame
                df = pd.DataFrame([dict(row) for row in rows])

                # 提取日期部分
                df['日期'] = pd.to_datetime(df['付款时间']).dt.strftime('%m月%d日')

                # 生成日期列表
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                end_dt = datetime.strptime(end_date, '%Y-%m-%d')
                date_list = []
                current_date = start_dt
                while current_date <= end_dt:
                    date_list.append(current_date.strftime('%m月%d日'))
                    current_date += timedelta(days=1)

                # 按商品类型统计（使用ProductInfo进行映射）
                type_stats = {}
                tab_stats = {}  # 用于存储每个tab的汇总数据
                daily_has_data = {}  # 记录每一天是否有任何交易数据

                # 初始化每个tab的统计数据
                for category in categories:
                    category_id = category['id']
                    category_name = category['name']

                    tab_stats[category_name] = {
                        'types': [],
                        'daily': {date: {'quantity': 0, 'amount': 0.0} for date in date_list},
                        'total': {'quantity': 0, 'amount': 0.0}
                    }

                # 初始化每一天是否有数据
                for date_str in date_list:
                    daily_has_data[date_str] = False

                # 遍历每条订单记录
                for idx, row in df.iterrows():
                    product_name = row['商品名称']
                    date_str = row['日期']

                    # 标记这一天有数据
                    daily_has_data[date_str] = True

                    # 查找商品映射
                    product_info = product_full_mapping.get(product_name)

                    if product_info is None or product_info['mapped_title'] is None:
                        continue

                    mapped_title = product_info['mapped_title']
                    category_id = product_info['category']

                    # 找到对应的category名称
                    category_name = None
                    for category in categories:
                        if category['id'] == category_id:
                            category_name = category['name']
                            break

                    if category_name is None:
                        continue

                    # 为每个商品类型统计每天的数据
                    if mapped_title not in type_stats:
                        type_stats[mapped_title] = {
                            'tab_name': category_name,
                            'daily': {date: {'quantity': 0, 'amount': 0.0} for date in date_list},
                            'total': {'quantity': 0, 'amount': 0.0}
                        }

                    # 添加到该tab的类型列表
                    if mapped_title not in tab_stats[category_name]['types']:
                        tab_stats[category_name]['types'].append(mapped_title)

                    # 按日期统计
                    quantity = int(row['支付数量']) if pd.notna(row['支付数量']) else 0
                    amount = float(row['金额']) if pd.notna(row['金额']) else 0

                    # 更新商品类型统计数据
                    type_stats[mapped_title]['daily'][date_str]['quantity'] += quantity
                    type_stats[mapped_title]['daily'][date_str]['amount'] += amount
                    type_stats[mapped_title]['total']['quantity'] += quantity
                    type_stats[mapped_title]['total']['amount'] += amount

                    # 更新tab统计数据
                    tab_stats[category_name]['daily'][date_str]['quantity'] += quantity
                    tab_stats[category_name]['daily'][date_str]['amount'] += amount
                    tab_stats[category_name]['total']['quantity'] += quantity
                    tab_stats[category_name]['total']['amount'] += amount

                # 准备网页数据
                web_data = []

                # 添加标题行
                title_text = f"{start_dt.year}年{start_dt.month}月{start_dt.day}日 - {end_dt.month}月{end_dt.day}日"
                web_data.append({
                    'type': 'title',
                    'value': title_text
                })

                # 添加副标题行
                web_data.append({
                    'type': 'subtitle',
                    'value': '重点商品'
                })

                # 添加表头
                web_data.append({
                    'type': 'header',
                    'product_type': '商品类型',
                    'date': '日期',
                    'quantity': '支付数量',
                    'amount': '金额'
                })

                # 按照CategoryInfo的顺序遍历每个tab
                for category in categories:
                    category_name = category['name']

                    if category_name not in tab_stats or not tab_stats[category_name]['types']:
                        continue

                    # 遍历该tab下的所有商品类型
                    for product_type in tab_stats[category_name]['types']:
                        type_data = type_stats[product_type]

                        # 遍历每一天
                        for i, date_str in enumerate(date_list):
                            quantity = type_data['daily'][date_str]['quantity']
                            amount = type_data['daily'][date_str]['amount']

                            # 如果这一天有数据但该商品没有交易，显示0；如果这一天完全没有数据，留空
                            if i == 0:
                                # 第一行，添加 rowspan
                                web_data.append({
                                    'type': 'data',
                                    'product_type': product_type,
                                    'date': date_str,
                                    'quantity': quantity if quantity > 0 else '0',
                                    'amount': f"{amount:.2f}" if amount > 0 else '0.00',
                                    'rowspan': len(date_list)  # rowspan 等于日期数量
                                })
                            else:
                                # 后续行，商品类型为空
                                if daily_has_data[date_str]:
                                    web_data.append({
                                        'type': 'data',
                                        'product_type': '',
                                        'date': date_str,
                                        'quantity': quantity if quantity > 0 else '0',
                                        'amount': f"{amount:.2f}" if amount > 0 else '0.00'
                                    })
                                else:
                                    web_data.append({
                                        'type': 'data',
                                        'product_type': '',
                                        'date': date_str,
                                        'quantity': '',
                                        'amount': ''
                                    })

                        # 添加该商品类型的合计行
                        web_data.append({
                            'type': 'subtotal',
                            'product_type': '',
                            'date': '合计',
                            'quantity': type_data['total']['quantity'] if type_data['total']['quantity'] > 0 else '0',
                            'amount': f"{type_data['total']['amount']:.2f}" if type_data['total']['amount'] > 0 else '0.00'
                        })

                    # 添加该tab的合计行
                    tab_data = tab_stats[category_name]
                    web_data.append({
                        'type': 'total',
                        'product_type': f"{category_name}合计",
                        'date': '',
                        'quantity': tab_data['total']['quantity'] if tab_data['total']['quantity'] > 0 else '',
                        'amount': f"{tab_data['total']['amount']:.2f}" if tab_data['total']['amount'] > 0 else ''
                    })

                return jsonify({
                    'success': True,
                    'data': web_data
                })

            finally:
                conn.close()

        except Exception as e:
            print(f'生成报表失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500