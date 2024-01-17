"""drams URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.0/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import include, path

#from allauth.account.views import login, logout

urlpatterns = [
    path('', include('data_management.urls')),
    #path('accounts/email/', login, name='disable_email'),
    #path('accounts/password/', login, name='disable_password'),
    #path('accounts/inactive/', login, name='disable_inactive'),
    #path('accounts/confirm-email/', login, name='disable_confirm_email'),
    #path('login/', login, name='account_login'),
    #path('logout/', logout, name='account_logout'),
    #path('signup/', login, name='account_signup'),
    #path('accounts/', include('allauth.urls')),
    path('grappelli', include('grappelli.urls')),
    path('admin/', admin.site.urls),
    path('', include('data_management.urls')),
    path('', include('social_django.urls', namespace='social'))
]
