def base_permission(request):
    return request.user.is_authenticated and request.user.is_staff