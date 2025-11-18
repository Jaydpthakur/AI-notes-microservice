from django.urls import path, include
from django.contrib import admin
from django.conf import settings

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from graphene_django.views import GraphQLView

urlpatterns = [
    path('', include('django_prometheus.urls')),
    path('admin/', admin.site.urls),
    path('api/', include('notes.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('graphql/', GraphQLView.as_view(graphiql=True)),
]
