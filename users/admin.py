from django.contrib import admin

# Register your models here.
from .models import User, Admin

admin.site.register(User)
admin.site.register(Admin)
