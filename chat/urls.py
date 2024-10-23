from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('', views.index, name='chat'),  # Protected home page
    path('login/', views.login_view, name='login'),  # Login page
    path('register/', views.register, name='register'),  # Registration page
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # Logout view
]
