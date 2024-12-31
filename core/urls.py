from django.urls import path
from core.views import base,home
urlpatterns = [
    # path('base/',base,name="base"),
    path('',home,name='home'),
]
