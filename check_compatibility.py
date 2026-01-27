#!/usr/bin/env python3
"""
Django SQLite 兼容性检查脚本
"""
import sys
import sqlite3
import django
from django.conf import settings

def check_django_sqlite_compatibility():
    """检查 Django 和 SQLite 版本兼容性"""
    
    print("=== Django SQLite 兼容性检查 ===")
    
    # 检查 Django 版本
    django_version = django.get_version()
    django_major = int(django_version.split('.')[0])
    django_minor = int(django_version.split('.')[1])
    
    print(f"Django 版本: {django_version}")
    
    # 检查 SQLite 版本
    sqlite_version = sqlite3.sqlite_version
    sqlite_version_info = tuple(map(int, sqlite_version.split('.')))
    
    print(f"SQLite 版本: {sqlite_version}")
    
    # 检查兼容性
    compatible = True
    recommendations = []
    
    if django_major >= 5:
        # Django 5.x 要求 SQLite 3.31+
        if sqlite_version_info < (3, 31, 0):
            compatible = False
            recommendations.append("Django 5.x 要求 SQLite 3.31 或更高版本")
            recommendations.append("建议降级到 Django 4.2 LTS")
    elif django_major == 4 and django_minor >= 2:
        # Django 4.2+ 要求 SQLite 3.21+
        if sqlite_version_info < (3, 21, 0):
            compatible = False
            recommendations.append("Django 4.2+ 要求 SQLite 3.21 或更高版本")
    
    # 输出结果
    if compatible:
        print("✅ 版本兼容")
    else:
        print("❌ 版本不兼容")
        print("\n推荐解决方案:")
        for i, rec in enumerate(recommendations, 1):
            print(f"{i}. {rec}")
    
    # 额外建议
    print("\n💡 云函数环境建议:")
    print("1. 使用 Django 4.2 LTS (长期支持版本)")
    print("2. 配置外部数据库 (PostgreSQL/MySQL)")
    print("3. 避免在云函数中使用 SQLite 文件数据库")
    
    return compatible

def suggest_requirements():
    """建议兼容的 requirements.txt"""
    
    print("\n📦 推荐的 requirements.txt:")
    print("""
# Django 4.2 LTS - 兼容 SQLite 3.26+
Django==4.2.16
asgiref==3.7.2
psycopg2-binary==2.9.11  # PostgreSQL 支持
sqlparse==0.4.4
typing_extensions==4.15.0
""")

def suggest_database_config():
    """建议数据库配置"""
    
    print("\n🗄️ 推荐的数据库配置:")
    print("""
# settings_scf.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',  # 或 mysql
        'NAME': os.environ.get('DB_NAME', 'cloudrun_django'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# 如果没有外部数据库，使用内存数据库
if not os.environ.get('DB_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
""")

if __name__ == '__main__':
    try:
        # 尝试配置 Django
        if not settings.configured:
            settings.configure(
                DEBUG=True,
                DATABASES={
                    'default': {
                        'ENGINE': 'django.db.backends.sqlite3',
                        'NAME': ':memory:',
                    }
                }
            )
        
        # 检查兼容性
        compatible = check_django_sqlite_compatibility()
        
        # 提供建议
        if not compatible:
            suggest_requirements()
            suggest_database_config()
        
        # 退出码
        sys.exit(0 if compatible else 1)
        
    except Exception as e:
        print(f"❌ 检查过程中出现错误: {e}")
        sys.exit(1)