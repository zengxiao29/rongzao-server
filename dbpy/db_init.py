# -*- coding: utf-8 -*-
"""
数据库初始化脚本
创建SQLite数据库和OrderDetails表
"""

import sqlite3
import os

def init_database():
    """初始化数据库"""
    # 数据库文件路径
    db_path = os.path.join(os.path.dirname(__file__), 'rongzao.db')

    # 如果数据库已存在，先删除（用于测试）
    if os.path.exists(db_path):
        print(f'数据库已存在: {db_path}')
        print('删除旧数据库...')
        os.remove(db_path)

    # 创建数据库连接
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 创建OrderDetails表
    create_table_sql = '''
    CREATE TABLE OrderDetails (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        record_hash TEXT NOT NULL,

        店铺类型 TEXT,
        店铺名称 TEXT,
        分销商名称 REAL,
        单据编号 TEXT,
        订单类型 TEXT,
        拍单时间 TEXT,
        付款时间 TEXT,
        审核时间 TEXT,
        会员代码 TEXT,
        会员名称 TEXT,
        内部便签 TEXT,
        业务员 TEXT,
        建议仓库 TEXT,
        建议快递 TEXT,
        到账 TEXT,
        商品图片 TEXT,
        品牌 TEXT,
        商品税率 REAL,
        商品代码 TEXT,
        商品名称 TEXT,
        商品简称 TEXT,
        规格代码 TEXT,
        规格名称 TEXT,
        商品备注 TEXT,
        代发订单 TEXT,
        订单标记 TEXT,
        预计发货时间 TEXT,
        订购数 INTEGER,
        总重量 REAL,
        折扣 REAL,
        标准进价 REAL,
        标准单价 REAL,
        标准金额 REAL,
        实际单价 REAL,
        实际金额 REAL,
        让利后金额 REAL,
        让利金额 REAL,
        物流费用 REAL,
        成本总价 REAL,
        买家备注 TEXT,
        卖家备注 TEXT,
        制单人 TEXT,
        商品实际利润 REAL,
        商品标准利润 REAL,
        商品已发货数量 INTEGER,
        平台旗帜 TEXT,
        发货时间 TEXT,
        原产地 TEXT,
        平台商品名称 TEXT,
        平台规格名称 TEXT,
        供应商 REAL,
        赠品来源 REAL,
        买家支付金额 REAL,
        平台支付金额 REAL,
        其他服务费 REAL,
        发票种类 TEXT,
        发票抬头类型 TEXT,
        发票类型 TEXT,
        开户行 TEXT,
        账号 TEXT,
        发票电话 TEXT,
        发票地址 TEXT,
        收货邮箱 TEXT,
        周期购商品 TEXT,
        平台单号 TEXT,
        到账时间 TEXT,
        附加信息 TEXT,
        发票抬头 TEXT,
        发票内容 TEXT,
        纳税人识别号 TEXT,
        收货人 TEXT,
        收货人手机 TEXT,
        邮编 REAL,
        收货地址 TEXT,
        商品类别 TEXT,
        二次备注 TEXT,
        商品单位 TEXT,
        币别 TEXT,
        会员邮箱 TEXT,
        订单标签 TEXT,
        平台交易状态 TEXT,
        赠品 TEXT,
        是否退款 TEXT,
        地区信息 TEXT,
        确认收货时间 REAL,
        作废 TEXT,

        创建时间 DATETIME DEFAULT CURRENT_TIMESTAMP,

        UNIQUE(record_hash)
    );
    '''

    cursor.execute(create_table_sql)
    print('✓ OrderDetails表创建成功')

    # 创建索引（可选，用于提高查询性能）
    create_indexes_sql = [
        'CREATE INDEX idx_单据编号 ON OrderDetails(单据编号);',
        'CREATE INDEX idx_商品代码 ON OrderDetails(商品代码);',
        'CREATE INDEX idx_商品名称 ON OrderDetails(商品名称);',
        'CREATE INDEX idx_是否退款 ON OrderDetails(是否退款);',
        'CREATE INDEX idx_创建时间 ON OrderDetails(创建时间);',
    ]

    for index_sql in create_indexes_sql:
        cursor.execute(index_sql)

    print('✓ 索引创建成功')

    # 提交事务
    conn.commit()
    conn.close()

    print(f'\n✓ 数据库初始化完成: {db_path}')
    print(f'  - 表: OrderDetails')
    print(f'  - 字段数: 87 (86个业务字段 + 1个record_hash)')
    print(f'  - 唯一约束: record_hash')

if __name__ == '__main__':
    init_database()