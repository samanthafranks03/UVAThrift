from django.contrib.auth.models import User as DjangoUser
from .models import Notification

def add_unread_count(request):
    # Add unread notification count to all templates
    unread_count = 0
    
    if request.session.get('user_data'):
        try:
            email = request.session['user_data']['email']
            user = DjangoUser.objects.get(username=email)
            unread_count = Notification.objects.filter(
                recipient=user, 
                is_read=False
            ).count()
        except DjangoUser.DoesNotExist:
            unread_count = 0
    
    return {'unread_count': unread_count}