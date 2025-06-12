from django.urls import path

from . import views


urlpatterns = [
    path('drop-classify', views.drop_classify_view, name='drop_classify'),
    path('process', views.process_view, name='process'),
    path('send_manuscripts', views.send_manuscripts_view, name='send_manuscripts'),
    path('transform', views.transform_view, name='transform'),
    path('set-csrf-token', views.set_csrf_token, name='set_csrf_token'),
    path('login', views.login_view, name='login'),
    path('logout', views.logout_view, name='logout'),
    path('user', views.user, name='user'),
    path('register', views.register, name='register'),
]