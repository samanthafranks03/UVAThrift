from .models import User as ProfileUser

def user_display_name(request):
    # Add display_name to all templates
    display_name = None
    
    if request.session.get('user_data'):
        email = request.session['user_data']['email']
        try:
            user = ProfileUser.objects.get(email=email)
            # Use nickname if set, otherwise use given_name from Google
            display_name = user.nickname if user.nickname else request.session['user_data']['given_name']
        except ProfileUser.DoesNotExist:
            display_name = request.session['user_data']['given_name']
    
    return {'display_name': display_name}