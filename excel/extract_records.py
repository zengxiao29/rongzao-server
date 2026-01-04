#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
提取符合条件的订单记录：
- 付款时间在2025-12-29
- 商品名称包含"舰载熊猫挂件"
"""

import pandas as pd
from datetime import datetime

# 读取Excel文件
input_file = '订单商品明细统计 (1201-1229)_副本.xls'
output_file = '舰载熊猫挂件_2025-12-29.xlsx'

print(f"正在读取文件: {input_file}")
df = pd.read_excel(input_file)

print(f"总记录数: {len(df)}")
print(f"列名: {df.columns.tolist()}")
print("\n前5条记录:")
print(df.head())

# 将付款时间列转换为datetime类型（假设列名为"付款时间"）
# 首先查看是否有付款时间相关的列
date_columns = [col for col in df.columns if '时间' in col or '日期' in col or 'time' in col.lower() or 'date' in col.lower()]
print(f"\n发现可能的时间列: {date_columns}")

# 查找商品名称列
product_columns = [col for col in df.columns if '商品' in col or '产品' in col or '名称' in col]
print(f"发现的商品相关列: {product_columns}")

# 使用最可能的列名
date_col = '付款时间' if '付款时间' in df.columns else date_columns[0] if date_columns else None
product_col = '商品名称' if '商品名称' in df.columns else product_columns[0] if product_columns else None

print(f"\n使用列 - 付款时间: {date_col}")
print(f"使用列 - 商品名称: {product_col}")

if not date_col or not product_col:
    print("错误: 无法找到必要的列!")
    print("请检查Excel文件的列名")
    exit(1)

# 转换付款时间为datetime
df[date_col] = pd.to_datetime(df[date_col])

# 筛选条件
target_date = datetime(2025, 12, 29).date()
keyword = '舰载熊猫挂件'

# 筛选付款时间为2025-12-29的记录
date_filtered = df[df[date_col].dt.date == target_date]
print(f"\n2025-12-29的记录数: {len(date_filtered)}")

# 在这些记录中筛选商品名称包含"舰载熊猫挂件"的记录
result = date_filtered[date_filtered[product_col].str.contains(keyword, na=False)]
print(f"包含'舰载熊猫挂件'的记录数: {len(result)}")

# 保存到新的Excel文件
result.to_excel(output_file, index=False)
print(f"\n已将 {len(result)} 条记录保存到: {output_file}")

# 显示提取的记录
if len(result) > 0:
    print("\n提取的记录预览:")
    print(result)