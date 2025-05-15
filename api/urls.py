from django.urls import path

from .views import drop_classify_view, process_view, send_manuscripts_view



urlpatterns = [
    path('drop-classify', drop_classify_view, name='drop_classify'),
    path('process', process_view, name='process'),
    path('send_manuscripts', send_manuscripts_view, name='send_manuscripts'),
]