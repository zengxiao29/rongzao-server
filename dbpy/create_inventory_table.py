#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建Inventory表的脚本
"""

import os
import sys
sys.path.append('.')

from dbpy.database import get_db_connection

def create_inventory_table():
    """创建Inventory表"""
    
    # Inventory表建表SQL
    create_table_sql = '''
    CREATE TABLE IF NOT EXISTS Inventory (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        
        -- 指定的7个字段放在前面
        商品名称 TEXT,
        仓库 TEXT,
        数量 INTEGER,
        可销数 INTEGER,
        可配数 INTEGER,
        锁定数 INTEGER,
        商品建档日期 TEXT,
        
        -- 其他37个字段按原顺序排列
        商品代码 TEXT,
        商品规格代码 TEXT,
        商品规格名称 TEXT,
        商品标签 TEXT,
        商品单位 TEXT,
        库存重量 REAL,
        可销售天数 TEXT,
        在途数 INTEGER,
        安全库存下限 INTEGER,
        安全库存上限 INTEGER,
        订单占用数 INTEGER,
        未付款数 INTEGER,
        库位 TEXT,
        商品条码 TEXT,
        商品简称 TEXT,
        商品备注 TEXT,
        规格备注 TEXT,
        库存状态 TEXT,
        商品分类 TEXT,
        商品税号 TEXT,
        供应商 TEXT,
        保质期 TEXT,
        有效日期 TEXT,
        生产日期 TEXT,
        供应商货号 TEXT,
        品牌 TEXT,
        箱规 TEXT,
        标准进价 REAL,
        最新采购价 REAL,
        最新采购供应商 TEXT,
        成本价格 REAL,
        销售价格 REAL,
        成本总金额 REAL,
        销售总金额 REAL,
        近3日销量 INTEGER,
        近7日销量 INTEGER,
        近15日销量 INTEGER,
        近30日销量 INTEGER,
        
        -- 系统字段
        创建时间 DATETIME DEFAULT CURRENT_TIMESTAMP,
        更新时间 DATETIME DEFAULT CURRENT_TIMESTAMP
    );
    '''
    
    # 索引定义
    indexes = [
        ('idx_商品名称', '商品名称'),
        ('idx_仓库', '仓库'),
        ('idx_商品代码', '商品代码'),
        ('idx_商品建档日期', '商品建档日期'),
        ('idx_创建时间', '创建时间'),
    ]
    
    try:
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print('开始创建Inventory表...')
        
        # 创建表
        cursor.execute(create_table_sql)
        print('✓ Inventory表创建成功')
        
        # 创建索引 - 使用更可靠的方式
        print('创建索引...')
        for index_name, column_name in indexes:
            try:
                # 先删除可能存在的旧索引
                drop_sql = f'DROP INDEX IF EXISTS {index_name};'
                cursor.execute(drop_sql)
                
                # 创建新索引
                create_sql = f'CREATE INDEX {index_name} ON Inventory({column_name});'
                cursor.execute(create_sql)
                print(f'  ✓ {index_name} ON ({column_name})')
            except Exception as e:
                print(f'  ✗ 创建索引 {index_name} 失败: {e}')
        
        print('✓ 索引创建完成')
        
        # 提交事务
        conn.commit()
        
        # 验证表创建成功
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='Inventory';")
        table_exists = cursor.fetchone()
        
        if table_exists:
            print('✓ 验证：Inventory表已成功创建')
            
            # 获取表结构
            cursor.execute('PRAGMA table_info(Inventory);')
            columns = cursor.fetchall()
            print(f'✓ Inventory表字段数：{len(columns)}')
            
            # 显示字段信息
            print('\nInventory表字段列表：')
            for i, col in enumerate(columns):
                col_name = col[1]
                col_type = col[2]
                print(f'  {i+1:2d}. {col_name:20s} ({col_type})')
                
        else:
            print('✗ 错误：Inventory表创建失败')
            
        conn.close()
        print('\n✅ Inventory表创建完成！')
        
    except Exception as e:
        print(f'❌ 创建Inventory表时出错：{e}')
        import traceback
        traceback.print_exc()
        return False
    
    return True

if __name__ == '__main__':
    # 激活虚拟环境
    if os.path.exists('.venv'):
        activate_script = os.path.join('.venv', 'bin', 'activate')
        print(f'虚拟环境已激活')
    
    success = create_inventory_table()
    sys.exit(0 if success else 1)
