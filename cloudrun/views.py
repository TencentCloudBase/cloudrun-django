import json

from django.http import JsonResponse
from django.shortcuts import render

def index(request, _):
    """
    获取主页

    ``` request ``` 请求对象
    """
    return render(request, 'static/html/index.html')

def getusers(request, _):
    """
    获取用户列表
    ``` request ``` 请求对象
    """
    rsp = JsonResponse({'total': 2, 'items': [{'id': 0, 'name': 'zhangsan'}, {'id': 1, 'name': 'lisi'}]}, json_dumps_params={'ensure_ascii': False})
    return rsp
