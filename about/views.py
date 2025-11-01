from django.shortcuts import render

# Create your views here.

def about(request):
    """
    About page:
    - Displays info about our app mission and policies
    - Allows users to understand the impact of second hand shopping
    """
    return render(request, "about.html")

