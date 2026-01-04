#!/bin/bash

# 生产环境启动脚本
# 使用方法：bash start_production.sh

set -e

echo "=========================================="
echo "启动生产环境服务"
echo "=========================================="

# 设置生产环境变量
export FLASK_ENV=production
export SECRET_KEY="${SECRET_KEY:-$(openssl rand -hex 32)}"

echo "环境变量："
echo "  FLASK_ENV=$FLASK_ENV"
echo "  SECRET_KEY=*** (已生成)"

# 检查端口 80 是否可用
echo ""
echo "检查端口 80..."
if lsof -Pi :80 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "错误: 端口 80 已被占用"
    echo "占用进程："
    lsof -i :80
    exit 1
else
    echo "端口 80 可用"
fi

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
echo "启动 Flask 应用（端口 80）..."
nohup python app.py > logs/app.log 2>&1 &
APP_PID=$!

echo ""
echo "=========================================="
echo "生产环境启动完成！"
echo "=========================================="
echo ""
echo "访问地址: http://your-server-ip"
echo "日志文件: logs/app.log"
echo "应用 PID: $APP_PID"
echo ""
echo "常用命令："
echo "  查看日志: tail -f logs/app.log"
echo "  停止服务: kill $APP_PID"
echo "  重启服务: bash start_production.sh"
echo ""
echo "注意：如果使用 Nginx 反向代理，请配置 Nginx"
echo "=========================================="