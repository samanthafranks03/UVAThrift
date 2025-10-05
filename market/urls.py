from django.urls import path
from . import views

urlpatterns = [
    path('', views.home, name='market-home'),
    # path('market/', include('market.urls')),
]