#!/bin/bash

# 数据库备份脚本
# 每天备份所有 .db 文件到 db_backup 目录
# 保留策略：
#   - 近7天：全量保留
#   - 7-21天：隔一天保留
#   - 超过21天：不保留

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
    backup_file="$BACKUP_DIR/${db_name}.backup_$DATE.zip"

    echo "正在备份: $db_name"
    # 使用 xz 压缩，压缩率高
    xz -c "$db_file" > "$backup_file"

    if [ $? -eq 0 ]; then
        echo "备份成功: $backup_file"
    else
        echo "备份失败: $db_name"
        # 清理失败的压缩文件
        rm -f "$backup_file"
    fi
done

# 实现保留策略
echo "开始清理旧备份文件 - $DATE"

# 获取当前时间戳（秒）
CURRENT_TIME=$(date +%s)

# 遍历所有备份文件
find "$BACKUP_DIR" -name "*.backup_*.zip" -type f | while read -r backup_file; do
    # 从文件名中提取日期（格式：YYYYMMDD_HHMMSS）
    file_date=$(basename "$backup_file" | sed -E 's/.*\.backup_([0-9]{8})_[0-9]{6}\.zip/\1/')
    
    # 计算文件日期的时间戳
    file_time=$(date -d "${file_date:0:4}-${file_date:4:2}-${file_date:6:2}" +%s 2>/dev/null)
    
    if [ -z "$file_time" ]; then
        echo "无法解析文件日期: $backup_file"
        continue
    fi
    
    # 计算文件天数
    days_diff=$(( (CURRENT_TIME - file_time) / 86400 ))
    
    # 判断是否需要保留
    if [ $days_diff -le 7 ]; then
        # 近7天：全量保留
        echo "保留（近7天）: $backup_file"
    elif [ $days_diff -le 21 ]; then
        # 7-21天：隔一天保留
        # 使用天数来判断是否保留（偶数天保留，奇数天删除，或反之）
        if [ $((days_diff % 2)) -eq 0 ]; then
            echo "保留（7-21天，隔一天）: $backup_file"
        else
            echo "删除（7-21天，隔一天）: $backup_file"
            rm -f "$backup_file"
        fi
    else
        # 超过21天：不保留
        echo "删除（超过21天）: $backup_file"
        rm -f "$backup_file"
    fi
done

echo "数据库备份完成 - $DATE"