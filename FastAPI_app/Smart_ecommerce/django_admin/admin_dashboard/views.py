import csv
from io import BytesIO
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum, Count
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import Order, Product, User

def dashboard_analytics(request):
    total_sales = Order.objects.filter(payment_status='completed').aggregate(Sum('total'))['total__sum'] or 0
    total_orders = Order.objects.count()
    low_stock_products = Product.objects.filter(stock__lt=10)
    
    context = {
        'total_sales': total_sales,
        'total_orders': total_orders,
        'low_stock_products': low_stock_products,
    }
    return render(request, 'dashboard/analytics.html', context)

def export_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_report.csv"'
    writer = csv.writer(response)
    writer.writerow(['Order ID', 'User ID', 'Total', 'Order Status', 'Payment Status', 'Created At'])
    for order in Order.objects.all():
        writer.writerow([order.id, order.user_id, order.total, order.order_status, order.payment_status, order.created_at])
    return response

def export_pdf(request):
    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.drawString(100, 750, "Sales & Order Summary Report")
    
    total_sales = Order.objects.filter(payment_status='completed').aggregate(Sum('total'))['total__sum'] or 0
    total_orders = Order.objects.count()
    
    p.drawString(100, 720, f"Total Orders: {total_orders}")
    p.drawString(100, 700, f"Total Completed Sales: ${total_sales:.2f}")
    
    p.showPage()
    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')