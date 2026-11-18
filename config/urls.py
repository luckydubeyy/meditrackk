from django.contrib import admin
from django.urls import path
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('register/', views.register_view, name='register'),
    path('logout/', views.logout_view, name='logout'),
    
    # Patient
    path('patient/dashboard/', views.patient_dashboard, name='patient_dashboard'),
    path('patient/consultation/new/', views.new_consultation, name='new_consultation'),
    path('consultation/<int:case_id>/', views.case_detail, name='case_detail'),

    # Doctor
    path('doctor/dashboard/', views.doctor_dashboard, name='doctor_dashboard'),
    path('doctor/case/<int:case_id>/review/', views.review_case, name='review_case'),

    # Nearby Healthcare API
    path('api/nearby-places/', views.nearby_places_api, name='nearby_places_api'),
]
