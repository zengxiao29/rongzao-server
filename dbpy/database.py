# -*- coding: utf-8 -*-
import sqlcipher3 as sqlite3  # 使用SQLCipher加密版本
import hashlib
import os
import pandas as pd
import bcrypt

# 数据库文件路径：指向项目根目录的rongzao.db
# os.path.dirname(__file__) 是 dbpy 目录
# os.path.dirname(os.path.dirname(__file__)) 是项目根目录
PROJECT_ROOT = os.path.dirname(os.path.dirname(__file__))
DB_PATH = os.path.join(PROJECT_ROOT, 'rongzao.db')

# 数据库加密配置
DB_ENCRYPTION_KEY = os.environ.get('DB_ENCRYPTION_KEY')

# 加密参数配置（与DB Browser兼容）
SQLCIPHER_COMPATIBILITY = 4  # SQLCipher 4.x 兼容
SQLCIPHER_KDF_ITER = 256000  # 高强度密钥派生迭代次数

# 简单数据库连接池
class SimpleConnectionPool:
    """简单的数据库连接池，最大连接数5"""
    
    def __init__(self, max_connections=5):
        self.max_connections = max_connections
        self.available_connections = []  # 可用连接列表
        self.active_connections = 0      # 活跃连接数
        self._lock = None  # 单线程环境，暂不需要锁
    
    def get_connection(self):
        """从连接池获取连接"""
        if self.available_connections:
            # 有可用连接，直接返回
            conn = self.available_connections.pop()
            # 确保连接仍然有效
            try:
                conn.execute('SELECT 1')
                return conn
            except sqlite3.ProgrammingError:
                # 连接已关闭或无效，创建新连接
                self.active_connections -= 1
                return self._create_new_connection()
        
        # 没有可用连接，检查是否达到最大连接数
        if self.active_connections < self.max_connections:
            return self._create_new_connection()
        else:
            # 达到最大连接数，等待或创建新连接（简化：直接创建）
            # 在实际生产环境中应该实现等待机制
            print(f"警告: 达到最大连接数({self.max_connections})，创建额外连接")
            return self._create_new_connection(False)  # 不计数
    
    def return_connection(self, conn):
        """归还连接到连接池"""
        if conn and self.active_connections <= self.max_connections:
            # 重置连接状态
            try:
                conn.rollback()  # 回滚任何未提交的事务
                self.available_connections.append(conn)
            except:
                # 连接可能已损坏，关闭它
                conn.close()
                self.active_connections -= 1
        else:
            # 超过最大连接数或连接无效，直接关闭
            if conn:
                conn.close()
    
    def _create_new_connection(self, count=True):
        """创建新数据库连接（支持SQLCipher加密）"""
        conn = sqlite3.connect(DB_PATH)
        
        # 如果设置了加密密钥，则启用SQLCipher加密
        if DB_ENCRYPTION_KEY:
            conn.execute(f"PRAGMA key='{DB_ENCRYPTION_KEY}'")
            conn.execute(f'PRAGMA cipher_compatibility={SQLCIPHER_COMPATIBILITY}')
            conn.execute(f'PRAGMA kdf_iter={SQLCIPHER_KDF_ITER}')
        
        conn.row_factory = sqlite3.Row
        conn.execute('PRAGMA foreign_keys = ON')
        
        if count:
            self.active_connections += 1
        return conn
    
    def close_all(self):
        """关闭所有连接"""
        for conn in self.available_connections:
            try:
                conn.close()
            except:
                pass
        self.available_connections = []
        self.active_connections = 0

# 全局连接池实例
_connection_pool = SimpleConnectionPool()


def get_db_connection():
    """获取数据库连接（从连接池）"""
    return _connection_pool.get_connection()

def release_db_connection(conn):
    """归还数据库连接到连接池"""
    _connection_pool.return_connection(conn)

def close_db_connection(conn):
    """关闭数据库连接（兼容旧代码，实际归还到连接池）"""
    _connection_pool.return_connection(conn)


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