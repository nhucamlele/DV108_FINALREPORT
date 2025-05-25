from django.urls import path
from . import views
from django.urls import path
from . import views
urlpatterns = [
    path('', views.dashboard_main, name='dashboard_main'),
    path('product/', views.dashboard_all_charts, name='dashboard'),
    path('sale/', views.sales_dashboard, name='dashboard'),
    path('customer/', views.customer_dashboard, name='dashboard'),
]
