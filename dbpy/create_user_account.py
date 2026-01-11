#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
创建新用户账户的脚本
创建用户：user，密码：user，角色：user
"""

import os
import sys
sys.path.append('.')

from dbpy.database import get_db_connection
import bcrypt

def create_user_account():
    """创建新用户账户"""
    
    username = 'user'
    password = 'user'
    role = 'user'
    
    try:
        # 获取数据库连接
        conn = get_db_connection()
        cursor = conn.cursor()
        
        print(f'开始创建用户账户...')
        print(f'  用户名: {username}')
        print(f'  密码: {password}')
        print(f'  角色: {role}')
        
        # 首先检查用户是否已存在
        cursor.execute('SELECT username FROM users WHERE username = ?', (username,))
        existing_user = cursor.fetchone()
        
        if existing_user:
            print(f'⚠️  用户 {username} 已存在，先删除旧用户...')
            cursor.execute('DELETE FROM users WHERE username = ?', (username,))
            conn.commit()
            print(f'✓ 旧用户已删除')
        
        # 生成密码哈希
        password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
        
        # 插入新用户
        insert_sql = '''
        INSERT INTO users (username, password_hash, role)
        VALUES (?, ?, ?)
        '''
        
        cursor.execute(insert_sql, (username, password_hash, role))
        conn.commit()
        
        print(f'✓ 用户 {username} 创建成功')
        
        # 验证用户创建
        cursor.execute('''
            SELECT id, username, role, created_at 
            FROM users 
            WHERE username = ?
        ''', (username,))
        
        user = cursor.fetchone()
        
        if user:
            print(f'\n✅ 用户创建验证成功：')
            print(f'  ID: {user[0]}')
            print(f'  用户名: {user[1]}')
            print(f'  角色: {user[2]}')
            print(f'  创建时间: {user[3]}')
        else:
            print('❌ 用户创建验证失败')
        
        # 显示所有用户
        print(f'\n当前所有用户账户：')
        cursor.execute('SELECT username, role, created_at FROM users ORDER BY username')
        all_users = cursor.fetchall()
        
        for u in all_users:
            role_display = '管理员' if u[1] == 'admin' else '普通用户'
            print(f'  {u[0]:15s} - 角色: {role_display:10s} - 创建时间: {u[2]}')
        
        conn.close()
        
        print(f'\n🎉 用户账户创建完成！')
        print(f'\n登录信息：')
        print(f'  • 用户名: {username}')
        print(f'  • 密码: {password}')
        print(f'  • 角色: {role}')
        print(f'  • 权限: 普通用户权限（非管理员）')
        
        return True
        
    except Exception as e:
        print(f'❌ 创建用户账户时出错：{e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == '__main__':
    # 激活虚拟环境
    if os.path.exists('.venv'):
        activate_script = os.path.join('.venv', 'bin', 'activate')
        print(f'虚拟环境已激活')
    
    success = create_user_account()
    sys.exit(0 if success else 1)