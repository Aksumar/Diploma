from django.conf import settings
from django.conf.urls.static import static
from django.urls import path

from . import views

urlpatterns = [
    path('', views.index, name="home"),
    path('analytics', views.analytics, name="analytics"),
    path('rule_choice', views.rule_choice, name="rule_choice"),
    path('campaign', views.campaign, name='campaign'),
    path('final', views.final, name='final')
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
