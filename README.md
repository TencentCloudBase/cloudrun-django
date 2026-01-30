# 快速部署 Django 应用

一个完整的 Django 应用模板，支持快速部署到 CloudBase 平台。

## 🚀 快速开始

### 前置条件

- [Python 3.10](https://www.python.org/downloads/) 或更高版本
- 了解基本的 Python 虚拟环境使用
- 腾讯云账号并开通了 CloudBase 服务
- 基本的 Python 和 Django 开发知识

### 创建应用

> **📋 详细指南**：完整的项目创建步骤请参考 [Django 项目创建指南](./docs/project-setup.md)

```bash
# 快速创建（基础步骤）
mkdir cloudrun-django && cd cloudrun-django
python -m venv env
source env/bin/activate  # Windows: env\Scripts\activate
pip install Django==4.2.16 psycopg2-binary==2.9.11
django-admin startproject cloudrun .
python manage.py startapp api
```

### 本地测试

```bash
# 启动开发服务器
python manage.py runserver 0.0.0.0:8080

# 访问应用
open http://localhost:8080
```

## 📦 项目结构

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
├── .gitignore              # Git 忽略文件
├── third_party             # Python 依赖安装目录，HTTP 云函数必须将依赖一同打包，并不会自己下载依赖
├── scf_bootstrap           # HTTP 云函数启动脚本
├── Dockerfile              # 云托管容器配置
└── .dockerignore           # Docker 忽略文件
```

## 🎯 部署方式

### 部署方式对比

| 特性 | HTTP 云函数 | 云托管 |
|------|------------|--------|
| **计费方式** | 按请求次数和执行时间 | 按资源使用量（CPU/内存） |
| **启动方式** | 冷启动，按需启动 | 持续运行 |
| **适用场景** | API 服务、轻量级应用 | 企业级应用、复杂 Web 应用 |
| **端口要求** | 固定 9000 端口 | 可自定义端口（默认 8080） |
| **扩缩容** | 自动按请求扩缩 | 支持自动扩缩容配置 |
| **Python 环境** | 预配置 Python 运行时 | 完全自定义 Python 环境 |

### 选择部署方式

- **选择 HTTP 云函数**：轻量级 API 服务、间歇性访问、成本敏感
- **选择云托管**：企业级应用、复杂 Web 应用、需要更多控制权

## 📚 详细部署指南

### 🔥 HTTP 云函数部署

适合轻量级应用和 API 服务，按请求计费，冷启动快。

**重要提醒**：云函数运行时目录不允许写文件，因此不能使用 SQLite 数据库。

**快速部署步骤：**
1. 创建 `scf_bootstrap` 启动脚本
2. 配置外部数据库连接
3. 安装依赖 ```pip3 install -r requirements.txt -t third_party```, 安装包必须包含依赖
4. 通过 CloudBase 控制台上传部署

[📖 查看详细的 HTTP 云函数部署指南](./docs/http-function.md)

### 🐳 云托管部署

适合企业级应用，支持更复杂的部署需求，容器化部署。

**快速部署步骤：**
1. 创建 `Dockerfile` 容器配置
2. 配置 `.dockerignore` 文件
3. 设置数据库和静态文件
4. 通过 CloudBase 控制台或 CLI 部署

[📖 查看详细的云托管部署指南](./docs/cloud-run.md)

## 🔧 API 接口

本模板包含以下 RESTful API 接口：

### 健康检查
```bash
GET /health/
```

### 用户管理
```bash
GET /api/users/              # 获取用户列表（支持分页）
GET /api/users/1/            # 获取单个用户
POST /api/users/create/      # 创建用户
PUT /api/users/1/update/     # 更新用户
DELETE /api/users/1/delete/  # 删除用户
```

### 示例请求

```bash
# 健康检查
curl https://your-app-url/health/

# 获取用户列表
curl https://your-app-url/api/users/

# 创建新用户
curl -X POST https://your-app-url/api/users/create/ \
  -H "Content-Type: application/json" \
  -d '{"name":"测试用户","email":"test@example.com"}'
```

## ❓ 常见问题

### 数据库配置
- **HTTP 云函数**：禁止使用 SQLite，必须配置外部数据库
- **云托管**：支持各种数据库，推荐 PostgreSQL

### 端口配置
- **HTTP 云函数**：必须使用 9000 端口
- **云托管**：推荐使用 8080 端口，支持自定义

### 文件要求
- **HTTP 云函数**：需要 `scf_bootstrap` 启动脚本和 `env` 目录
- **云托管**：需要 `Dockerfile` 和 `.dockerignore`

### 如何选择部署方式？
- **轻量级应用**：选择 HTTP 云函数
- **企业级应用**：选择云托管
- **成本敏感**：选择 HTTP 云函数
- **需要持续运行**：选择云托管

## 🔗 相关链接

### 📚 项目文档
- [Django 项目创建指南](./docs/project-setup.md) - 从零开始创建项目
- [HTTP 云函数部署指南](./docs/http-function.md) - 云函数部署详细步骤
- [云托管部署指南](./docs/cloud-run.md) - 云托管部署详细步骤

### 🌐 官方文档
- [CloudBase 官方文档](https://docs.cloudbase.net/)
- [Django 官方文档](https://docs.djangoproject.com/)
- [Python 官方文档](https://docs.python.org/)

## 📄 许可证

本项目采用 MIT 许可证。详情请查看 [LICENSE](./LICENSE) 文件。

---

**需要帮助？** 

- 查看 [HTTP 云函数部署指南](./docs/http-function.md)
- 查看 [云托管部署指南](./docs/cloud-run.md)
- 访问 [CloudBase 官方文档](https://docs.cloudbase.net/)