from django.urls import path
from . import views

urlpatterns = [
    path('', views.dashboard_analytics, name='dashboard_analytics'),
    path('export/csv/', views.export_csv, name='export_csv'),
    path('export/pdf/', views.export_pdf, name='export_pdf'),
]