from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from django.shortcuts import get_object_or_404
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Model

from .responses import amis_success, amis_error
from .pagination import AmisPagination
from .utils import queryset_to_excel, queryset_to_csv

import pandas as pd
import inspect

class AmisModelViewSet(viewsets.ModelViewSet):
    """
    通用 AMIS 风格的 CRUD + 批量操作 + 导入导出
    自动检测模型所有字段作为筛选字段
    自动生成queryset和serializer_class
    """

    pagination_class = AmisPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = None  # 默认不设置，将在get_queryset中自动检测
    queryset = None  # 初始化queryset为None
    model = None  # 可以通过model属性直接指定模型类
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 如果没有设置queryset但设置了model，自动创建queryset
        if self.queryset is None and self.model is not None and issubclass(self.model, Model):
            self.queryset = self.model.objects.all().order_by('-id')
    
    def get_queryset(self):
        # 自动检测模型字段作为筛选字段
        if self.filterset_fields is None:
            # 获取模型类
            model = self._get_model_class()
            
            # 如果找到了模型，获取所有字段名
            if model and issubclass(model, Model):
                # 获取模型的所有字段名（包括自动生成的id字段）
                self.filterset_fields = [field.name for field in model._meta.get_fields() 
                                         if not field.is_relation]  # 排除关系字段，但包含普通字段和id字段
        
        # 如果没有设置queryset，尝试自动创建
        if not hasattr(self, 'queryset') or self.queryset is None:
            model = self._get_model_class()
            if model and issubclass(model, Model):
                # 默认按id降序排列
                self.queryset = model.objects.all().order_by('-id')
                return self.queryset
        
        return super().get_queryset()
        
    def _get_model_class(self):
        """
        获取模型类的辅助方法
        按优先级从queryset、serializer_class、model中获取
        """
        # 1. 从queryset获取
        if hasattr(self, 'queryset') and self.queryset is not None:
            return self.queryset.model
        # 2. 从serializer_class获取
        elif hasattr(self, 'serializer_class') and self.serializer_class is not None:
            return self.serializer_class.Meta.model if hasattr(self.serializer_class, 'Meta') else None
        # 3. 直接从model属性获取
        elif hasattr(self, 'model') and self.model is not None:
            return self.model
        return None
    
    def get_serializer_class(self):
        """
        自动创建序列化器类
        如果没有设置serializer_class，则根据模型自动生成
        """
        # 如果已经设置了serializer_class，则使用它
        if hasattr(self, 'serializer_class') and self.serializer_class is not None:
            return self.serializer_class
        
        # 尝试获取模型类
        model = None
        if hasattr(self, 'queryset') and self.queryset is not None:
            model = self.queryset.model
        elif hasattr(self, 'model') and self.model is not None:
            model = self.model
        
        # 如果找到了模型，动态创建序列化器类
        if model and issubclass(model, Model):
            # 生成序列化器类名
            serializer_name = f"{model.__name__}Serializer"
            
            # 检查当前类中是否已经存在该序列化器
            if serializer_name not in self.__class__.__dict__:
                # 动态创建序列化器类
                meta_class = type('Meta', (), {
                    'model': model,
                    'fields': "__all__"
                })
                
                serializer_class = type(serializer_name, (serializers.ModelSerializer,), {
                    'Meta': meta_class
                })
                
                # 将序列化器类添加到当前类的属性中，避免重复创建
                setattr(self.__class__, serializer_name, serializer_class)
            
            return getattr(self.__class__, serializer_name)
        
        # 如果无法获取模型，抛出异常
        raise AttributeError("Could not automatically determine serializer class. Please set 'serializer_class', 'queryset' or 'model'.")
        
    def options(self, request, *args, **kwargs):
        """
        支持前端 AMIS 发起 OPTIONS 预检请求
        """
        response = super().options(request, *args, **kwargs)
        # 如果跨域请求可以在这里加允许头
        response["access-control-allow-credentials"] = "true"
        response["Access-Control-Allow-Origin"] = "*"
        response["Access-Control-Allow-Methods"] = "GET,POST,PUT,PATCH,DELETE,OPTIONS,HEAD"
        response["Access-Control-Allow-Headers"] = "x-requested-with,content-type"
        return response

    # CRUD
    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(queryset, many=True)
        return amis_success(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset(), pk=kwargs.get("pk"))
        serializer = self.get_serializer(instance)
        return amis_success(serializer.data)

    def create(self, request, *args, **kwargs):
        # 排除 AMIS 发送的内部字段
        skip_fields = {"type", "api", "columns", "bulkActions","items", "itemActions"}
        data_fields = {k: v for k, v in request.data.items() if k not in skip_fields}

        # 获取模型的字段名列表
        model_fields = [field.name for field in self.get_queryset().model._meta.get_fields()]
        
        # 如果data_fields的字段不在模型字段名里则为查询
        if not any([k in model_fields for k in data_fields.keys()]):
            queryset = self.filter_queryset(self.get_queryset())
            page = self.paginate_queryset(queryset)
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset, many=True)
            return amis_success(serializer.data)

        # 否则按正常创建处理
        data = {k: v for k, v in data_fields.items() if v is not None}
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return amis_success(serializer.data, msg="创建成功")

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = get_object_or_404(self.get_queryset(), pk=kwargs.get("pk"))
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return amis_success(serializer.data, msg="更新成功")

    def destroy(self, request, *args, **kwargs):
        instance = get_object_or_404(self.get_queryset(), pk=kwargs.get("pk"))
        self.perform_destroy(instance)
        return amis_success(None, msg="删除成功")

    # 单个删除
    @action(detail=False, methods=["post"], url_path="delete")
    def single_delete(self, request, *args, **kwargs):
        # 从请求体获取id参数
        id_param = request.data.get("id")
        # 检查是否提供了id参数
        if id_param is None:
            return amis_error("缺少参数 id")
        # 尝试转换为整数
        try:
            pk = int(id_param)
        except (ValueError, TypeError):
            return amis_error("id参数必须是整数")
        # 检查对象是否存在
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        # 执行删除
        self.perform_destroy(instance)
        return amis_success(None, msg="删除成功")
    
    # 单个更新
    @action(detail=False, methods=["post"], url_path="update")
    def single_update(self, request, *args, **kwargs):
        # 从请求体获取id参数
        id_param = request.data.get("id")
        # 检查是否提供了id参数
        if id_param is None:
            return amis_error("缺少参数 id")
        # 尝试转换为整数
        try:
            pk = int(id_param)
        except (ValueError, TypeError):
            return amis_error("id参数必须是整数")
        # 检查对象是否存在
        instance = get_object_or_404(self.get_queryset(), pk=pk)
        
        # 更新对象
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return amis_success(serializer.data, msg="更新成功")
    
    # 批量删除
    @action(detail=False, methods=["post"], url_path="batch-delete")
    def bulk_delete(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        
        # 处理字符串格式的ids（如"33,32"）
        if isinstance(ids, str):
            # 按逗号分割字符串，并去除空格
            ids = [id_.strip() for id_ in ids.split(',') if id_.strip()]
    
        #如果没有ids 和 ”id“，则返回错误
        if not ids and "id" not in request.data:
            return amis_error("缺少参数 ids")

        # 如果ids和id都有，ids=ids；如果只有id，ids=[id]
        if ids and "id" in request.data:
            ids.append(request.data["id"])
        elif "id" in request.data:
            ids=[request.data["id"]]

        # 转换为整数列表
        try:
            ids = [int(id_) for id_ in ids]
        except (ValueError, TypeError):
            return amis_error("ids参数格式错误")
            
        queryset = self.get_queryset().filter(pk__in=ids)
        count = queryset.count()
        queryset.delete()
        return amis_success(None, msg=f"成功删除 {count} 条记录")

    # 批量更新
    @action(detail=False, methods=["post"], url_path="batch-update")
    def bulk_update(self, request, *args, **kwargs):
        ids = request.data.get("ids", [])
        data = request.data.get("data", {})
        if not ids or not data:
            return amis_error("缺少参数 ids 或 data")
        queryset = self.get_queryset().filter(pk__in=ids)
        updated = queryset.update(**data)
        return amis_success(None, msg=f"成功更新 {updated} 条记录")
    
    # 高级筛选
    @action(detail=False, methods=["post"], url_path="advanced-filter")
    def advanced_filter(self, request, *args, **kwargs):
        """
        高级筛选功能，支持复杂条件筛选
        请求体格式: {"filters": [{"field": "字段名", "operator": "操作符", "value": "值"}]}
        """
        filters = request.data.get("filters", [])
        
        # 获取基础查询集
        queryset = self.get_queryset()
        
        # 构建筛选条件
        filter_conditions = {}
        for filter_item in filters:
            field = filter_item.get("field")
            operator = filter_item.get("operator", "eq")
            value = filter_item.get("value")
            
            if field and value is not None:
                # 构建查询表达式
                if operator == "eq":
                    filter_conditions[field] = value
                elif operator == "contains":
                    filter_conditions[f"{field}__contains"] = value
                elif operator == "startswith":
                    filter_conditions[f"{field}__startswith"] = value
                elif operator == "endswith":
                    filter_conditions[f"{field}__endswith"] = value
                elif operator == "gt":
                    filter_conditions[f"{field}__gt"] = value
                elif operator == "gte":
                    filter_conditions[f"{field}__gte"] = value
                elif operator == "lt":
                    filter_conditions[f"{field}__lt"] = value
                elif operator == "lte":
                    filter_conditions[f"{field}__lte"] = value
                elif operator == "in":
                    filter_conditions[f"{field}__in"] = value if isinstance(value, list) else [value]
        
        # 应用筛选条件
        if filter_conditions:
            queryset = queryset.filter(**filter_conditions)
        
        # 应用分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return amis_success(serializer.data)

    # 模糊查询
    @action(detail=False, methods=["get"], url_path="fuzzy-search")
    def fuzzy_search(self, request, *args, **kwargs):
        """
        模糊查询功能，支持对模型的多个字段进行关键词搜索
        请求参数: keyword=搜索关键词&fields=字段1,字段2 (可选，默认为所有文本字段)
        """
        keyword = request.query_params.get("keyword")
        fields_param = request.query_params.get("fields")
        
        # 获取基础查询集
        queryset = self.get_queryset()
        
        if not keyword:
            # 没有关键词时返回空结果
            page = self.paginate_queryset(queryset.none())
            if page is not None:
                serializer = self.get_serializer(page, many=True)
                return self.get_paginated_response(serializer.data)
            serializer = self.get_serializer(queryset.none(), many=True)
            return amis_success(serializer.data)
        
        # 获取模型
        if hasattr(self, 'queryset') and self.queryset is not None:
            model = self.queryset.model
        elif hasattr(self, 'serializer_class'):
            model = self.serializer_class.Meta.model if hasattr(self.serializer_class, 'Meta') else None
        else:
            return amis_error("无法获取模型信息")
        
        # 确定要搜索的字段
        if fields_param:
            # 如果指定了字段，使用指定的字段
            search_fields = fields_param.split(',')
        else:
            # 否则使用所有文本类型的字段
            search_fields = []
            for field in model._meta.get_fields():
                # 只包括文本类型的字段（CharField, TextField等）
                if field.__class__.__name__ in ['CharField', 'TextField'] and not field.is_relation:
                    search_fields.append(field.name)
        
        # 构建模糊搜索条件
        from django.db.models import Q
        search_query = Q()
        for field in search_fields:
            if hasattr(model, field):
                search_query |= Q(**{f"{field}__icontains": keyword})
        
        # 应用搜索条件
        queryset = queryset.filter(search_query)
        
        # 应用分页
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(queryset, many=True)
        return amis_success(serializer.data)
    
    # 导出 Excel
    @action(detail=False, methods=["get"], url_path="export-excel")
    def export_excel(self, request, *args, **kwargs):
        fields = [f.name for f in self.queryset.model._meta.fields]
        return queryset_to_excel(self.get_queryset(), fields)

    # 导出 CSV
    @action(detail=False, methods=["get"], url_path="export-csv")
    def export_csv(self, request, *args, **kwargs):
        fields = [f.name for f in self.queryset.model._meta.fields]
        return queryset_to_csv(self.get_queryset(), fields)

    # 导入 Excel/CSV
    @action(detail=False, methods=["post"], url_path="import-data")
    def import_data(self, request, *args, **kwargs):
        file = request.FILES.get("file")
        if not file:
            return amis_error("缺少上传文件")

        ext = file.name.split(".")[-1].lower()
        try:
            if ext in ["xlsx", "xls"]:
                df = pd.read_excel(file)
            elif ext == "csv":
                df = pd.read_csv(file)
            else:
                return amis_error("仅支持 Excel/CSV 格式")

            model = self.queryset.model
            objs = [model(**row) for row in df.to_dict(orient="records")]
            model.objects.bulk_create(objs, ignore_conflicts=True)
            return amis_success(None, msg=f"成功导入 {len(objs)} 条记录")
        except Exception as e:
            return amis_error(f"导入失败: {str(e)}")
