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

            # 读取Tab配置
            with open(os.path.join(os.path.dirname(__file__), '..', 'tab_config.json'), 'r', encoding='utf-8') as f:
                config_data = json.load(f)
                tabs_config = config_data.get('tabs', [])

            # 获取数据
            conn = get_db_connection()
            cursor = conn.cursor()

            # 查询指定日期范围内的数据
            sql = '''
                SELECT
                    商品名称,
                    付款时间,
                    订购数 as 支付数量,
                    让利后金额 as 金额
                FROM OrderDetails
                WHERE 付款时间 >= ? AND 付款时间 <= ?
                AND (是否退款 != "退款成功" OR 是否退款 IS NULL)
                ORDER BY 付款时间
            '''

            cursor.execute(sql, (start_date, end_date))
            rows = cursor.fetchall()

            if not rows:
                conn.close()
                return jsonify({'error': '指定日期范围内没有数据'}), 400

            # 转换为DataFrame
            df = pd.DataFrame([dict(row) for row in rows])

            # 为每行商品标记是否已匹配
            df['已匹配'] = False

            # 提取日期部分
            df['日期'] = pd.to_datetime(df['付款时间']).dt.strftime('%m月%d日')

            # 生成一周7天的日期列表
            start_dt = datetime.strptime(start_date, '%Y-%m-%d')
            week_dates = []
            for i in range(7):
                date = start_dt + timedelta(days=i)
                week_dates.append(date.strftime('%m月%d日'))

            # 按商品类型统计（复用页面统计逻辑），按照tab_config.json的顺序组织
            type_stats = {}
            tab_stats = {}  # 用于存储每个tab的汇总数据

            for tab in tabs_config:
                tab_name = tab['name']
                mappings = tab.get('mappings', [])

                # 初始化该tab的统计数据
                if tab_name not in tab_stats:
                    tab_stats[tab_name] = {
                        'types': [],
                        'daily': {date: {'quantity': 0, 'amount': 0.0} for date in week_dates},
                        'total': {'quantity': 0, 'amount': 0.0}
                    }

                for mapping in mappings:
                    original_product = mapping['product']
                    mapped_type = mapping['type']

                    # 查找匹配的商品行（子串匹配，只匹配未匹配的行）
                    mask = ~df['已匹配'] & df['商品名称'].str.contains(original_product, na=False)
                    matching_rows = df[mask].copy()

                    if len(matching_rows) > 0:
                        # 标记这些行为已匹配
                        df.loc[matching_rows.index, '已匹配'] = True

                        # 为每个商品类型统计每天的数据
                        if mapped_type not in type_stats:
                            type_stats[mapped_type] = {
                                'tab_name': tab_name,
                                'daily': {date: {'quantity': 0, 'amount': 0.0} for date in week_dates},
                                'total': {'quantity': 0, 'amount': 0.0}
                            }

                        # 添加到该tab的类型列表
                        if mapped_type not in tab_stats[tab_name]['types']:
                            tab_stats[tab_name]['types'].append(mapped_type)

                        # 按日期统计
                        for week_date in week_dates:
                            day_mask = matching_rows['日期'] == week_date
                            day_data = matching_rows[day_mask]

                            if not day_data.empty:
                                quantity = int(day_data['支付数量'].sum())
                                amount = float(day_data['金额'].sum())

                                # 更新商品类型统计数据
                                type_stats[mapped_type]['daily'][week_date]['quantity'] += quantity
                                type_stats[mapped_type]['daily'][week_date]['amount'] += amount
                                type_stats[mapped_type]['total']['quantity'] += quantity
                                type_stats[mapped_type]['total']['amount'] += amount

                                # 更新tab统计数据
                                tab_stats[tab_name]['daily'][week_date]['quantity'] += quantity
                                tab_stats[tab_name]['daily'][week_date]['amount'] += amount
                                tab_stats[tab_name]['total']['quantity'] += quantity
                                tab_stats[tab_name]['total']['amount'] += amount

            # 准备PDF数据
            pdf_data = []

            # 计算周数
            title_week = f"{start_dt.month}月第{(start_dt.day - 1) // 7 + 1}周"

            # 添加标题行
            pdf_data.append([title_week, '', '', ''])
            pdf_data.append(['重点商品', '', '', ''])
            pdf_data.append(['商品类型', '日期', '支付数量', '金额'])

            # 按照tab_config.json的顺序遍历每个tab
            for tab in tabs_config:
                tab_name = tab['name']

                if tab_name not in tab_stats or not tab_stats[tab_name]['types']:
                    continue

                # 遍历该tab下的所有商品类型
                for product_type in tab_stats[tab_name]['types']:
                    type_data = type_stats[product_type]

                    # 遍历一周7天
                    for week_date in week_dates:
                        quantity = type_data['daily'][week_date]['quantity']
                        amount = type_data['daily'][week_date]['amount']

                        pdf_data.append([
                            product_type,
                            week_date,
                            quantity if quantity > 0 else '',
                            f"{amount:.2f}" if amount > 0 else ''
                        ])

                    # 添加该商品类型的合计行（7天总和）
                    pdf_data.append([
                        '',
                        '合计',
                        type_data['total']['quantity'] if type_data['total']['quantity'] > 0 else '',
                        f"{type_data['total']['amount']:.2f}" if type_data['total']['amount'] > 0 else ''
                    ])

                # 添加该tab的合计行（所有商品类型的总和，不包括商品类型合计行）
                tab_data = tab_stats[tab_name]
                pdf_data.append([
                    f"{tab_name}合计",
                    '',
                    tab_data['total']['quantity'] if tab_data['total']['quantity'] > 0 else '',
                    f"{tab_data['total']['amount']:.2f}" if tab_data['total']['amount'] > 0 else ''
                ])

            conn.close()

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
            # 从第4行开始（索引3），按照tab_config.json的顺序组织
            base_row = 3
            for tab in tabs_config:
                tab_name = tab['name']

                if tab_name not in tab_stats or not tab_stats[tab_name]['types']:
                    continue

                # 遍历该tab下的所有商品类型
                for product_type in tab_stats[tab_name]['types']:
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

        except Exception as e:
            print(f'导出周报失败: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500
