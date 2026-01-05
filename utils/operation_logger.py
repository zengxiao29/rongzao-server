# -*- coding: utf-8 -*-
import os
import json
from datetime import datetime, timedelta
from flask import request


class OperationLogger:
    """数据库操作日志记录器"""
    
    def __init__(self, log_dir='operation_logs'):
        """初始化日志记录器
        
        Args:
            log_dir: 日志目录名称
        """
        self.log_dir = log_dir
        self._ensure_log_dir()
    
    def _ensure_log_dir(self):
        """确保日志目录存在"""
        if not os.path.exists(self.log_dir):
            os.makedirs(self.log_dir)
    
    def _get_log_file_path(self, date=None):
        """获取日志文件路径
        
        Args:
            date: 日期对象，如果为None则使用当前日期
        
        Returns:
            日志文件的完整路径
        """
        if date is None:
            date = datetime.now()
        return os.path.join(self.log_dir, date.strftime('%Y-%m-%d.log'))
    
    def _cleanup_old_logs(self):
        """清理超过30天的日志文件"""
        cutoff_date = datetime.now() - timedelta(days=30)
        
        if not os.path.exists(self.log_dir):
            return
        
        for filename in os.listdir(self.log_dir):
            if filename.endswith('.log'):
                try:
                    # 从文件名中提取日期
                    date_str = filename.replace('.log', '')
                    file_date = datetime.strptime(date_str, '%Y-%m-%d')
                    
                    # 如果文件日期超过30天，删除它
                    if file_date < cutoff_date:
                        file_path = os.path.join(self.log_dir, filename)
                        os.remove(file_path)
                        print(f'已删除旧日志文件: {filename}')
                except (ValueError, OSError) as e:
                    print(f'清理日志文件失败 {filename}: {str(e)}')
    
    def _get_client_ip(self):
        """获取客户端IP地址"""
        if request:
            # 检查是否有代理头
            if 'X-Forwarded-For' in request.headers:
                return request.headers.get('X-Forwarded-For', '').split(',')[0].strip()
            if 'X-Real-IP' in request.headers:
                return request.headers.get('X-Real-IP', '')
            return request.remote_addr
        return 'unknown'
    
    def log(self, username, role, operation_type, detail=None, result='success', error_message=None):
        """记录操作日志
        
        Args:
            username: 用户名
            role: 用户角色
            operation_type: 操作类型
            detail: 操作详情（字典或字符串）
            result: 操作结果（success/failed）
            error_message: 错误信息（如果失败）
        """
        try:
            # 清理旧日志
            self._cleanup_old_logs()
            
            # 获取当前时间和IP
            timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            ip_address = self._get_client_ip()
            
            # 格式化详情
            if detail and isinstance(detail, dict):
                detail_str = json.dumps(detail, ensure_ascii=False)
            elif detail:
                detail_str = str(detail)
            else:
                detail_str = ''
            
            # 构建日志消息
            log_parts = [
                f'[{timestamp}]',
                f'用户: {username} ({role})',
                f'操作: {operation_type}'
            ]
            
            if detail_str:
                log_parts.append(f'详情: {detail_str}')
            
            log_parts.append(f'结果: {result}')
            log_parts.append(f'IP: {ip_address}')
            
            if error_message:
                log_parts.append(f'错误: {error_message}')
            
            log_message = ' | '.join(log_parts)
            
            # 写入日志文件
            log_file_path = self._get_log_file_path()
            with open(log_file_path, 'a', encoding='utf-8') as f:
                f.write(log_message + '\n')
            
        except Exception as e:
            print(f'写入操作日志失败: {str(e)}')


# 创建全局日志记录器实例
operation_logger = OperationLogger()


def log_operation(username, role, operation_type, detail=None, result='success', error_message=None):
    """记录操作日志的便捷函数
    
    Args:
        username: 用户名
        role: 用户角色
        operation_type: 操作类型
        detail: 操作详情（字典或字符串）
        result: 操作结果（success/failed）
        error_message: 错误信息（如果失败）
    """
    operation_logger.log(username, role, operation_type, detail, result, error_message)