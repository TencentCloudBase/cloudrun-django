# cloudrun-django

## 快速开始

前往 [腾讯云托管快速开始页面](https://tcb.cloud.tencent.com/dev?envId=lowcode-9gms1m53798f7294#/platform-run),选择相应语言的模版，根据引导完成部署。

## 本地调试

## Dockerfile 最佳实践

请参考 [优化容器镜像](https://docs.cloudbase.net/run/develop/image-optimization)

## 目录结构说明

```
├── Dockerfile
├── README.md
├── cloudrun
│   ├── __init__.py
│   ├── asgi.py
│   ├── settings.py
│   ├── templates
│   │   └── static
│   │       └── html
│   │           └── index.html
│   ├── urls.py
│   ├── views.py
│   └── wsgi.py
├── manage.py
└── requirements.txt
```

## 服务 API 文档

### `GET /apis/users`

获取用户列表

### 请求参数

无

### 返回参数

- `total`: 用户总数
- `items`: 返回用户列表

### 返回结果示例

```json
{
  "total": 2,
  "items": [
    {
      "id": 0,
      "name": "zhangsan"
    },
    {
      "id": 1,
      "name": "lisi"
    }
  ]
}
```

### 调用示例

```curl https://<云托管域名>/apis/users```
