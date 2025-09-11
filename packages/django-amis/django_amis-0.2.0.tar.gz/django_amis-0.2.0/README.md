# Django AMIS

Django AMIS 是一个为 Django REST Framework 提供 AMIS 风格接口的工具包，简化了 RESTful API 的开发过程。

## 功能特性

- 自动生成查询集（queryset）和序列化器（serializer_class）
- 支持自动检测模型字段作为筛选字段
- 内置 AMIS 风格的响应格式化
- 支持数据导出（Excel、CSV）
- 可插拔的 Django 应用设计

## 安装

```bash
# 使用 uv 安装
uv install django-amis

# 或使用 pip
pip install django-amis
```

## 使用方法

1. 将 `amis_rest` 添加到你的 Django 项目的 `INSTALLED_APPS` 中：

```python
# settings.py
INSTALLED_APPS = [
    # ...
    'rest_framework',
    'django_filters',
    'amis_rest',
    # ...
]
```

2. 在你的视图中继承 `AmisModelViewSet`：

```python
# views.py
from amis_rest.views import AmisModelViewSet
from .models import YourModel

class YourModelViewSet(AmisModelViewSet):
    model = YourModel  # 设置模型类
    # 不需要手动设置 queryset 和 serializer_class
```

3. 在你的 URL 配置中注册视图集，注意需要指定 basename：

```python
# urls.py
from rest_framework.routers import DefaultRouter
from .views import YourModelViewSet

router = DefaultRouter()
router.register(r"your-models", YourModelViewSet, basename='yourmodel')

urlpatterns = [
    # ...
    *router.urls,
]
```

## 配置

Django AMIS 使用 Django REST Framework 的标准配置。你可以在 `settings.py` 中添加以下配置：

```python
# settings.py
REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'amis_rest.pagination.AmisPagination',
    'PAGE_SIZE': 10,
    # 其他 DRF 配置...
}
```

## 许可证

本项目使用 MIT 许可证。