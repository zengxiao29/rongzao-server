# -*- coding: utf-8 -*-
import json
import os
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta
from urllib.parse import quote
from flask import jsonify, request
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
from database import get_db_connection
from utils import register_chinese_font


def register_export_routes(app):
    """注册导出相关 API 路由"""

    @app.route('/api/analyse/export-weekly-report', methods=['POST'])
    def export_weekly_report():
        """导出周报PDF"""
        try:
            # 注册中文字体
            font_name = register_chinese_font()

            data = request.json
            start_date = data.get('startDate')
            end_date = data.get('endDate')

            if not start_date or not end_date:
                return jsonify({'error': '缺少日期参数'}), 400

            print(f'导出周报: {start_date} 到 {end_date}')

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
                    return jsonify({'error': '指定日期范围内没有数据'}), 400

                # 转换为DataFrame
                df = pd.DataFrame([dict(row) for row in rows])

                # 提取日期部分
                df['日期'] = pd.to_datetime(df['付款时间']).dt.strftime('%m月%d日')

                # 生成一周7天的日期列表
                start_dt = datetime.strptime(start_date, '%Y-%m-%d')
                week_dates = []
                for i in range(7):
                    date = start_dt + timedelta(days=i)
                    week_dates.append(date.strftime('%m月%d日'))

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
                        'daily': {date: {'quantity': 0, 'amount': 0.0} for date in week_dates},
                        'total': {'quantity': 0, 'amount': 0.0}
                    }

                # 初始化每一天是否有数据
                for week_date in week_dates:
                    daily_has_data[week_date] = False

                # 遍历每条订单记录
                for idx, row in df.iterrows():
                    product_name = row['商品名称']
                    week_date = row['日期']

                    # 标记这一天有数据
                    daily_has_data[week_date] = True

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
                            'daily': {date: {'quantity': 0, 'amount': 0.0} for date in week_dates},
                            'total': {'quantity': 0, 'amount': 0.0}
                        }

                    # 添加到该tab的类型列表
                    if mapped_title not in tab_stats[category_name]['types']:
                        tab_stats[category_name]['types'].append(mapped_title)

                    # 按日期统计
                    quantity = int(row['支付数量']) if pd.notna(row['支付数量']) else 0
                    amount = float(row['金额']) if pd.notna(row['金额']) else 0

                    # 更新商品类型统计数据
                    type_stats[mapped_title]['daily'][week_date]['quantity'] += quantity
                    type_stats[mapped_title]['daily'][week_date]['amount'] += amount
                    type_stats[mapped_title]['total']['quantity'] += quantity
                    type_stats[mapped_title]['total']['amount'] += amount

                    # 更新tab统计数据
                    tab_stats[category_name]['daily'][week_date]['quantity'] += quantity
                    tab_stats[category_name]['daily'][week_date]['amount'] += amount
                    tab_stats[category_name]['total']['quantity'] += quantity
                    tab_stats[category_name]['total']['amount'] += amount

                # 准备PDF数据
                pdf_data = []

                # 计算周数
                title_week = f"{start_dt.month}月第{(start_dt.day - 1) // 7 + 1}周"

                # 添加标题行
                pdf_data.append([title_week, '', '', ''])
                pdf_data.append(['重点商品', '', '', ''])
                pdf_data.append(['商品类型', '日期', '支付数量', '金额'])

                # 按照CategoryInfo的顺序遍历每个tab
                for category in categories:
                    category_name = category['name']

                    if category_name not in tab_stats or not tab_stats[category_name]['types']:
                        continue

                    # 遍历该tab下的所有商品类型
                    for product_type in tab_stats[category_name]['types']:
                        type_data = type_stats[product_type]

                        # 遍历一周7天
                        for week_date in week_dates:
                            quantity = type_data['daily'][week_date]['quantity']
                            amount = type_data['daily'][week_date]['amount']

                            # 如果这一天有数据但该商品没有交易，显示0；如果这一天完全没有数据，留空
                            if daily_has_data[week_date]:
                                pdf_data.append([
                                    product_type,
                                    week_date,
                                    quantity if quantity > 0 else '0',
                                    f"{amount:.2f}" if amount > 0 else '0.00'
                                ])
                            else:
                                pdf_data.append([
                                    product_type,
                                    week_date,
                                    '',
                                    ''
                                ])

                        # 添加该商品类型的合计行（7天总和）
                        pdf_data.append([
                            '',
                            '合计',
                            type_data['total']['quantity'] if type_data['total']['quantity'] > 0 else '0',
                            f"{type_data['total']['amount']:.2f}" if type_data['total']['amount'] > 0 else '0.00'
                        ])

                    # 添加该tab的合计行（所有商品类型的总和，不包括商品类型合计行）
                    tab_data = tab_stats[category_name]
                    pdf_data.append([
                        f"{category_name}合计",
                        '',
                        tab_data['total']['quantity'] if tab_data['total']['quantity'] > 0 else '',
                        f"{tab_data['total']['amount']:.2f}" if tab_data['total']['amount'] > 0 else ''
                    ])

                # 生成PDF
                buffer = BytesIO()
                doc = SimpleDocTemplate(buffer, pagesize=A4, topMargin=1*cm, bottomMargin=1*cm, leftMargin=1*cm, rightMargin=1*cm)

                # 创建表格
                table = Table(pdf_data, colWidths=[6*cm, 3*cm, 2*cm, 3*cm])

                # 设置表格样式
                styles = [
                    # 标题行样式 - 合并单元格
                    ('SPAN', (0, 0), (-1, 0)),  # 第一行标题合并所有列
                    ('SPAN', (0, 1), (-1, 1)),  # 第二行标题合并所有列

                    ('BACKGROUND', (0, 0), (-1, 1), colors.lightcyan),
                    ('FONTNAME', (0, 0), (-1, 1), font_name),
                    ('FONTSIZE', (0, 0), (-1, 1), 14),
                    ('ALIGN', (0, 0), (-1, 1), 'CENTER'),

                    # 表头样式
                    ('BACKGROUND', (0, 2), (-1, 2), colors.white),
                    ('FONTNAME', (0, 2), (-1, 2), font_name),
                    ('FONTSIZE', (0, 2), (-1, 2), 10),
                    ('ALIGN', (0, 2), (-1, 2), 'CENTER'),

                    # 数据行样式
                    ('FONTNAME', (0, 3), (-1, -1), font_name),
                    ('FONTSIZE', (0, 3), (-1, -1), 9),
                    ('ALIGN', (0, 3), (0, -1), 'LEFT'),  # 商品类型左对齐
                    ('ALIGN', (1, 3), (1, -1), 'CENTER'),  # 日期居中
                    ('ALIGN', (2, 3), (3, -1), 'RIGHT'),  # 数量和金额右对齐

                    # 边框
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
                    ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ]

                # 添加商品类型名称合并单元格、商品类型合计行样式和tab合计行样式
                # 从第4行开始（索引3），按照CategoryInfo的顺序组织
                base_row = 3
                for category in categories:
                    category_name = category['name']

                    if category_name not in tab_stats or not tab_stats[category_name]['types']:
                        continue

                    # 遍历该tab下的所有商品类型
                    for product_type in tab_stats[category_name]['types']:
                        # 合并该商品类型的商品类型列（7天数据）
                        styles.append(('SPAN', (0, base_row), (0, base_row + 6)))

                        # 商品类型合计行（第8行），添加灰色背景
                        styles.append(('BACKGROUND', (0, base_row + 7), (-1, base_row + 7), colors.lightgrey))

                        base_row += 8  # 7天数据 + 1行合计 = 8行

                    # tab合计行，添加绿色背景
                    styles.append(('BACKGROUND', (0, base_row), (-1, base_row), colors.lightgreen))
                    base_row += 1

                table.setStyle(TableStyle(styles))

                # 构建PDF
                elements = [table]
                doc.build(elements)

                # 返回PDF文件
                buffer.seek(0)
                pdf_data = buffer.getvalue()

                # 对文件名进行URL编码，避免中文字符问题
                encoded_filename = quote(f'周报_{start_date}_{end_date}.pdf', safe='')

                response = app.response_class(
                    pdf_data,
                    mimetype='application/pdf',
                    headers={
                        'Content-Disposition': f'attachment; filename*=UTF-8\'\'{encoded_filename}'
                    }
                )
                return response

            finally:
                conn.close()

        except Exception as e:
            print(f'导出周报失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
