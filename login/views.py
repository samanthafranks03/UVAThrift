import os

from django.http import HttpResponse
from django.shortcuts import render, redirect
from django.views.decorators.csrf import csrf_exempt
from google.oauth2 import id_token
from google.auth.transport import requests


@csrf_exempt
def sign_in(request):
    return render(request, 'sign_in.html')


@csrf_exempt
def auth_receiver(request):
    """
    Google calls this URL after the user has signed in with their Google account.
    """
    print('Inside')
    token = request.POST['credential']

    try:
        user_data = id_token.verify_oauth2_token(
            token, requests.Request(), audience=os.environ['GOOGLE_OAUTH_CLIENT_ID']
        )
    except ValueError as e:
        print(e)
        return HttpResponse(status=403)


    from users.models import User
    # Does user exist in database yet?
    if User.objects.filter(email=user_data['email']).exists():
        # User exists
        print('User already exists')
        user = User.objects.get(email=user_data['email'])
        user.is_new_user = False
        user.save()
    else:
        # Create new user
        user = User(
            name=user_data.get('given_name'),
            email=user_data.get('email'),
            picture_url=user_data.get('picture'),
            is_new_user = True
        )
        user.save()

    request.session['user_data'] = user_data
    request.session['user_URL'] = user.get_absolute_url()

    return redirect('sign_in')


def sign_out(request):
    del request.session['user_data']
    return redirect('sign_in')