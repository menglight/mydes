from django.urls import path
from . import views

app_name = 'dashboard_app'  # Define app_name for namespacing

urlpatterns = [
    # path('', views.index, name='index'),  # Example path
    path('login/', views.login_view, name='login'),
    path('logout/', views.logout_view, name='logout'),
    path('pic_all/', views.pic_all, name='pic_all'),
    path('map_pro/', views.map_pro, name='map_pro'),
    path('pie_pro/', views.pie_pro, name='pie_pro'),
    path('line_pro/', views.line_pro, name='line_pro'),
    path('table_pro/', views.table_pro, name='table_pro'),
    path('radar_pro/', views.radar_pro, name='radar_pro'),
]
