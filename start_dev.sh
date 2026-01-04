#!/bin/bash

# 本地开发环境启动脚本
# 使用方法：bash start_dev.sh

set -e

echo "=========================================="
echo "启动开发环境服务"
echo "=========================================="

# 设置开发环境变量
export FLASK_ENV=development

echo "环境变量："
echo "  FLASK_ENV=$FLASK_ENV"

# 检查虚拟环境
echo ""
echo "检查虚拟环境..."
if [ ! -d "venv" ]; then
    echo "错误: 虚拟环境不存在"
    echo "请先运行: bash deploy.sh"
    exit 1
fi

# 激活虚拟环境
source venv/bin/activate

# 创建日志目录
mkdir -p logs

# 启动应用
echo ""
echo "启动 Flask 应用（端口 5001）..."
echo "按 Ctrl+C 停止应用"
echo ""

python app.py