class AllowIframeMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Gỡ bỏ hoặc sửa đổi X-Frame-Options ở đây
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'  # hoặc 'ALLOWALL'
        return response