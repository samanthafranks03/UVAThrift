# REFERENCES:
# Google Sign-In w/ Django App: https://tomdekan.com/articles/google-sign-in
#   * Use: Overall layout and template for integrating Google Sign-In for the project
# Copilot
#   * Use: Fixing unknown errors, additional Django reference, HTML assistance

import os

from typing import Any
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

    user = add_update_user(user_data)

    # List of admin email addresses
    ADMIN_EMAILS = [
        'heba.ahmed.ha1215@gmail.com',
        'shofu360@gmail.com',
        'samantha.franks70@gmail.com',
        'nadellasrikar@gmail.com',
        'daniel815jimenez@gmail.com',
        'dummymcdumdum7@gmail.com'
    ]

    request.session['user_data'] = user_data
    request.session['user_URL'] = user.get_absolute_url()
    request.session['is_admin'] = user_data['email'] in ADMIN_EMAILS

    return redirect('market-home')


def add_update_user(user_data: dict[str, Any]):
    from users.models import User
    from django.contrib.auth.models import User as DjangoUser

    # List of admin email addresses
    ADMIN_EMAILS = [
        'heba.ahmed.ha1215@gmail.com',
        'shofu360@gmail.com',
        'samantha.franks70@gmail.com',
        'nadellasrikar@gmail.com',
        'daniel815jimenez@gmail.com',
        'dummymcdumdum7@gmail.com'
    ]
    
    is_admin = user_data['email'] in ADMIN_EMAILS

    # Does user exist in database yet?
    if User.objects.filter(email=user_data['email']).exists():
        # User exists
        print('User already exists')
        user = User.objects.get(email=user_data['email'])
        user.is_new_user = False
        user.is_admin = is_admin  # Update admin status
        user.save()
    else:
        # Create new user
        user = User(
            name=user_data.get('given_name'),
            nickname=user_data.get('given_name'),
            email=user_data.get('email'),
            picture=user_data.get('picture'),
            is_new_user = True,
            is_admin = is_admin
        )
        user.save()

    # Create or get Django User for messaging system
    django_user, created = DjangoUser.objects.get_or_create(
        username=user_data['email'],
        defaults={
            'email': user_data['email'],
            'first_name': user_data.get('given_name', ''),
            'last_name': user_data.get('family_name', ''),
        }
    )

    return user


def sign_out(request):
    del request.session['user_data']
    return redirect('sign_in')

########## Admin Views ##########

# feature that allows admin to view all users and ban users
from users.models import User
from django.views.decorators.csrf import csrf_protect

@csrf_protect
def admin_panel(request):
    # Only allow admins
    if not request.session.get('is_admin', False):
        return HttpResponse('Forbidden', status=403)

    # Get all users
    users = User.objects.all()

    # Get flagged posts count
    from posts.models import Post, PostFlag
    from django.db.models import Count
    flagged_posts_count = Post.objects.annotate(
        flag_count_db=Count('postflag')
    ).filter(flag_count_db__gt=0).count()

    context = {
        'users': users,
        'flagged_posts_count': flagged_posts_count
    }
    return render(request, 'admin_panel.html', context)


@csrf_protect
def ban_user(request):
    # Only allow admins
    if not request.session.get('is_admin', False):
        return HttpResponse('Forbidden', status=403)
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            user.is_flagged = True
            user.save()
        except User.DoesNotExist:
            pass
    return redirect('admin_panel')


@csrf_protect
def unban_user(request):
    # Only allow admins
    if not request.session.get('is_admin', False):
        return HttpResponse('Forbidden', status=403)
    if request.method == 'POST':
        email = request.POST.get('email')
        try:
            user = User.objects.get(email=email)
            user.is_flagged = False
            user.save()
        except User.DoesNotExist:
            pass
    return redirect('admin_panel')