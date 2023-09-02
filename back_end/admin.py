from django.contrib import admin
from .models import User  # Assuming User is in models.py in the back_end app

admin.site.register(User)