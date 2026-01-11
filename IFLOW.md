# iFlow 项目上下文文件

## ⚠️ 重要工作原则

### Git 操作原则
- **禁止主动执行 `git push`**：除非用户明确指示，否则不要将代码推送到远程仓库
- **只执行本地提交**：可以使用 `git add` 和 `git commit` 提交到本地仓库
- **等待用户指令**：所有推送到远程仓库的操作必须等待用户明确指令

### 任务执行原则
- **先分析后执行**：在执行任务之前，必须先分析用户的指令
- **不明确就问**：如果指令中有不明确的部分，不要猜测或假设，必须先向用户确认
- **避免创建文件**：不要主动创建文档文件（*.md）或 README 文件，除非明确要求

## 项目概述

**项目名称**: rongzao_server（荣造服务器）

**项目类型**: Flask Web 应用 - 电商数据分析与报表系统

**项目描述**:
这是一个基于 Flask 的电商数据分析平台，用于分析和管理电商订单数据。系统支持多渠道（抖音、天猫、有赞、京东）订单数据统计、商品管理、报表生成等功能。采用 SQLite 数据库存储，前端使用原生 JavaScript 和 CSS，支持响应式设计。

**主要技术栈**:
- **后端**: Python 3 + Flask 3.0.0
- **数据库**: SQLite
- **数据处理**: Pandas
- **Excel 处理**: openpyxl
- **认证**: PyJWT (JWT Token)
- **报表生成**: reportlab (PDF)
- **前端**: 原生 JavaScript + CSS + HTML
- **图表库**: ApexCharts (本地部署)

**项目架构**:
```
rongzao_server/
├── app.py                    # Flask 应用入口
├── config.py                 # 配置管理
├── database.py               # 数据库连接和初始化
├── routes.py                 # 页面路由注册
├── utils_common.py           # 通用工具函数
├── api/                      # API 模块
│   ├── analyse.py           # 数据分析 API
│   ├── analyse_by_product.py # 商品详情分析 API
│   ├── auth.py              # 认证 API
│   ├── dates.py             # 日期管理 API
│   ├── export.py            # 数据导出 API
│   ├── product_manage.py    # 商品管理 API
│   ├── report.py            # 报表生成 API
│   └── upload.py            # 文件上传 API
├── utils/                    # 工具模块
│   ├── auth.py              # 认证工具
│   └── operation_logger.py  # 操作日志
├── static/                   # 静态资源
│   ├── css/
│   │   └── style.css        # 样式文件
│   └── js/                  # JavaScript 文件
│       ├── analyse.js       # 数据分析页面逻辑
│       ├── analyse_by_product.js # 商品详情分析
│       ├── analyse_common.js # 数据分析通用逻辑
│       ├── apexcharts.min.js # 图表库
│       ├── auth.js          # 认证逻辑
│       ├── login.js         # 登录逻辑
│       ├── product_manage.js # 商品管理逻辑
│       ├── report.js        # 报表逻辑
│       └── upload.js        # 上传逻辑
├── templates/                # HTML 模板
│   ├── index.html           # 首页
│   ├── login.html           # 登录页
│   ├── analyse.html         # 数据分析页
│   ├── product_manage.html  # 商品管理页
│   ├── report.html          # 报表页
│   └── ...
├── fonts/                    # 字体文件
│   └── SimHei.ttf           # 黑体字体
├── operation_logs/           # 操作日志目录
├── analysis_debug/           # 调试脚本目录
├── .env                      # 环境变量配置（本地）
├── .env.example              # 环境变量配置示例
├── requirements.txt          # Python 依赖
├── rongzao.db                # SQLite 数据库
└── rongzao.service           # Systemd 服务配置
```

## 构建和运行

### 环境要求
- Python 3.x（推荐 Python 3.8+）
- pip（Python 包管理器）

### 本地开发环境

#### 1. 安装依赖
```bash
# 创建虚拟环境（推荐）
python3 -m venv .venv
source .venv/bin/activate

# 安装依赖（使用国内镜像加速）
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/
```

#### 2. 配置环境变量
```bash
# 复制环境变量示例文件
cp .env.example .env

# 编辑 .env 文件，设置必要的配置
# 必须设置：JWT_SECRET 和 SECRET_KEY
```

#### 3. 启动应用
```bash
# 方式一：直接运行
python3 app.py

# 方式二：使用虚拟环境
source .venv/bin/activate
python app.py
```

#### 4. 访问应用
- 开发环境端口：`8818`
- 访问地址：`http://localhost:8818`

**默认管理员账户**:
- 用户名：`zengxiao`
- 密码：`zeng`

### 服务器部署环境

#### 1. 服务器环境配置
```bash
# 创建 .ecs 标识文件（表示这是服务器环境）
touch .ecs

# 应用会自动使用生产环境配置
```

#### 2. 使用 Systemd 服务（推荐）
```bash
# 复制服务配置文件
cp rongzao.service.example rongzao.service

# 编辑服务配置，修改路径和用户
vim rongzao.service

# 安装服务
sudo cp rongzao.service /etc/systemd/system/

# 启动服务
sudo systemctl start rongzao
sudo systemctl enable rongzao

# 查看服务状态
sudo systemctl status rongzao
```

#### 3. 手动启动
```bash
# 激活虚拟环境
source .venv/bin/activate

# 启动应用（服务器环境）
python app.py
```

### 数据库初始化

首次运行时，应用会自动：
1. 创建 `users` 表（用户认证）
2. 创建默认管理员账户（`zengxiao` / `zeng`）

**手动初始化脚本**（可选）:
```bash
# 初始化商品信息
python3 init_product_info.py

# 数据库初始化
python3 db_init.py
```

### 常用命令

```bash
# 查看应用日志
tail -f logs/app.log

# 备份数据库
bash backup_db.sh

# 检查环境配置
bash check_env.sh

# 打包部署
bash package_for_deploy.sh
```

## 开发约定

### 代码规范

#### Python 代码
- 文件编码：UTF-8
- 文件头注释：`# -*- coding: utf-8 -*-`
- 函数命名：使用小写字母和下划线（snake_case）
- 类命名：使用大驼峰（PascalCase）
- 常量命名：使用大写字母和下划线（UPPER_CASE）

#### JavaScript 代码
- 函数命名：使用小驼峰（camelCase）
- 常量命名：使用大写字母和下划线（UPPER_CASE）
- 代码注释：使用 JSDoc 风格

#### 数据库命名
- 表名：使用大驼峰（PascalCase），如 `OrderDetails`, `ProductInfo`
- 字段名：使用小驼峰（camelCase），如 `productId`, `orderTime`

### API 设计规范

#### RESTful API
- 所有 API 路径以 `/api/` 开头
- 使用 HTTP 方法：GET（查询）、POST（创建/更新）、DELETE（删除）

#### 认证
- 使用 JWT Token 认证
- 受保护的 API 需要添加 `@token_required` 装饰器
- 管理员权限需要添加 `@admin_required` 装饰器

#### 响应格式
```python
# 成功响应
return jsonify({
    'success': True,
    'data': {...}
})

# 错误响应
return jsonify({
    'success': False,
    'error': '错误信息'
}), 500
```

### 数据处理规范

#### 数据过滤
- 上传 Excel 时，过滤"金蝶对接"记录
- 使用 Pandas DataFrame 进行数据处理
- 计算记录哈希值用于去重

#### 数据统计
- 按商品类型和渠道统计订单数据
- 计算客单价：`渠道让利后金额 / 渠道订单数`
- 客单价显示：四舍五入取整

### 前端开发规范

#### 页面结构
- 使用 Semantic HTML
- 响应式设计（PC + 移动端）
- 使用 Flexbox 布局

#### JavaScript 模块化
- 每个页面对应一个 JS 文件
- 公共逻辑放在 `analyse_common.js`
- 使用事件委托处理动态元素

#### 样式规范
- 使用 CSS 类名控制样式
- 颜色使用十六进制值
- 字体大小使用 px 单位

### Git 提交规范
- 不主动提交远程仓库；除非用户明确指示git push

#### 提交信息格式
```
<类型>: <简短描述>

<详细说明（可选）>
```

#### 类型说明
- `feat`: 新功能
- `fix`: 修复 bug
- `docs`: 文档更新
- `style`: 代码格式调整
- `refactor`: 重构
- `test`: 测试相关
- `chore`: 构建/工具相关

#### 示例
```
feat: 在数据分析表格中添加渠道客单价显示

- 后端：为每个渠道单独统计让利后金额
- 前端：在抖音、天猫、京东三列显示格式为"订单数\t¥客单价"
- 客单价计算公式：渠道让利后金额 / 渠道订单数
```

### 环境变量管理

#### 必须设置的环境变量
- `JWT_SECRET`: JWT 签名密钥（生产环境必须设置）
- `SECRET_KEY`: Flask 密钥（生产环境必须设置）

#### 可选环境变量
- `FLASK_ENV`: Flask 环境（development/production）
- `PORT`: 服务器端口（默认 8818）
- `HOST`: 服务器主机（默认 0.0.0.0）

#### 安全注意事项
- 不要将 `.env` 文件提交到 Git
- 生产环境使用强随机密钥
- 定期更换密钥（建议每季度）

### 测试规范

#### 本地测试
- 在提交代码前，确保功能正常
- 测试文件上传、数据导出等关键功能
- 检查控制台是否有错误信息

#### 服务器部署前检查
- [ ] 所有功能测试通过
- [ ] 环境变量配置正确
- [ ] 数据库备份完成
- [ ] 日志文件权限正确
- [ ] 服务能正常启动

### 错误处理

#### Python 错误处理
```python
try:
    # 业务逻辑
    pass
except Exception as e:
    print(f'处理数据时出错: {str(e)}')
    import traceback
    traceback.print_exc()
    return jsonify({'error': str(e)}), 500
```

#### JavaScript 错误处理
```javascript
try {
    // 业务逻辑
} catch (error) {
    console.error('发生错误:', error);
    alert('操作失败，请重试');
}
```

### 日志记录

#### 操作日志
- 记录用户操作（上传、导出、删除等）
- 日志文件路径：`operation_logs/`
- 日志格式：`[时间] [用户] [操作] [详情]`

#### 应用日志
- 日志文件路径：`logs/app.log`
- 日志级别：DEBUG, INFO, WARNING, ERROR, CRITICAL

## 重要提示

### Python 版本说明
- **重要**: 用户电脑只安装了 Python 3，没有 Python 2
- **执行 Python 命令时**:
  - 使用 `python3` 或 `pip3`
  - 或先激活虚拟环境：`source .venv/bin/activate`，然后使用 `python` 和 `pip`

### pip 安装加速
- 使用国内镜像源（如阿里云镜像）加速安装过程
- 镜像地址：`https://mirrors.aliyun.com/pypi/simple/`
- 安装命令：`pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/`

### 任务执行前确认
- 在执行任务之前，必须先分析用户的指令
- 如果指令中有不明确的部分，不要猜测或假设
- 必须先向用户确认清楚后再执行

### 数据库操作注意事项
- 数据库文件：`rongzao.db`
- 删除数据前先备份
- 使用事务确保数据一致性
- 大批量操作时考虑性能

### 前端文件修改后测试
- 修改 `.html`、`.css`、`.js` 文件后，需要刷新页面查看效果
- 建议使用浏览器开发者工具检查控制台错误
- 移动端测试使用浏览器开发者工具的设备模拟功能

## 项目特色功能

### 1. 数据分析
- 支持按日期范围筛选数据
- 按商品类型和渠道（抖音、天猫、有赞、京东）统计
- 显示客单价（四舍五入取整）
- 支持表格排序
- 点击行显示商品详情（销售曲线、渠道分布）

### 2. 商品管理
- 商品信息增删改查
- 商品分类管理
- 商品审核功能

### 3. 报表生成
- 支持生成周报、月报
- PDF 导出功能
- 自定义日期范围

### 4. 文件上传
- 支持 Excel 文件上传
- 自动过滤"金蝶对接"记录
- 记录去重（基于哈希值）
- 上传后自动刷新页面

### 5. 用户认证
- JWT Token 认证
- 角色权限管理（admin/user）
- 密码加密存储（bcrypt）

### 6. 响应式设计
- PC 端和移动端自适应
- 移动端使用卡片布局
- 触摸友好的交互

## 常见问题

### 1. 如何重置管理员密码？
编辑 `database.py`，修改 `init_user_table()` 函数中的密码，然后重新运行应用。

### 2. 如何修改端口？
- 方式一：修改 `app.py` 中的 `port` 变量
- 方式二：设置环境变量 `PORT`

### 3. 如何备份数据库？
```bash
# 备份数据库
cp rongzao.db rongzao.db.backup

# 或使用备份脚本
bash backup_db.sh
```

### 4. 如何查看应用日志？
```bash
# 查看应用日志
tail -f logs/app.log

# 查看操作日志
tail -f operation_logs/*.log
```

### 5. 如何清理缓存？
```bash
# 清理 Python 缓存
find . -type d -name __pycache__ -exec rm -rf {} +

# 清理浏览器缓存
# 在浏览器中按 Ctrl+Shift+Delete
```

## 联系方式

- 项目仓库：`git@github.com:zengxiao29/rongzao-server.git`
- 部署文档：`DEPLOYMENT.md`
- 部署前检查：`PRE_DEPLOY_CHECKLIST.md`

---

**最后更新**: 2026年1月8日
**版本**: 1.0.0
**维护者**: iFlow CLI