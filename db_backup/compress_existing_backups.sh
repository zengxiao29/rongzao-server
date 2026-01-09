#!/bin/bash

# 压缩现有的未压缩数据库备份文件

BACKUP_DIR="/root/rongzao-server/db_backup"
DATE=$(date +%Y%m%d_%H%M%S)

echo "开始压缩现有的未压缩备份文件 - $DATE"

# 查找所有未压缩的备份文件（.backup_YYYYMMDD_HHMMSS 格式，没有 .zip 扩展名）
find "$BACKUP_DIR" -name "*.backup_*" -type f ! -name "*.zip" | while read -r backup_file; do
    echo "正在压缩: $backup_file"
    
    # 使用 xz 压缩，压缩率高
    xz -c "$backup_file" > "${backup_file}.zip"
    
    if [ $? -eq 0 ]; then
        echo "压缩成功: ${backup_file}.zip"
        
        # 验证压缩文件
        if [ -s "${backup_file}.zip" ]; then
            echo "验证通过，删除原文件: $backup_file"
            rm -f "$backup_file"
        else
            echo "压缩文件为空，保留原文件: $backup_file"
            rm -f "${backup_file}.zip"
        fi
    else
        echo "压缩失败: $backup_file"
        # 清理失败的压缩文件
        rm -f "${backup_file}.zip"
    fi
done

echo "压缩完成 - $DATE"