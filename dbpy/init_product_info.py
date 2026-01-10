# -*- coding: utf-8 -*-
"""
初始化ProductInfo表
从OrderDetails提取商品信息并填充到ProductInfo表
"""
import json
import os
from database import get_db_connection


def extract_alias(product_name):
    """
    提取商品别名
    去除-后面的颜色、尺码等信息
    """
    if '-' in product_name:
        # 找到第一个-的位置，去除后面的内容
        alias = product_name.split('-')[0].strip()
        return alias
    return product_name


def determine_category(product_name, category_keywords):
    """
    自动判断商品大类
    根据关键词匹配返回category_id
    """
    for category_id, keywords in category_keywords.items():
        for keyword in keywords:
            if keyword in product_name:
                return category_id
    return None


def determine_mapped_title(product_name, mappings):
    """
    根据tab_config.json的映射逻辑确定mapped_title
    优先匹配第一个，匹配不到则返回None
    """
    for mapping in mappings:
        product_pattern = mapping['product']
        mapped_type = mapping['type']
        if product_pattern in product_name:
            return mapped_type
    return None


def main():
    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. 从OrderDetails提取所有去重的商品名称
    cursor.execute('SELECT DISTINCT 商品名称 FROM OrderDetails WHERE 商品名称 IS NOT NULL')
    product_names = [row['商品名称'] for row in cursor.fetchall()]

    print(f'从OrderDetails提取到 {len(product_names)} 个去重商品名称')

    # 2. 获取CategoryInfo表中的大类信息
    cursor.execute('SELECT id, name FROM CategoryInfo')
    categories = cursor.fetchall()
    category_map = {cat['name']: cat['id'] for cat in categories}

    # 定义大类关键词映射
    category_keywords = {
        category_map['帽子']: ['帽', '帽子'],
        category_map['夹克']: ['夹克'],
        category_map['包']: ['包', '双肩包', '头盔包', '斜挎包', '单肩包'],
        category_map['羽绒服']: ['羽绒服'],
        category_map['章']: ['章', '徽章'],
        category_map['舰载熊猫系列']: ['熊猫', '公仔'],
    }

    # 3. 读取tab_config.json获取映射规则
    config_path = os.path.join(os.path.dirname(__file__), 'tab_config.json')
    all_mappings = []
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            for tab in config.get('tabs', []):
                mappings = tab.get('mappings', [])
                for mapping in mappings:
                    all_mappings.append({
                        'product': mapping['product'],
                        'type': mapping['type']
                    })
    print(f'读取到 {len(all_mappings)} 条映射规则')

    # 4. 填充ProductInfo表
    inserted_count = 0
    for product_name in product_names:
        # 提取alias
        alias = extract_alias(product_name)

        # 判断大类
        category_id = determine_category(product_name, category_keywords)

        # 确定mapped_title
        mapped_title = determine_mapped_title(product_name, all_mappings)

        # 插入数据
        cursor.execute('''
            INSERT INTO ProductInfo (name, alias, category, mapped_title)
            VALUES (?, ?, ?, ?)
        ''', (product_name, alias, category_id, mapped_title))
        inserted_count += 1

    conn.commit()
    print(f'成功插入 {inserted_count} 条商品信息到ProductInfo表')

    # 5. 显示统计信息
    cursor.execute('SELECT COUNT(*) as total FROM ProductInfo')
    total = cursor.fetchone()['total']
    print(f'\nProductInfo表总记录数: {total}')

    cursor.execute('''
        SELECT c.name as category_name, COUNT(*) as count
        FROM ProductInfo p
        LEFT JOIN CategoryInfo c ON p.category = c.id
        GROUP BY c.name
        ORDER BY count DESC
    ''')
    print('\n按大类统计:')
    for row in cursor.fetchall():
        category_name = row['category_name'] if row['category_name'] else '未分类'
        print(f'  {category_name}: {row["count"]} 个商品')

    conn.close()
    print('\n初始化完成！')


if __name__ == '__main__':
    main()