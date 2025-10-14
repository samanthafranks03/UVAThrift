from django.shortcuts import render
from django.http import HttpResponse


def login(request):
    return HttpResponse("Hello, world. You're at the login page.")

def new_user(request):
    return HttpResponse("Hello new user, this is where to create a new account.")
