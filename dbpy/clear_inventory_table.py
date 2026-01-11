#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
清空Inventory表中的所有记录
"""

import os
import sys

# 添加项目路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from dbpy.database import get_db_connection


def clear_inventory_table():
    """清空Inventory表"""
    
    # 检查数据库加密密钥是否已设置
    if not os.environ.get('DB_ENCRYPTION_KEY'):
        print("❌ 错误: 未设置数据库加密密钥环境变量 DB_ENCRYPTION_KEY")
        print("💡 请设置环境变量: export DB_ENCRYPTION_KEY='your-encryption-key'")
        sys.exit(1)
    
    print("🧹 开始清空Inventory表...")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        # 获取当前记录数
        cursor.execute('SELECT COUNT(*) FROM Inventory')
        count_before = cursor.fetchone()[0]
        print(f"📊 清空前记录数: {count_before}")
        
        if count_before == 0:
            print("✅ Inventory表已经是空的")
            return
        
        # 执行清空操作
        cursor.execute('DELETE FROM Inventory')
        
        # 验证清空结果
        cursor.execute('SELECT COUNT(*) FROM Inventory')
        count_after = cursor.fetchone()[0]
        
        conn.commit()
        
        print(f"✅ 成功清空 {count_before} 条记录")
        print(f"📊 清空后记录数: {count_after}")
        
        if count_after == 0:
            print("🎉 Inventory表已成功清空！")
        else:
            print(f"⚠️  仍有 {count_after} 条记录未清空，请检查")
            
    except Exception as e:
        conn.rollback()
        print(f"❌ 清空Inventory表时发生错误: {e}")
        import traceback
        traceback.print_exc()
    finally:
        conn.close()


if __name__ == '__main__':
    clear_inventory_table()