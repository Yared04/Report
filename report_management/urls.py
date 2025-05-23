from .views import  DatabaseView, NodeView
from django.urls import path


urlpatterns = [
    # path('query/', QueryView.as_view(), name='query-list'),
    path('database/', DatabaseView.as_view(), name='database-list'),
    path('node/', NodeView.as_view(), name='node-list'),
]
