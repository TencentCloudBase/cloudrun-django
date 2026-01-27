# SCF 云函数专用设置文件
import os
from .settings import *

# 云函数环境检测
SCF_RUNTIME = os.environ.get('SCF_RUNTIME_API') is not None

if SCF_RUNTIME:
    # 云函数环境配置
    DEBUG = False
    ALLOWED_HOSTS = ['*']
    
    # 数据库配置 - 解决 SQLite 版本问题
    if os.environ.get('DB_HOST'):
        # 使用外部数据库（推荐）
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('DB_NAME', 'cloudrun_django'),
                'USER': os.environ.get('DB_USER', 'postgres'),
                'PASSWORD': os.environ.get('DB_PASSWORD', ''),
                'HOST': os.environ.get('DB_HOST'),
                'PORT': os.environ.get('DB_PORT', '5432'),
                'OPTIONS': {
                    'connect_timeout': 10,
                },
            }
        }
    else:
        # 使用内存数据库（测试用）
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': ':memory:',
                'OPTIONS': {
                    'timeout': 20,
                },
            }
        }
    
    # 静态文件配置
    STATIC_ROOT = '/tmp/static/'
    MEDIA_ROOT = '/tmp/media/'
    
    # 缓存配置
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        }
    }
    
    # 日志配置
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
            'level': 'INFO',
        },
        'loggers': {
            'django': {
                'handlers': ['console'],
                'level': 'INFO',
                'propagate': False,
            },
        },
    }
    
    # 安全设置
    SECRET_KEY = os.environ.get('SECRET_KEY', 'scf-django-secret-key-change-in-production')
    
    # 禁用不必要的中间件
    MIDDLEWARE = [
        'django.middleware.security.SecurityMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
    ]
else:
    # 本地开发环境保持原有配置
    pass