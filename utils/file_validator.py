# -*- coding: utf-8 -*-
"""
文件格式验证工具模块
用于验证上传的Excel和CSV文件格式
"""

import pandas as pd
import os
from typing import Dict, List, Tuple, Optional


class FileValidator:
    """文件格式验证器"""
    
    @staticmethod
    def validate_excel_format(file_path: str, required_columns: List[str] = None) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        验证Excel文件格式
        
        Args:
            file_path: Excel文件路径
            required_columns: 必需的列名列表
            
        Returns:
            (是否有效, 错误信息, 数据框)
        """
        try:
            # 检查文件扩展名
            if not file_path.lower().endswith(('.xlsx', '.xls')):
                return False, "文件格式不正确，请上传Excel文件(.xlsx或.xls)", None
            
            # 读取Excel文件
            df = pd.read_excel(file_path)
            
            if df.empty:
                return False, "Excel文件为空", None
            
            # 如果没有指定必需列，则使用默认的电商订单列
            if required_columns is None:
                required_columns = ['商品名称', '订购数', '付款时间', '店铺类型', '让利后金额']
            
            # 检查必需列是否存在
            missing_columns = []
            for col in required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
            
            if missing_columns:
                return False, f"Excel文件缺少必需列: {', '.join(missing_columns)}", None
            
            # 验证数据类型和格式
            errors = []
            
            # 检查订购数列是否为数值类型
            if '订购数' in df.columns:
                for idx, value in enumerate(df['订购数']):
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"第{idx + 2}行订购数格式不正确: {value}")
            
            # 检查让利后金额列是否为数值类型
            if '让利后金额' in df.columns:
                for idx, value in enumerate(df['让利后金额']):
                    try:
                        float(value)
                    except (ValueError, TypeError):
                        errors.append(f"第{idx + 2}行让利后金额格式不正确: {value}")
            
            # 检查付款时间列格式
            if '付款时间' in df.columns:
                for idx, value in enumerate(df['付款时间']):
                    # 付款时间允许为空，所以跳过空值检查
                    if pd.notna(value) and value != '':
                        # 如果有值，则进行格式验证
                        try:
                            pd.to_datetime(value)
                        except:
                            errors.append(f"第{idx + 2}行付款时间格式不正确: {value}")
            
            if errors:
                return False, "数据格式错误:\n" + "\n".join(errors), None
            
            return True, "Excel文件格式验证通过", df
            
        except Exception as e:
            return False, f"读取Excel文件失败: {str(e)}", None
    
    @staticmethod
    def validate_csv_format(file_input, required_columns: List[str] = None) -> Tuple[bool, str, Optional[pd.DataFrame]]:
        """
        验证CSV文件格式
        
        Args:
            file_input: CSV文件路径（字符串）或文件对象（如Flask的FileStorage对象）
            required_columns: 必需的列名列表
            
        Returns:
            (是否有效, 错误信息, 数据框)
        """
        try:
            # 确定输入类型并获取文件名
            if isinstance(file_input, str):
                # 输入是文件路径字符串
                file_path = file_input
                filename = file_path
                is_file_object = False
            else:
                # 输入可能是文件对象
                file_path = None
                # 尝试获取文件名属性
                filename = getattr(file_input, 'filename', '')
                is_file_object = True
            
            # 确保filename是字符串
            if not isinstance(filename, str):
                try:
                    filename = str(filename)
                except Exception as e:
                    return False, f"无法获取文件名: {str(e)}", None
            
            # 检查文件扩展名
            try:
                if not filename.lower().endswith('.csv'):
                    return False, "文件格式不正确，请上传CSV文件(.csv)", None
            except AttributeError as e:
                return False, f"文件名格式错误: {str(e)}，文件名: {repr(filename)}", None
            except Exception as e:
                return False, f"检查文件扩展名时出错: {str(e)}", None
            
            # 检测文件编码并读取
            encodings = ['utf-8', 'gb18030', 'gbk']
            df = None
            used_encoding = None
            
            for encoding in encodings:
                try:
                    if is_file_object:
                        # 重置文件指针到开头（如果是文件对象）
                        if hasattr(file_input, 'seek'):
                            file_input.seek(0)
                        # 使用pandas读取文件对象
                        df = pd.read_csv(file_input, encoding=encoding)
                    else:
                        # 使用文件路径读取
                        df = pd.read_csv(file_path, encoding=encoding)
                    
                    used_encoding = encoding
                    break
                except UnicodeDecodeError:
                    continue
                except Exception as e:
                    # 如果是第一次尝试，继续尝试其他编码
                    if encoding == encodings[0]:
                        continue
                    else:
                        raise
            
            if df is None:
                return False, f"无法读取CSV文件，不支持的编码格式", None
            
            if df.empty:
                return False, "CSV文件为空", None
            
            # 如果没有指定必需列，则使用默认的库存列
            if required_columns is None:
                required_columns = ['商品名称', '仓库', '数量', '可销数']
            
            # 检查必需列是否存在
            missing_columns = []
            for col in required_columns:
                if col not in df.columns:
                    missing_columns.append(col)
            
            if missing_columns:
                return False, f"CSV文件缺少必需列: {', '.join(missing_columns)}", None
            
            # 验证数据类型和格式
            errors = []
            
            # 检查数量列是否为数值类型
            if '数量' in df.columns:
                for idx, value in enumerate(df['数量']):
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        errors.append(f"第{idx + 2}行数量格式不正确: {value}")
            
            # 检查可销数列是否为数值类型
            if '可销数' in df.columns:
                for idx, value in enumerate(df['可销数']):
                    try:
                        int(value)
                    except (ValueError, TypeError):
                        errors.append(f"第{idx + 2}行可销数格式不正确: {value}")
            
            # 检查商品名称和仓库不能为空
            if '商品名称' in df.columns:
                for idx, value in enumerate(df['商品名称']):
                    if pd.isna(value) or str(value).strip() == '':
                        errors.append(f"第{idx + 2}行商品名称不能为空")
            
            if '仓库' in df.columns:
                for idx, value in enumerate(df['仓库']):
                    if pd.isna(value) or str(value).strip() == '':
                        errors.append(f"第{idx + 2}行仓库不能为空")
            
            if errors:
                return False, "数据格式错误:\n" + "\n".join(errors), None
            
            # 重置文件指针（如果是文件对象），以便后续处理
            if is_file_object and hasattr(file_input, 'seek'):
                file_input.seek(0)
            
            return True, f"CSV文件格式验证通过 (编码: {used_encoding})", df
            
        except Exception as e:
            return False, f"读取CSV文件失败: {str(e)}", None

    @staticmethod
    def validate_file_extension(file_path: str, allowed_extensions: List[str]) -> Tuple[bool, str]:
        """
        验证文件扩展名
        
        Args:
            file_path: 文件路径
            allowed_extensions: 允许的扩展名列表 (e.g., ['.xlsx', '.xls'])
            
        Returns:
            (是否有效, 错误信息)
        """
        _, ext = os.path.splitext(file_path.lower())
        if ext not in allowed_extensions:
            allowed_str = ', '.join(allowed_extensions)
            return False, f"不支持的文件格式。允许的格式: {allowed_str}"
        return True, "扩展名验证通过"
    
    @staticmethod
    def validate_file_size(file_path: str, max_size_mb: int = 350) -> Tuple[bool, str]:
        """
        验证文件大小
        
        Args:
            file_path: 文件路径
            max_size_mb: 最大文件大小(MB)
            
        Returns:
            (是否有效, 错误信息)
        """
        try:
            file_size_bytes = os.path.getsize(file_path)
            file_size_mb = file_size_bytes / (1024 * 1024)
            
            if file_size_mb > max_size_mb:
                return False, f"文件过大 ({file_size_mb:.2f}MB)，最大允许 {max_size_mb}MB"
            
            return True, "文件大小验证通过"
        except OSError:
            return False, "无法获取文件大小"
