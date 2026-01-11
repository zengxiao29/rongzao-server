#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库定期维护脚本
建议每月执行一次，优化数据库性能和存储空间
使用方法：
    python3 db_maintenance.py
或添加到crontab（每月1日执行）：
    0 2 1 * * cd /path/to/rongzao_server && python3 db_maintenance.py
"""

import os
import sqlite3
import sys
from datetime import datetime

# 数据库文件路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, '../rongzao.db')

def run_maintenance():
    """执行数据库维护任务"""
    if not os.path.exists(DB_PATH):
        print(f"错误: 数据库文件不存在: {DB_PATH}")
        return False
    
    print(f"开始数据库维护: {DB_PATH}")
    print(f"时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 1. 执行VACUUM - 整理数据库文件，释放未使用空间
        print("执行 VACUUM...")
        cursor.execute("VACUUM")
        print("✓ VACUUM 完成")
        
        # 2. 执行ANALYZE - 更新查询优化器的统计信息
        print("执行 ANALYZE...")
        cursor.execute("ANALYZE")
        print("✓ ANALYZE 完成")
        
        # 3. 检查并修复索引（SQLite 3.18+）
        print("优化查询计划...")
        cursor.execute("PRAGMA optimize")
        print("✓ 查询计划优化完成")
        
        # 4. 检查数据库完整性
        print("检查数据库完整性...")
        cursor.execute("PRAGMA integrity_check")
        result = cursor.fetchone()
        if result and result[0] == 'ok':
            print("✓ 数据库完整性检查通过")
        else:
            print(f"⚠️ 数据库完整性警告: {result}")
        
        # 5. 更新数据库统计信息
        print("更新数据库统计...")
        cursor.execute("PRAGMA analysis_limit=400")
        cursor.execute("PRAGMA optimize")
        print("✓ 数据库统计更新完成")
        
        conn.commit()
        conn.close()
        
        # 获取文件大小
        file_size_mb = os.path.getsize(DB_PATH) / (1024 * 1024)
        print(f"\n✅ 数据库维护完成")
        print(f"   数据库文件大小: {file_size_mb:.2f} MB")
        print(f"   维护时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        
        return True
        
    except Exception as e:
        print(f"❌ 数据库维护失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    success = run_maintenance()
    sys.exit(0 if success else 1)
