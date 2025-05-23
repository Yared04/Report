from users.views import OrganizationView, CustomUserViewSet
from django.urls import path


urlpatterns = [
    path('organizations/', OrganizationView.as_view(), name='organization-list'),
    path('users/', CustomUserViewSet.as_view({'get': 'list', 'post': 'create', 'patch': 'partial_update', 'delete': 'destroy'}), name='user-list'),

]
