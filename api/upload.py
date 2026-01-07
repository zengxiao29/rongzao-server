# -*- coding: utf-8 -*-
import pandas as pd
import re
from flask import jsonify, request, g
from database import get_db_connection, calculate_record_hash
from utils.auth import token_required
from utils.operation_logger import log_operation


def register_upload_routes(app):
    """注册上传相关 API 路由"""

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