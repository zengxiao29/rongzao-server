# -*- coding: utf-8 -*-
from flask import Flask, render_template, request, jsonify, send_from_directory
import pandas as pd
import re
import base64
from io import BytesIO
import os
import sqlite3
import hashlib
import json
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from datetime import datetime, timedelta
from urllib.parse import quote

app = Flask(__name__)

# 数据库配置
DB_PATH = os.path.join(os.path.dirname(__file__), 'rongzao.db')

def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def calculate_record_hash(row):
    """计算记录的哈希值（基于所有字段）"""
    # 将所有字段按固定顺序拼接成字符串
    field_values = []
    for col in sorted(row.index):
        # 处理NaN值
        value = row[col]
        if pd.isna(value):
            value = ''
        field_values.append(str(value))

    # 计算MD5哈希
    hash_string = '|'.join(field_values)
    return hashlib.md5(hash_string.encode('utf-8')).hexdigest()

@app.route('/')
def index():
    """首页"""
    return render_template('index.html')

@app.route('/data-analysis')
def data_analysis():
    """数据分析页面"""
    return render_template('data_analysis.html')

@app.route('/test')
def test():
    """测试页面"""
    return render_template('test.html')

@app.route('/project-management')
def project_management():
    """项目管理页面"""
    return render_template('project_management.html')

@app.route('/production-management')
def production_management():
    """生产管理页面"""
    return render_template('production_management.html')

@app.route('/analyse')
def analyse():
    """数据分析页面"""
    return render_template('analyse.html')

@app.route('/<path:filename>')
def serve_static_file(filename):
    """提供静态文件服务"""
    return send_from_directory('.', filename)

@app.route('/api/db/dates', methods=['GET'])
def get_available_dates():
    """获取数据库中所有可用的付款时间日期"""
    print('收到获取可用日期请求')

    try:
        conn = get_db_connection()
        cursor = conn.cursor()

        # 获取所有付款时间不为空的记录
        cursor.execute('SELECT DISTINCT 付款时间 FROM OrderDetails WHERE 付款时间 IS NOT NULL AND 付款时间 != "" ORDER BY 付款时间')
        rows = cursor.fetchall()

        # 提取日期部分（YYYY-MM-DD）
        dates = set()
        for row in rows:
            if row['付款时间']:
                try:
                    # 处理日期字符串，提取日期部分
                    date_str = str(row['付款时间'])
                    if ' ' in date_str:
                        date_part = date_str.split(' ')[0]  # 提取日期部分
                        dates.add(date_part)
                except:
                    continue

        conn.close()

        # 转换为排序后的列表
        sorted_dates = sorted(list(dates))

        return {
            'success': True,
            'dates': sorted_dates,
            'count': len(sorted_dates)
        }
    except Exception as e:
        print(f'获取可用日期时出错: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/analyse/config', methods=['GET'])
def get_analyse_config():
    """获取 tab 配置"""
    import json
    import os

    config_file = os.path.join(os.path.dirname(__file__), 'tab_config.json')
    if os.path.exists(config_file):
        with open(config_file, 'r', encoding='utf-8') as f:
            config = json.load(f)
        return jsonify(config)
    else:
        return jsonify({'tabs': []})

@app.route('/api/analyse/config', methods=['POST'])
def save_analyse_config():
    """保存 tab 配置"""
    import json
    import os

    config_file = os.path.join(os.path.dirname(__file__), 'tab_config.json')

    try:
        config = request.json
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'error': str(e)}), 500

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
        config_file = os.path.join(os.path.dirname(__file__), 'tab_config.json')
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

@app.route('/api/analyse/upload', methods=['POST'])
def analyse_upload():
    """处理 Excel 文件上传并上传到数据库"""
    print('收到 analyse 文件上传请求')

    if 'file' not in request.files:
        print('错误：请求中没有文件')
        return jsonify({'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        print('错误：文件名为空')
        return jsonify({'error': '未选择文件'}), 400

    print(f'开始处理文件: {file.filename}')

    try:
        # 直接上传到数据库
        return upload_to_database_internal(file)
    except Exception as e:
        print(f'处理文件时出错: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """处理Excel文件上传"""
    print('收到文件上传请求')

    if 'file' not in request.files:
        print('错误：请求中没有文件')
        return jsonify({'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        print('错误：文件名为空')
        return jsonify({'error': '未选择文件'}), 400

    print(f'开始处理文件: {file.filename}')

    try:
        # 读取Excel文件
        df = pd.read_excel(file)
        print(f'成功读取Excel文件，共 {len(df)} 行数据')

        # 处理数据
        result = process_data(df)
        print(f'数据处理完成，共 {len(result["products"])} 个商品')

        return jsonify(result)
    except Exception as e:
        print(f'处理文件时出错: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def process_data(df):
    """处理Excel数据，生成商品销量统计"""
    # 商品名称去重：移除颜色、尺码等后缀信息
    def normalize_product_name(name):
        # 移除常见的颜色、尺码后缀
        # 例如：--蓝马甲, -58, 58CM, -XS, -61等
        name = str(name)
        # 移除 -- 后面的内容
        name = re.sub(r'--.*', '', name)
        # 移除 - 后面跟着数字或字母的内容（尺码）
        name = re.sub(r'-\s*\d+[A-Za-z]*', '', name)
        name = re.sub(r'-\s*[A-Za-z]+', '', name)
        # 移除末尾的数字+单位（如 58CM）
        name = re.sub(r'\d+CM$', '', name)
        name = re.sub(r'\d+$', '', name)
        return name.strip()

    # 标准化商品名称
    df['标准化商品名称'] = df['商品名称'].apply(normalize_product_name)

    # 计算销量：订购数减去退款成功的订单
    def calculate_sales(group):
        total = group['订购数'].sum()
        refunded = group[group['是否退款'] == '退款成功']['订购数'].sum()
        return total - refunded

    # 按标准化商品名称分组计算销量
    sales_data = df.groupby('标准化商品名称').apply(calculate_sales).reset_index()
    sales_data.columns = ['商品名称', '销量']

    # 按销量降序排序
    sales_data = sales_data.sort_values('销量', ascending=False)

    # 转换为前端可用的格式
    result = {
        'products': sales_data['商品名称'].tolist(),
        'sales': sales_data['销量'].tolist()
    }

    return result

@app.route('/api/db/upload', methods=['POST'])
def upload_to_database():
    """上传Excel数据到数据库"""
    print('收到数据库上传请求')

    if 'file' not in request.files:
        print('错误：请求中没有文件')
        return jsonify({'error': '没有文件'}), 400

    file = request.files['file']
    if file.filename == '':
        print('错误：文件名为空')
        return jsonify({'error': '未选择文件'}), 400

    print(f'开始处理文件: {file.filename}')

    try:
        return upload_to_database_internal(file)
    except Exception as e:
        print(f'处理文件时出错: {str(e)}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

def upload_to_database_internal(file):
    """内部函数：上传Excel数据到数据库"""
    print(f'开始处理文件: {file.filename}')

    # 读取Excel文件
    df = pd.read_excel(file)
    print(f'成功读取Excel文件，共 {len(df)} 行数据')

    # 将所有Timestamp类型转换为字符串
    for col in df.columns:
        if pd.api.types.is_datetime64_any_dtype(df[col]):
            df[col] = df[col].astype(str)
        # 将NaT（Not a Time）转换为空字符串
        df[col] = df[col].where(pd.notna(df[col]), '')

    # 应用层去重：处理Excel文件内部的重复
    df_deduped = df.drop_duplicates(keep='first')
    print(f'Excel内去重: {len(df)} -> {len(df_deduped)} 条记录')

    # 插入数据库
    conn = get_db_connection()
    cursor = conn.cursor()

    success_count = 0
    duplicate_count = 0
    error_count = 0

    # 准备插入SQL
    insert_sql = '''
        INSERT OR IGNORE INTO OrderDetails (
            record_hash, 店铺类型, 店铺名称, 分销商名称, 单据编号, 订单类型,
            拍单时间, 付款时间, 审核时间, 会员代码, 会员名称, 内部便签, 业务员,
            建议仓库, 建议快递, 到账, 商品图片, 品牌, 商品税率, 商品代码,
            商品名称, 商品简称, 规格代码, 规格名称, 商品备注, 代发订单, 订单标记,
            预计发货时间, 订购数, 总重量, 折扣, 标准进价, 标准单价, 标准金额,
            实际单价, 实际金额, 让利后金额, 让利金额, 物流费用, 成本总价,
            买家备注, 卖家备注, 制单人, 商品实际利润, 商品标准利润, 商品已发货数量,
            平台旗帜, 发货时间, 原产地, 平台商品名称, 平台规格名称, 供应商,
            赠品来源, 买家支付金额, 平台支付金额, 其他服务费, 发票种类,
            发票抬头类型, 发票类型, 开户行, 账号, 发票电话, 发票地址, 收货邮箱,
            周期购商品, 平台单号, 到账时间, 附加信息, 发票抬头, 发票内容,
            纳税人识别号, 收货人, 收货人手机, 邮编, 收货地址, 商品类别,
            二次备注, 商品单位, 币别, 会员邮箱, 订单标签, 平台交易状态,
            赠品, 是否退款, 地区信息, 确认收货时间, 作废
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    '''

    # 遍历每一行数据
    for idx, row in df_deduped.iterrows():
        try:
            # 计算哈希值
            record_hash = calculate_record_hash(row)

            # 准备数据
            data = (
                record_hash,
                row.get('店铺类型'), row.get('店铺名称'), row.get('分销商名称'),
                row.get('单据编号'), row.get('订单类型'), row.get('拍单时间'),
                row.get('付款时间'), row.get('审核时间'), row.get('会员代码'),
                row.get('会员名称'), row.get('内部便签'), row.get('业务员'),
                row.get('建议仓库'), row.get('建议快递'), row.get('到账'),
                row.get('商品图片'), row.get('品牌'), row.get('商品税率'),
                row.get('商品代码'), row.get('商品名称'), row.get('商品简称'),
                row.get('规格代码'), row.get('规格名称'), row.get('商品备注'),
                row.get('代发订单'), row.get('订单标记'), row.get('预计发货时间'),
                row.get('订购数'), row.get('总重量'), row.get('折扣'),
                row.get('标准进价'), row.get('标准单价'), row.get('标准金额'),
                row.get('实际单价'), row.get('实际金额'), row.get('让利后金额'),
                row.get('让利金额'), row.get('物流费用'), row.get('成本总价'),
                row.get('买家备注'), row.get('卖家备注'), row.get('制单人'),
                row.get('商品实际利润'), row.get('商品标准利润'),
                row.get('商品已发货数量'), row.get('平台旗帜'), row.get('发货时间'),
                row.get('原产地'), row.get('平台商品名称'), row.get('平台规格名称'),
                row.get('供应商'), row.get('赠品来源'), row.get('买家支付金额'),
                row.get('平台支付金额'), row.get('其他服务费'), row.get('发票种类'),
                row.get('发票抬头类型'), row.get('发票类型'), row.get('开户行'),
                row.get('账号'), row.get('发票电话'), row.get('发票地址'),
                row.get('收货邮箱'), row.get('周期购商品'), row.get('平台单号'),
                row.get('到账时间'), row.get('附加信息'), row.get('发票抬头'),
                row.get('发票内容'), row.get('纳税人识别号'), row.get('收货人'),
                row.get('收货人手机'), row.get('邮编'), row.get('收货地址'),
                row.get('商品类别'), row.get('二次备注'), row.get('商品单位'),
                row.get('币别'), row.get('会员邮箱'), row.get('订单标签'),
                row.get('平台交易状态'), row.get('赠品'), row.get('是否退款'),
                row.get('地区信息'), row.get('确认收货时间'), row.get('作废')
            )

            # 执行插入
            cursor.execute(insert_sql, data)

            if cursor.rowcount > 0:
                success_count += 1
            else:
                duplicate_count += 1

        except Exception as e:
            print(f'插入第 {idx} 行时出错: {e}')
            error_count += 1
            continue

    # 提交事务
    conn.commit()
    conn.close()

    print(f'上传完成: 成功={success_count}, 重复={duplicate_count}, 错误={error_count}')

    return {
        'success': True,
        'total': len(df_deduped),
        'success_count': success_count,
        'duplicate_count': duplicate_count,
        'error_count': error_count
    }

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

@app.route('/api/analyse/export-weekly-report', methods=['POST'])
def export_weekly_report():
    """导出周报PDF"""
    try:
        # 注册中文字体
        font_name = 'Helvetica'  # 默认字体
        font_paths = [
            '/System/Library/Fonts/PingFang.ttc',
            '/System/Library/Fonts/STHeiti Light.ttc',
            '/System/Library/Fonts/STHeiti Medium.ttc',
            '/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf',
        ]
        
        for font_path in font_paths:
            try:
                if os.path.exists(font_path):
                    # 根据文件类型选择注册方式
                    if font_path.endswith('.ttc'):
                        # TTC文件需要指定子字体索引
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path, subfontIndex=0))
                    else:
                        # TTF文件直接注册
                        pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                    font_name = 'ChineseFont'
                    print(f'成功注册中文字体: {font_path}')
                    break
            except Exception as e:
                print(f'尝试注册字体 {font_path} 失败: {str(e)}')
                continue
        
        if font_name == 'Helvetica':
            print('警告: 未能注册中文字体，PDF中的中文可能显示为方框')
        
        data = request.json
        start_date = data.get('startDate')
        end_date = data.get('endDate')
        
        if not start_date or not end_date:
            return jsonify({'error': '缺少日期参数'}), 400
        
        print(f'导出周报: {start_date} 到 {end_date}')
        
        # 读取Tab配置
        with open('tab_config.json', 'r', encoding='utf-8') as f:
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

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)