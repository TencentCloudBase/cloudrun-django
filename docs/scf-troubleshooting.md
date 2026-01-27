# SCF 云函数故障排除指南

当 SCF 云函数部署后无反应时，请按照以下步骤进行排查。

## 🔍 问题诊断步骤

### 1. 检查函数日志

在 CloudBase 控制台查看函数执行日志：

1. 进入 CloudBase 控制台
2. 选择 "云函数" → "函数列表"
3. 点击你的函数名称
4. 查看 "日志" 标签页

**常见错误信息**：
```bash
# 启动脚本权限问题
/bin/bash: ./scf_bootstrap: Permission denied

# Python 路径问题
ModuleNotFoundError: No module named 'django'

# 端口占用问题
OSError: [Errno 98] Address already in use

# 超时问题
Task timed out after 30.00 seconds
```

### 2. 使用调试启动脚本

将 `scf_bootstrap_debug` 重命名为 `scf_bootstrap` 进行调试：

```bash
# 本地测试
cp scf_bootstrap_debug scf_bootstrap
chmod +x scf_bootstrap

# 重新打包部署
```

### 3. 检查文件结构

确保部署包包含以下文件：

```
deployment-package/
├── manage.py                    # Django 管理脚本
├── scf_bootstrap               # 启动脚本（必须有执行权限）
├── cloudrun/                   # Django 项目目录
├── api/                        # Django 应用目录
├── requirements.txt            # 依赖文件
└── env/                        # 虚拟环境目录
    └── lib/
        └── python3.10/
            └── site-packages/  # 所有依赖包
```

## 🛠️ 常见问题解决方案

### 问题 1: 启动脚本无执行权限

**错误信息**：
```
/bin/bash: ./scf_bootstrap: Permission denied
```

**解决方案**：
```bash
# 本地设置权限
chmod +x scf_bootstrap

# 或在启动脚本中自动设置
echo "chmod +x /var/user/scf_bootstrap" >> scf_bootstrap
```

### 问题 2: Django 模块找不到

**错误信息**：
```
ModuleNotFoundError: No module named 'django'
```

**解决方案**：

1. **检查依赖安装**：
```bash
# 确保依赖安装到正确目录
pip install -r requirements.txt -t env/lib/python3.10/site-packages/
```

2. **修正 PYTHONPATH**：
```bash
export PYTHONPATH="/var/user:/var/user/env/lib/python3.10/site-packages:$PYTHONPATH"
```

### 问题 3: 端口配置错误

**错误信息**：
```
OSError: [Errno 98] Address already in use
```

**解决方案**：
```bash
# 确保使用 9000 端口
export PORT=9000
/var/lang/python310/bin/python3.10 manage.py runserver 0.0.0.0:9000
```

### 问题 4: 数据库连接问题

**错误信息**：
```
django.db.utils.OperationalError: could not connect to server
```

**解决方案**：

1. **配置环境变量**：
```bash
# 在云函数控制台设置环境变量
DB_HOST=your-database-host
DB_NAME=your-database-name
DB_USER=your-username
DB_PASSWORD=your-password
```

2. **使用内存数据库（测试用）**：
```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': ':memory:',
    }
}
```

### 问题 5: 函数超时

**错误信息**：
```
Task timed out after 30.00 seconds
```

**解决方案**：

1. **增加超时时间**：
   - 在云函数控制台将超时时间设置为 60 秒或更长

2. **优化启动时间**：
```python
# settings.py - 禁用不必要的中间件
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    # 注释掉不需要的中间件
]

# 禁用调试模式
DEBUG = False
```

### 问题 6: 静态文件问题

**解决方案**：
```python
# settings.py
import os

# 静态文件配置
STATIC_URL = '/static/'
STATIC_ROOT = '/tmp/static/'  # 使用 /tmp 目录

# 在启动前收集静态文件
# python manage.py collectstatic --noinput
```

## 📋 部署检查清单

部署前请确认以下项目：

- [ ] `scf_bootstrap` 文件存在且有执行权限
- [ ] `requirements.txt` 包含所有必要依赖
- [ ] 依赖已安装到 `env/lib/python3.10/site-packages/`
- [ ] Django 设置中端口配置为 9000
- [ ] 数据库配置正确（避免使用 SQLite 文件）
- [ ] 静态文件配置正确
- [ ] 函数超时时间设置合理（建议 60 秒）

## 🔧 调试技巧

### 1. 本地模拟云函数环境

```bash
# 创建模拟环境
mkdir -p /tmp/scf-test
cp -r . /tmp/scf-test/
cd /tmp/scf-test

# 设置环境变量
export PYTHONPATH="/tmp/scf-test:/tmp/scf-test/env/lib/python3.10/site-packages:$PYTHONPATH"
export PORT=9000

# 测试启动
./scf_bootstrap
```

### 2. 逐步调试

```bash
# 1. 测试 Python 环境
/var/lang/python310/bin/python3.10 --version

# 2. 测试 Django 导入
/var/lang/python310/bin/python3.10 -c "import django; print(django.get_version())"

# 3. 测试项目检查
/var/lang/python310/bin/python3.10 manage.py check

# 4. 测试启动（不绑定端口）
/var/lang/python310/bin/python3.10 manage.py runserver --help
```

### 3. 日志增强

在 `scf_bootstrap` 中添加详细日志：

```bash
#!/bin/bash
exec > >(tee -a /tmp/scf_bootstrap.log) 2>&1
echo "$(date): Starting SCF bootstrap"
echo "Working directory: $(pwd)"
echo "Python path: $PYTHONPATH"

# 你的启动命令...
```

### 问题 7: SQLite 版本不兼容

**错误信息**：
```
django.db.utils.NotSupportedError: SQLite 3.31 or later is required (found 3.26.0).
```

**根本原因**：
- Django 5.x 要求 SQLite 3.31+
- 腾讯云函数环境中的 SQLite 版本是 3.26.0
- 版本不兼容导致无法启动

**解决方案**：

#### 方案 A：降级 Django 版本（推荐）
```txt
# requirements.txt - 使用 Django 4.2 LTS
Django==4.2.16
asgiref==3.7.2
psycopg2-binary==2.9.11
sqlparse==0.4.4
typing_extensions==4.15.0
```

#### 方案 B：使用外部数据库
```python
# settings_scf.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME', 'cloudrun_django'),
        'USER': os.environ.get('DB_USER', 'postgres'),
        'PASSWORD': os.environ.get('DB_PASSWORD', ''),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
    }
}
```

#### 方案 C：兼容性检查
```bash
# 运行兼容性检查脚本
python check_compatibility.py
```

## 📞 获取帮助

如果问题仍然存在：

1. 运行兼容性检查：`python check_compatibility.py`
2. 查看 [Django HTTP 云函数部署指南](./http-function.md)
3. 检查 CloudBase 官方文档
4. 在控制台提交工单获取技术支持