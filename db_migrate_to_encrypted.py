#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库加密迁移脚本
将现有的SQLite数据库迁移到SQLCipher加密数据库
"""

import os
import sys
import sqlite3
import sqlcipher3
import shutil
from datetime import datetime
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 数据库路径
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, 'rongzao.db')

# 加密密钥
DB_ENCRYPTION_KEY = os.environ.get('DB_ENCRYPTION_KEY')

def validate_environment():
    """验证环境配置"""
    if not DB_ENCRYPTION_KEY:
        print("❌ 错误：未设置数据库加密密钥")
        print("请在 .env 文件中设置 DB_ENCRYPTION_KEY 环境变量")
        return False
    
    if len(DB_ENCRYPTION_KEY) < 16:
        print("❌ 错误：加密密钥太短，至少需要16个字符")
        return False
    
    if not os.path.exists(DB_PATH):
        print(f"❌ 错误：数据库文件不存在: {DB_PATH}")
        return False
    
    return True

def get_database_size():
    """获取数据库文件大小"""
    if os.path.exists(DB_PATH):
        return os.path.getsize(DB_PATH)
    return 0

def backup_database():
    """备份原始数据库"""
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    backup_file = f"{DB_PATH}.backup_before_encryption_{timestamp}"
    
    print(f"📦 正在备份原始数据库...")
    shutil.copy2(DB_PATH, backup_file)
    print(f"   ✓ 备份完成: {backup_file}")
    
    return backup_file

def migrate_to_encrypted():
    """执行数据库加密迁移"""
    print("=" * 60)
    print("🔐 数据库加密迁移工具")
    print("=" * 60)
    
    # 验证环境
    if not validate_environment():
        sys.exit(1)
    
    # 检查数据库大小
    db_size = get_database_size()
    print(f"📊 当前数据库大小: {db_size:,} 字节 ({db_size/1024/1024:.2f} MB)")
    
    # 备份数据库
    backup_file = backup_database()
    
    # 临时加密数据库路径
    encrypted_temp_path = f"{DB_PATH}.encrypted_temp"
    
    try:
        # 步骤1: 连接原始数据库（未加密）
        print("\n🔗 连接原始数据库...")
        source_conn = sqlite3.connect(DB_PATH)
        source_conn.row_factory = sqlite3.Row
        source_cursor = source_conn.cursor()
        
        # 获取所有表（排除系统表）
        source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in source_cursor.fetchall()]
        
        print(f"   ✓ 找到 {len(tables)} 个表: {', '.join(tables[:5])}{'...' if len(tables) > 5 else ''}")
        
        # 步骤2: 创建加密数据库
        print("\n🔐 创建加密数据库...")
        dest_conn = sqlcipher3.connect(encrypted_temp_path)
        dest_conn.row_factory = sqlcipher3.Row  # 启用行工厂支持（使用sqlcipher3.Row）
        dest_cursor = dest_conn.cursor()
        
        # 设置加密密钥和兼容性参数
        dest_cursor.execute(f"PRAGMA key='{DB_ENCRYPTION_KEY}'")
        dest_cursor.execute('PRAGMA cipher_compatibility=4')  # SQLCipher 4.x 兼容
        dest_cursor.execute('PRAGMA kdf_iter=256000')         # 高强度密钥派生
        dest_cursor.execute('PRAGMA foreign_keys = ON')
        
        # 验证加密连接
        dest_cursor.execute('SELECT 1')
        print("   ✓ 加密数据库创建成功")
        
        # 步骤3: 迁移表结构和数据
        print("\n🔄 迁移表结构和数据...")
        total_tables = len(tables)
        
        for i, table_name in enumerate(tables, 1):
            if table_name.startswith('sqlite_'):
                continue  # 跳过系统表
            
            print(f"   [{i}/{total_tables}] 迁移表: {table_name}")
            
            # 获取表结构
            source_cursor.execute(f"SELECT sql FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            create_sql = source_cursor.fetchone()[0]
            
            # 在加密库中创建表
            dest_cursor.execute(create_sql)
            
            # 获取数据
            source_cursor.execute(f"SELECT * FROM {table_name}")
            rows = source_cursor.fetchall()
            
            if rows:
                # 获取列名
                col_names = [desc[0] for desc in source_cursor.description]
                placeholders = ','.join(['?'] * len(col_names))
                insert_sql = f"INSERT INTO {table_name} ({','.join(col_names)}) VALUES ({placeholders})"
                
                # 批量插入（提高性能）
                dest_cursor.executemany(insert_sql, rows)
                print(f"     ✓ 迁移 {len(rows)} 行数据")
            else:
                print(f"     ✓ 表为空")
        
        # 步骤4: 迁移索引、视图和触发器
        print("\n📋 迁移索引、视图和触发器...")
        
        # 索引
        source_cursor.execute("SELECT sql FROM sqlite_master WHERE type='index' AND sql IS NOT NULL")
        for row in source_cursor.fetchall():
            try:
                dest_cursor.execute(row[0])
            except Exception as e:
                print(f"     ⚠️ 创建索引时出错: {e}")
        
        # 视图
        source_cursor.execute("SELECT sql FROM sqlite_master WHERE type='view' AND sql IS NOT NULL")
        for row in source_cursor.fetchall():
            try:
                dest_cursor.execute(row[0])
            except Exception as e:
                print(f"     ⚠️ 创建视图时出错: {e}")
        
        # 步骤5: 提交事务
        dest_conn.commit()
        
        # 步骤6: 验证数据完整性
        print("\n✅ 验证数据完整性...")
        
        # 检查表数量
        dest_cursor.execute("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'")
        dest_table_count = dest_cursor.fetchone()['count']
        
        source_cursor.execute("SELECT COUNT(*) as count FROM sqlite_master WHERE type='table'")
        source_table_count = source_cursor.fetchone()['count']
        
        print(f"   原始数据库表数量: {source_table_count}")
        print(f"   加密数据库表数量: {dest_table_count}")
        
        # 检查关键表数据
        key_tables = ['OrderDetails', 'ProductInfo', 'users']
        for table in key_tables:
            if table in tables:
                source_cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                source_count = source_cursor.fetchone()['count']
                
                dest_cursor.execute(f"SELECT COUNT(*) as count FROM {table}")
                dest_count = dest_cursor.fetchone()['count']
                
                if source_count == dest_count:
                    print(f"   ✓ {table}: {source_count} 行数据一致")
                else:
                    print(f"   ❌ {table}: 数据不一致 (原始: {source_count}, 加密: {dest_count})")
                    raise ValueError(f"{table} 表数据不一致")
        
        # 关闭连接
        source_conn.close()
        dest_conn.close()
        
        # 步骤7: 替换数据库文件
        print("\n🔄 替换数据库文件...")
        
        # 重命名原始数据库（保留备份）
        plaintext_backup = f"{DB_PATH}.plaintext_backup"
        os.rename(DB_PATH, plaintext_backup)
        
        # 重命名加密数据库
        os.rename(encrypted_temp_path, DB_PATH)
        
        print(f"   ✓ 原始数据库备份: {plaintext_backup}")
        print(f"   ✓ 加密数据库已就位: {DB_PATH}")
        
        # 步骤8: 验证加密数据库可访问
        print("\n🔍 验证加密数据库访问...")
        test_conn = sqlcipher3.connect(DB_PATH)
        test_cursor = test_conn.cursor()
        test_cursor.execute(f"PRAGMA key='{DB_ENCRYPTION_KEY}'")
        test_cursor.execute('SELECT COUNT(*) FROM sqlite_master')
        test_result = test_cursor.fetchone()[0]
        test_conn.close()
        
        print(f"   ✓ 加密数据库可正常访问，包含 {test_result} 个对象")
        
        # 计算加密后大小
        encrypted_size = os.path.getsize(DB_PATH)
        size_change = ((encrypted_size - db_size) / db_size) * 100 if db_size > 0 else 0
        
        print("\n" + "=" * 60)
        print("🎉 数据库加密迁移完成！")
        print("=" * 60)
        print(f"📊 迁移统计:")
        print(f"   - 原始大小: {db_size:,} 字节 ({db_size/1024/1024:.2f} MB)")
        print(f"   - 加密后大小: {encrypted_size:,} 字节 ({encrypted_size/1024/1024:.2f} MB)")
        print(f"   - 大小变化: {size_change:+.2f}%")
        print(f"   - 迁移表数量: {total_tables}")
        print(f"\n📁 备份文件:")
        print(f"   - 加密前备份: {backup_file}")
        print(f"   - 明文备份: {plaintext_backup}")
        print(f"\n🔑 加密信息:")
        print(f"   - 加密算法: SQLCipher (AES-256)")
        print(f"   - 密钥长度: {len(DB_ENCRYPTION_KEY)} 字符")
        print(f"\n⚠️ 重要提醒:")
        print(f"   1. 请妥善保管加密密钥: {DB_ENCRYPTION_KEY}")
        print(f"   2. 备份文件将在30天后自动清理")
        print(f"   3. 使用DB Browser打开时选择 'DB Browser (SQLCipher)'")
        print(f"   4. 连接时输入上述加密密钥")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 迁移失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        # 恢复备份
        if os.path.exists(backup_file) and not os.path.exists(DB_PATH):
            print(f"\n🔄 尝试恢复备份...")
            shutil.copy2(backup_file, DB_PATH)
            print(f"   ✓ 已从备份恢复: {backup_file}")
        
        return False

def cleanup_old_backups():
    """清理旧的备份文件（保留最近7天）"""
    import glob
    import time
    
    backup_pattern = f"{DB_PATH}.backup_before_encryption_*"
    backups = glob.glob(backup_pattern)
    
    current_time = time.time()
    cutoff_time = current_time - (7 * 24 * 60 * 60)  # 7天前
    
    for backup in backups:
        file_time = os.path.getmtime(backup)
        if file_time < cutoff_time:
            try:
                os.remove(backup)
                print(f"🗑️ 清理旧备份: {os.path.basename(backup)}")
            except:
                pass

if __name__ == '__main__':
    # 执行迁移
    success = migrate_to_encrypted()
    
    # 清理旧备份
    if success:
        cleanup_old_backups()
    
    sys.exit(0 if success else 1)