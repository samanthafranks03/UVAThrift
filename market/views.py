from django.shortcuts import render, redirect
from django.http import HttpResponse
from users.models import User

# Create your views here.
def home(request):
    #if a logged-in user is banned, redirect them to their profile page
    user_data = request.session.get('user_data')
    if user_data:
        email = user_data.get('email')
        try:
            u = User.objects.get(email=email)
            if u.is_flagged:
                # Ensure we have their profile URL in session
                user_url = request.session.get('user_URL') or u.get_absolute_url()
                request.session['user_URL'] = user_url
                return redirect(user_url)
        except User.DoesNotExist:
            pass

    return render(request, 'home_page.html')