# Django HTTP 云函数部署指南

本指南详细介绍如何将 Django 应用部署到 CloudBase HTTP 云函数。

> **📋 前置要求**：如果您还没有创建 Django 项目，请先阅读 [Django 项目创建指南](./project-setup.md)。

## 📋 目录导航

- [准备部署文件](#准备部署文件)
- [项目结构](#项目结构)
- [部署步骤](#部署步骤)
- [访问应用](#访问应用)
- [常见问题](#常见问题)
- [性能优化](#性能优化)

---

## 准备部署文件

### 1. 创建启动脚本

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

### 2. 数据库配置

> ⚠️ **重要提醒**：云函数运行时目录不允许写文件，因此不能使用 SQLite 数据库。请确保配置外部数据库服务。

在 `settings.py` 中配置数据库：

```python
import os

# 数据库配置 - 禁止使用 SQLite
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

### 3. 环境变量配置

配置数据库连接环境变量：

```bash
export DB_HOST=your-database-host
export DB_NAME=cloudrun_django
export DB_USER=your-username
export DB_PASSWORD=your-password
export SECRET_KEY=your-secret-key
```

### 4. 依赖管理

确保 `requirements.txt` 包含必要依赖：

```txt
# Django 4.2 LTS - 兼容 SQLite 3.26+
Django==4.2.16
asgiref==3.7.2
psycopg2-binary==2.9.11
sqlparse==0.4.4
typing_extensions==4.15.0
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
├── scf_bootstrap            # 🔑 云函数启动脚本
└── third_party/                     # Python 依赖包
```

> 💡 **说明**：
> - `scf_bootstrap` 是 CloudBase 云函数的启动脚本
> - 设置 `PORT=9000` 环境变量确保应用监听云函数要求的端口
> - 设置 `PYTHONPATH` 环境变量确保应用能找到依赖包
> - 使用云函数运行时环境的 Python 解释器启动应用
> - **重要**：HTTP 云函数部署时需要包含 `third_party` 目录及其依赖包

## 部署步骤

### 通过控制台部署

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

### 通过 CLI 部署(敬请期待)

### 打包部署

如果需要手动打包：

```bash
# 创建部署包（包含 env 目录）
zip -r cloudrun-django-app.zip . -x ".git/*" "*.log" "Dockerfile" ".dockerignore" "__pycache__/*" "env/*"
```

## 访问应用

### 获取访问地址

部署成功后，您可以参考[通过 HTTP 访问云函数](https://docs.cloudbase.net/service/access-cloud-function)设置自定义域名访问 HTTP 云函数。

访问地址格式：`https://your-function-url/`

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
curl https://your-function-url/health/

# 获取用户列表
curl https://your-function-url/api/users/

# 分页查询
curl "https://your-function-url/api/users/?page=1&limit=2"

# 创建新用户
curl -X POST https://your-function-url/api/users/create/ \
  -H "Content-Type: application/json" \
  -d '{"name":"测试用户","email":"test@example.com"}'
```

## 常见问题

### Q: 部署后云函数无反应怎么办？

这是最常见的问题，请按以下步骤排查：

#### 🔍 快速诊断
1. **查看函数日志**：CloudBase 控制台 → 云函数 → 函数列表 → 点击函数名 → 日志标签页
2. **检查启动脚本权限**：确保 `scf_bootstrap` 有执行权限
3. **验证文件结构**：确保所有必要文件都在部署包中

#### 🛠️ 详细解决方案
**完整故障排除指南**：[SCF 云函数故障排除指南](./scf-troubleshooting.md)

**常见错误及解决方案**：

| 错误类型 | 错误信息 | 解决方案 |
|---------|---------|---------|
| 权限问题 | `Permission denied` | `chmod +x scf_bootstrap` |
| 模块缺失 | `ModuleNotFoundError` | 检查 PYTHONPATH 和依赖安装 |
| 端口占用 | `Address already in use` | 确保使用 9000 端口 |
| 超时问题 | `Task timed out` | 增加函数超时时间到 60 秒 |

#### 🔧 调试模式
使用调试启动脚本：
```bash
# 将 scf_bootstrap_debug 重命名为 scf_bootstrap
cp scf_bootstrap_debug scf_bootstrap
chmod +x scf_bootstrap
# 重新部署查看详细日志
```

### Q: 为什么 HTTP 云函数必须使用 9000 端口？
A: CloudBase HTTP 云函数要求应用监听 9000 端口，这是平台的标准配置。通过在 `scf_bootstrap` 中设置 `PORT=9000` 环境变量来控制端口，本地开发时默认使用 8080 端口。应用代码通过 `os.environ.get('PORT', 8080)` 实现端口的动态配置。

### Q: 数据库如何配置？
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

### Q: 虚拟环境依赖如何处理？
A: HTTP 云函数部署时需要包含 `env` 目录及其依赖包。在 `scf_bootstrap` 中通过 `PYTHONPATH` 环境变量指向虚拟环境的 site-packages 目录，确保应用能正确加载依赖。同时建议在虚拟环境中生成 `requirements.txt`，避免包含系统级包。

### Q: Django 静态文件如何处理？
A: HTTP 云函数环境中，建议将静态文件托管到 CDN 或对象存储，或者在 Django 设置中配置静态文件服务。可以使用 WhiteNoise 中间件处理静态文件：

```python
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',
    # ... 其他中间件
]
```

### Q: 如何处理 CSRF 保护？
A: API 接口可以使用 `@csrf_exempt` 装饰器禁用 CSRF 保护，或者配置 CSRF 令牌机制：

```python
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def api_view(request):
    # API 逻辑
    pass
```

### Q: 如何查看云函数日志？
A: 在 CloudBase 控制台的云函数页面，点击函数名称进入详情页查看运行日志。

### Q: 云函数支持哪些 Python 版本？
A: CloudBase 支持 Python 3.7、3.8、3.9、3.10、3.11 等版本，建议使用最新的稳定版本。

### 5. 部署前检查清单

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

## 性能优化

### 1. 减少冷启动时间

```python
# 全局变量缓存
import os
from django.conf import settings

# 缓存数据库连接配置
_db_config = None

def get_db_config():
    global _db_config
    if _db_config is None:
        _db_config = {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME'),
            'USER': os.environ.get('DB_USER'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    return _db_config
```

### 2. 依赖优化

```bash
# 只安装生产依赖
pip install --no-deps -r requirements.txt

# 清理不必要的文件
find . -name "*.pyc" -delete
find . -name "__pycache__" -type d -exec rm -rf {} +
```

### 3. 内存管理

```python
# 监控内存使用
import psutil
import logging

logger = logging.getLogger(__name__)

def log_memory_usage():
    process = psutil.Process()
    memory_info = process.memory_info()
    logger.info(f'Memory usage: {memory_info.rss / 1024 / 1024:.2f} MB')
```

### 4. 数据库连接优化

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
            'MAX_CONNS': 1,  # 限制连接数
            'connect_timeout': 10,
        },
        'CONN_MAX_AGE': 0,  # 不保持连接
    }
}
```

---

## 相关文档

- [返回主文档](../README.md)
- [云托管部署指南](./cloud-run.md)
- [CloudBase 官方文档](https://docs.cloudbase.net/)