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
