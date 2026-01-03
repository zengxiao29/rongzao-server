# -*- coding: utf-8 -*-
import sqlite3
import hashlib
import os
import pandas as pd

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