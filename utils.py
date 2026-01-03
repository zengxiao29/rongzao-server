# -*- coding: utf-8 -*-
import re
import os
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont


def normalize_product_name(name):
    """标准化商品名称：移除颜色、尺码等后缀信息"""
    name = str(name)
    # 移除 -- 后面的内容
    name = re.sub(r'--.*', '', name)
    # 移除 - 后面跟着数字或字母的内容（尺码）
    name = re.sub(r'-\s*\d+[A-Za-z]*', '', name)
    name = re.sub(r'-\s*[A-Za-z]+', '', name)
    # 移除末尾的数字+单位（如 58CM）
    name = re.sub(r'\d+CM$', '', name)
    name = re.sub(r'\d+$', '', name)
    return name.strip()


def register_chinese_font():
    """注册中文字体，返回字体名称"""
    font_name = 'Helvetica'  # 默认字体
    font_paths = [
        '/System/Library/Fonts/PingFang.ttc',
        '/System/Library/Fonts/STHeiti Light.ttc',
        '/System/Library/Fonts/STHeiti Medium.ttc',
        '/System/Library/Fonts/Supplemental/Arial Unicode MS.ttf',
    ]

    for font_path in font_paths:
        try:
            if os.path.exists(font_path):
                # 根据文件类型选择注册方式
                if font_path.endswith('.ttc'):
                    # TTC文件需要指定子字体索引
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path, subfontIndex=0))
                else:
                    # TTF文件直接注册
                    pdfmetrics.registerFont(TTFont('ChineseFont', font_path))
                font_name = 'ChineseFont'
                print(f'成功注册中文字体: {font_path}')
                break
        except Exception as e:
            print(f'尝试注册字体 {font_path} 失败: {str(e)}')
            continue

    if font_name == 'Helvetica':
        print('警告: 未能注册中文字体，PDF中的中文可能显示为方框')

    return font_name