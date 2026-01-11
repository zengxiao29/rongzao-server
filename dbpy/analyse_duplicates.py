#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import pandas as pd
import sys
import os

def analyse_duplicates():
    """分析CSV文件中的重复记录"""
    
    csv_file = "商品库存.csv"
    
    if not os.path.exists(csv_file):
        print(f"文件 {csv_file} 不存在")
        return
    
    try:
        # 读取CSV文件
        df = pd.read_csv(csv_file, encoding='gb18030')
        print(f"CSV文件总行数: {len(df)}")
        print(f"CSV文件列名: {df.columns.tolist()}")
        
        # 检查必要的列是否存在
        required_columns = ['商品名称', '仓库', '数量', '可销数', '可配数', '锁定数', '商品建档日期']
        missing_columns = [col for col in required_columns if col not in df.columns]
        
        if missing_columns:
            print(f"缺少必要列: {missing_columns}")
            return
        
        # 检查重复行（基于商品名称 + 仓库）
        duplicates = df[df.duplicated(subset=['商品名称', '仓库'], keep=False)]
        duplicate_count = len(df[df.duplicated(subset=['商品名称', '仓库'], keep=False)])
        total_duplicates = len(duplicates)
        
        print(f"\n基于'商品名称+仓库'的重复记录分析:")
        print(f"重复记录组数: {duplicate_count}")
        print(f"重复记录总行数: {total_duplicates}")
        
        if duplicate_count > 0:
            print(f"\n重复记录详情:")
            grouped = duplicates.groupby(['商品名称', '仓库'])
            for i, ((product_name, warehouse), group) in enumerate(grouped, 1):
                if len(group) > 1:
                    print(f"\n重复组 {i}: 商品名称='{product_name}', 仓库='{warehouse}'")
                    print(f"  重复次数: {len(group)}")
                    print(f"  行号: {[idx+2 for idx in group.index.tolist()]}")  # +2因为从0开始且跳过表头
        
        # 检查是否有空值或异常值
        print(f"\n数据质量检查:")
        null_counts = df[['商品名称', '仓库']].isnull().sum()
        print(f"商品名称空值数: {null_counts['商品名称']}")
        print(f"仓库空值数: {null_counts['仓库']}")
        
        # 检查唯一记录数
        unique_records = df.drop_duplicates(subset=['商品名称', '仓库'])
        print(f"\n唯一记录数（基于商品名称+仓库去重）: {len(unique_records)}")
        print(f"预计数据库中的记录数: {len(unique_records)}")
        
        # 检查是否有整行都是空值的情况
        empty_rows = df.isnull().all(axis=1).sum()
        print(f"空行数: {empty_rows}")
        
    except Exception as e:
        print(f"分析时出错: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyse_duplicates()