#!/bin/bash

# 环境检查脚本
# 使用方法：bash check_env.sh

echo "=========================================="
echo "环境检查"
echo "=========================================="

# 1. 检查 Python 版本
echo "1. Python 版本:"
python3 --version
if [ $? -ne 0 ]; then
    echo "   ❌ 未找到 Python 3"
else
    echo "   ✅ Python 3 已安装"
fi

# 2. 检查 pip
echo ""
echo "2. pip 版本:"
pip3 --version
if [ $? -ne 0 ]; then
    echo "   ❌ 未找到 pip3"
else
    echo "   ✅ pip3 已安装"
fi

# 3. 检查虚拟环境
echo ""
echo "3. 虚拟环境:"
if [ -d "venv" ]; then
    echo "   ✅ 虚拟环境已存在"
else
    echo "   ❌ 虚拟环境不存在"
fi

# 4. 检查数据库文件
echo ""
echo "4. 数据库文件:"
if [ -f "rongzao.db" ]; then
    echo "   ✅ 数据库文件存在"
    ls -lh rongzao.db
else
    echo "   ❌ 数据库文件不存在"
fi

# 5. 检查依赖文件
echo ""
echo "5. 依赖文件:"
if [ -f "requirements.txt" ]; then
    echo "   ✅ requirements.txt 存在"
    echo "   内容:"
    cat requirements.txt
else
    echo "   ❌ requirements.txt 不存在"
fi

# 6. 检查端口占用
echo ""
echo "6. 端口 5001 占用情况:"
if lsof -Pi :5001 -sTCP:LISTEN -t >/dev/null 2>&1; then
    echo "   ⚠️  端口 5001 已被占用"
    lsof -i :5001
else
    echo "   ✅ 端口 5001 可用"
fi

# 7. 检查磁盘空间
echo ""
echo "7. 磁盘空间:"
df -h . | tail -1

# 8. 检查内存
echo ""
echo "8. 可用内存:"
free -h | grep Mem

echo ""
echo "=========================================="
echo "检查完成"
echo "=========================================="