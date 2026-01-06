#!/bin/bash

# 数据库备份脚本
# 每天备份所有 .db 文件到 db_backup 目录

# 定义变量
DB_DIR="/root/rongzao-server"
BACKUP_DIR="/root/rongzao-server/db_backup"
BACKUP_LOG="$BACKUP_DIR/backup_db.log"
DATE=$(date +%Y%m%d_%H%M%S)

# 创建备份目录（如果不存在）
mkdir -p "$BACKUP_DIR"

# 查找并备份所有 .db 文件
echo "开始备份数据库文件 - $DATE"

find "$DB_DIR" -maxdepth 1 -name "*.db" -type f | while read -r db_file; do
    db_name=$(basename "$db_file")
    backup_file="$BACKUP_DIR/${db_name}.backup_$DATE"

    echo "正在备份: $db_name"
    cp "$db_file" "$backup_file"

    if [ $? -eq 0 ]; then
        echo "备份成功: $backup_file"
    else
        echo "备份失败: $db_name"
    fi
done

# 删除 30 天前的备份文件（保留最近 30 天）
find "$BACKUP_DIR" -name "*.backup_*" -type f -mtime +30 -delete

echo "数据库备份完成 - $DATE"