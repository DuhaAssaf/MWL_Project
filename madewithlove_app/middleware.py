from .models import MerchantProfile, CustomerProfile

class SyncSessionMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        if user.is_authenticated and 'user_id' not in request.session:
            request.session['user_id'] = user.id
            request.session['username'] = user.username
            request.session['full_name'] = user.full_name
            request.session['role'] = user.role

            default_url = '/static/img/default-profile.png'
            profile_url = None

            if user.role == 'merchant':
                profile = MerchantProfile.objects.filter(user=user).first()
                if profile and profile.profile_picture:
                    profile_url = profile.profile_picture.url

            elif user.role == 'customer':
                profile = CustomerProfile.objects.filter(user=user).first()
                if profile and profile.profile_picture:
                    profile_url = profile.profile_picture.url

            request.session['profile_picture_url'] = profile_url or default_url

        response = self.get_response(request)
        return response
