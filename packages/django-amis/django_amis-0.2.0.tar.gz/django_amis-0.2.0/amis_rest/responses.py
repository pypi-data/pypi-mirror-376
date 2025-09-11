from rest_framework.response import Response

def amis_success(data=None, msg="ok"):
    return Response({
        "status": 0,
        "msg": msg,
        "data": data
    })

def amis_error(msg="error", data=None):
    return Response({
        "status": 1,
        "msg": msg,
        "data": data
    })
