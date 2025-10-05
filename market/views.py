from django.shortcuts import render
from django.http import HttpResponse

# Create your views here.
def home(request):
    return HttpResponse('<h1>This is gonna be the most swagalicious app anyone has ever seen sorry it took so long guys been having a rough weekend wompwomp but we on the comeup now</h1>')