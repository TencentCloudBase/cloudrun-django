# 快速部署 Django 应用

## 📋 目录导航

- [部署方式对比](#部署方式对比)
- [前置条件](#前置条件)
- [第一步：创建 Django 应用](#第一步创建-django-应用)
- [第二步：添加 API 路由](#第二步添加-api-路由)
- [第三步：本地测试](#第三步本地测试)
- [第四步：准备部署文件](#第四步准备部署文件)
- [第五步：项目结构](#第五步项目结构)
- [第六步：部署应用](#第六步部署应用)
- [第七步：访问您的应用](#第七步访问您的应用)
- [常见问题](#常见问题)
- [最佳实践](#最佳实践)
- [进阶功能](#进阶功能)

---

[Django](https://www.djangoproject.com/) 是一个高级的 Python Web 框架，它鼓励快速开发和干净、实用的设计。Django 遵循 MVC 模式，提供了强大的 ORM、自动化的管理界面、用户认证系统等功能。

本指南介绍如何在 CloudBase 上部署 Django 应用程序，支持两种部署方式：

- **HTTP 云函数**：适合轻量级应用和 API 服务，按请求计费，冷启动快
- **云托管**：适合企业级应用，支持更复杂的部署需求，容器化部署

## 部署方式对比

| 特性 | HTTP 云函数 | 云托管 |
|------|------------|--------|
| **计费方式** | 按请求次数和执行时间 | 按资源使用量（CPU/内存） |
| **启动方式** | 冷启动，按需启动 | 持续运行 |
| **适用场景** | API 服务、轻量级应用 | 企业级应用、复杂 Web 应用 |
| **部署文件** | 需要 `scf_bootstrap` 启动脚本 | 需要 `Dockerfile` 容器配置 |
| **端口要求** | 固定 9000 端口 | 可自定义端口（默认 8080） |
| **扩缩容** | 自动按请求扩缩 | 支持自动扩缩容配置 |
| **Python 环境** | 预配置 Python 运行时 | 完全自定义 Python 环境 |

## 前置条件

在开始之前，请确保您已经：

- 安装了 [Python 3.10](https://www.python.org/downloads/) 或更高版本
- 了解基本的 Python 虚拟环境使用
- 拥有腾讯云账号并开通了 CloudBase 服务
- 了解基本的 Python 和 Django 开发知识

## 第一步：创建 Django 应用

> 💡 **提示**：如果您已经有一个 Django 应用，可以跳过此步骤。

### 创建项目目录

```bash
mkdir cloudrun-django
cd cloudrun-django
```

### 创建虚拟环境

```bash
# 创建虚拟环境（推荐使用 Python 3.10）
python -m venv env

# 激活虚拟环境
# Windows
env\Scripts\activate
# macOS/Linux
source env/bin/activate
```

### 安装 Django 和依赖

```bash
# 安装 Django 和数据库驱动
pip install django psycopg2-binary

# 生成依赖文件
pip freeze > requirements.txt
```

### 创建 Django 项目

```bash
# 创建 Django 项目
django-admin startproject cloudrun .

# 创建应用
python manage.py startapp api
```

### 配置 Django 设置

编辑 `cloudrun/settings.py` 文件：

```python
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# 安全设置
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me-in-production')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# 允许的主机
ALLOWED_HOSTS = ['*']  # 生产环境应该设置具体域名

# 应用配置
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

# 数据库配置
# 注意：云函数运行时目录不允许写文件，禁止使用 SQLite
# 推荐使用 CloudBase 数据库或其他外部数据库服务
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

## 第二步：添加 API 路由

### 创建用户模型

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

### 创建 API 视图

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

### 配置 URL 路由

编辑 `api/urls.py`（创建此文件）：

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

编辑 `cloudrun/urls.py`：

```python
from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('api.urls')),
]
```

### 数据库迁移

> ⚠️ **重要提醒**：云函数运行时目录不允许写文件，因此不能使用 SQLite 数据库。请确保配置外部数据库服务（如 CloudBase 数据库、PostgreSQL 等）。

```bash
# 配置数据库连接环境变量（示例）
export DB_HOST=your-database-host
export DB_NAME=cloudrun_django
export DB_USER=your-username
export DB_PASSWORD=your-password

# 创建迁移文件
python manage.py makemigrations

# 执行迁移
python manage.py migrate

# 创建超级用户（可选）
python manage.py createsuperuser
```

> 💡 **数据库选择建议**：
> - **CloudBase 数据库**：腾讯云原生数据库服务，与 CloudBase 深度集成
> - **PostgreSQL**：开源关系型数据库，功能强大
> - **MySQL**：流行的关系型数据库
> - **内存数据库**：仅用于开发测试，数据不持久化

## 第三步：本地测试

### 启动开发服务器

```bash
# 默认端口 8080，HTTP 云函数通过环境变量设置为 9000
python manage.py runserver 0.0.0.0:8080
```

### 测试 API 接口

```bash
# 测试健康检查
curl http://localhost:8080/health/

# 测试首页
curl http://localhost:8080/

# 测试用户列表
curl http://localhost:8080/api/users/

# 测试分页
curl "http://localhost:8080/api/users/?page=1&limit=2"

# 测试创建用户
curl -X POST http://localhost:8080/api/users/create/ \
  -H "Content-Type: application/json" \
  -d '{"name":"张三","email":"zhangsan@example.com"}'

# 测试获取单个用户
curl http://localhost:8080/api/users/1/

# 测试更新用户
curl -X PUT http://localhost:8080/api/users/1/update/ \
  -H "Content-Type: application/json" \
  -d '{"name":"更新的用户名"}'

# 测试删除用户
curl -X DELETE http://localhost:8080/api/users/1/delete/
```

## 第四步：准备部署文件

根据您选择的部署方式，需要准备不同的配置文件：

### 📋 选择部署方式

<details>
<summary><strong>🔥 HTTP 云函数部署配置</strong></summary>

HTTP 云函数需要 `scf_bootstrap` 启动脚本和特定的端口配置。

#### 1. 创建启动脚本

创建 `scf_bootstrap` 文件（无扩展名）：

```bash
#!/bin/bash
export PORT=9000
export PYTHONPATH="./env/lib/python3.10/site-packages:$PYTHONPATH"
/var/lang/python310/bin/python3.10 manage.py runserver 0.0.0.0:9000
```

为启动脚本添加执行权限：

```bash
chmod +x scf_bootstrap
```

#### 2. 项目结构

```
cloudrun-django/
├── manage.py                # Django 管理脚本
├── cloudrun/              # Django 项目配置
│   ├── __init__.py
│   ├── settings.py
│   ├── urls.py
│   └── wsgi.py
├── api/                    # API 应用
│   ├── __init__.py
│   ├── models.py
│   ├── views.py
│   └── urls.py
├── requirements.txt         # Python 依赖
├── scf_bootstrap           # 🔑 云函数启动脚本
└── env/                   # 🔑 虚拟环境（部署时需要包含）
    └── lib/
        └── python3.10/
            └── site-packages/  # Python 依赖包
```

> 💡 **说明**：
> - `scf_bootstrap` 是 CloudBase 云函数的启动脚本
> - 设置 `PORT=9000` 环境变量确保应用监听云函数要求的端口
> - 设置 `PYTHONPATH` 环境变量确保应用能找到依赖包
> - 使用云函数运行时环境的 Python 解释器启动应用
> - **重要**：HTTP 云函数部署时需要包含 `env` 目录及其依赖包
> - 云函数会自动安装 `requirements.txt` 中的依赖，但建议同时上传 `env` 目录以确保依赖完整性

</details>

<details>
<summary><strong>🐳 云托管部署配置</strong></summary>

云托管使用 Docker 容器化部署，需要 `Dockerfile` 配置文件。

#### 1. 创建 Dockerfile

创建 `Dockerfile` 文件：

```dockerfile
# 使用官方 Python 运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# 复制依赖文件
COPY requirements.txt .

# 设置 pip 镜像源以提高下载速度
RUN pip config set global.index-url https://mirrors.cloud.tencent.com/pypi/simple/ \
    && pip config set global.trusted-host mirrors.cloud.tencent.com

# 安装 Python 依赖
RUN pip install --no-cache-dir -r requirements.txt

# 复制应用代码
COPY . .

# 收集静态文件
RUN python manage.py collectstatic --noinput

# 暴露端口
EXPOSE 8080

# 设置环境变量
ENV PORT=8080
ENV DJANGO_SETTINGS_MODULE=cloudrun.settings
ENV PYTHONPATH=/app

# 启动命令
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
```

#### 2. 创建 .dockerignore 文件

创建 `.dockerignore` 文件以优化构建性能：

```
env/
__pycache__/
*.pyc
*.pyo
*.pyd
.Python
.git
.gitignore
README.md
.env
.DS_Store
*.log
.pytest_cache/
.coverage
scf_bootstrap
.vscode/
.idea/
db.sqlite3
```

#### 3. 项目结构

```
cloudrun-django/
├── manage.py                # Django 管理脚本
├── cloudrun/              # Django 项目配置
├── api/                    # API 应用
├── requirements.txt         # Python 依赖
├── Dockerfile              # 🔑 容器配置文件
├── .dockerignore           # Docker 忽略文件
└── env/                   # 虚拟环境（部署时排除）
```

> 💡 **说明**：
> - 云托管支持自定义端口，默认使用 8080 端口
> - 使用 Django 内置开发服务器启动应用
> - Docker 容器提供了完整的 Python 环境控制

</details>

## 第五步：项目结构

确保您的项目目录结构包含必要的文件。根据部署方式的不同，某些文件是可选的：

```
cloudrun-django/
├── manage.py                # Django 管理脚本
├── cloudrun/              # Django 项目配置
│   ├── __init__.py
│   ├── settings.py         # 项目设置
│   ├── urls.py            # 主 URL 配置
│   └── wsgi.py            # WSGI 配置
├── api/                    # API 应用
│   ├── __init__.py
│   ├── models.py          # 数据模型
│   ├── views.py           # 视图函数
│   └── urls.py            # API URL 配置
├── requirements.txt         # Python 依赖文件
├── env/                   # 虚拟环境（本地开发用）
├── scf_bootstrap           # HTTP 云函数启动脚本 (仅云函数需要)
├── Dockerfile              # 云托管容器配置 (仅云托管需要)
└── .dockerignore           # Docker 忽略文件 (仅云托管需要)
```

## 第六步：部署应用

选择您需要的部署方式：

### 🚀 部署方式选择

<details>
<summary><strong>🔥 部署到 HTTP 云函数</strong></summary>

#### 通过控制台部署

1. 登录 [CloudBase 控制台](https://console.cloud.tencent.com/tcb)
2. 选择您的环境，进入「云函数」页面
3. 点击「新建云函数」
4. 选择「HTTP 云函数」
5. 填写函数名称（如：`cloudrun-django-app`）
6. 选择运行时：**Python 3.10**（或其他支持的版本）
7. 提交方法选择：**本地上传文件夹**
8. 函数代码选择 `cloudrun-django` 目录进行上传
9. **自动安装依赖**：开启此选项
10. 点击「创建」按钮等待部署完成

#### 打包部署

如果需要手动打包：

```bash
# 创建部署包（包含 env 目录）
zip -r cloudrun-django-app.zip . -x ".git/*" "*.log" "Dockerfile" ".dockerignore" "__pycache__/*"
```

</details>

<details>
<summary><strong>🐳 部署到云托管</strong></summary>

#### 通过控制台部署

1. 登录 [CloudBase 控制台](https://console.cloud.tencent.com/tcb)
2. 选择您的环境，进入「云托管」页面
3. 点击「新建服务」
4. 填写服务名称（如：`cloudrun-django-service`）
5. 选择「本地代码」上传方式
6. 上传包含 `Dockerfile` 的项目目录
7. 配置服务参数：
   - **端口**：8080（或您在应用中配置的端口）
   - **CPU**：0.25 核
   - **内存**：0.5 GB
   - **实例数量**：1-10（根据需求调整）
8. 点击「创建」按钮等待部署完成

#### 模板部署（快速开始）

1. 登录 [腾讯云托管控制台](https://tcb.cloud.tencent.com/dev#/platform-run/service/create?type=image)
2. 点击「通过模板部署」，选择 **Django 模板**
3. 输入自定义服务名称，点击部署
4. 等待部署完成后，点击左上角箭头，返回到服务详情页
5. 点击概述，获取默认域名并访问

</details>

## 第七步：访问您的应用

### HTTP 云函数访问

部署成功后，您可以参考[通过 HTTP 访问云函数](https://docs.cloudbase.net/service/access-cloud-function)设置自定义域名访问 HTTP 云函数。

访问地址格式：`https://your-function-url/`

### 云托管访问

云托管部署成功后，系统会自动分配访问地址。您也可以绑定自定义域名。

访问地址格式：`https://your-service-url/`

### 测试接口

无论使用哪种部署方式，您都可以测试以下接口：

- **根路径**：`/` - Django 欢迎页面
- **健康检查**：`/health/` - 查看应用状态
- **用户列表**：`/api/users/` - 获取用户列表
- **用户详情**：`/api/users/1/` - 获取特定用户
- **创建用户**：`POST /api/users/create/` - 创建新用户
- **更新用户**：`PUT /api/users/1/update/` - 更新用户信息
- **删除用户**：`DELETE /api/users/1/delete/` - 删除用户

### 示例请求

```bash
# 健康检查
curl https://your-app-url/health/

# 获取用户列表
curl https://your-app-url/api/users/

# 分页查询
curl "https://your-app-url/api/users/?page=1&limit=2"

# 创建新用户
curl -X POST https://your-app-url/api/users/create/ \
  -H "Content-Type: application/json" \
  -d '{"name":"测试用户","email":"test@example.com"}'
```

## 常见问题

### ❓ 问题分类

<details>
<summary><strong>🔥 HTTP 云函数相关问题</strong></summary>

#### Q: 为什么 HTTP 云函数必须使用 9000 端口？
A: CloudBase HTTP 云函数要求应用监听 9000 端口，这是平台的标准配置。通过在 `scf_bootstrap` 中设置 `PORT=9000` 环境变量来控制端口，本地开发时默认使用 8080 端口。

#### Q: Django 静态文件如何处理？
A: HTTP 云函数环境中，建议将静态文件托管到 CDN 或对象存储，或者在 Django 设置中配置静态文件服务。

#### Q: 数据库如何配置？
A: **重要**：云函数运行时目录不允许写文件，因此禁止使用 SQLite 数据库。必须使用外部数据库服务：
- **CloudBase 数据库**：推荐使用，与 CloudBase 深度集成
- **PostgreSQL**：通过环境变量配置连接信息
- **MySQL**：适合大型应用
- **内存数据库**：仅用于开发测试，数据不持久化

配置示例：
```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

#### Q: 虚拟环境依赖如何处理？
A: HTTP 云函数部署时需要包含 `env` 目录及其依赖包。在 `scf_bootstrap` 中通过 `PYTHONPATH` 环境变量指向虚拟环境的 site-packages 目录，确保应用能正确加载依赖。

</details>

<details>
<summary><strong>🐳 云托管相关问题</strong></summary>

#### Q: 云托管支持哪些端口？
A: 云托管支持自定义端口，Django 应用默认使用 8080 端口，也可以根据需要配置其他端口。

#### Q: 如何处理数据库迁移？
A: 云托管环境中，数据库迁移应该在部署后手动执行或通过初始化脚本执行，不建议在 Dockerfile 构建时执行迁移。可以创建管理命令或使用容器启动后的初始化脚本：

```python
# 创建初始化脚本
def init_database():
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'migrate'])
```

#### Q: 静态文件如何处理？
A: 在 Dockerfile 中使用 `python manage.py collectstatic` 收集静态文件，并配置 Web 服务器提供静态文件服务。

#### Q: 如何配置生产环境设置？
A: 创建单独的生产环境设置文件，通过环境变量控制 DEBUG、ALLOWED_HOSTS 等配置。

</details>

<details>
<summary><strong>🔧 通用问题</strong></summary>

#### Q: 如何处理 CSRF 保护？
A: API 接口可以使用 `@csrf_exempt` 装饰器禁用 CSRF 保护，或者配置 CSRF 令牌机制。

#### Q: 如何查看应用日志？
A: 
- **HTTP 云函数**：在 CloudBase 控制台的云函数页面查看运行日志
- **云托管**：在云托管服务详情页面查看实例日志

#### Q: 支持哪些 Python 版本？
A: CloudBase 支持 Python 3.7、3.8、3.9、3.10、3.11 等版本，建议使用最新的稳定版本。

#### Q: 两种部署方式如何选择？
A: 
- **选择 HTTP 云函数**：轻量级 API 服务、间歇性访问、成本敏感
- **选择云托管**：企业级应用、复杂 Web 应用、需要更多控制权

</details>

## 最佳实践

### 1. 环境变量管理

使用 python-dotenv 管理环境变量：

```python
# settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')
    DATABASE_URL = os.getenv('DATABASE_URL', 'sqlite:///db.sqlite3')
```

### 2. 端口配置策略

创建自定义管理命令支持动态端口：

```python
# management/commands/runserver_port.py
from django.core.management.commands.runserver import Command as RunserverCommand
import os

class Command(RunserverCommand):
    def handle(self, *args, **options):
        port = os.environ.get('PORT', '8080')
        options['addrport'] = f"0.0.0.0:{port}"
        super().handle(*args, **options)
```

### 3. 数据库配置

```python
# settings.py
import dj_database_url

# 注意：禁止使用 SQLite，云函数运行时目录不允许写文件
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://user:password@localhost:5432/dbname',
        conn_max_age=600
    )
}

# 如果没有配置数据库 URL，使用内存数据库（仅用于测试）
if not os.environ.get('DATABASE_URL'):
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': ':memory:',
        }
    }
```

### 4. 静态文件配置

```python
# settings.py
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 生产环境使用 WhiteNoise
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... 其他中间件
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 5. 日志配置

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
    },
    'root': {
        'handlers': ['console'],
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}
```

### 6. 部署前检查清单

<details>
<summary><strong>🔥 HTTP 云函数部署检查</strong></summary>

#### HTTP 云函数部署检查

- [ ] `scf_bootstrap` 文件存在且有执行权限
- [ ] 端口配置为 9000
- [ ] `requirements.txt` 包含所有必需依赖（包括 `psycopg2-binary`）
- [ ] **包含 `env` 目录及其依赖包**
- [ ] **配置外部数据库连接**（禁止使用 SQLite 文件数据库）
- [ ] 数据库迁移文件已生成
- [ ] 环境变量配置正确（DB_HOST、DB_NAME 等）
- [ ] 排除不必要的文件（如 `Dockerfile`、`.dockerignore`）
- [ ] 测试本地启动是否正常
- [ ] 检查启动脚本语法是否正确

</details>

<details>
<summary><strong>🐳 云托管部署检查</strong></summary>

#### 云托管部署检查

- [ ] `Dockerfile` 文件存在且配置正确
- [ ] `.dockerignore` 文件配置合理
- [ ] 端口配置灵活（支持环境变量）
- [ ] 容器启动命令正确
- [ ] **排除 `env` 目录**（云托管使用 Docker 容器内的 Python 环境）
- [ ] 静态文件收集配置正确
- [ ] **数据库连接配置正确**（通过环境变量）
- [ ] 数据库迁移策略明确（手动执行或初始化脚本）
- [ ] 排除不必要的文件（如 `scf_bootstrap`）
- [ ] 本地 Docker 构建测试通过

</details>

## 进阶功能

### 数据库集成

集成 PostgreSQL 数据库：

```bash
pip install psycopg2-binary dj-database-url
```

### 身份验证

添加 JWT 身份验证：

```bash
pip install djangorestframework djangorestframework-simplejwt
```

### API 文档

使用 Django REST Framework 生成 API 文档：

```bash
pip install djangorestframework drf-yasg
```

### 缓存支持

添加 Redis 缓存：

```bash
pip install django-redis
```

### 异步支持

Django 4.1+ 支持异步视图：

```python
from django.http import JsonResponse
import asyncio

async def async_view(request):
    await asyncio.sleep(1)  # 模拟异步操作
    return JsonResponse({'message': 'Async response'})
```