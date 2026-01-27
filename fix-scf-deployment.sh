#!/bin/bash

# SCF 云函数部署修复脚本
echo "🔧 SCF 云函数部署修复脚本"
echo "=========================="

# 1. 检查并修复启动脚本权限
echo "1. 检查启动脚本..."
if [ -f "scf_bootstrap" ]; then
    chmod +x scf_bootstrap
    echo "✅ 启动脚本权限已修复"
else
    echo "❌ 未找到 scf_bootstrap 文件"
    exit 1
fi

# 2. 检查依赖安装
echo "2. 检查依赖安装..."
if [ ! -d "env/lib/python3.10/site-packages" ]; then
    echo "📦 安装依赖到正确目录..."
    mkdir -p env/lib/python3.10/site-packages
    pip install -r requirements.txt -t env/lib/python3.10/site-packages/
    echo "✅ 依赖安装完成"
else
    echo "✅ 依赖目录存在"
fi

# 3. 检查必要文件
echo "3. 检查必要文件..."
required_files=("manage.py" "requirements.txt" "cloudrun/settings.py")
for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        echo "✅ $file 存在"
    else
        echo "❌ $file 缺失"
    fi
done

# 4. 创建部署包
echo "4. 创建部署包..."
deployment_files=(
    "manage.py"
    "scf_bootstrap"
    "requirements.txt"
    "cloudrun/"
    "api/"
    "env/"
)

# 检查部署文件
echo "检查部署文件："
for file in "${deployment_files[@]}"; do
    if [ -e "$file" ]; then
        echo "✅ $file"
    else
        echo "❌ $file (缺失)"
    fi
done

# 5. 检查 Django SQLite 兼容性
echo "5. 检查 Django SQLite 兼容性..."
if [ -f "check_compatibility.py" ]; then
    python check_compatibility.py
    if [ $? -ne 0 ]; then
        echo "⚠️  发现兼容性问题，建议："
        echo "   - 使用 Django 4.2 LTS 版本"
        echo "   - 配置外部数据库（PostgreSQL/MySQL）"
        echo "   - 使用 settings_scf.py 配置文件"
    fi
else
    echo "💡 建议运行兼容性检查：python check_compatibility.py"
fi

# 6. 生成部署建议
echo ""
echo "📋 部署建议："
echo "1. 确保在 CloudBase 控制台设置函数超时时间为 60 秒"
echo "2. 如果使用数据库，请设置相应的环境变量："
echo "   - DB_HOST"
echo "   - DB_NAME" 
echo "   - DB_USER"
echo "   - DB_PASSWORD"
echo "3. 部署后查看函数日志进行调试"
echo ""
echo "🔍 如果仍有问题，请查看："
echo "   - docs/scf-troubleshooting.md (详细故障排除指南)"
echo "   - docs/http-function.md (完整部署指南)"

echo ""
echo "✅ 修复脚本执行完成！"