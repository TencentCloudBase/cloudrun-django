# 快速部署 Django 应用

本篇文章为您介绍应用控制台的部署方案, 您可以通过以下操作完成部署。

## 模版部署 Django 应用

1、登录 [腾讯云托管控制台](https://tcb.cloud.tencent.com/dev#/platform-run/service/create?type=image)

2、点击通过模版部署，选择 ```Django 模版```

3、输入自定义服务名称，点击部署

4、等待部署完成之后，点击左上角箭头，返回到服务详情页

5、点击概述，获取默认域名并访问，会显示云托管默认首页

## 自定义部署 Django 应用

### 创建一个 Django 应用

要创建新的 Django 应用程序，请确保你的机器上安装了[Python](https://www.python.org/downloads/)和 Django。

按照以下步骤在目录中设置项目。

创建虚拟环境

```sh
python -m venv env
```

激活虚拟环境

```sh
source env/bin/activate
```

安装 Django

```sh
python -m pip install django
```

一切设置完成后，在终端运行以下命令来配置新的 Django 项目:

```sh
django-admin startproject cloudrun-django
```

此命令将创建一个名为`cloudrun-django`的新项目。

接下来，`cd` 进入目录并运行`python manage.py runserver`以启动项目。

打开浏览器并查看`http://127.0.0.1:8000`, 您将看到 Django 欢迎页面。

### 源码

[cloudrun-django](https://github.com/TencentCloudBase/tcbr-templates/tree/main/cloudrun-django)

### 部署到云托管

1、### 配置依赖项

创建 `requirements.txt` 文件:
要跟踪部署的所有依赖项，请创建一个`requirements.txt`文件:

```sh
pip freeze > requirements.txt
```

Note: 只有在虚拟环境中运行上述命令才是安全的，否则它将生成系统上所有安装的 python 包。可能导致云托管上无法启动该应用程序。

2、在cloudrun-django目录下创建一个名称为Dockerfile的新文件,内容如下:

```
FROM alpine:3.21.3

# 容器默认时区为UTC，如需使用上海时间请启用以下时区设置命令
RUN apk add tzdata && cp /usr/share/zoneinfo/Asia/Shanghai /etc/localtime && echo Asia/Shanghai > /etc/timezone

# 选用国内镜像源以提高下载速度
RUN sed -i 's/dl-cdn.alpinelinux.org/mirrors.tencent.com/g' /etc/apk/repositories \
&& apk add --update --no-cache python3 py3-pip gcc python3-dev linux-headers musl-dev \
&& rm -rf /var/cache/apk/*

# 使用 HTTPS 协议访问容器云调用证书安装
RUN apk add ca-certificates

# 拷贝当前项目到/app目录下(.dockerignore中文件除外)
COPY . /app

# 设定当前的工作目录
WORKDIR /app

# 安装依赖到指定的/install文件夹
# 选用国内镜像源以提高下载速度
RUN pip config set global.index-url http://mirrors.cloud.tencent.com/pypi/simple \
&& pip config set global.trusted-host mirrors.cloud.tencent.com \
&& pip install --upgrade pip --break-system-packages \
# pip install scipy 等数学包失败，可使用 apk add py3-scipy 进行， 参考安装 https://pkgs.alpinelinux.org/packages?name=py3-scipy&branch=v3.13
&& pip install --user -r requirements.txt --break-system-packages

# 执行启动命令
# 写多行独立的CMD命令是错误写法！只有最后一行CMD命令会被执行，之前的都会被忽略，导致业务报错。
# 请参考[Docker官方文档之CMD命令](https://docs.docker.com/engine/reference/builder/#cmd)
CMD ["python3", "manage.py", "runserver","0.0.0.0:8080"]
```

2、进入 [腾讯云托管](https://tcb.cloud.tencent.com/dev#/platform-run/service/create?type=package),

3、选择 ```通过本地代码``` 部署,

4、填写配置信息:

  * 代码包类型: 选择文件夹
  * 代码包: 点击选择 cloudrun-django 目录，并上传目录文件
  * 服务名称: 填写服务名称
  * 部署类型: 选择容器服务型
  * 端口: 默认填写 8080
  * 目标目录: 默认为空
  * Dockerfile 名称: Dockerfile
  * 环境变量: 如果有按需要填写
  * 公网访问: 默认打开
  * 内网访问: 默认关闭

5、配置填写完成之后，点击部署等待部署完成,

6、部署完成之后，跳转到服务概述页面，点击默认域名进行公网访问及测试。
