import csv
import io
from django.shortcuts import render
from django.http import HttpResponse
from django.db.models import Sum
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from .models import CustomUser, Product, Order


def dashboard_analytics(request):
    # Aggregate total sales
    sales_data = Order.objects.aggregate(Sum('total'))
    total_sales = sales_data['total__sum'] or 0.0

    total_orders = Order.objects.count()
    total_users = CustomUser.objects.count()
    low_stock_products = Product.objects.filter(stock__lt=10)
    recent_orders = Order.objects.all().order_by('-id')[:10]

    context = {
        'total_sales': round(float(total_sales), 2),
        'total_orders': total_orders,
        'total_users': total_users,
        'low_stock_products': low_stock_products,
        'recent_orders': recent_orders,
    }
    return render(request, 'dashboard/analytics.html', context)


def export_orders_csv(request):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="orders_report.csv"'

    writer = csv.writer(response)
    writer.writerow(['Order ID', 'Customer Name', 'Email', 'Total Amount', 'Order Status', 'Payment Status', 'Date'])

    for o in Order.objects.all():
        cust_name = o.user.name if o.user else 'N/A'
        cust_email = o.user.email if o.user else 'N/A'
        writer.writerow([o.id, cust_name, cust_email, o.total, o.order_status, o.payment_status, o.created_at])

    return response


def export_orders_pdf(request):
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, 750, "Smart E-Commerce Sales & Orders Report")
    
    p.setFont("Helvetica-Bold", 10)
    y = 710
    p.drawString(50, y, "Order ID")
    p.drawString(120, y, "Customer")
    p.drawString(240, y, "Amount (INR)")
    p.drawString(340, y, "Order Status")
    p.drawString(450, y, "Payment")
    p.line(50, y - 5, 550, y - 5)

    p.setFont("Helvetica", 9)
    y -= 25
    for o in Order.objects.all()[:25]:
        cust_name = o.user.name if o.user else "N/A"
        p.drawString(50, y, str(o.id))
        p.drawString(120, y, str(cust_name)[:16])
        p.drawString(240, y, f"Rs. {o.total}")
        p.drawString(340, y, str(o.order_status))
        p.drawString(450, y, str(o.payment_status))
        y -= 20
        if y < 50:
            p.showPage()
            y = 750

    p.save()
    buffer.seek(0)
    return HttpResponse(buffer, content_type='application/pdf')