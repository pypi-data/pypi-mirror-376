#!/bin/bash

# 检查必要参数
if [ $# -ne 2 ]; then
    echo "使用方法: $0 <license文件路径> <项目根目录>"
    exit 1
fi

LICENSE_FILE=$1
PROJECT_ROOT=$2

# 验证输入文件是否存在
if [ ! -f "$LICENSE_FILE" ]; then
    echo "错误: 许可文件 '$LICENSE_FILE' 不存在"
    exit 1
fi

# 验证项目目录是否存在
if [ ! -d "$PROJECT_ROOT" ]; then
    echo "错误: 项目目录 '$PROJECT_ROOT' 不存在"
    exit 1
fi

# 遍历所有Python文件并添加许可声明
find "$PROJECT_ROOT" -type f -name "*.py" | while read file; do
    # 创建备份文件
    # cp "$file" "${file}.bak"

    # 检查文件是否已经包含许可声明（简单检查）
    if ! grep -q "Copyright" "$file"; then
        # 将许可内容添加到文件开头
        cat "$LICENSE_FILE" "$file" > "${file}.tmp"

        # 替换临时文件
        mv "${file}.tmp" "$file"

        echo "已为 $file 添加许可声明"
    else
        echo "跳过 $file（已包含许可声明）"
    fi
done