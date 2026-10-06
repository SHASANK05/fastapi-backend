from django.urls import path
from .views import CardListCreateView

urlpatterns = [
    path('', CardListCreateView.as_view(), name='card-list-create'),
]