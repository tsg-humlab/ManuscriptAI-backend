from django.urls import path

from .views import drop_classify_view



urlpatterns = [
    path('drop-classify', drop_classify_view, name='drop_classify'),
]