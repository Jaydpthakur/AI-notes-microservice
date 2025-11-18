from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView
from .views import NoteViewSet, stats_view, task_status

router = DefaultRouter()
router.register(r'notes', NoteViewSet, basename='note')

urlpatterns = [
    path('', include(router.urls)),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('stats/', stats_view, name='stats'),
    path('tasks/<str:task_id>/', task_status, name='task_status'),
]
