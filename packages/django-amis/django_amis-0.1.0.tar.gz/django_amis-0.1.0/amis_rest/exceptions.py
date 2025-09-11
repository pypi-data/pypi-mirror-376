from rest_framework.views import exception_handler
from .responses import amis_error

def amis_exception_handler(exc, context):
    """
    全局异常处理，返回 AMIS 风格的错误信息
    """
    response = exception_handler(exc, context)

    if response is not None:
        msg = response.data.get("detail", str(exc))
        return amis_error(msg=msg)

    return amis_error(msg=str(exc))
