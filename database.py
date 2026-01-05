# -*- coding: utf-8 -*-
import sqlite3
import hashlib
import os
import pandas as pd
import bcrypt

DB_PATH = os.path.join(os.path.dirname(__file__), 'rongzao.db')


def get_db_connection():
    """获取数据库连接"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_user_table():
    """初始化用户表"""
    conn = get_db_connection()
    cursor = conn.cursor()

    try:
        # 创建用户表
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                username TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                role TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # 检查是否已有用户
        cursor.execute('SELECT COUNT(*) as count FROM users')
        user_count = cursor.fetchone()['count']

        # 如果没有用户，创建默认管理员账户
        if user_count == 0:
            # 密码：zeng
            password = 'zeng'
            password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')

            cursor.execute('''
                INSERT INTO users (username, password_hash, role)
                VALUES (?, ?, ?)
            ''', ('zengxiao', password_hash, 'admin'))

            print('已创建默认管理员账户：zengxiao / zeng')

        conn.commit()
        print('用户表初始化完成')

    except Exception as e:
        print(f'初始化用户表失败: {str(e)}')
        conn.rollback()
    finally:
        conn.close()


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