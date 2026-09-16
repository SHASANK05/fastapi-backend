from django.contrib import admin
from django.urls import path
from admin_dashboard import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('dashboard/', views.dashboard_analytics, name='analytics_dashboard'),
    path('export/orders/csv/', views.export_orders_csv, name='export_orders_csv'),
    path('export/orders/pdf/', views.export_orders_pdf, name='export_orders_pdf'),
]
