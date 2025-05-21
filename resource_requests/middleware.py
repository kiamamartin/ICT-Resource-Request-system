from django.shortcuts import redirect
from django.urls import resolve
from django.contrib import messages

class DirectorRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        # Director-only URLs
        self.director_urls = [
            'approve_request',
        ]

    def __call__(self, request):
        if not request.user.is_authenticated:
            return self.get_response(request)
            
        url_name = resolve(request.path_info).url_name
        
        if url_name in self.director_urls:
            # Check if user is director or admin
            is_director = False
            try:
                profile = request.user.profile
                is_director = profile.is_director() or profile.is_admin() or request.user.is_staff
            except:
                is_director = request.user.is_staff
                
            if not is_director:
                messages.error(request, "You don't have permission to access that page.")
                return redirect('dashboard')
                
        return self.get_response(request)