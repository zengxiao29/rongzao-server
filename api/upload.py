# -*- coding: utf-8 -*-
import pandas as pd
import re
from flask import jsonify, request, g
from dbpy.database import get_db_connection, release_db_connection, calculate_record_hash
from utils.auth import token_required
from utils.operation_logger import log_operation


def register_upload_routes(app):
    """注册上传相关 API 路由"""

    @app.route('/api/analyse/upload', methods=['POST'])
    @token_required
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
    @token_required
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
    
    # 注册库存上传路由
    register_inventory_upload_routes(app)

    @app.route('/api/db/upload', methods=['POST'])
    @token_required
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
            result = upload_to_database_internal(file)
            
            # 记录上传日志
            if result.get('success'):
                log_operation(
                    username=g.current_user['username'],
                    role=g.current_user['role'],
                    operation_type='upload_excel',
                    detail={
                        'filename': file.filename,
                        'total': result.get('total', 0),
                        'success_count': result.get('success_count', 0),
                        'duplicate_count': result.get('duplicate_count', 0),
                        'error_count': result.get('error_count', 0),
                        'filtered_count': result.get('filtered_count', 0)
                    },
                    result='success'
                )
            
            return result
        except Exception as e:
            print(f'处理文件时出错: {str(e)}')
            import traceback
            traceback.print_exc()
            
            # 记录失败日志
            log_operation(
                username=g.current_user['username'],
                role=g.current_user['role'],
                operation_type='upload_excel',
                detail={'filename': file.filename},
                result='failed',
                error_message=str(e)
            )
            
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

    # 过滤掉店铺名称为"金蝶对接"的记录
    df_filtered = df_deduped[df_deduped['店铺名称'] != '金蝶对接'].copy()
    print(f'过滤金蝶对接记录: {len(df_deduped)} -> {len(df_filtered)} 条记录')

    if len(df_filtered) == 0:
        print('过滤后没有数据可上传')
        return {
            'success': True,
            'total': len(df_deduped),
            'success_count': 0,
            'duplicate_count': 0,
            'error_count': 0,
            'filtered_count': len(df_deduped)
        }

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

    # 遍历每一行数据（使用过滤后的数据 df_filtered）
    for idx, row in df_filtered.iterrows():
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

    # 检查数据库中是否存在"金蝶对接"数据
    cursor.execute("SELECT COUNT(*) FROM OrderDetails WHERE 店铺名称 = '金蝶对接'")
    jindie_count = cursor.fetchone()[0]

    conn.close()

    filtered_count = len(df_deduped) - len(df_filtered)

    print(f'上传完成: 成功={success_count}, 重复={duplicate_count}, 错误={error_count}, 过滤={filtered_count}')
    print(f'数据库中"金蝶对接"记录数: {jindie_count}')

    result = {
        'success': True,
        'total': len(df_deduped),
        'success_count': success_count,
        'duplicate_count': duplicate_count,
        'error_count': error_count,
        'filtered_count': filtered_count
    }

    # 如果数据库中存在"金蝶对接"数据，添加警告信息
    if jindie_count > 0:
        result['warning'] = f'数据库中存在 {jindie_count} 条"金蝶对接"记录，请联系管理员处理'

    return result


def register_inventory_upload_routes(app):
    """注册库存上传相关 API 路由"""

    @app.route('/api/upload/inventory', methods=['POST'])
    @token_required
    def upload_inventory():
        """处理库存CSV文件上传"""
        print('收到库存文件上传请求')

        if 'file' not in request.files:
            print('错误：请求中没有文件')
            return jsonify({'error': '没有文件'}), 400

        file = request.files['file']
        if file.filename == '':
            print('错误：文件名为空')
            return jsonify({'error': '未选择文件'}), 400

        print(f'开始处理库存文件: {file.filename}')

        try:
            # 处理库存CSV文件，传递当前用户信息用于记录操作日志
            return process_inventory_csv(file, g.current_user)
        except Exception as e:
            print(f'处理库存文件时出错: {str(e)}')
            import traceback
            traceback.print_exc()
            return jsonify({'error': str(e)}), 500


def process_inventory_csv(file, current_user=None):
    """处理库存CSV数据并插入/更新到Inventory表
    
    Args:
        file: 上传的CSV文件对象
        current_user: 当前用户信息字典（包含username和role字段）
    """
    import pandas as pd
    import io
    
    # 读取CSV文件（使用GB18030编码，因为商品库存.csv是GB18030编码）
    content = file.read()
    
    try:
        # 尝试用GB18030解码
        decoded_content = content.decode('gb18030')
    except UnicodeDecodeError:
        try:
            # 如果GB18030失败，尝试utf-8
            decoded_content = content.decode('utf-8')
        except UnicodeDecodeError as e:
            print(f'文件编码解码失败: {e}')
            return jsonify({'error': f'文件编码不支持，请使用GB18030或UTF-8编码: {str(e)}'}), 400
    
    # 使用pandas读取CSV
    try:
        df = pd.read_csv(io.StringIO(decoded_content))
        print(f'成功读取CSV文件，共 {len(df)} 行，{len(df.columns)} 列')
        print(f'列名: {df.columns.tolist()}')
    except Exception as e:
        print(f'读取CSV文件失败: {e}')
        return jsonify({'error': f'读取CSV文件失败: {str(e)}'}), 400
    
    # 检查必要的列是否存在
    required_columns = ['商品名称', '仓库', '数量', '可销数', '可配数', '锁定数', '商品建档日期']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        print(f'CSV文件缺少必要列: {missing_columns}')
        return jsonify({'error': f'CSV文件缺少必要列: {missing_columns}'}), 400
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # 记录数据库当前状态
    cursor.execute('SELECT COUNT(*) FROM Inventory')
    db_existing_count = cursor.fetchone()[0]
    print(f'📊 数据库当前记录数: {db_existing_count}')
    
    # 统计CSV中的唯一记录数（基于商品名称+仓库）
    unique_keys = df[['商品名称', '仓库']].drop_duplicates()
    csv_unique_count = len(unique_keys)
    print(f'📊 CSV文件唯一记录数（商品名称+仓库）: {csv_unique_count}')
    print(f'📊 CSV文件总行数: {len(df)}')
    print(f'📊 CSV文件列数: {len(df.columns)}')
    print('=' * 60)
    
    # 定义清理函数，去除字符串开头和结尾的空白字符（空格、制表符等）
    def clean_value(value):
        """清理字段值：去除开头和结尾的空白字符，保留中间的空白"""
        if value is None:
            return None
        if isinstance(value, str):
            # 去除开头和结尾的空白字符（包括空格、制表符等）
            cleaned = value.strip()
            # 如果去除空白后变为空字符串，返回None
            return cleaned if cleaned != '' else None
        # 非字符串值保持不变
        return value
    
    # 定义字段转换函数，处理各种类型的字段转换
    def convert_field_value(value, field_type='str'):
        """转换字段值，如果clean_value后为空则返回None
        
        Args:
            value: 原始值
            field_type: 字段类型，可选 'str', 'int', 'float'
        Returns:
            转换后的值，如果清理后为空则返回None
        """
        # 首先清理值
        cleaned = clean_value(value)
        if cleaned is None:
            return None
        
        # 根据字段类型转换
        try:
            if field_type == 'int':
                return int(cleaned)
            elif field_type == 'float':
                return float(cleaned)
            else:  # 'str' 或其他类型
                return cleaned
        except (ValueError, TypeError):
            # 转换失败时返回None
            return None
    
    total_count = 0
    inserted_count = 0
    updated_count = 0
    failed_count = 0
    
    try:
        # 处理每一行数据
        for index, row in df.iterrows():
            total_count += 1
            
            try:
                # 清理关键字段值
                product_name = clean_value(row['商品名称'])
                warehouse = clean_value(row['仓库'])
                
                # 检查商品名称和仓库是否已存在（使用清理后的值）
                cursor.execute('''
                    SELECT id FROM Inventory 
                    WHERE 商品名称 = ? AND 仓库 = ?
                ''', (product_name, warehouse))
                
                existing_record = cursor.fetchone()
                
                if existing_record:
                    # 更新现有记录
                    update_sql = '''
                    UPDATE Inventory SET
                        数量 = ?,
                        可销数 = ?,
                        可配数 = ?,
                        锁定数 = ?,
                        商品建档日期 = ?,
                        商品代码 = ?,
                        商品规格代码 = ?,
                        商品规格名称 = ?,
                        商品标签 = ?,
                        商品单位 = ?,
                        库存重量 = ?,
                        可销售天数 = ?,
                        在途数 = ?,
                        安全库存下限 = ?,
                        安全库存上限 = ?,
                        订单占用数 = ?,
                        未付款数 = ?,
                        库位 = ?,
                        商品条码 = ?,
                        商品简称 = ?,
                        商品备注 = ?,
                        规格备注 = ?,
                        库存状态 = ?,
                        商品分类 = ?,
                        商品税号 = ?,
                        供应商 = ?,
                        保质期 = ?,
                        有效日期 = ?,
                        生产日期 = ?,
                        供应商货号 = ?,
                        品牌 = ?,
                        箱规 = ?,
                        标准进价 = ?,
                        最新采购价 = ?,
                        最新采购供应商 = ?,
                        成本价格 = ?,
                        销售价格 = ?,
                        成本总金额 = ?,
                        销售总金额 = ?,
                        近3日销量 = ?,
                        近7日销量 = ?,
                        近15日销量 = ?,
                        近30日销量 = ?,
                        更新时间 = CURRENT_TIMESTAMP
                    WHERE id = ?
                    '''
                    
                    # 准备更新数据
                    update_data = (
                        convert_field_value(row['数量'], 'int'),
                        convert_field_value(row['可销数'], 'int'),
                        convert_field_value(row['可配数'], 'int'),
                        convert_field_value(row['锁定数'], 'int'),
                        convert_field_value(row['商品建档日期'], 'str'),
                        convert_field_value(row.get('商品代码'), 'str'),
                        convert_field_value(row.get('商品规格代码'), 'str'),
                        convert_field_value(row.get('商品规格名称'), 'str'),
                        convert_field_value(row.get('商品标签'), 'str'),
                        convert_field_value(row.get('商品单位'), 'str'),
                        convert_field_value(row.get('库存重量'), 'float'),
                        convert_field_value(row.get('可销售天数'), 'str'),
                        convert_field_value(row.get('在途数'), 'int'),
                        convert_field_value(row.get('安全库存下限'), 'int'),
                        convert_field_value(row.get('安全库存上限'), 'int'),
                        convert_field_value(row.get('订单占用数'), 'int'),
                        convert_field_value(row.get('未付款数'), 'int'),
                        convert_field_value(row.get('库位'), 'str'),
                        convert_field_value(row.get('商品条码'), 'str'),
                        convert_field_value(row.get('商品简称'), 'str'),
                        convert_field_value(row.get('商品备注'), 'str'),
                        convert_field_value(row.get('规格备注'), 'str'),
                        convert_field_value(row.get('库存状态'), 'str'),
                        convert_field_value(row.get('商品分类'), 'str'),
                        convert_field_value(row.get('商品税号'), 'str'),
                        convert_field_value(row.get('供应商'), 'str'),
                        convert_field_value(row.get('保质期'), 'str'),
                        convert_field_value(row.get('有效日期'), 'str'),
                        convert_field_value(row.get('生产日期'), 'str'),
                        convert_field_value(row.get('供应商货号'), 'str'),
                        convert_field_value(row.get('品牌'), 'str'),
                        convert_field_value(row.get('箱规'), 'str'),
                        convert_field_value(row.get('标准进价'), 'float'),
                        convert_field_value(row.get('最新采购价'), 'float'),
                        convert_field_value(row.get('最新采购供应商'), 'str'),
                        convert_field_value(row.get('成本价格'), 'float'),
                        convert_field_value(row.get('销售价格'), 'float'),
                        convert_field_value(row.get('成本总金额'), 'float'),
                        convert_field_value(row.get('销售总金额'), 'float'),
                        convert_field_value(row.get('近3日销量'), 'int'),
                        convert_field_value(row.get('近7日销量'), 'int'),
                        convert_field_value(row.get('近15日销量'), 'int'),
                        convert_field_value(row.get('近30日销量'), 'int'),
                        existing_record[0]  # WHERE id = ?
                    )
                    
                    cursor.execute(update_sql, update_data)
                    updated_count += 1
                    print(f'✅ 第 {index + 1} 行: 更新记录 (ID: {existing_record[0]}) 商品名称="{product_name}" 仓库="{warehouse}"')
                    
                else:
                    # 插入新记录
                    insert_sql = '''
                    INSERT INTO Inventory (
                        商品名称, 仓库, 数量, 可销数, 可配数, 锁定数, 商品建档日期,
                        商品代码, 商品规格代码, 商品规格名称, 商品标签, 商品单位,
                        库存重量, 可销售天数, 在途数, 安全库存下限, 安全库存上限,
                        订单占用数, 未付款数, 库位, 商品条码, 商品简称, 商品备注,
                        规格备注, 库存状态, 商品分类, 商品税号, 供应商, 保质期,
                        有效日期, 生产日期, 供应商货号, 品牌, 箱规, 标准进价,
                        最新采购价, 最新采购供应商, 成本价格, 销售价格, 成本总金额,
                        销售总金额, 近3日销量, 近7日销量, 近15日销量, 近30日销量
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                             ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 
                             ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    '''
                    
                    # 准备插入数据（商品名称和仓库已使用clean_value清理）
                    insert_data = (
                        product_name,
                        warehouse,
                        convert_field_value(row['数量'], 'int'),
                        convert_field_value(row['可销数'], 'int'),
                        convert_field_value(row['可配数'], 'int'),
                        convert_field_value(row['锁定数'], 'int'),
                        convert_field_value(row['商品建档日期'], 'str'),
                        convert_field_value(row.get('商品代码'), 'str'),
                        convert_field_value(row.get('商品规格代码'), 'str'),
                        convert_field_value(row.get('商品规格名称'), 'str'),
                        convert_field_value(row.get('商品标签'), 'str'),
                        convert_field_value(row.get('商品单位'), 'str'),
                        convert_field_value(row.get('库存重量'), 'float'),
                        convert_field_value(row.get('可销售天数'), 'str'),
                        convert_field_value(row.get('在途数'), 'int'),
                        convert_field_value(row.get('安全库存下限'), 'int'),
                        convert_field_value(row.get('安全库存上限'), 'int'),
                        convert_field_value(row.get('订单占用数'), 'int'),
                        convert_field_value(row.get('未付款数'), 'int'),
                        convert_field_value(row.get('库位'), 'str'),
                        convert_field_value(row.get('商品条码'), 'str'),
                        convert_field_value(row.get('商品简称'), 'str'),
                        convert_field_value(row.get('商品备注'), 'str'),
                        convert_field_value(row.get('规格备注'), 'str'),
                        convert_field_value(row.get('库存状态'), 'str'),
                        convert_field_value(row.get('商品分类'), 'str'),
                        convert_field_value(row.get('商品税号'), 'str'),
                        convert_field_value(row.get('供应商'), 'str'),
                        convert_field_value(row.get('保质期'), 'str'),
                        convert_field_value(row.get('有效日期'), 'str'),
                        convert_field_value(row.get('生产日期'), 'str'),
                        convert_field_value(row.get('供应商货号'), 'str'),
                        convert_field_value(row.get('品牌'), 'str'),
                        convert_field_value(row.get('箱规'), 'str'),
                        convert_field_value(row.get('标准进价'), 'float'),
                        convert_field_value(row.get('最新采购价'), 'float'),
                        convert_field_value(row.get('最新采购供应商'), 'str'),
                        convert_field_value(row.get('成本价格'), 'float'),
                        convert_field_value(row.get('销售价格'), 'float'),
                        convert_field_value(row.get('成本总金额'), 'float'),
                        convert_field_value(row.get('销售总金额'), 'float'),
                        convert_field_value(row.get('近3日销量'), 'int'),
                        convert_field_value(row.get('近7日销量'), 'int'),
                        convert_field_value(row.get('近15日销量'), 'int'),
                        convert_field_value(row.get('近30日销量'), 'int')
                    )
                    
                    cursor.execute(insert_sql, insert_data)
                    inserted_count += 1
                    print(f'✅ 第 {index + 1} 行: 插入新记录 商品名称="{product_name}" 仓库="{warehouse}"')
                    
            except Exception as e:
                print(f'❌ 处理第 {index + 1} 行时出错: {e}')
                print(f'   问题数据: 商品名称="{product_name}", 仓库="{warehouse}"')
                import traceback
                traceback.print_exc()
                failed_count += 1
                continue
        
        conn.commit()
        
        # 查询最终数据库记录数
        cursor.execute('SELECT COUNT(*) FROM Inventory')
        db_final_count = cursor.fetchone()[0]
        print(f'📊 数据库最终记录数: {db_final_count}')
        print(f'📊 数据库记录变化: +{inserted_count}新增, {updated_count}更新')
        print('=' * 60)
        
        # 记录操作日志
        from utils.operation_logger import log_operation
        if current_user:
            log_operation(current_user['username'], current_user['role'], 'upload_inventory', 
                         f'上传库存数据: 总计{total_count}行, 新增{inserted_count}行, 更新{updated_count}行, 失败{failed_count}行')
        else:
            print('警告：current_user为空，跳过操作日志记录')
        
        print(f'库存上传完成: 总计{total_count}行, 新增{inserted_count}行, 更新{updated_count}行, 失败{failed_count}行')
        
        return jsonify({
            'success': True,
            'total': total_count,
            'inserted': inserted_count,
            'updated': updated_count,
            'failed': failed_count,
            'message': '库存数据上传完成'
        })
        
    except Exception as e:
        conn.rollback()
        print(f'处理库存数据时发生错误: {e}')
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'处理库存数据时发生错误: {str(e)}'}), 500
    finally:
        conn.close()