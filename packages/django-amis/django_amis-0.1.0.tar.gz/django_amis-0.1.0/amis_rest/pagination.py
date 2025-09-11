from rest_framework.pagination import PageNumberPagination
from .responses import amis_success

class AmisPagination(PageNumberPagination):
    page_size_query_param = "perPage"
    page_query_param = "page"

    def get_paginated_response(self, data):
        return amis_success({
            "items": data,
            "total": self.page.paginator.count
        })
