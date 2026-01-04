#!/bin/bash

# 阿里云 ECS 快速部署脚本
# 使用方法：bash deploy.sh

set -e

echo "=========================================="
echo "开始部署 Rongzao 服务器"
echo "=========================================="

# 1. 检查 Python 版本
echo "步骤 1: 检查 Python 版本..."
python3 --version
if [ $? -ne 0 ]; then
    echo "错误: 未找到 Python 3，请先安装 Python 3"
    exit 1
fi

# 2. 创建虚拟环境
echo "步骤 2: 创建虚拟环境..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "虚拟环境创建成功"
else
    echo "虚拟环境已存在"
fi

# 3. 激活虚拟环境
echo "步骤 3: 激活虚拟环境..."
source venv/bin/activate

# 4. 升级 pip
echo "步骤 4: 升级 pip..."
pip install --upgrade pip -i https://mirrors.aliyun.com/pypi/simple/

# 5. 安装依赖
echo "步骤 5: 安装依赖..."
pip install -r requirements.txt -i https://mirrors.aliyun.com/pypi/simple/

# 6. 检查数据库文件
echo "步骤 6: 检查数据库文件..."
if [ ! -f "rongzao.db" ]; then
    echo "警告: 未找到数据库文件 rongzao.db"
    echo "请确保数据库文件已上传到项目目录"
else
    echo "数据库文件存在"
    ls -lh rongzao.db
fi

# 7. 设置文件权限
echo "步骤 7: 设置文件权限..."
chmod 644 rongzao.db
chmod -R 755 static templates

# 8. 创建日志目录
echo "步骤 8: 创建日志目录..."
mkdir -p logs

# 9. 测试启动
echo "步骤 9: 测试启动应用..."
echo "应用将在后台启动，使用以下命令查看日志："
echo "  tail -f logs/app.log"
echo ""

# 检查是否为生产环境
if [ "$FLASK_ENV" = "production" ]; then
    echo "生产环境模式：使用端口 80"
    PORT=80
else
    echo "开发环境模式：使用端口 5001"
    PORT=5001
fi

# 使用 nohup 在后台启动应用
nohup python app.py > logs/app.log 2>&1 &
APP_PID=$!

echo "应用已启动，PID: $APP_PID"
echo "=========================================="
echo "部署完成！"
echo "=========================================="
echo ""
echo "访问地址: http://localhost:5001"
echo "日志文件: logs/app.log"
echo ""
echo "常用命令："
echo "  查看日志: tail -f logs/app.log"
echo "  停止应用: kill $APP_PID"
echo "  重启应用: bash deploy.sh"
echo ""