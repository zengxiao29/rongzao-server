#!/bin/bash

# 打包部署脚本
# 使用方法：bash package_for_deploy.sh

set -e

echo "=========================================="
echo "打包部署文件"
echo "=========================================="

# 定义版本号
VERSION=$(date +%Y%m%d-%H%M%S)
PACKAGE_NAME="rongzao-server-${VERSION}.tar.gz"

# 创建临时目录
TEMP_DIR="/tmp/rongzao-deploy-${VERSION}"
mkdir -p "$TEMP_DIR"

echo "步骤 1: 复制项目文件..."
# 复制项目文件
cp -r api "$TEMP_DIR/"
cp -r static "$TEMP_DIR/"
cp -r templates "$TEMP_DIR/"
cp *.py "$TEMP_DIR/"
cp requirements.txt "$TEMP_DIR/"
cp .gitignore "$TEMP_DIR/"
cp deploy.sh "$TEMP_DIR/"
cp check_env.sh "$TEMP_DIR/"

echo "步骤 2: 复制配置文件..."
cp config.py "$TEMP_DIR/"
cp nginx.conf.example "$TEMP_DIR/"
cp rongzao.service.example "$TEMP_DIR/"

echo "步骤 3: 复制数据库文件..."
cp rongzao.db "$TEMP_DIR/"

echo "步骤 4: 创建必要的目录..."
mkdir -p "$TEMP_DIR/logs"
mkdir -p "$TEMP_DIR/uploads"

echo "步骤 5: 创建部署说明..."
cat > "$TEMP_DIR/README.md" << EOF
# Rongzao 服务器部署包

版本: ${VERSION}
打包时间: $(date)

## 快速部署

1. 上传此包到服务器
2. 解压: tar -xzf ${PACKAGE_NAME}
3. 进入目录: cd rongzao-server-${VERSION}
4. 运行检查: bash check_env.sh
5. 运行部署: bash deploy.sh

## 文件说明

- \`app.py\` - Flask 应用主文件
- \`config.py\` - 配置文件
- \`rongzao.db\` - SQLite 数据库
- \`requirements.txt\` - Python 依赖
- \`deploy.sh\` - 自动部署脚本
- \`check_env.sh\` - 环境检查脚本
- \`api/\` - API 模块
- \`static/\` - 静态文件
- \`templates/\` - HTML 模板
- \`nginx.conf.example\` - Nginx 配置示例
- \`rongzao.service.example\` - Systemd 服务配置示例

## 访问地址

- 应用地址: http://your-server-ip:5001
- 主页: http://your-server-ip:5001/

## 注意事项

1. 确保 Python 3 已安装
2. 确保端口 5001 可用
3. 数据库文件权限设置为 644
4. 建议使用 Nginx 反向代理
5. 定期备份数据库文件

## 维护

- 查看日志: tail -f logs/app.log
- 重启应用: kill \$(cat logs/app.pid) && bash deploy.sh
- 备份数据: cp rongzao.db rongzao.db.backup
EOF

echo "步骤 6: 打包..."
cd /tmp
tar -czf "$PACKAGE_NAME" "rongzao-deploy-${VERSION}"

echo "步骤 7: 移动到当前目录..."
mv "$PACKAGE_NAME" "$OLDPWD"

echo "步骤 8: 清理临时目录..."
rm -rf "$TEMP_DIR"

echo ""
echo "=========================================="
echo "打包完成！"
echo "=========================================="
echo ""
echo "包文件: $PACKAGE_NAME"
echo "大小: $(du -h "$PACKAGE_NAME" | cut -f1)"
echo "位置: $(pwd)"
echo ""
echo "上传命令示例:"
echo "  scp $PACKAGE_NAME user@your-server:/tmp/"
echo ""
echo "服务器解压命令:"
echo "  cd /path/to/deploy"
echo "  tar -xzf /tmp/$PACKAGE_NAME"
echo "  cd rongzao-deploy-${VERSION}"
echo "  bash deploy.sh"
echo ""