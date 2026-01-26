# Django 云托管部署指南

本指南详细介绍如何将 Django 应用部署到 CloudBase 云托管服务。

> **📋 前置要求**：如果您还没有创建 Django 项目，请先阅读 [Django 项目创建指南](./project-setup.md)。

## 📋 目录导航

- [部署特性](#部署特性)
- [准备部署文件](#准备部署文件)
- [项目结构](#项目结构)
- [部署步骤](#部署步骤)
- [访问应用](#访问应用)
- [常见问题](#常见问题)
- [最佳实践](#最佳实践)
- [高级配置](#高级配置)

---

## 部署特性

云托管适合以下场景：

- **企业级应用**：复杂的 Web 应用和管理系统
- **高并发**：需要处理大量并发请求
- **自定义环境**：需要特定的运行时环境
- **微服务架构**：容器化部署和管理

### 技术特点

| 特性 | 说明 |
|------|------|
| **计费方式** | 按资源使用量（CPU/内存） |
| **启动方式** | 持续运行 |
| **端口配置** | 可自定义端口（默认 8080） |
| **扩缩容** | 支持自动扩缩容配置 |
| **Python 环境** | 完全自定义 Python 环境 |

## 准备部署文件

### 1. 创建 Dockerfile

创建 `Dockerfile` 文件：

```dockerfile
# 使用官方 Python 运行时作为基础镜像
FROM python:3.11-slim

# 设置工作目录
WORKDIR /app

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    gcc \
    libpq-dev \
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

### 2. 创建 .dockerignore 文件

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
docs/
```

### 3. 数据库配置

在 `settings.py` 中配置生产环境数据库：

```python
import os
import dj_database_url

# 数据库配置
DATABASES = {
    'default': dj_database_url.config(
        default='postgresql://user:password@localhost:5432/dbname',
        conn_max_age=600
    )
}

# 如果没有配置数据库 URL，使用环境变量
if not os.environ.get('DATABASE_URL'):
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
```

### 4. 静态文件配置

```python
# settings.py
import os

# 静态文件配置
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# 使用 WhiteNoise 处理静态文件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'
```

### 5. 依赖管理

确保 `requirements.txt` 包含所有必要依赖：

```txt
Django>=4.2.0
psycopg2-binary>=2.9.0
dj-database-url>=2.0.0
whitenoise>=6.5.0
python-dotenv>=1.0.0
gunicorn>=21.0.0
```

## 项目结构

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
├── Dockerfile              # 🔑 容器配置文件
├── .dockerignore           # Docker 忽略文件
└── staticfiles/           # 静态文件（构建时生成）
```

> 💡 **说明**：
> - 云托管支持自定义端口，默认使用 8080 端口
> - 使用 Django 内置开发服务器或 Gunicorn 启动应用
> - Docker 容器提供了完整的 Python 环境控制

## 部署步骤

### 通过控制台部署

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

### 通过 CLI 部署

```bash
# 安装 CloudBase CLI
npm install -g @cloudbase/cli

# 登录
tcb login

# 初始化云托管配置
tcb run init

# 部署云托管服务
tcb run deploy --port 8080
```

### 配置文件部署

创建 `cloudbaserc.json` 配置文件：

```json
{
  "envId": "your-env-id",
  "framework": {
    "name": "django",
    "plugins": {
      "run": {
        "name": "@cloudbase/framework-plugin-run",
        "options": {
          "serviceName": "cloudrun-django-service",
          "servicePath": "/",
          "localPath": "./",
          "dockerfile": "./Dockerfile",
          "buildDir": "./",
          "cpu": 0.25,
          "mem": 0.5,
          "minNum": 1,
          "maxNum": 10,
          "policyType": "cpu",
          "policyThreshold": 60,
          "containerPort": 8080,
          "envVariables": {
            "DJANGO_SETTINGS_MODULE": "cloudrun.settings",
            "DEBUG": "False"
          }
        }
      }
    }
  }
}
```

然后执行部署：

```bash
tcb framework deploy
```

### 模板部署（快速开始）

1. 登录 [腾讯云托管控制台](https://tcb.cloud.tencent.com/dev#/platform-run/service/create?type=image)
2. 点击「通过模板部署」，选择 **Django 模板**
3. 输入自定义服务名称，点击部署
4. 等待部署完成后，点击左上角箭头，返回到服务详情页
5. 点击概述，获取默认域名并访问

## 访问应用

### 获取访问地址

云托管部署成功后，系统会自动分配访问地址。您也可以绑定自定义域名。

访问地址格式：`https://your-service-url/`

### 测试接口

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
curl https://your-service-url/health/

# 获取用户列表
curl https://your-service-url/api/users/

# 分页查询
curl "https://your-service-url/api/users/?page=1&limit=2"

# 创建新用户
curl -X POST https://your-service-url/api/users/create/ \
  -H "Content-Type: application/json" \
  -d '{"name":"测试用户","email":"test@example.com"}'
```

## 常见问题

### Q: 云托管支持哪些端口？
A: 云托管支持自定义端口，Django 应用默认使用 8080 端口，也可以根据需要配置其他端口。

### Q: 如何处理数据库迁移？
A: 云托管环境中，数据库迁移应该在部署后手动执行或通过初始化脚本执行，不建议在 Dockerfile 构建时执行迁移。可以创建管理命令或使用容器启动后的初始化脚本：

```python
# 创建初始化脚本
def init_database():
    from django.core.management import execute_from_command_line
    execute_from_command_line(['manage.py', 'migrate'])
```

### Q: 静态文件如何处理？
A: 在 Dockerfile 中使用 `python manage.py collectstatic` 收集静态文件，并配置 WhiteNoise 中间件提供静态文件服务：

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... 其他中间件
]
```

### Q: 如何配置生产环境设置？
A: 创建单独的生产环境设置文件，通过环境变量控制 DEBUG、ALLOWED_HOSTS 等配置：

```python
# settings.py
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '*').split(',')
SECRET_KEY = os.environ.get('SECRET_KEY', 'django-insecure-change-me')
```

### Q: 如何配置环境变量？
A: 可以通过以下方式配置：
- 控制台服务配置页面
- `cloudbaserc.json` 配置文件
- Dockerfile 中的 ENV 指令

### Q: 云托管支持哪些数据库？
A: 云托管支持连接：
- CloudBase 数据库
- 云数据库 MySQL
- 云数据库 PostgreSQL
- Redis
- MongoDB

### Q: 如何查看云托管日志？
A: 在云托管服务详情页面可以查看：
- 实例日志
- 构建日志
- 访问日志
- 错误日志

## 最佳实践

### 1. 多阶段构建优化

```dockerfile
# 构建阶段
FROM python:3.11-slim AS builder

WORKDIR /app
COPY requirements.txt .
RUN pip install --user -r requirements.txt

# 运行阶段
FROM python:3.11-slim

WORKDIR /app
COPY --from=builder /root/.local /root/.local
COPY . .

# 确保 Python 用户包在 PATH 中
ENV PATH=/root/.local/bin:$PATH

RUN python manage.py collectstatic --noinput

EXPOSE 8080
CMD ["python", "manage.py", "runserver", "0.0.0.0:8080"]
```

### 2. 使用 Gunicorn 生产服务器

```dockerfile
# Dockerfile 中使用 Gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "2", "cloudrun.wsgi:application"]
```

```python
# gunicorn.conf.py
bind = "0.0.0.0:8080"
workers = 2
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
```

### 3. 环境变量管理

```python
# settings.py
import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me')
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', '*').split(',')
    
    # 数据库配置
    DATABASE_URL = os.getenv('DATABASE_URL')
    DB_NAME = os.getenv('DB_NAME', 'cloudrun_django')
    DB_USER = os.getenv('DB_USER', 'postgres')
    DB_PASSWORD = os.getenv('DB_PASSWORD', '')
    DB_HOST = os.getenv('DB_HOST', 'localhost')
    DB_PORT = os.getenv('DB_PORT', '5432')
```

### 4. 健康检查增强

```python
# api/views.py
import sys
import os
from django.http import JsonResponse
from django.db import connection

def health_check(request):
    """增强的健康检查接口"""
    try:
        # 检查数据库连接
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
        
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
    
    return JsonResponse({
        'status': 'healthy' if db_status == 'healthy' else 'unhealthy',
        'timestamp': timezone.now().isoformat(),
        'framework': 'Django',
        'deployment': '云托管',
        'version': '4.2.0',
        'python_version': sys.version,
        'database': db_status,
        'environment': os.environ.get('DJANGO_SETTINGS_MODULE', 'unknown')
    })
```

### 5. 日志配置

```python
# settings.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
        'cloudrun': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}
```

### 6. 安全配置

```python
# settings.py
import os

# 安全设置
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'

if not DEBUG:
    SECURE_SSL_REDIRECT = True
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
```

### 7. 部署前检查清单

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

## 高级配置

### 1. 负载均衡配置

```json
{
  "run": {
    "name": "@cloudbase/framework-plugin-run",
    "options": {
      "serviceName": "cloudrun-django-service",
      "cpu": 1,
      "mem": 2,
      "minNum": 2,
      "maxNum": 20,
      "policyType": "cpu",
      "policyThreshold": 70,
      "containerPort": 8080,
      "customLogs": "stdout",
      "initialDelaySeconds": 2,
      "dataBaseName": "django-db"
    }
  }
}
```

### 2. 数据库连接池

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        },
        'CONN_MAX_AGE': 600,
    }
}
```

### 3. Redis 缓存配置

```python
# settings.py
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# 会话存储
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'
```

### 4. 监控和告警

```python
# middleware.py
import time
import logging
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)

class PerformanceMonitoringMiddleware(MiddlewareMixin):
    def process_request(self, request):
        request.start_time = time.time()
    
    def process_response(self, request, response):
        if hasattr(request, 'start_time'):
            duration = time.time() - request.start_time
            logger.info(f'{request.method} {request.path} - {response.status_code} - {duration:.3f}s')
        return response
```

---

## 相关文档

- [返回主文档](../README.md)
- [HTTP 云函数部署指南](./http-function.md)
- [CloudBase 官方文档](https://docs.cloudbase.net/)