# 阿里云 ECS 部署准备清单

## 1. 项目文件清单

### 必需文件
- ✅ `app.py` - Flask 应用主文件
- ✅ `database.py` - 数据库连接模块
- ✅ `routes.py` - 路由注册
- ✅ `utils.py` - 工具函数
- ✅ `requirements.txt` - Python 依赖
- ✅ `.gitignore` - Git 忽略规则
- ✅ `api/` - API 模块目录
  - `analyse.py` - 数据分析 API
  - `config.py` - 配置管理
  - `dates.py` - 日期管理
  - `export.py` - 导出功能
  - `stats.py` - 统计功能
  - `upload.py` - 上传功能
  - `metabase.py` - Metabase 集成
- ✅ `static/` - 静态文件目录
  - `css/style.css` - 样式文件
  - `js/` - JavaScript 文件
- ✅ `templates/` - HTML 模板目录
- ✅ `rongzao.db` - SQLite 数据库（4.7MB）

### 可选文件
- `db_init.py` - 数据库初始化脚本
- `init_product_info.py` - 商品信息初始化脚本
- `tab_config.json` - Tab 配置（已迁移到数据库）
- `excel/` - Excel 处理脚本

## 2. 依赖检查

### 当前 requirements.txt
```
Flask==3.0.0
reportlab==4.0.7
```

### 需要补充的依赖
```
pandas
openpyxl
PyJWT
```

### 更新后的 requirements.txt
```
Flask==3.0.0
reportlab==4.0.7
pandas
openpyxl
PyJWT
```

## 3. 数据库准备

### 数据库文件
- 文件名：`rongzao.db`
- 大小：4.7MB
- 位置：项目根目录
- 包含数据：
  - OrderDetails 订单详情
  - ProductInfo 商品信息
  - CategoryInfo 分类信息

### 数据库表结构
1. **OrderDetails** - 订单详情表
2. **ProductInfo** - 商品信息表（包含 reviewed 字段）
3. **CategoryInfo** - 分类信息表

## 4. 配置文件准备

### 需要创建的配置文件

#### 4.1 生产环境配置（可选）
创建 `config.py`：
```python
import os

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-here')
    DEBUG = False
    HOST = '0.0.0.0'
    PORT = 5001

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
```

#### 4.2 Systemd 服务文件（用于服务器自动启动）
创建 `rongzao.service`：
```ini
[Unit]
Description=Rongzao Flask Application
After=network.target

[Service]
User=your-username
WorkingDirectory=/path/to/rongzao_server
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python app.py
Restart=always

[Install]
WantedBy=multi-user.target
```

#### 4.3 Nginx 配置（可选，用于反向代理）
创建 `nginx.conf`：
```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:5001;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
    }

    location /static {
        alias /path/to/rongzao_server/static;
    }
}
```

## 5. 部署步骤

### 5.1 本地准备工作

1. **更新 requirements.txt**
2. **打包项目文件**
3. **备份数据库**
4. **测试本地运行**

### 5.2 服务器端准备工作

1. **安装 Python 3**
2. **安装依赖**
3. **上传文件**
4. **配置环境**
5. **启动服务**

## 6. 文件上传方式

### 方式一：使用 SCP
```bash
scp -r rongzao_server user@your-server:/path/to/destination/
scp rongzao.db user@your-server:/path/to/rongzao_server/
```

### 方式二：使用 Git
```bash
# 在服务器上
git clone git@github.com:zengxiao29/rongzao-server.git
# 然后上传数据库文件
scp rongzao.db user@your-server:/path/to/rongzao-server/
```

### 方式三：使用 FTP/SFTP 工具
- FileZilla
- WinSCP
- Cyberduck

## 7. 安全注意事项

### 7.1 需要修改的配置
- ✅ Flask SECRET_KEY
- ✅ 数据库文件权限
- ✅ 日志文件路径
- ✅ 上传文件大小限制

### 7.2 防火墙配置
- 开放端口：5001（或使用 Nginx 代理时开放 80/443）
- 限制数据库文件访问

## 8. 监控和维护

### 8.1 日志管理
- 应用日志
- 错误日志
- 访问日志

### 8.2 数据备份
- 定期备份数据库
- 备份上传的文件

## 9. 快速部署命令

### 在服务器上执行：

```bash
# 1. 安装 Python 3 和 pip
sudo apt update
sudo apt install python3 python3-pip python3-venv

# 2. 克隆代码
cd /path/to/your/project
git clone git@github.com:zengxiao29/rongzao-server.git
cd rongzao-server

# 3. 创建虚拟环境
python3 -m venv venv
source venv/bin/activate

# 4. 安装依赖
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 5. 创建 .ecs 标识文件（表示这是服务器环境）
touch .ecs

# 6. 部署
bash deploy.sh
```

### 本地开发环境（Mac）

```bash
# 直接运行
python3 app.py
```

### 端口说明

- **开发环境**：5001 端口（本地 Mac，无 .ecs 文件）
- **服务器环境**：80 端口（Ubuntu 服务器，有 .ecs 文件）
- **自动切换**：通过检查项目根目录是否存在 `.ecs` 文件
  - 开发环境：不创建 `.ecs` 文件
  - 服务器环境：手动创建 `.ecs` 文件

## 10. 检查清单

部署前检查：
- [ ] requirements.txt 已更新
- [ ] 数据库文件已备份
- [ ] 配置文件已准备
- [ ] 测试本地运行正常
- [ ] 了解服务器登录信息
- [ ] 准备好上传方式

部署后检查：
- [ ] 应用能正常启动
- [ ] 所有页面能正常访问
- [ ] 文件上传功能正常
- [ ] 数据导出功能正常
- [ ] 数据库查询正常