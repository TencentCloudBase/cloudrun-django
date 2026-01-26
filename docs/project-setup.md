# Django 项目创建指南

本指南详细介绍如何从零开始创建一个适用于 CloudBase 部署的 Django 项目。

## 📋 目录导航

- [环境准备](#环境准备)
- [创建项目](#创建项目)
- [基础配置](#基础配置)
- [创建应用](#创建应用)
- [数据库配置](#数据库配置)
- [安装依赖](#安装依赖)
- [本地测试](#本地测试)
- [下一步](#下一步)

---

## 环境准备

### 1. 检查 Python 版本

```bash
# 检查 Python 版本（推荐 3.8+）
python --version
# 或
python3 --version
```

### 2. 创建项目目录

```bash
# 创建项目根目录
mkdir cloudrun-django && cd cloudrun-django

# 创建虚拟环境
python -m venv env

# 激活虚拟环境
# Windows
env\Scripts\activate
# macOS/Linux
source env/bin/activate
```

## 创建项目

### 1. 安装 Django

```bash
# 安装最新版本的 Django
pip install django

# 验证安装
django-admin --version
```

### 2. 创建 Django 项目

```bash
# 在当前目录创建项目
django-admin startproject cloudrun .

# 项目结构预览
ls -la
# 应该看到：
# manage.py
# cloudrun/
#   __init__.py
#   settings.py
#   urls.py
#   wsgi.py
#   asgi.py
```

## 基础配置

### 1. 更新 `settings.py`

编辑 `cloudrun/settings.py`，添加以下配置：

```python
# cloudrun/settings.py
import os
from pathlib import Path

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# 允许所有主机（CloudBase 环境需要）
ALLOWED_HOSTS = ['*']  # 生产环境应该设置具体域名

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api',  # 添加我们的 API 应用
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'cloudrun.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'cloudrun.wsgi.application'

# 国际化
LANGUAGE_CODE = 'zh-hans'
TIME_ZONE = 'Asia/Shanghai'
USE_I18N = True
USE_TZ = True

# 静态文件
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 默认主键字段类型
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
```

## 创建应用

### 1. 创建 Django 应用

```bash
# 创建一个名为 api 的应用
python manage.py startapp api
```

### 2. 注册应用

在 `cloudrun/settings.py` 中添加应用：

```python
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'api',  # 添加你的应用
]
```

### 3. 创建模型

编辑 `api/models.py`：

```python
from django.db import models

class User(models.Model):
    name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

    class Meta:
        db_table = 'api_users'
```

### 4. 创建视图

编辑 `api/views.py`：

```python
import os
import sys
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.core.paginator import Paginator
from django.shortcuts import get_object_or_404
from .models import User
import json

def hello(request):
    """根路径处理函数"""
    return JsonResponse({
        'message': 'Hello from Django on CloudBase!', 
        'framework': 'Django', 
        'version': '4.2.0'
    })

def health_check(request):
    """健康检查接口"""
    return JsonResponse({
        'status': 'healthy', 
        'framework': 'Django', 
        'python_version': sys.version
    })

def get_users(request):
    """获取用户列表（支持分页）"""
    page = int(request.GET.get('page', 1))
    limit = int(request.GET.get('limit', 10))
    
    users = User.objects.all().order_by('id')
    paginator = Paginator(users, limit)
    page_obj = paginator.get_page(page)
    
    users_data = [
        {
            'id': user.id,
            'name': user.name,
            'email': user.email,
            'created_at': user.created_at.isoformat(),
            'updated_at': user.updated_at.isoformat()
        }
        for user in page_obj
    ]
    
    return JsonResponse({
        'success': True,
        'data': {
            'total': paginator.count,
            'page': page,
            'limit': limit,
            'items': users_data
        }
    })

def get_user(request, user_id):
    """根据 ID 获取用户"""
    try:
        user = get_object_or_404(User, id=user_id)
        return JsonResponse({
            'success': True,
            'data': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            }
        })
    except:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)

@csrf_exempt
@require_http_methods(["POST"])
def create_user(request):
    """创建新用户"""
    try:
        data = json.loads(request.body)
        
        if not data.get('name') or not data.get('email'):
            return JsonResponse({'success': False, 'message': 'Name and email are required'}, status=400)
        
        # 检查邮箱是否已存在
        if User.objects.filter(email=data['email']).exists():
            return JsonResponse({'success': False, 'message': 'Email already exists'}, status=400)
        
        # 创建新用户
        user = User.objects.create(
            name=data['name'],
            email=data['email']
        )
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            }
        }, status=201)
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        return JsonResponse({'success': False, 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["PUT"])
def update_user(request, user_id):
    """更新用户信息"""
    try:
        user = get_object_or_404(User, id=user_id)
        data = json.loads(request.body)
        
        if not data:
            return JsonResponse({'success': False, 'message': 'No data provided'}, status=400)
        
        # 检查邮箱是否被其他用户使用
        if 'email' in data and User.objects.filter(email=data['email']).exclude(id=user_id).exists():
            return JsonResponse({'success': False, 'message': 'Email already exists'}, status=400)
        
        # 更新用户信息
        if 'name' in data:
            user.name = data['name']
        if 'email' in data:
            user.email = data['email']
        
        user.save()
        
        return JsonResponse({
            'success': True,
            'data': {
                'id': user.id,
                'name': user.name,
                'email': user.email,
                'created_at': user.created_at.isoformat(),
                'updated_at': user.updated_at.isoformat()
            }
        })
        
    except json.JSONDecodeError:
        return JsonResponse({'success': False, 'message': 'Invalid JSON'}, status=400)
    except:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)

@csrf_exempt
@require_http_methods(["DELETE"])
def delete_user(request, user_id):
    """删除用户"""
    try:
        user = get_object_or_404(User, id=user_id)
        user_name = user.name
        user.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'User {user_name} deleted successfully'
        })
    except:
        return JsonResponse({'success': False, 'message': 'User not found'}, status=404)
```

### 5. 配置 URL

创建 `api/urls.py`：

```python
from django.urls import path
from . import views

urlpatterns = [
    path('', views.hello, name='hello'),
    path('health/', views.health_check, name='health_check'),
    path('api/users/', views.get_users, name='get_users'),
    path('api/users/<int:user_id>/', views.get_user, name='get_user'),
    path('api/users/create/', views.create_user, name='create_user'),
    path('api/users/<int:user_id>/update/', views.update_user, name='update_user'),
    path('api/users/<int:user_id>/delete/', views.delete_user, name='delete_user'),
]
```

更新 `cloudrun/urls.py`：

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api.urls')),
]
```

## 数据库配置

### 1. 云函数环境（MySQL）

如果要部署到 **HTTP 云函数**，必须使用外部数据库：

```python
# cloudrun/settings.py
# 数据库配置
# 注意：云函数运行时目录不允许写文件，禁止使用 SQLite
# 推荐使用 CloudBase 数据库或其他外部数据库服务
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'cloudrun_django'),
        'USER': os.environ.get('DB_USER', 'root'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}
```

### 2. 云托管环境（PostgreSQL 推荐）

如果要部署到 **云托管**，推荐使用 PostgreSQL：

```python
# cloudrun/settings.py
# 数据库配置
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'cloudrun_django'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}

# 如果没有配置数据库连接，使用内存数据库（仅用于测试）
if not os.environ.get('DB_HOST'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
```

### 3. 开发环境（SQLite）

开发阶段可以使用 SQLite（仅限本地开发）：

```python
# cloudrun/settings.py
# 默认配置，适用于本地开发
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

## 安装依赖

### 1. 基础依赖

```bash
# 安装基础依赖（与项目 requirements.txt 一致）
pip install Django==5.2.10
pip install psycopg2-binary==2.9.11

# 根据部署方式选择数据库驱动
# MySQL (云函数)
pip install mysqlclient

# 生产服务器 (云托管)
pip install gunicorn
```

### 2. 生成依赖文件

```bash
# 生成 requirements.txt
pip freeze > requirements.txt

# 查看生成的依赖（应该包含以下内容）
cat requirements.txt
# asgiref==3.11.0
# Django==5.2.10
# psycopg2-binary==2.9.11
# sqlparse==0.5.5
# typing_extensions==4.15.0
```

### 3. 创建 .gitignore

```bash
cat > .gitignore << EOF
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Django
*.log
local_settings.py
db.sqlite3
db.sqlite3-journal
media/

# 虚拟环境
env/
venv/
.venv/
ENV/
env.bak/
venv.bak/

# IDE
.vscode/
.idea/
*.swp
*.swo
*~

# 操作系统
.DS_Store
.DS_Store?
._*
.Spotlight-V100
.Trashes
ehthumbs.db
Thumbs.db

# 环境变量
.env
.env.local
.env.production

# 部署文件
deployment.zip
*.tar.gz

# CloudBase
.cloudbaserc.json
cloudbaserc.json

# 静态文件收集目录
staticfiles/
EOF
```

## 本地测试

### 1. 数据库迁移

```bash
# 创建迁移文件
python manage.py makemigrations

# 应用迁移
python manage.py migrate

# 创建超级用户（可选）
python manage.py createsuperuser
```

### 2. 收集静态文件

```bash
# 收集静态文件
python manage.py collectstatic --noinput
```

### 3. 启动开发服务器

```bash
# 启动开发服务器
python manage.py runserver

# 服务器启动后，访问以下地址测试：
# http://127.0.0.1:8000/          - 首页
# http://127.0.0.1:8000/health/   - 健康检查
# http://127.0.0.1:8000/admin/    - 管理后台
```

### 4. API 测试

```bash
# 测试基础接口
curl http://127.0.0.1:8000/
# 返回: {"message": "Hello from Django on CloudBase!", "framework": "Django", "version": "4.2.0"}

curl http://127.0.0.1:8000/health/
# 返回: {"status": "healthy", "framework": "Django", "python_version": "..."}

# 测试用户 API
# 获取用户列表
curl http://127.0.0.1:8000/api/users/
curl "http://127.0.0.1:8000/api/users/?page=1&limit=5"

# 创建用户
curl -X POST http://127.0.0.1:8000/api/users/create/ \
  -H "Content-Type: application/json" \
  -d '{"name": "张三", "email": "zhangsan@example.com"}'

# 获取单个用户
curl http://127.0.0.1:8000/api/users/1/

# 更新用户
curl -X PUT http://127.0.0.1:8000/api/users/1/update/ \
  -H "Content-Type: application/json" \
  -d '{"name": "张三更新", "email": "zhangsan_new@example.com"}'

# 删除用户
curl -X DELETE http://127.0.0.1:8000/api/users/1/delete/
```

## 下一步

项目创建完成后，根据您的部署需求选择相应的部署指南：

### 🚀 部署选择

| 部署方式 | 适用场景 | 详细指南 |
|----------|----------|----------|
| **HTTP 云函数** | 轻量级 API、间歇性访问 | [HTTP 云函数部署指南](./http-function.md) |
| **云托管** | 企业应用、高并发、持续运行 | [云托管部署指南](./cloud-run.md) |

### 📚 相关文档

- [返回主文档](../README.md)
- [HTTP 云函数部署指南](./http-function.md)
- [云托管部署指南](./cloud-run.md)

### 🔧 进一步开发

1. **添加更多应用**：`python manage.py startapp another_app`
2. **配置数据库模型**：在 `models.py` 中定义数据模型
3. **添加用户认证**：集成 Django 认证系统
4. **API 开发**：使用 Django REST Framework
5. **前端集成**：添加 Vue.js 或 React 前端

---

**提示**：确保在部署前测试所有功能，特别是数据库连接和静态文件服务。